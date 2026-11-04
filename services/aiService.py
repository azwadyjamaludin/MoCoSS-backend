import json
import logging
import os
import re
import shutil
import subprocess
import tempfile
import time
from collections import defaultdict, deque

from fastapi import HTTPException

log = logging.getLogger("mocoss.ai")

PROMPT_VERSION = "v1"
DEFAULT_MODEL = "gemini-3.6-flash"
INLINE_LIMIT_BYTES = 15 * 1024 * 1024  # inline request limit is 20 MB in total, keep headroom for the prompt

MIME_BY_EXT = {
    ".mp3": "audio/mp3", ".wav": "audio/wav", ".aac": "audio/aac", ".ogg": "audio/ogg",
    ".flac": "audio/flac", ".m4a": "audio/mp4",
}


class AiError(Exception):
    """Raised when the AI step fails. The message is safe to store and show to users."""


def _model() -> str:
    return os.getenv("GEMINI_MODEL", DEFAULT_MODEL)


def is_mock() -> bool:
    return os.getenv("AI_MOCK", "").strip().lower() == "true" or not os.getenv("GEMINI_API_KEY")


def _client():
    try:
        from google import genai
    except ImportError as e:  # pragma: no cover
        raise AiError("AI library is not installed on the server.") from e
    return genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


_calls = defaultdict(deque)


def check_rate_limit(user_id: int) -> None:
    limit = int(os.getenv("AI_MAX_PER_HOUR", "30"))
    now = time.time()
    window = _calls[user_id]
    while window and now - window[0] > 3600:
        window.popleft()
    if len(window) >= limit:
        raise HTTPException(status_code=429, detail="AI request limit reached. Try again later.")
    window.append(now)


_EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
_IC = re.compile(r"\b\d{6}-?\d{2}-?\d{4}\b")
_PHONE = re.compile(r"(?<!\d)(?:\+?6?0)1\d[- ]?\d{3,4}[- ]?\d{4}(?!\d)")


def scrub_text(text) -> str:
    if not text:
        return ""
    text = _EMAIL.sub("[email]", text)
    text = _IC.sub("[id number]", text)
    return _PHONE.sub("[phone]", text)


def _prepare_audio(path: str, workdir: str) -> str:
    ffmpeg = shutil.which("ffmpeg")
    ext = os.path.splitext(path)[1].lower()
    if ffmpeg:
        out = os.path.join(workdir, "audio.mp3")
        result = subprocess.run(
            [ffmpeg, "-y", "-i", path, "-vn", "-ac", "1", "-ar", "16000", "-b:a", "48k", out],
            capture_output=True, timeout=600,
        )
        if result.returncode == 0 and os.path.exists(out):
            return out
        log.warning("ffmpeg failed: %s", result.stderr[-300:].decode("utf-8", "ignore"))
    if ext in MIME_BY_EXT:
        return path
    raise AiError("Could not read the recording. The server needs ffmpeg to process video or this audio format.")


def _parse_json(raw: str) -> dict:
    raw = (raw or "").strip()
    raw = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw)
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        raise AiError("The AI returned an unreadable answer.") from e
    if not isinstance(data, dict):
        raise AiError("The AI returned an unexpected answer.")
    return data


def _string_list(value, limit=8):
    if not isinstance(value, list):
        return []
    return [str(v).strip() for v in value if str(v).strip()][:limit]


_SESSION_PROMPT = """You are an experienced counseling supervisor giving feedback to a counseling trainee in Malaysia.
Listen to this {kind} counseling session recording and notes, then respond with JSON only.

Rules:
- Comment on the COUNSELOR's practice: rapport, active listening, questioning, reflection of feeling, structure,
  pacing, use of silence, and ethical practice (consent, confidentiality, boundaries, cultural and religious sensitivity).
- Base every point on what you actually heard. Do not invent events.
- Never repeat names, places or other identifying details. Refer to "the client" or "a member".
- Do not diagnose the client or give clinical conclusions. You are giving training feedback, not treatment advice.
- Be specific, kind and practical. Keep each item to one or two sentences.
- Write the feedback values in {language_name}. Keep the JSON keys in English.

Counselor's own notes (may be empty): {notes}

Return JSON with exactly these keys:
{{
  "transcript": "a faithful transcript with speaker labels Counselor / Client (or Member 1, 2... for groups). Replace any names with [name].",
  "summary": "2-3 sentence overview of the session",
  "strengths": ["..."],
  "areas_to_improve": ["..."],
  "skills_observed": ["micro-skills you heard, e.g. open questions, paraphrasing"],
  "ethical_flags": ["anything the supervisor should look at, or an empty list"],
  "questions_for_supervision": ["questions the trainee could bring to supervision"]
}}"""

_SECTION_GUIDE = {
    "concern": "Presenting concern: what the client brings and why now.",
    "background": "Background and history: family, education, work and relevant history, with no identifying details.",
    "assessment": "Assessment: observations, measures used and risk level.",
    "formulation": "Case formulation: theory-based understanding covering precipitating, maintaining and protective factors.",
    "plan": "Intervention plan: goals, approach and how progress is measured.",
    "ethics": "Ethical and cultural considerations: consent, confidentiality, cultural and religious factors.",
}

_SECTION_PROMPT = """You help a counseling trainee in Malaysia draft one section of a case analysis.
Section: {guide}
Case code: {case_ref}

Material the trainee has written (may be empty):
{current_text}

Notes from linked sessions (may be empty):
{notes}

Write a clear first draft of this section in {language_name}, 80 to 150 words, as plain text with no headings.
Rules: use only the material above and mark gaps as "[to be completed]". Do not invent facts about the client.
Never include names or identifying details. Do not diagnose. The trainee will review and edit your draft."""


