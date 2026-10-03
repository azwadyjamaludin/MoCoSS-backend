import os
import shutil
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware

# 1. Initialize FastAPI App
app = FastAPI(
    title="MoCoSS v2 AI Supervision API",
    description="FastAPI backend to process counseling audio and generate Gemini AI feedback.",
    version="2.0.0"
)

# 2. Configure CORS for frontend communication (Expo / Web / React Native)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Directory to temporarily store incoming audio recordings
UPLOAD_DIR = "./temp_audio_uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@app.get("/")
async def health_check():
    """Simple health check endpoint to verify backend status."""
    return {"status": "online", "system": "MoCoSS v2 FastAPI Engine"}


@app.post("/api/analyze-audio")
async def analyze_audio(file: UploadFile = File(...)):
    """
    Receives an audio file from the frontend, saves it temporarily,
    and forwards it to the Google Gemini API for clinical supervision analysis.
    """
    try:
        # Validate file extension
        allowed_extensions = [".m4a", ".mp3", ".wav", ".webm", ".aac"]
        file_ext = os.path.splitext(file.filename)[1].lower()
        if file_ext not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file format: {file_ext}. Allowed: {allowed_extensions}"
            )

        # Save audio file locally
        temp_file_path = os.path.join(UPLOAD_DIR, file.filename)
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        print(f"[MoCoSS v2] Audio successfully received and saved to: {temp_file_path}")

        # --- Gemini AI Processing Placeholders ---
        # 1. Upload audio to Gemini API using google-genai SDK
        # 2. Prompt Gemini for counseling feedback & transcript analysis
        # 3. Clean up local file after processing

        # Temporary structured response for testing
        return {
            "success": True,
            "filename": file.filename,
            "content_type": file.content_type,
            "supervision_feedback": {
                "summary": "Counseling session recorded successfully.",
                "key_themes": ["Active listening", "Empathy validation"],
                "recommendation": "Ready for Gemini API integration step."
            }
        }

    except Exception as e:
        print(f"Error processing audio upload: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Audio processing error: {str(e)}")
    finally:
        # Clean up temporary file memory pointer
        file.file.close()


if __name__ == "__main__":
    import uvicorn
    # Launch server on port 8000
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)