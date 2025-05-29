#!/usr/bin/env python3
"""
ConvAi-IntroEval Main Application

This FastAPI application provides a comprehensive self-introduction evaluation system
that processes audio/video introductions through three stages:
1. STT (Speech-to-Text): Audio → Transcript
2. LLM Field Extraction: Transcript → Filled Form
3. Background Rating Generation: profile_rating and intro_rating

Author: ConvAi Team
Date: May 28, 2025
"""

import asyncio
import json
import os
import shutil
import traceback
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import uvicorn
from fastapi import (
    FastAPI,
    File,
    Form,
    HTTPException,
    Request,
    UploadFile,
    BackgroundTasks,
    status,
    Depends
)

#login 
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from argon2 import PasswordHasher #argon2 for password hashing
from argon2.exceptions import VerifyMismatchError

import secrets
from datetime import datetime, timedelta

from models import User, SessionLocal , PasswordResetToken #database models

from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from sse_starlette.sse import EventSourceResponse as StreamingResponse

#db setup
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
#password hasher
ph = PasswordHasher()

# Import project modules
from stt import transcribe_file, SUPPORTED_EXTENSIONS
from app.llm.form_extractor import (
    extract_fields_from_transcript,
    extract_fields_from_transcript_stream
)
from app.llm.profile_rater_updated import (
    evaluate_profile_rating,
    evaluate_profile_rating_stream
)
from app.llm.intro_rater_updated import (
    evaluate_intro_rating_sync,
    evaluate_intro_rating_stream
)
from app.llm.utils import (
    get_latest_form_file,
    get_latest_transcript_file,
    save_rating_to_file,
    DISABLE_LLM
)

# ==================== CONFIGURATION ====================

# Application settings
APP_HOST = "localhost"
APP_PORT = 8000
DEBUG_MODE = True

# Directory paths
BASE_DIR = Path(__file__).parent
VIDEOS_DIR = BASE_DIR / "videos"
TRANSCRIPTION_DIR = BASE_DIR / "transcription"
FILLED_FORMS_DIR = BASE_DIR / "filled_forms"
RATINGS_DIR = BASE_DIR / "ratings"
STATIC_DIR = BASE_DIR / "static"
TEMPLATES_DIR = BASE_DIR / "templates"

# Ensure directories exist
for directory in [VIDEOS_DIR, TRANSCRIPTION_DIR, FILLED_FORMS_DIR, RATINGS_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# ==================== FASTAPI APPLICATION ====================

app = FastAPI(
    title="ConvAi-IntroEval",
    description="Self-Introduction Evaluation System with STT, LLM Field Extraction, and Rating Generation",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# ==================== UTILITY FUNCTIONS ====================

def log_info(message: str):
    """Log information with timestamp."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] INFO: {message}")

def log_error(message: str, error: Exception = None):
    """Log error with timestamp and optional exception details."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] ERROR: {message}")
    if error:
        print(f"[{timestamp}] ERROR DETAILS: {str(error)}")
        if DEBUG_MODE:
            traceback.print_exc()

def get_safe_filename(filename: str) -> str:
    """Generate a safe filename for uploaded files."""
    # Remove any path components and get just the filename
    filename = os.path.basename(filename)
    # Replace spaces and special characters
    safe_name = "".join(c for c in filename if c.isalnum() or c in "._-")
    return safe_name or "uploaded_file"

def validate_file_extension(filename: str) -> bool:
    """Validate if the file has a supported extension."""
    file_path = Path(filename)
    return file_path.suffix.lower() in SUPPORTED_EXTENSIONS

# ==================== BACKGROUND TASKS ====================

async def process_rating_background(form_filepath: str, transcript_filepath: str, rating_type: str):
    """
    Background task to process ratings asynchronously.
    
    Args:
        form_filepath: Path to the filled form JSON file
        transcript_filepath: Path to the transcript file
        rating_type: Either 'profile' or 'intro'
    """
    try:
        log_info(f"Starting background {rating_type} rating processing...")
        
        if rating_type == "profile":
            # Process profile rating - use sync function, not async
            rating_data = evaluate_profile_rating(form_filepath)
        elif rating_type == "intro":
            # Process intro rating - use sync function, not async
            rating_data = evaluate_intro_rating_sync(transcript_filepath)
        else:
            raise ValueError(f"Invalid rating type: {rating_type}")
        
        # Save the rating to file
        if rating_data:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            rating_filename = f"{rating_type}_rating_{timestamp}.json"
            rating_filepath = RATINGS_DIR / rating_filename
            
            with open(rating_filepath, 'w', encoding='utf-8') as f:
                json.dump(rating_data, f, indent=2, ensure_ascii=False)
            
            log_info(f"✅ {rating_type.title()} rating saved to: {rating_filepath}")
        else:
            log_error(f"❌ Failed to generate {rating_type} rating - no data returned")
            
    except Exception as e:
        log_error(f"❌ Background {rating_type} rating processing failed", e)

# ==================== API ROUTES ====================

@app.get("/", response_class=HTMLResponse)
async def serve_homepage():
    """Serve the main application login page."""
    try:
        index_file = TEMPLATES_DIR / "login.html"
        if index_file.exists():
            with open(index_file, 'r', encoding='utf-8') as f:
                content = f.read()
            return HTMLResponse(content=content)
        else:
            return HTMLResponse(
                content="<h1>ConvAi-IntroEval</h1><p>login.html not found in templates folder. Please ensure the file exists.</p>",
                status_code=404
            )
    except Exception as e:
        log_error("Error serving login page", e)
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "2.0.0",
        "llm_disabled": DISABLE_LLM
    }

