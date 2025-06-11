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
from typing import Dict, List, Optional, Union

import uvicorn
from fastapi import (
    FastAPI,
    File,
    Form,
    HTTPException,
    Request,
    UploadFile,
    status,
    Depends
)
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse

#login 
from sqlalchemy.orm import Session
from argon2 import PasswordHasher #argon2 for password hashing
from auth import get_current_teacher, create_access_token, get_current_user
from argon2.exceptions import VerifyMismatchError

import secrets
from datetime import datetime, timedelta

from models import User, Teacher, TeacherStudentMap, SessionLocal, PasswordResetToken #database models

from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, FileResponse
from fastapi.staticfiles import StaticFiles

# Import teacher routes
from teacher_routes import router as teacher_router

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
from auth import get_current_user
from file_organizer import (
    get_user_directory,
    organize_path,
    extract_roll_number_from_path,
    save_file_with_organization,
    glob_with_roll_number,
    find_latest_file_for_user,
    log_file_operation
)
from app.llm.form_extractor import (
    extract_fields_from_transcript
)
from app.llm.profile_rater_updated import (
    evaluate_profile_rating
)
from app.llm.intro_rater_updated import (
    evaluate_intro_rating_sync
)
from app.llm.utils import (
    get_latest_form_file,
    get_latest_transcript_file,
    save_rating_to_file,
    DISABLE_LLM
)
from app.llm.queue_manager import PhaseType, TaskStatus

# ==================== CONFIGURATION ====================

# Application settings
APP_HOST = "localhost"
APP_PORT = 8000
DEBUG_MODE = True  # Consistent debug mode setting


# Directory paths
BASE_DIR = Path(__file__).parent
VIDEOS_DIR = BASE_DIR / "videos"
TRANSCRIPTION_DIR = BASE_DIR / "transcription"
FILLED_FORMS_DIR = BASE_DIR / "filled_forms"
RATINGS_DIR = BASE_DIR / "ratings"
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"

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

# Mount transcription and filled_forms directories for file serving
if TRANSCRIPTION_DIR.exists():
    app.mount("/transcription", StaticFiles(directory=str(TRANSCRIPTION_DIR)), name="transcription")
if FILLED_FORMS_DIR.exists():
    app.mount("/filled_forms", StaticFiles(directory=str(FILLED_FORMS_DIR)), name="filled_forms")

# Include teacher routes
app.include_router(teacher_router)

# ==================== QUEUE MANAGER INITIALIZATION ====================

# Import queue manager directly
from app.llm.queue_manager import TwoPhaseQueueManager, PhaseType, TaskStatus

# Global queue manager instance (will be initialized in startup event)
queue_manager = None

# Initialize queue manager only once
_queue_manager_initialized = False

@app.on_event("startup")
async def startup_event():
    """Initialize queue manager on startup."""
    global _queue_manager_initialized, queue_manager
    
    log_info("🚀 Starting ConvAi-IntroEval with Two-Phase Queue System")
    
    # Initialize queue manager only if not already initialized
    if not _queue_manager_initialized and not DISABLE_LLM:
        queue_manager = TwoPhaseQueueManager()
        queue_manager.start()
        _queue_manager_initialized = True
        log_info("✅ Two-Phase Queue Manager started successfully")
    else:
        log_info("ℹ️ Two-Phase Queue Manager already initialized, skipping")
    
    # Additional startup checks
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
    """Clean shutdown of queue manager."""
    log_info("🛑 Shutting down ConvAi-IntroEval")
    
    # Shutdown queue manager
    queue_manager.stop()
    log_info("✅ Queue Manager stopped successfully")

# ==================== UTILITY FUNCTIONS ====================

def log_info(message: str):
    """Log information with timestamp."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] INFO: {message}")

def log_warning(message: str):
    """Log warning with timestamp."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] WARNING: {message}")

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

async def process_rating_background(form_filepath: str, transcript_filepath: str, rating_type: str, roll_number: str = None):
    """
    Background task to process ratings asynchronously with file organization.
    Now uses the queue manager system directly for task processing.
    
    Args:
        form_filepath: Path to the filled form JSON file
        transcript_filepath: Path to the transcript file
        rating_type: Either 'profile' or 'intro'
        roll_number: Student roll number for file organization (optional)
    """
    try:
        log_info(f"Starting {rating_type} rating processing for roll: {roll_number or 'unknown'}")
        
        # Import rating functions directly
        if rating_type == "profile":
            from app.llm.profile_rater_updated import evaluate_profile_rating
            
            # Generate profile rating synchronously 
            rating_filepath = await asyncio.to_thread(
                evaluate_profile_rating,
                form_filepath, 
                transcript_filepath, 
                roll_number
            )
        elif rating_type == "intro":
            from app.llm.intro_rater_updated import evaluate_intro_rating_sync
            
            # Generate intro rating synchronously
            rating_filepath = await asyncio.to_thread(
                evaluate_intro_rating_sync,
                form_filepath, 
                transcript_filepath, 
                roll_number
            )
        else:
            raise ValueError(f"Invalid rating type: {rating_type}")
        
        if rating_filepath:
            log_info(f"✅ {rating_type.title()} rating completed: {rating_filepath}")
            log_file_operation(f"CREATE {rating_type}_rating", rating_filepath, roll_number)
            return rating_filepath
        else:
            log_error(f"❌ Failed to generate {rating_type} rating - no file path returned")
            return None
            
    except Exception as e:
        log_error(f"❌ {rating_type} rating processing failed", e)
        log_error(traceback.format_exc())
        return None

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
        "version": "2.0.0",        "llm_disabled": DISABLE_LLM
    }

