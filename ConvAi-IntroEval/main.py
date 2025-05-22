from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import shutil
import os
import traceback

from stt import transcribe_file

app = FastAPI()

# Enable CORS to allow requests from any origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)

# Base directories
base_dir = Path(__file__).parent
video_dir = base_dir / "videos"
transcription_dir = base_dir / "transcription"

# Ensure folders exist
video_dir.mkdir(parents=True, exist_ok=True)
transcription_dir.mkdir(parents=True, exist_ok=True)

# Clean up any video files accidentally saved in transcription directory
def cleanup_transcription_dir():
    for ext in [".mp3", ".mp4", ".wav", ".m4a", ".webm", ".flac", ".ogg", ".aac"]:
        for file in transcription_dir.glob(f"*{ext}"):
            try:
                # Move to videos directory instead of deleting
                target_path = video_dir / file.name
                print(f"Moving misplaced video file from transcription to videos folder: {file.name}")
                shutil.move(str(file), str(target_path))
            except Exception as e:
                print(f"Error moving file {file}: {str(e)}")

# Run cleanup on startup
cleanup_transcription_dir()

@app.get("/", response_class=HTMLResponse)
async def get_html():
    """Serve the index.html file directly"""
    try:
        html_path = base_dir / "index.html"
        with open(html_path, "r", encoding="utf-8") as html_file:
            return html_file.read()
    except Exception as e:
        return HTMLResponse(content=f"<html><body><h1>Error loading index.html</h1><p>{str(e)}</p></body></html>", 
                           status_code=500)

@app.post("/transcribe")
async def transcribe_endpoint(file: UploadFile = File(...)):
    # Secure filename and path
    safe_filename = os.path.basename(file.filename)
    file_path = video_dir / safe_filename    # Save uploaded file in the videos folder
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    await file.close()
    
    try:
        # Transcribe audio and get path to saved transcription
        transcription_text, transcription_path = transcribe_file(file_path, transcription_dir)
    except Exception as e:
        error_detail = traceback.format_exc()
        print(f"Error during transcription: {str(e)}\n{error_detail}")
        return JSONResponse(status_code=500, content={
            "error": str(e),
            "detail": error_detail
        })

    return JSONResponse(content={
        "transcription_file": str(transcription_path),
        "transcript": transcription_text
    })