@app.post("/transcribe")
async def transcribe_endpoint(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    extract_fields: bool = Form(True),
    generate_ratings: bool = Form(True)
):
    """
    Transcribe uploaded file and optionally extract fields.
    This endpoint is specifically designed for frontend compatibility.
    
    Args:
        file: The uploaded audio/video file
        extract_fields: Whether to extract fields from the transcript
        generate_ratings: Whether to generate ratings in the background
    
    Returns:
        JSON response with transcription_file path and extracted_fields info
    """
    try:
        log_info(f"📤 Frontend transcribe request: {file.filename}")
        
        # Validate file extension
        if not validate_file_extension(file.filename):
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type. Supported extensions: {', '.join(SUPPORTED_EXTENSIONS)}"
            )
        
        # Generate safe filename and save uploaded file
        safe_filename = get_safe_filename(file.filename)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        final_filename = f"{timestamp}_{safe_filename}"
        file_path = VIDEOS_DIR / final_filename
        
        # Save uploaded file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        log_info(f"💾 File saved: {file_path}")
        
        # Transcribe the file
        log_info("🎤 Starting transcription...")
        transcript, transcript_path = transcribe_file(file_path, TRANSCRIPTION_DIR)
        log_info(f"✅ Transcription completed: {transcript_path}")
        
        response_data = {
            "transcription_file": str(transcript_path),
            "transcript": transcript
        }
        
        # Extract fields if requested
        if extract_fields and not DISABLE_LLM:
            try:
                log_info("🧠 Starting field extraction...")
                
                # Read the transcript content
                with open(transcript_path, 'r', encoding='utf-8') as f:
                    transcript_content = f.read()
                
                # extract_fields_from_transcript is a sync function, not async
                extracted_data = extract_fields_from_transcript(transcript_content)
                
                if extracted_data:
                    # Save extracted fields
                    form_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    form_filename = f"filled_form_{form_timestamp}.json"
                    form_filepath = FILLED_FORMS_DIR / form_filename
                    
                    with open(form_filepath, 'w', encoding='utf-8') as f:
                        json.dump(extracted_data, f, indent=2, ensure_ascii=False)
                    
                    log_info(f"✅ Fields extracted and saved: {form_filepath}")
                    
                    response_data["extracted_fields"] = {
                        "status": "saved",
                        "file": str(form_filepath),
                        "data": extracted_data
                    }
                    
                    # Generate ratings in background if requested
                    if generate_ratings:
                        log_info("🔄 Starting background rating generation...")
                        background_tasks.add_task(
                            process_rating_background,
                            str(form_filepath),
                            str(transcript_path),
                            "profile"
                        )
                        background_tasks.add_task(
                            process_rating_background,
                            str(form_filepath),
                            str(transcript_path),
                            "intro"
                        )
                        response_data["extracted_fields"]["ratings_status"] = "generating_in_background"
                    
                else:
                    log_error("❌ Field extraction failed - no data returned")
                    response_data["extracted_fields"] = {
                        "status": "failed",
                        "error": "No data extracted from transcript"
                    }
                    
            except Exception as e:
                log_error("❌ Field extraction failed", e)
                response_data["extracted_fields"] = {
                    "status": "failed",
                    "error": str(e)
                }
        elif extract_fields and DISABLE_LLM:
            response_data["extracted_fields"] = {
                "status": "disabled",
                "message": "LLM functionality is disabled"
            }
        
        return JSONResponse(content=response_data)
        
    except HTTPException:
        raise
    except Exception as e:
        log_error("❌ Transcription endpoint failed", e)
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")