# ==================== FIELD EXTRACTION STATUS ====================

@app.get("/extract-fields-status")
async def extract_fields_status(
    task_id: str = None,
    current_user: Optional[Union[User, Teacher]] = Depends(get_current_user)
):
    """
    Check status of field extraction for a specific task or user.
    Returns immediate status without streaming.
    """
    try:
        if not current_user:
            raise HTTPException(status_code=401, detail="Authentication required")
        
        user_id = current_user.username
        roll_number = current_user.roll_number if hasattr(current_user, 'roll_number') else None
        
        log_info(f"🔄 Checking field extraction status for user: {user_id} (roll: {roll_number})")
        
        if DISABLE_LLM:
            return JSONResponse(content={
                "status": "disabled",
                "message": "LLM functionality is disabled"
            })
        
        # Check if user has completed forms
        form_files = glob_with_roll_number("filled_forms", "*.json", roll_number)
        
        if form_files:
            # Get the most recent form
            latest_form = max(form_files, key=lambda x: x.stat().st_mtime)
            
            try:
                with open(latest_form, 'r', encoding='utf-8') as f:
                    form_data = json.load(f)
                
                return JSONResponse(content={
                    "status": "completed",
                    "file_path": str(latest_form),
                    "data": form_data,
                    "message": "Field extraction completed"
                })
            except Exception as e:
                log_error(f"❌ Error loading form file: {latest_form}", e)
                return JSONResponse(content={
                    "status": "error",
                    "message": f"Error loading form file: {str(e)}"
                })
        else:
            return JSONResponse(content={
                "status": "pending",
                "message": "Field extraction not yet completed"
            })
            
    except HTTPException:
        raise
    except Exception as e:
        log_error("❌ Field extraction status check failed", e)
        raise HTTPException(status_code=500, detail=f"Status check failed: {str(e)}")

@app.get("/profile-rating-status")
async def profile_rating_status(
    current_user: Optional[Union[User, Teacher]] = Depends(get_current_user)
):
    """
    Check status of profile rating for the current user.
    Returns immediate status without streaming.
    """
    try:
        if not current_user:
            raise HTTPException(status_code=401, detail="Authentication required")
        
        user_id = current_user.username
        roll_number = current_user.roll_number if hasattr(current_user, 'roll_number') else None
        
        log_info(f"🔄 Checking profile rating status for user: {user_id} (roll: {roll_number})")
        
        if DISABLE_LLM:
            return JSONResponse(content={
                "status": "disabled",
                "message": "LLM functionality is disabled"
            })
        
        # Check for existing profile ratings for this user
        profile_files = glob_with_roll_number("ratings", "*profile_rating*.json", roll_number)
        
        if profile_files:
            # Get the most recent profile rating
            latest_rating = max(profile_files, key=lambda x: x.stat().st_mtime)
            
            try:
                with open(latest_rating, 'r', encoding='utf-8') as f:
                    rating_data = json.load(f)
                
                return JSONResponse(content={
                    "status": "completed",
                    "file_path": str(latest_rating),
                    "data": rating_data,
                    "message": "Profile rating completed"
                })
            except Exception as e:
                log_error(f"❌ Error loading profile rating: {latest_rating}", e)
                return JSONResponse(content={
                    "status": "error",
                    "message": f"Error loading profile rating: {str(e)}"
                })
        else:
            return JSONResponse(content={
                "status": "pending",
                "message": "Profile rating not yet completed"
            })
            
    except HTTPException:
        raise
    except Exception as e:
        log_error("❌ Profile rating status check failed", e)
        raise HTTPException(status_code=500, detail=f"Status check failed: {str(e)}")

@app.get("/intro-rating-status")
async def intro_rating_status(
    current_user: Optional[Union[User, Teacher]] = Depends(get_current_user)
):
    """
    Check status of intro rating for the current user.
    Returns immediate status without streaming.
    """
    try:
        if not current_user:
            raise HTTPException(status_code=401, detail="Authentication required")
        
        user_id = current_user.username
        roll_number = current_user.roll_number if hasattr(current_user, 'roll_number') else None
        
        log_info(f"🔄 Checking intro rating status for user: {user_id} (roll: {roll_number})")
        
        if DISABLE_LLM:
            return JSONResponse(content={
                "status": "disabled",
                "message": "LLM functionality is disabled"
            })
        
        # Check for existing intro ratings for this user
        intro_files = glob_with_roll_number("ratings", "*intro_rating*.json", roll_number)
        
        if intro_files:
            # Get the most recent intro rating
            latest_rating = max(intro_files, key=lambda x: x.stat().st_mtime)
            
            try:
                with open(latest_rating, 'r', encoding='utf-8') as f:
                    rating_data = json.load(f)
                
                return JSONResponse(content={
                    "status": "completed",
                    "file_path": str(latest_rating),
                    "data": rating_data,
                    "message": "Introduction rating completed"
                })
            except Exception as e:
                log_error(f"❌ Error loading intro rating: {latest_rating}", e)
                return JSONResponse(content={
                    "status": "error",
                    "message": f"Error loading intro rating: {str(e)}"
                })
        else:
            return JSONResponse(content={
                "status": "pending",
                "message": "Introduction rating not yet completed"
            })
            
    except HTTPException:
        raise
    except Exception as e:
        log_error("❌ Intro rating status check failed", e)
        raise HTTPException(status_code=500, detail=f"Status check failed: {str(e)}")