def _language_name(language: str) -> str:
    return "Bahasa Malaysia" if (language or "").upper() == "BM" else "English"


def analyze_session(media_path: str, notes, kind: str, language: str = "EN") -> dict:
    """Transcribe a session recording and produce structured supervision feedback.

    Returns {"transcript": str, "feedback": dict, "model": str, "prompt_version": str, "is_mock": bool}.
    """
    if is_mock():
        return _mock_session(language)

    prompt = _SESSION_PROMPT.format(
        kind=kind, notes=scrub_text(notes) or "none", language_name=_language_name(language)
    )
    with tempfile.TemporaryDirectory() as workdir:
        audio_path = _prepare_audio(media_path, workdir)
        mime = MIME_BY_EXT.get(os.path.splitext(audio_path)[1].lower(), "audio/mp3")
        data = _generate_with_audio(audio_path, mime, prompt)

    feedback = {
        "summary": str(data.get("summary", "")).strip(),
        "strengths": _string_list(data.get("strengths")),
        "areas_to_improve": _string_list(data.get("areas_to_improve")),
        "skills_observed": _string_list(data.get("skills_observed")),
        "ethical_flags": _string_list(data.get("ethical_flags")),
        "questions_for_supervision": _string_list(data.get("questions_for_supervision")),
        "is_mock": False,
    }
    if not feedback["summary"] and not feedback["strengths"]:
        raise AiError("The AI did not return usable feedback.")
    return {
        "transcript": str(data.get("transcript", "")).strip(),
        "feedback": feedback, "model": _model(), "prompt_version": PROMPT_VERSION, "is_mock": False,
    }


def _generate_with_audio(audio_path: str, mime: str, prompt: str) -> dict:
    from google.genai import types

    client = _client()
    config = types.GenerateContentConfig(response_mime_type="application/json", temperature=0.2)
    remote = None
    try:
        if os.path.getsize(audio_path) <= INLINE_LIMIT_BYTES:
            with open(audio_path, "rb") as f:
                part = types.Part.from_bytes(data=f.read(), mime_type=mime)
            contents = [prompt, part]
        else:
            remote = client.files.upload(file=audio_path, config=types.UploadFileConfig(mime_type=mime))
            contents = [prompt, remote]

        last_error = None
        for attempt in range(2):  # one retry for transient failures
            try:
                response = client.models.generate_content(model=_model(), contents=contents, config=config)
                return _parse_json(response.text)
            except AiError:
                raise
            except Exception as e:  # network, quota, server errors
                last_error = e
                log.warning("Gemini call failed (attempt %s): %s", attempt + 1, e)
                time.sleep(2)
        raise AiError("The AI service is unavailable right now.") from last_error
    finally:
        if remote is not None:  # do not leave the recording stored with the provider
            try:
                client.files.delete(name=remote.name)
            except Exception:  # pragma: no cover
                log.warning("Could not delete uploaded file %s", remote.name)


def draft_case_section(section: str, case_ref, current_text, notes: list, language: str = "EN") -> dict:
    """Draft one case-analysis section. Returns {"draft": str, "is_mock": bool}."""
    guide = _SECTION_GUIDE.get(section)
    if guide is None:
        raise HTTPException(status_code=422, detail="Unknown section.")
    if is_mock():
        label = "[Sample draft: AI is not configured] "
        text = "Rangka contoh bahagian ini. Isi butiran sebenar." if _language_name(language).startswith("Bahasa") \
            else "Sample outline for this section. Replace it with the real details."
        return {"draft": label + text, "is_mock": True}

    prompt = _SECTION_PROMPT.format(
        guide=guide, case_ref=scrub_text(case_ref) or "not given",
        current_text=scrub_text(current_text) or "none",
        notes=scrub_text("\n".join(notes)) or "none",
        language_name=_language_name(language),
    )
    client = _client()
    from google.genai import types

    last_error = None
    for attempt in range(2):
        try:
            response = client.models.generate_content(
                model=_model(), contents=prompt, config=types.GenerateContentConfig(temperature=0.3)
            )
            text = (response.text or "").strip()
            if not text:
                raise AiError("The AI returned an empty draft.")
            return {"draft": text, "is_mock": False}
        except AiError:
            raise
        except Exception as e:
            last_error = e
            log.warning("Gemini draft failed (attempt %s): %s", attempt + 1, e)
            time.sleep(2)
    raise AiError("The AI service is unavailable right now.") from last_error


def _mock_session(language: str) -> dict:
    bm = _language_name(language).startswith("Bahasa")
    feedback = {
        "summary": "Contoh maklum balas: AI belum dikonfigurasi pada pelayan." if bm
        else "Sample feedback: AI is not configured on the server, so this is not based on your recording.",
        "strengths": ["Contoh: nada yang tenang dan mesra."] if bm else ["Sample: calm and warm tone."],
        "areas_to_improve": ["Contoh: beri ruang untuk senyap."] if bm else ["Sample: leave room for silence."],
        "skills_observed": ["Contoh: soalan terbuka"] if bm else ["Sample: open questions"],
        "ethical_flags": [],
        "questions_for_supervision": ["Contoh: bagaimana menutup sesi dengan lebih jelas?"] if bm
        else ["Sample: how can I close the session more clearly?"],
        "is_mock": True,
    }
    return {"transcript": "", "feedback": feedback, "model": "mock", "prompt_version": PROMPT_VERSION, "is_mock": True}