@app.get("/extract-fields-stream")
async def extract_fields_stream(transcript_path: str):
    """
    Stream field extraction from transcript file.
    Expected by frontend for real-time field extraction.
    NOTE: This returns already extracted data instead of re-processing to avoid duplicate LLM calls.
    """
    try:
        log_info(f"🔄 Checking for existing extracted fields for: {transcript_path}")
        
        if DISABLE_LLM:
            # Return a simple SSE response indicating LLM is disabled
            async def generate_disabled_response():
                yield f"data: {json.dumps({'status': 'disabled', 'message': 'LLM functionality is disabled'})}\n\n"
            
            return StreamingResponse(generate_disabled_response(), media_type="text/event-stream")
        
        # Check if we already have extracted data for this transcript
        try:
            result = get_latest_form_file()
            if isinstance(result, tuple) and len(result) == 2:
                form_filepath, form_data = result
            else:
                log_info("⚠️ get_latest_form_file did not return expected tuple format")
                form_filepath, form_data = None, None
        except Exception as form_error:
            log_error(f"❌ Error getting latest form file: {str(form_error)}", form_error)
            form_filepath, form_data = None, None
        
        async def generate_field_stream():
            try:
                # Properly check if form_filepath is a string and the file exists
                if isinstance(form_filepath, str) and Path(form_filepath).exists():
                    log_info(f"📄 Found existing extracted form: {form_filepath}")
                    
                    # Use the already loaded form data
                    extracted_data = form_data
                    
                    # Send the extracted data as a completion message
                    yield f"data: {json.dumps({'status': 'completed', 'data': extracted_data, 'message': 'Field extraction already completed'})}\n\n"
                    yield f"data: {json.dumps({'status': 'done'})}\n\n"
                else:
                    log_info("🔄 No existing form found, performing live extraction...")
                    # Only if no extracted data exists, perform live extraction
                    try:
                        async for chunk in extract_fields_from_transcript_stream(transcript_path):
                            yield chunk
                    except Exception as extraction_error:
                        log_error(f"❌ Live extraction failed: {str(extraction_error)}", extraction_error)
                        yield f"data: {json.dumps({'status': 'error', 'message': f'Extraction failed: {str(extraction_error)}'})}\n\n"
            except Exception as stream_error:
                log_error("❌ Error in field stream generation", stream_error)
                yield f"data: {json.dumps({'status': 'error', 'message': str(stream_error)})}\n\n"
        
        return StreamingResponse(generate_field_stream(), media_type="text/event-stream")
            
    except Exception as e:
        log_error("❌ Streaming field extraction failed", e)
        
        async def generate_error_response():
            yield f"data: {json.dumps({'status': 'error', 'message': str(e)})}\n\n"
        
        return StreamingResponse(generate_error_response(), media_type="text/event-stream")