@app.get("/rating/{filename}")
async def get_rating_file(filename: str):
    """
    Get a specific rating file by filename.
    Expected by frontend for loading individual rating files.
    """
    try:
        log_info(f"📄 Loading rating file: {filename}")
        
        # Look for the file in both root and roll number subdirectories
        matching_files = glob_with_roll_number(RATINGS_DIR, filename)
        
        if not matching_files:
            # Try with just the filename in case the path has issues
            log_info(f"⚠️ Exact filename not found, trying pattern matching: {filename}")
            
            # Try different patterns to maximize chances of finding the file
            patterns = [
                f"**/{filename}",  # Full recursive search
                f"*/*/{filename}",  # Two levels deep (for roll number subdirectories)
                f"*/{filename}",    # One level deep
                f"*{filename}*"     # Partial match anywhere
            ]
            
            for pattern in patterns:
                log_info(f"🔍 Searching with pattern: {pattern}")
                found_files = glob_with_roll_number(RATINGS_DIR, pattern)
                if found_files:
                    matching_files = found_files
                    log_info(f"✅ Found {len(matching_files)} matching files with pattern: {pattern}")
                    break
            
        if not matching_files:
            log_error(f"❌ Rating file not found: {filename}")
            raise HTTPException(status_code=404, detail=f"Rating file '{filename}' not found")
        
        # Use the first matching file (should be only one with that exact name)
        rating_file = matching_files[0]
        log_info(f"📄 Using rating file: {rating_file}")
        
        # Load and return the rating data
        with open(rating_file, 'r', encoding='utf-8') as f:
            rating_data = json.load(f)
        
        # Log the data structure for debugging
        log_info(f"✅ Rating data loaded from {rating_file}: {json.dumps(rating_data)[:200]}...")
        
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
            
            # Use glob_with_roll_number to search in both root and roll number subdirectories
            for rating_file in glob_with_roll_number(RATINGS_DIR, "*.json"):
                try:
                    file_time = datetime.fromtimestamp(rating_file.stat().st_mtime)
                    if (now - file_time).total_seconds() < 1800:  # 30 minutes
                        # Try to quickly validate the file is proper JSON
                        with open(rating_file, 'r', encoding='utf-8') as f:
                            # Just read a small portion to check it's valid JSON
                            json.load(f)
                            
                        recent_ratings.append({
                            "filename": rating_file.name,
                            "filepath": str(rating_file),
                            "type": "profile" if "profile" in rating_file.name else "intro",
                            "created": file_time.isoformat()
                        })
                except Exception as file_error:
                    log_error(f"⚠️ Skipping invalid rating file {rating_file.name}", file_error)
                    continue
            
            # Log the number of recent ratings found
            log_info(f"📊 Found {len(recent_ratings)} recent rating files")
            
            # Sort recent_ratings by creation time (newest first)
            recent_ratings.sort(key=lambda x: x["created"], reverse=True)
            
            # Get the most recent file for each type
            profile_files = [r["filepath"] for r in recent_ratings if r["type"] == "profile"]
            intro_files = [r["filepath"] for r in recent_ratings if r["type"] == "intro"]
            
            # Take only the most recent file for each type
            most_recent_profile = profile_files[0] if profile_files else None
            most_recent_intro = intro_files[0] if intro_files else None
            
            log_info(f"📋 Most recent profile file: {most_recent_profile}")
            log_info(f"📋 Most recent intro file: {most_recent_intro}")
            
            # Create filtered recent_ratings with only the most recent files
            filtered_recent_ratings = []
            if most_recent_profile:
                profile_entry = next((r for r in recent_ratings if r["filepath"] == most_recent_profile), None)
                if profile_entry:
                    filtered_recent_ratings.append(profile_entry)
            if most_recent_intro:
                intro_entry = next((r for r in recent_ratings if r["filepath"] == most_recent_intro), None)
                if intro_entry:
                    filtered_recent_ratings.append(intro_entry)
            
            # Extract just the filenames for the response (not full paths)
            profile_filenames = [Path(most_recent_profile).name] if most_recent_profile else []
            intro_filenames = [Path(most_recent_intro).name] if most_recent_intro else []
            log_info(f"📝 Returning profile filenames: {profile_filenames}")
            log_info(f"📝 Returning intro filenames: {intro_filenames}")
            
            return JSONResponse(content={
                "success": True,
                "form_id": form_id,
                "recent_ratings": filtered_recent_ratings,  # Only most recent files
                "profile_ready": most_recent_profile is not None,
                "intro_ready": most_recent_intro is not None,
                "profile_files": profile_filenames,
                "intro_files": intro_filenames,
                "status": "completed" if (most_recent_profile or most_recent_intro) else "pending"
            })
        
        # Look for ratings related to the specific form_id
        log_info(f"🔍 Looking for ratings related to form_id: {form_id}")
        profile_files = []
        intro_files = []
        
        # Try to find files with the form_id in the name - use glob_with_roll_number
        for profile_pattern in [f"*profile*{form_id}*.json", "*profile_rating_*.json"]:
            log_info(f"🔍 Searching for profile ratings with pattern: {profile_pattern}")
            found_files = glob_with_roll_number(RATINGS_DIR, profile_pattern)
            profile_files.extend(found_files)
            log_info(f"📊 Found {len(found_files)} profile rating files with pattern: {profile_pattern}")
            
        for intro_pattern in [f"*intro*{form_id}*.json", "*intro_rating_*.json"]:
            log_info(f"🔍 Searching for intro ratings with pattern: {intro_pattern}")
            found_files = glob_with_roll_number(RATINGS_DIR, intro_pattern)
            intro_files.extend(found_files)
            log_info(f"📊 Found {len(found_files)} intro rating files with pattern: {intro_pattern}")
        
        # Filter files that are valid JSON
        valid_profile_files = []
        valid_intro_files = []
        
        for file in profile_files:
            try:
                with open(file, 'r', encoding='utf-8') as f:
                    json.load(f)
                valid_profile_files.append(file)
            except Exception as e:
                log_error(f"⚠️ Skipping invalid profile rating file {file.name}", e)
                continue
                
        for file in intro_files:
            try:
                with open(file, 'r', encoding='utf-8') as f:
                    json.load(f)
                valid_intro_files.append(file)
            except Exception as e:
                log_error(f"⚠️ Skipping invalid intro rating file {file.name}", e)
                continue
        
        # Get the most recent files if profile or intro files are found
        if valid_profile_files:
            valid_profile_files = [max(valid_profile_files, key=lambda x: x.stat().st_mtime)]
            log_info(f"📋 Most recent profile file for form_id {form_id}: {valid_profile_files[0]}")
        
        if valid_intro_files:
            valid_intro_files = [max(valid_intro_files, key=lambda x: x.stat().st_mtime)]
            log_info(f"📋 Most recent intro file for form_id {form_id}: {valid_intro_files[0]}")
        
        # Extract just the filenames for the response (not full paths)
        profile_filenames = [f.name for f in valid_profile_files]
        intro_filenames = [f.name for f in valid_intro_files]
        
        log_info(f"📝 Returning profile filenames for form_id {form_id}: {profile_filenames}")
        log_info(f"📝 Returning intro filenames for form_id {form_id}: {intro_filenames}")
        
        return JSONResponse(content={
            "success": True,
            "form_id": form_id,
            "profile_ready": len(valid_profile_files) > 0,
            "intro_ready": len(valid_intro_files) > 0,
            "profile_files": profile_filenames,
            "intro_files": intro_filenames,
            "status": "completed" if (valid_profile_files or valid_intro_files) else "pending"
        })
        
    except Exception as e:
        log_error(f"❌ Error checking rating status for form_id {form_id}", e)
        raise HTTPException(status_code=500, detail=f"Error checking rating status: {str(e)}")

