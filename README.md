title="MoCoSS v2 AI Supervision API",
description="FastAPI backend to process counseling audio and generate Gemini AI feedback.",
version="2.0.0"

-- use this command every time to launch FastAPI backend
   python3 -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

-- Local SQL insert (MySQL schema)
   /Volumes/MacintoshHD2/Users/azwady/Projects/DB/mysql/bin/mysql -S /Volumes/MacintoshHD2/Users/azwady/Projects/DB/mysql/tmp/mysql.sock -u root -p

   USE mocoss;
   SOURCE /Volumes/MacintoshHD2/Users/azwady/Projects/VSCode/MoCoSS backend/mocoss_schema.sql;