@app.get("/profile-rating-stream")
async def profile_rating_stream():
    """
    Stream profile rating generation.
    Expected by frontend for real-time profile rating.
    NOTE: This checks for existing ratings to avoid duplicate processing.
    """
    try:
        log_info("🔄 Checking for existing profile rating...")
        
        if DISABLE_LLM:
            async def generate_disabled_response():
                yield f"data: {json.dumps({'status': 'disabled', 'message': 'LLM functionality is disabled'})}\n\n"
            
            return StreamingResponse(generate_disabled_response(), media_type="text/event-stream")
        
        # Check if we already have a recent profile rating
        recent_profile_files = list(RATINGS_DIR.glob("*profile_rating*.json"))
        if recent_profile_files:
            # Get the most recent profile rating
            latest_rating_file = max(recent_profile_files, key=lambda x: x.stat().st_mtime)
            
            async def generate_existing_rating():
                try:
                    log_info(f"📄 Found existing profile rating: {latest_rating_file}")
                    
                    # Load the existing rating data
                    with open(latest_rating_file, 'r', encoding='utf-8') as f:
                        rating_data = json.load(f)
                    
                    # Send the rating data as a completion message
                    yield f"data: {json.dumps({'status': 'completed', 'data': rating_data, 'message': 'Profile rating already available'})}\n\n"
                    yield f"data: {json.dumps({'status': 'done'})}\n\n"
                except Exception as e:
                    log_error("❌ Error loading existing rating", e)
                    yield f"data: {json.dumps({'status': 'error', 'message': str(e)})}\n\n"
            
            return StreamingResponse(generate_existing_rating(), media_type="text/event-stream")
        
        # If no existing rating, get the form file and generate new rating
        form_filepath = get_latest_form_file(str(FILLED_FORMS_DIR))
        
        if not form_filepath:
            async def generate_error_response():
                yield f"data: {json.dumps({'status': 'error', 'message': 'No form file found for rating'})}\n\n"
            
            return StreamingResponse(generate_error_response(), media_type="text/event-stream")
        
        # Generate new profile rating using streaming
        async def generate_rating_stream():
            try:
                log_info("🔄 Generating new profile rating...")
                # evaluate_profile_rating_stream is an async generator
                async for chunk in evaluate_profile_rating_stream(str(form_filepath)):
                    yield chunk
            except Exception as stream_error:
                yield f"data: {json.dumps({'status': 'error', 'message': str(stream_error)})}\n\n"
        
        return StreamingResponse(generate_rating_stream(), media_type="text/event-stream")
            
    except Exception as e:
        log_error("❌ Streaming profile rating failed", e)
        
        async def generate_error_response():
            yield f"data: {json.dumps({'status': 'error', 'message': str(e)})}\n\n"
        
        return StreamingResponse(generate_error_response(), media_type="text/event-stream")