# ==================== NEW QUEUE-BASED API ENDPOINTS ====================

@app.post("/queue/submit")
async def submit_to_queue(
    file: UploadFile = File(...),
    current_user: Optional[Union[User, Teacher]] = Depends(get_current_user)
):
    """
    Submit a file to the two-phase queue system for processing.
    This is the new optimized endpoint that uses the dual LLM setup.
    """
    try:
        # Check if user is authenticated
        if not current_user:
            log_warning("🚫 Queue submission without authentication")
            raise HTTPException(
                status_code=401,
                detail="Authentication required. Please log in to submit files."
            )
        
        log_info(f"📤 Queue submission: {file.filename} (user: {current_user.username})")
        
        # Validate file extension
        if not validate_file_extension(file.filename):
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type. Supported extensions: {', '.join(SUPPORTED_EXTENSIONS)}"
            )
        
        # Extract user information - now guaranteed to be authenticated
        roll_number = current_user.roll_number if hasattr(current_user, 'roll_number') else None
        user_id = current_user.username
        
        # Generate safe filename and determine path
        safe_filename = get_safe_filename(file.filename)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        final_filename = f"{timestamp}_{safe_filename}"
        
        # Get the file path with proper organization
        file_path = organize_path(VIDEOS_DIR, final_filename, roll_number)
          # Read file content and save it synchronously to ensure it's available for processing
        file_content = await file.read()
        
        # Create parent directory if it doesn't exist
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save file synchronously to ensure it's available immediately
        with open(file_path, 'wb') as f:
            f.write(file_content)
        
        log_info(f"💾 File saved successfully: {file_path}")
        log_file_operation("SAVE video", file_path, roll_number)        # Submit to queue for processing
        task_id = queue_manager.submit_task(
            user_id=user_id,
            roll_number=roll_number or f"user_{user_id}_{timestamp}",
            file_path=str(file_path)
        )
        
        log_info(f"📋 Task submitted to queue: {task_id}")
        
        # Return task information
        return JSONResponse(content={
            "task_id": task_id,
            "status": "submitted",
            "message": "File submitted to processing queue",
            "queue_position": queue_manager.get_queue_position(task_id),
            "current_phase": queue_manager.current_phase.value
        })
        
    except HTTPException:
        raise
    except Exception as e:
        log_error("❌ Queue submission failed", e)
        log_error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Queue submission failed: {str(e)}")

@app.get("/queue/status/{task_id}")

async def get_task_status(task_id: str):
    """Get the current status of a task in the queue with enhanced queue information."""
    try:
        status = queue_manager.get_task_status(task_id)
        if not status:
            raise HTTPException(status_code=404, detail="Task not found")
        
        # Add queue position information
        task_position = queue_manager.get_queue_position(task_id) or 0
        
        # Get queue stats for better estimates
        queue_stats = queue_manager.get_stats()
        current_phase = queue_stats.get("current_phase", "idle")
        
        # Calculate more accurate average processing time based on recent completions
        recent_avg_time = queue_stats.get("average_processing_time", 45)  # seconds per task
        avg_processing_time = recent_avg_time if recent_avg_time > 0 else 45
        
        # Calculate estimated wait time based on queue position and phase
        estimated_wait_time = task_position * avg_processing_time
        
        # Add phase-specific time if this task is in the first position
        if task_position == 0 and status.get("status") == "processing":
            # Task is currently processing, use phase-specific progress to estimate remaining time
            phase_progress = queue_stats.get("phase_progress", 0) 
            remaining_phase_time = avg_processing_time * (1 - (phase_progress / 100))
            estimated_wait_time = max(5, int(remaining_phase_time))  # At least 5 seconds
        
        # Create detailed user-friendly message based on status
        task_status = status.get("status")
        message = ""
        progress_percent = 0
        
        if task_status == "pending":
            if task_position > 0:
                if task_position == 1:
                    message = "You're second in line. Processing will begin soon."
                else:
                    message = f"Waiting in queue. There are {task_position} users ahead of you."
                progress_percent = 10
            else:
                message = "You're next in line. Processing will begin shortly."
                progress_percent = 15
        elif task_status == "processing":
            message = "Your file is being processed. Speech-to-text conversion in progress..."
            progress_percent = 30
        elif task_status == "stt_complete":
            message = "Transcription complete! Now analyzing your introduction..."
            progress_percent = 60
        elif task_status == "form_complete":
            message = "Analysis complete! Generating final ratings and feedback..."
            progress_percent = 80
        elif task_status == "complete":
            message = "Processing complete! Your results are ready to view."
            progress_percent = 100
        elif task_status == "failed":
            error_msg = status.get("error_message", "")
            message = f"Processing failed. {error_msg} Please try again or contact support."
            progress_percent = 100
        else:
            message = "Processing your file..."
            progress_percent = 25
        
        # Add more context about the queue system status
        system_message = ""
        if current_phase == "stt_phase":
            system_message = "System is currently processing speech-to-text tasks."
        elif current_phase == "evaluation_phase":
            system_message = "System is currently processing evaluation tasks."
        
        # Add time estimate to message if pending
        if task_status == "pending" and estimated_wait_time > 0:
            if estimated_wait_time < 60:
                time_msg = f"Estimated wait: about {estimated_wait_time} seconds."
            else:
                minutes = estimated_wait_time // 60
                time_msg = f"Estimated wait: about {minutes} minute{'s' if minutes > 1 else ''}."
            
            message = f"{message} {time_msg}"
        
        # Enhance status with detailed queue information
        enhanced_status = {
            **status,
            "users_ahead": task_position,
            "estimated_wait_time": estimated_wait_time,
            "message": message,
            "system_message": system_message,
            "current_phase": current_phase,
            "progress_percent": progress_percent,
            "queue_length": queue_stats.get("queue_length", 0),
            "active_users": queue_stats.get("active_users", 0)
        }
        
        log_info(f"📊 Task status for {task_id}: {task_status}, position: {task_position}, wait: {estimated_wait_time}s")
        return JSONResponse(content=enhanced_status)
    except HTTPException:
        raise
    except Exception as e:
        log_error("❌ Failed to get task status", e)
        log_error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to get task status: {str(e)}")

@app.get("/queue/stats")
async def get_queue_stats():
    """Get current queue statistics and system status."""
    try:
        stats = queue_manager.get_stats()
        return JSONResponse(content=stats)
    except Exception as e:
        log_error("❌ Failed to get queue stats", e)
        raise HTTPException(status_code=500, detail=f"Failed to get queue stats: {str(e)}")

@app.get("/queue/results/{task_id}")
async def get_task_results(task_id: str):
    """Get the complete results for a finished task."""
    try:
        results = queue_manager.get_task_results(task_id)
        if not results:
            raise HTTPException(status_code=404, detail="Task results not found")
        
        return JSONResponse(content=results)
    except HTTPException:
        raise
    except Exception as e:
        log_error("❌ Failed to get task results", e)
        raise HTTPException(status_code=500, detail=f"Failed to get task results: {str(e)}")