@app.get("/intro-rating-stream")
async def intro_rating_stream():
    """
    Stream introduction rating generation.
    Expected by frontend for real-time intro rating.
    NOTE: This checks for existing ratings to avoid duplicate processing.
    """
    try:
        log_info("🔄 Checking for existing intro rating...")
        
        if DISABLE_LLM:
            async def generate_disabled_response():
                yield f"data: {json.dumps({'status': 'disabled', 'message': 'LLM functionality is disabled'})}\n\n"
            
            return StreamingResponse(generate_disabled_response(), media_type="text/event-stream")
        
        # Check if we already have a recent intro rating
        recent_intro_files = list(RATINGS_DIR.glob("*intro_rating*.json"))
        if recent_intro_files:
            # Get the most recent intro rating
            latest_rating_file = max(recent_intro_files, key=lambda x: x.stat().st_mtime)
            
            async def generate_existing_rating():
                try:
                    log_info(f"📄 Found existing intro rating: {latest_rating_file}")
                    
                    # Load the existing rating data
                    with open(latest_rating_file, 'r', encoding='utf-8') as f:
                        rating_data = json.load(f)
                    
                    # Send the rating data as a completion message
                    yield f"data: {json.dumps({'status': 'completed', 'data': rating_data, 'message': 'Intro rating already available'})}\n\n"
                    yield f"data: {json.dumps({'status': 'done'})}\n\n"
                except Exception as e:
                    log_error("❌ Error loading existing intro rating", e)
                    yield f"data: {json.dumps({'status': 'error', 'message': str(e)})}\n\n"
            
            return StreamingResponse(generate_existing_rating(), media_type="text/event-stream")
        
        # If no existing rating, get the transcript file and generate new rating
        transcript_filepath = get_latest_transcript_file(str(TRANSCRIPTION_DIR))
        
        if not transcript_filepath:
            async def generate_error_response():
                yield f"data: {json.dumps({'status': 'error', 'message': 'No transcript file found for rating'})}\n\n"
            
            return StreamingResponse(generate_error_response(), media_type="text/event-stream")
        
        # Generate new intro rating using streaming
        async def generate_rating_stream():
            try:
                log_info("🔄 Generating new intro rating...")
                # evaluate_intro_rating_stream is an async generator
                async for chunk in evaluate_intro_rating_stream(str(transcript_filepath)):
                    yield chunk
            except Exception as stream_error:
                yield f"data: {json.dumps({'status': 'error', 'message': str(stream_error)})}\n\n"
        
        return StreamingResponse(generate_rating_stream(), media_type="text/event-stream")
            
    except Exception as e:
        log_error("❌ Streaming intro rating failed", e)
        
        async def generate_error_response():
            yield f"data: {json.dumps({'status': 'error', 'message': str(e)})}\n\n"
        
        return StreamingResponse(generate_error_response(), media_type="text/event-stream")

@app.get("/rating/{filename}")
async def get_rating_file(filename: str):
    """
    Get a specific rating file by filename.
    Expected by frontend for loading individual rating files.
    """
    try:
        log_info(f"📄 Loading rating file: {filename}")
        
        # Look for the file in the ratings directory
        rating_file = RATINGS_DIR / filename
        
        if not rating_file.exists():
            raise HTTPException(status_code=404, detail=f"Rating file '{filename}' not found")
        
        # Load and return the rating data
        with open(rating_file, 'r', encoding='utf-8') as f:
            rating_data = json.load(f)
        
        # Log the data structure for debugging
        log_info(f"✅ Rating data loaded: {json.dumps(rating_data)[:200]}...")
        
        return JSONResponse(content={
            "success": True,
            "filename": filename,
            "rating_data": rating_data,
            "file_path": str(rating_file),
            "created": datetime.fromtimestamp(rating_file.stat().st_mtime).isoformat()
        })
        
    except HTTPException:
        raise
    except Exception as e:
        log_error(f"❌ Error loading rating file {filename}", e)
        raise HTTPException(status_code=500, detail=f"Error loading rating file: {str(e)}")