@app.post("/queue/force-phase/{phase}")
async def force_phase_switch(phase: str):
    """Force switch to a specific phase (for testing/admin use)."""
    try:
        if phase not in ["stt_phase", "evaluation_phase", "idle"]:
            raise HTTPException(status_code=400, detail="Invalid phase")
        
        target_phase = PhaseType(phase)
        success = queue_manager.force_phase_switch(target_phase)
        
        return JSONResponse(content={
            "success": success,
            "current_phase": queue_manager.current_phase.value,
            "message": f"Phase switch {'successful' if success else 'failed'}"
        })
    except Exception as e:
        log_error("❌ Failed to force phase switch", e)
        raise HTTPException(status_code=500, detail=f"Failed to force phase switch: {str(e)}")

@app.get("/queue/my-results")
async def get_my_results(current_user: Optional[Union[User, Teacher]] = Depends(get_current_user)):
    """Get results for the current user's tasks with enhanced real-time info."""
    try:
        if not current_user:
            raise HTTPException(status_code=401, detail="Authentication required")
        
        user_id = current_user.username
        roll_number = current_user.roll_number if hasattr(current_user, 'roll_number') else None
        
        log_info(f"📊 Fetching results for user: {user_id}, roll_number: {roll_number}")
          # Try to use the user_tasks method if it exists, otherwise fall back to manual iteration
        try:
            # Fall back to manual iteration
            user_tasks = []
            for task_id, task in queue_manager.task_registry.items():
                if task.user_id == user_id and (not roll_number or task.roll_number == roll_number):
                    # Enhanced task info with queue position
                    queue_position = queue_manager.get_queue_position(task_id)
                    user_tasks.append({
                        "task_id": task_id,
                        "status": task.status.value,
                        "created_at": task.created_at.isoformat(),
                        "file_path": task.file_path,
                        "transcript_path": task.transcript_path,
                        "form_path": task.form_path,
                        "profile_rating_path": task.profile_rating_path,
                        "intro_rating_path": task.intro_rating_path,
                        "error_message": task.error_message,
                        "queue_position": queue_position
                    })
            
            # Sort by creation time (newest first)
            user_tasks.sort(key=lambda x: x["created_at"], reverse=True)
            log_info(f"📋 Found {len(user_tasks)} tasks for user {user_id} using fallback method")
        except Exception as e:
            log_error(f"❌ Error using enhanced user tasks method: {e}")
            log_error(traceback.format_exc())
            # Fall back to original method
            user_tasks = []
            for task_id, task in queue_manager.task_registry.items():
                if task.user_id == user_id and (not roll_number or task.roll_number == roll_number):
                    user_tasks.append({
                        "task_id": task_id,
                        "status": task.status.value,
                        "created_at": task.created_at.isoformat(),
                        "file_path": task.file_path,
                        "transcript_path": task.transcript_path,
                        "form_path": task.form_path,
                        "profile_rating_path": task.profile_rating_path,
                        "intro_rating_path": task.intro_rating_path,
                        "error_message": task.error_message
                    })
            log_info(f"📋 Found {len(user_tasks)} tasks for user {user_id} using simple fallback")
        
        # Get the most recent completed task
        completed_tasks = [t for t in user_tasks if t["status"] == "complete"]
        latest_task = None
        
        if completed_tasks:
            latest_task = max(completed_tasks, key=lambda x: x["created_at"])
            log_info(f"📊 Found latest completed task: {latest_task.get('task_id')}")
        
            # For the latest completed task, try to load its file contents if not already included
            if latest_task and "data" not in latest_task:
                try:
                    # Find the task in the registry
                    task_id = latest_task["task_id"]
                    task = queue_manager.task_registry.get(task_id)
                    
                    if task:
                        # Load file contents using helper function
                        content = {}
                        
                        # Load transcript if available
                        if task.transcript_path and Path(task.transcript_path).exists():
                            with open(task.transcript_path, 'r', encoding='utf-8') as f:
                                content["transcript_content"] = f.read()
                                log_info(f"📄 Loaded transcript from {task.transcript_path}")
                        
                        # Load form data if available
                        if task.form_path and Path(task.form_path).exists():
                            with open(task.form_path, 'r', encoding='utf-8') as f:
                                content["form_data"] = json.load(f)
                                log_info(f"📄 Loaded form data from {task.form_path}")
                        
                        # Load profile rating if available
                        if task.profile_rating_path and Path(task.profile_rating_path).exists():
                            with open(task.profile_rating_path, 'r', encoding='utf-8') as f:
                                content["profile_rating"] = json.load(f)
                                log_info(f"📄 Loaded profile rating from {task.profile_rating_path}")
                        
                        # Load intro rating if available
                        if task.intro_rating_path and Path(task.intro_rating_path).exists():
                            with open(task.intro_rating_path, 'r', encoding='utf-8') as f:
                                content["intro_rating"] = json.load(f)
                                log_info(f"📄 Loaded intro rating from {task.intro_rating_path}")
                        
                        latest_task["data"] = content
                except Exception as e:
                    log_error(f"❌ Error loading task file contents: {e}")
                    log_error(traceback.format_exc())
        else:
            log_info(f"📊 No completed tasks found for user {user_id}")
        
        response_data = {
            "user_id": user_id,
            "roll_number": roll_number,
            "all_tasks": user_tasks,
            "latest_completed": latest_task,
            "has_results": len(completed_tasks) > 0
        }
        
        return JSONResponse(content=response_data)
        
    except HTTPException:
        raise
    except Exception as e:
        log_error("❌ Failed to get user results", e)
        log_error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to get user results: {str(e)}")
    except Exception as e:
        log_error("❌ Failed to get user results", e)
        raise HTTPException(status_code=500, detail=f"Failed to get user results: {str(e)}")

# ==================== APPLICATION STARTUP ====================

# ==================== USER AUTHENTICATION ====================
@app.get("/login", response_class=HTMLResponse)
async def get_login():
    html_path = TEMPLATES_DIR / "login.html"
    with open(html_path, "r", encoding="utf-8") as html_file:
        return html_file.read()

@app.post("/login")
async def login(username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    # First try teacher login
    teacher = db.query(Teacher).filter(Teacher.username == username).first()
    if teacher:
        try:
            ph.verify(teacher.hashed_password, password)
            access_token = create_access_token(data={"sub": teacher.username})
            response = RedirectResponse(url="/teacher/dashboard", status_code=status.HTTP_303_SEE_OTHER)
            response.set_cookie(
                key="access_token",
                value=f"Bearer {access_token}",
                httponly=True,
                secure=False,  # Set to False for local development
                samesite='lax',  # Allow proper session isolation while maintaining security
                max_age=1800,  # 30 minutes
                path="/"  # Ensure cookie is scoped properly
            )
            return response
        except VerifyMismatchError:
            raise HTTPException(status_code=401, detail="Invalid username or password")
    
    # If not a teacher, try student login
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    
    try:
        ph.verify(user.hashed_password, password)
        access_token = create_access_token(data={"sub": user.username})
        response = RedirectResponse(url="/index", status_code=status.HTTP_303_SEE_OTHER)
        response.set_cookie(
            key="access_token",
            value=f"Bearer {access_token}",
            httponly=True,
            secure=False,  # Set to False for local development
            samesite='lax',  # Allow proper session isolation while maintaining security
            max_age=1800,  # 30 minutes
            path="/"  # Ensure cookie is scoped properly
        )
        return response
    except VerifyMismatchError:
        raise HTTPException(status_code=401, detail="Invalid username or password")

    
@app.get("/index", response_class=HTMLResponse)
async def get_index(current_user: Optional[Union[User, Teacher]] = Depends(get_current_user)):
    # Check if user is authenticated
    if not current_user:
        # Redirect to login if not authenticated
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    
    html_path = TEMPLATES_DIR / "index.html"
    with open(html_path, "r", encoding="utf-8") as html_file:
        return html_file.read()

#DATABASE SETUP


@app.post("/register")
async def register(
    username: str = Form(...),
    password: str = Form(...),
    roll_number: str = Form(None),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.username == username).first()
    if user:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    if roll_number:
        existing_roll = db.query(User).filter(User.roll_number == roll_number).first()
        if existing_roll:
            raise HTTPException(status_code=400, detail="Roll number already registered")
    
    hashed_password = ph.hash(password)
    new_user = User(
        username=username,
        hashed_password=hashed_password,
        roll_number=roll_number
    )
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

# ==================== TEACHER AUTHENTICATION ====================

@app.post("/teacher/login")
async def teacher_login(username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    teacher = db.query(Teacher).filter(Teacher.username == username).first()
    if not teacher:
        raise HTTPException(status_code=400, detail="Teacher not found")
    try:
        ph.verify(teacher.hashed_password, password)
    except VerifyMismatchError:
        raise HTTPException(status_code=400, detail="Incorrect password")
    
    access_token = create_access_token(data={"sub": teacher.username})
    response = RedirectResponse(url="/teacher/dashboard", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(
        key="access_token",
        value=f"Bearer {access_token}",
        httponly=True,
        secure=False,  # Set to False for local development
        samesite='lax',
        max_age=1800  # 30 minutes
    )
    return response

@app.get("/teacher/dashboard", response_class=HTMLResponse)
async def get_teacher_dashboard(request: Request, current_teacher: dict = Depends(get_current_teacher)):
    html_path = TEMPLATES_DIR / "teacher_dashboard.html"
    with open(html_path, "r", encoding="utf-8") as html_file:
        return html_file.read()

@app.get("/api/auth/me")
async def get_current_user_info(current_user: Optional[Union[User, Teacher]] = Depends(get_current_user)):
    """Get current user profile information"""
    try:
        if not current_user:
            raise HTTPException(status_code=401, detail="Authentication required")
        
        user_info = {
            "username": current_user.username,
            "user_type": "teacher" if hasattr(current_user, "id") and hasattr(current_user, "username") and not hasattr(current_user, "roll_number") else "student"
        }
        
        # Add roll number if user is a student
        if hasattr(current_user, 'roll_number'):
            user_info["roll_number"] = current_user.roll_number
        
        return JSONResponse(content=user_info)
        
    except HTTPException:
        raise
    except Exception as e:
        log_error("❌ Failed to get user info", e)
        raise HTTPException(status_code=500, detail="Failed to retrieve user information")

# ==================== TEACHER MANAGEMENT ====================

@app.post("/teacher/register")
async def register_teacher(
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    teacher = db.query(Teacher).filter(Teacher.username == username).first()
    if teacher:
        raise HTTPException(status_code=400, detail="Username already registered")
    hashed_password = ph.hash(password)
    new_teacher = Teacher(username=username, hashed_password=hashed_password)
    db.add(new_teacher)
    db.commit()
    db.refresh(new_teacher)
    return {"message": "Teacher registered successfully"}

@app.post("/teacher/assign-student")
async def assign_student(
    request: Request,
    teacher_username: str = Form(...),
    student_roll: str = Form(...),
    db: Session = Depends(get_db),
    current_teacher: dict = Depends(get_current_teacher)
):
    # Only allow teachers to assign students to themselves
    if current_teacher["username"] != teacher_username:
        raise HTTPException(status_code=403, detail="Not authorized to assign students to other teachers")
    
    # Check if student exists
    student = db.query(User).filter(User.roll_number == student_roll).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    # Check if mapping already exists
    existing_mapping = db.query(TeacherStudentMap).filter(
        TeacherStudentMap.teacher_username == teacher_username,
        TeacherStudentMap.student_roll == student_roll
    ).first()
    
    if existing_mapping:
        raise HTTPException(status_code=400, detail="Student already assigned to this teacher")
    
    # Create new mapping
    new_mapping = TeacherStudentMap(
        teacher_username=teacher_username,
        student_roll=student_roll
    )
    db.add(new_mapping)
    db.commit()
    
    return {"message": "Student assigned successfully"}

# Update register endpoint to include roll number for students
# (This endpoint was moved above to avoid duplication)

@app.post("/logout")
async def logout():
    """Logout endpoint"""
    response = RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie(key="access_token")
    return response

# ==================== MAIN ENTRY POINT ====================

def main():
    """Main entry point for the application."""
    log_info("🎯 Starting ConvAi-IntroEval server...")
    log_info(f"🌐 Server will be available at: http://{APP_HOST}:{APP_PORT}")
    log_info(f"📚 API documentation: http://{APP_HOST}:{APP_PORT}/docs")
    log_info(f"🐞 Debug mode: {DEBUG_MODE}")
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

# ==================== FILE SERVING API ROUTES ====================

@app.get("/api/files/transcript/{roll_number}/{filename}")
async def get_transcript_file(
    roll_number: str, 
    filename: str,
    current_user: Optional[Union[User, Teacher]] = Depends(get_current_user)
):
    """
    Serve transcript files from roll number subdirectories with access control.
    """
    try:
        if not current_user:
            raise HTTPException(status_code=401, detail="Authentication required")
        
        # For students, ensure they can only access their own files
        if hasattr(current_user, 'roll_number') and current_user.roll_number != roll_number:
            raise HTTPException(status_code=403, detail="Access denied to other user's files")
        
        # Construct the file path
        file_path = TRANSCRIPTION_DIR / roll_number / filename
        
        if not file_path.exists():
            # Try alternative locations
            alt_paths = [
                TRANSCRIPTION_DIR / filename,  # Root directory
                TRANSCRIPTION_DIR / f"{roll_number}_{filename}",  # Roll number prefixed
            ]
            
            for alt_path in alt_paths:
                if alt_path.exists():
                    file_path = alt_path
                    break
            else:
                raise HTTPException(status_code=404, detail=f"Transcript file not found: {filename}")
        
        log_info(f"📄 Serving transcript file: {file_path}")
        
        # Read and return the file content
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return JSONResponse(content={
            "success": True,
            "filename": filename,
            "roll_number": roll_number,
            "content": content,
            "file_path": str(file_path)
        })
        
    except HTTPException:
        raise
    except Exception as e:
        log_error(f"❌ Error serving transcript file {filename}", e)
        raise HTTPException(status_code=500, detail=f"Error serving transcript file: {str(e)}")

@app.get("/api/files/form/{roll_number}/{filename}")
async def get_form_file(
    roll_number: str, 
    filename: str,
    current_user: Optional[Union[User, Teacher]] = Depends(get_current_user)
):
    """
    Serve form files from roll number subdirectories with access control.
    """
    try:
        if not current_user:
            raise HTTPException(status_code=401, detail="Authentication required")
        
        # For students, ensure they can only access their own files
        if hasattr(current_user, 'roll_number') and current_user.roll_number != roll_number:
            raise HTTPException(status_code=403, detail="Access denied to other user's files")
        
        # Construct the file path
        file_path = FILLED_FORMS_DIR / roll_number / filename
        
        if not file_path.exists():
            # Try alternative locations
            alt_paths = [
                FILLED_FORMS_DIR / filename,  # Root directory
                FILLED_FORMS_DIR / f"{roll_number}_{filename}",  # Roll number prefixed
            ]
            
            for alt_path in alt_paths:
                if alt_path.exists():
                    file_path = alt_path
                    break
            else:
                raise HTTPException(status_code=404, detail=f"Form file not found: {filename}")
        
        log_info(f"📄 Serving form file: {file_path}")
          # Read and return the file content
        with open(file_path, 'r', encoding='utf-8') as f:
            content = json.load(f)
        
        return JSONResponse(content={
            "success": True,
            "filename": filename,
            "roll_number": roll_number,
            "data": content,
            "file_path": str(file_path)
        })
        
    except HTTPException:
        raise
    except Exception as e:
        log_error(f"❌ Error serving form file {filename}", e)
        raise HTTPException(status_code=500, detail=f"Error serving form file: {str(e)}")