@app.get("/ratings/check_status")
async def check_rating_status(form_id: str = None):
    """
    Check the status of rating generation for a specific form.
    Expected by frontend for polling rating completion status.
    """
    try:
        log_info(f"🔍 Checking rating status for form_id: {form_id}")
        
        # If no form_id provided, check for recent ratings
        if not form_id:
            now = datetime.now()
            recent_ratings = []
            
            for rating_file in RATINGS_DIR.glob("*.json"):
                try:
                    file_time = datetime.fromtimestamp(rating_file.stat().st_mtime)
                    if (now - file_time).total_seconds() < 1800:  # 30 minutes
                        # Try to quickly validate the file is proper JSON
                        with open(rating_file, 'r', encoding='utf-8') as f:
                            # Just read a small portion to check it's valid JSON
                            json.load(f)
                            
                        recent_ratings.append({
                            "filename": rating_file.name,
                            "type": "profile" if "profile" in rating_file.name else "intro",
                            "created": file_time.isoformat()
                        })
                except Exception as file_error:
                    log_error(f"⚠️ Skipping invalid rating file {rating_file.name}", file_error)
                    continue
              # Sort recent_ratings by creation time (newest first)
            recent_ratings.sort(key=lambda x: x["created"], reverse=True)
            
            # Get the most recent file for each type
            profile_files = [r["filename"] for r in recent_ratings if r["type"] == "profile"]
            intro_files = [r["filename"] for r in recent_ratings if r["type"] == "intro"]
              # Take only the most recent file for each type
            most_recent_profile = profile_files[0] if profile_files else None
            most_recent_intro = intro_files[0] if intro_files else None
            
            log_info(f"📋 Most recent profile file: {most_recent_profile}")
            log_info(f"📋 Most recent intro file: {most_recent_intro}")
            
            # Create filtered recent_ratings with only the most recent files
            filtered_recent_ratings = []
            if most_recent_profile:
                profile_entry = next((r for r in recent_ratings if r["filename"] == most_recent_profile), None)
                if profile_entry:
                    filtered_recent_ratings.append(profile_entry)
            if most_recent_intro:
                intro_entry = next((r for r in recent_ratings if r["filename"] == most_recent_intro), None)
                if intro_entry:
                    filtered_recent_ratings.append(intro_entry)
            
            return JSONResponse(content={
                "success": True,
                "form_id": form_id,
                "recent_ratings": filtered_recent_ratings,  # Only most recent files
                "profile_ready": most_recent_profile is not None,
                "intro_ready": most_recent_intro is not None,
                "profile_files": [most_recent_profile] if most_recent_profile else [],
                "intro_files": [most_recent_intro] if most_recent_intro else [],
                "status": "completed" if (most_recent_profile or most_recent_intro) else "pending"
            })
        
        # Look for ratings related to the specific form_id
        profile_files = []
        intro_files = []
        
        # Try to find files with the form_id in the name
        for profile_pattern in [f"*profile*{form_id}*.json", "*profile_rating_*.json"]:
            for file in RATINGS_DIR.glob(profile_pattern):
                try:
                    # Quick validation
                    with open(file, 'r', encoding='utf-8') as f:
                        json.load(f)
                    profile_files.append(file)
                except Exception:
                    continue
                    
        for intro_pattern in [f"*intro*{form_id}*.json", "*intro_rating_*.json"]:
            for file in RATINGS_DIR.glob(intro_pattern):
                try:
                    # Quick validation
                    with open(file, 'r', encoding='utf-8') as f:
                        json.load(f)
                    intro_files.append(file)
                except Exception:
                    continue
        
        # Get the most recent files if multiple are found
        if profile_files:
            profile_files = [max(profile_files, key=lambda x: x.stat().st_mtime)]
        
        if intro_files:
            intro_files = [max(intro_files, key=lambda x: x.stat().st_mtime)]
        
        return JSONResponse(content={
            "success": True,
            "form_id": form_id,
            "profile_ready": len(profile_files) > 0,
            "intro_ready": len(intro_files) > 0,
            "profile_files": [f.name for f in profile_files],
            "intro_files": [f.name for f in intro_files],
            "status": "completed" if (profile_files or intro_files) else "pending"
        })
        
    except Exception as e:
        log_error(f"❌ Error checking rating status for form_id {form_id}", e)
        raise HTTPException(status_code=500, detail=f"Error checking rating status: {str(e)}")

# ==================== APPLICATION STARTUP ====================

@app.on_event("startup")
async def startup_event():
    """Application startup event handler."""
    log_info("🚀 ConvAi-IntroEval application starting up...")
    log_info(f"📁 Base directory: {BASE_DIR}")
    log_info(f"🎥 Videos directory: {VIDEOS_DIR}")
    log_info(f"📝 Transcription directory: {TRANSCRIPTION_DIR}")
    log_info(f"📋 Forms directory: {FILLED_FORMS_DIR}")
    log_info(f"⭐ Ratings directory: {RATINGS_DIR}")
    log_info(f"🧠 LLM disabled: {DISABLE_LLM}")
    
    # Check if Ollama is running (if LLM is enabled)
    if not DISABLE_LLM:
        try:
            import requests
            response = requests.get("http://localhost:11434/api/tags", timeout=5)
            if response.status_code == 200:
                log_info("✅ Ollama server is running and accessible")
            else:
                log_info("⚠️ Ollama server may not be running properly")
        except Exception as e:
            log_info(f"⚠️ Could not connect to Ollama server: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown event handler."""
    log_info("🛑 ConvAi-IntroEval application shutting down...")

# ==================== USER AUTHENTICATION ====================
@app.get("/login", response_class=HTMLResponse)
async def get_login():
    html_path = TEMPLATES_DIR / "login.html"
    with open(html_path, "r", encoding="utf-8") as html_file:
        return html_file.read()

@app.post("/login")
async def login(username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    try:
        ph.verify(user.hashed_password, password)  # Use argon2 to verify
    except VerifyMismatchError:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    return {"message": "Login successful", "username": username}

    
@app.get("/index", response_class=HTMLResponse)
async def get_index():
    html_path = TEMPLATES_DIR / "index.html"
    with open(html_path, "r", encoding="utf-8") as html_file:
        return html_file.read()

#DATABASE SETUP


@app.post("/register")
async def register(username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == username).first()
    if user:
        raise HTTPException(status_code=400, detail="Username already registered")
    hashed_password = ph.hash(password)
    new_user = User(username=username, hashed_password=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"message": "User registered successfully"}


@app.post("/request-password-reset")
async def request_password_reset(username: str = Form(...), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == username).first()
    if not user:
        # Always respond with success to avoid leaking user existence
        return {"message": "If this email exists, a reset link was sent."}
    # Generate secure token
    token = secrets.token_urlsafe(64)
    expires_at = datetime.utcnow() + timedelta(hours=1)
    # Store token
    db.add(PasswordResetToken(user_id=user.id, token=token, expires_at=expires_at))
    db.commit()
    # TODO: Send email to user with link (e.g., http://yourdomain/reset-password?token=...)
    print(f"Password reset link: http://localhost:8000/reset-password?token={token}")
    return {"message": "If this username exists, a reset link was sent."}

@app.post("/reset-password")
async def reset_password(token: str = Form(...), new_password: str = Form(...), db: Session = Depends(get_db)):
    prt = db.query(PasswordResetToken).filter(PasswordResetToken.token == token).first()
    if not prt or prt.expires_at < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Invalid or expired token")
    user = db.query(User).filter(User.id == prt.user_id).first()
    if not user:
        raise HTTPException(status_code=400, detail="User not found")
    user.hashed_password = ph.hash(new_password)
    db.delete(prt)  # Remove used token
    db.commit()
    return {"message": "Password reset successfully"}

@app.get("/reset-password", response_class=HTMLResponse)
async def get_reset_password():
    html_path = TEMPLATES_DIR / "reset_password.html"
    with open(html_path, "r", encoding="utf-8") as html_file:
        return html_file.read()

# ==================== MAIN ENTRY POINT ====================

def main():
    """Main entry point for the application."""
    log_info("🎯 Starting ConvAi-IntroEval server...")
    log_info(f"🌐 Server will be available at: http://{APP_HOST}:{APP_PORT}")
    log_info(f"📚 API documentation: http://{APP_HOST}:{APP_PORT}/docs")
    
    try:
        uvicorn.run(
            "main:app",
            host=APP_HOST,
            port=APP_PORT,
            reload=DEBUG_MODE,
            log_level="info" if DEBUG_MODE else "warning",
            access_log=DEBUG_MODE
        )
    except KeyboardInterrupt:
        log_info("🛑 Server stopped by user")
    except Exception as e:
        log_error("❌ Server failed to start", e)
        raise

if __name__ == "__main__":
    main()