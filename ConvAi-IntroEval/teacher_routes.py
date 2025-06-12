from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import List, Dict, Any
import json
import os
from datetime import datetime
from pathlib import Path
import glob
import statistics

from models import get_db, TeacherStudentMap, User, Note
from auth import get_current_teacher

router = APIRouter()

# Initialize Jinja2 templates
templates = Jinja2Templates(directory="templates")

@router.get("/api/teacher/students/{teacher_username}")
async def get_teacher_students(
    request: Request,
    teacher_username: str,
    current_teacher: dict = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    # Verify teacher is accessing their own data
    if current_teacher["username"] != teacher_username:
        raise HTTPException(status_code=403, detail="Not authorized to view other teacher's data")

    # Get all student mappings for this teacher
    student_mappings = db.query(TeacherStudentMap).filter(
        TeacherStudentMap.teacher_username == teacher_username
    ).all()

    # Get student details
    students = []
    for mapping in student_mappings:
        student = db.query(User).filter(
            User.roll_number == mapping.student_roll
        ).first()
        if student:
            students.append({
                "name": student.name,
                "roll_number": student.roll_number
            })

    return {"students": students}

@router.get("/api/student/analytics/{roll_number}")
async def get_student_analytics(
    request: Request,
    roll_number: str,
    current_teacher: dict = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """
    Get comprehensive analytics for a student including all ratings, trends, and insights
    """
    # Verify teacher has access to this student
    student_mapping = db.query(TeacherStudentMap).filter(
        TeacherStudentMap.teacher_username == current_teacher["username"],
        TeacherStudentMap.student_roll == roll_number
    ).first()
    
    if not student_mapping:
        raise HTTPException(status_code=403, detail="Not authorized to view this student's data")

    # Get all JSON files from student's rating directory
    student_ratings_dir = Path(f"ratings/{roll_number}")
    analytics_data = {
        "roll_number": roll_number,
        "total_evaluations": 0,
        "intro_ratings": [],
        "profile_ratings": [],
        "score_trends": [],
        "performance_summary": {},
        "latest_feedback": {},
        "improvement_areas": [],
        "strengths": []
    }
    
    if not student_ratings_dir.exists():
        return analytics_data
    
    # Collect all rating files
    intro_files = []
    profile_files = []
    
    for file in student_ratings_dir.glob("*.json"):
        try:
            with open(file, "r") as f:
                data = json.load(f)
                timestamp = data.get("evaluation_timestamp", "")
                
                if "intro_rating" in file.name:
                    intro_files.append({
                        "file": file.name,
                        "data": data,
                        "timestamp": timestamp,
                        "score": float(data.get("intro_rating", 0))
                    })
                elif "profile_rating" in file.name:
                    profile_files.append({
                        "file": file.name,
                        "data": data,
                        "timestamp": timestamp,
                        "score": float(data.get("profile_rating", 0))
                    })
        except (json.JSONDecodeError, ValueError):
            continue
    
    # Sort by timestamp
    intro_files.sort(key=lambda x: x["timestamp"])
    profile_files.sort(key=lambda x: x["timestamp"])
    
    analytics_data["intro_ratings"] = intro_files
    analytics_data["profile_ratings"] = profile_files
    analytics_data["total_evaluations"] = len(intro_files) + len(profile_files)
    
    # Create score trends for charts
    if intro_files:
        analytics_data["score_trends"].append({
            "type": "intro",
            "scores": [item["score"] for item in intro_files],
            "timestamps": [item["timestamp"][:10] for item in intro_files],  # Date only
            "average": round(statistics.mean([item["score"] for item in intro_files]), 2),
            "latest": intro_files[-1]["score"],
            "improvement": round(intro_files[-1]["score"] - intro_files[0]["score"], 2) if len(intro_files) > 1 else 0
        })
    
    if profile_files:
        analytics_data["score_trends"].append({
            "type": "profile",
            "scores": [item["score"] for item in profile_files],
            "timestamps": [item["timestamp"][:10] for item in profile_files],  # Date only
            "average": round(statistics.mean([item["score"] for item in profile_files]), 2),
            "latest": profile_files[-1]["score"],
            "improvement": round(profile_files[-1]["score"] - profile_files[0]["score"], 2) if len(profile_files) > 1 else 0
        })
    
    # Performance summary
    all_scores = []
    if intro_files:
        all_scores.extend([item["score"] for item in intro_files])
    if profile_files:
        all_scores.extend([item["score"] for item in profile_files])
    
    if all_scores:
        analytics_data["performance_summary"] = {
            "overall_average": round(statistics.mean(all_scores), 2),
            "highest_score": max(all_scores),
            "lowest_score": min(all_scores),
            "total_assessments": len(all_scores),
            "score_variance": round(statistics.variance(all_scores) if len(all_scores) > 1 else 0, 2)
        }
    
    # Latest feedback and areas for improvement
    if intro_files and intro_files[-1]["data"].get("feedback"):
        analytics_data["latest_feedback"]["intro"] = intro_files[-1]["data"]["feedback"]
    if profile_files and profile_files[-1]["data"].get("grading_explanation"):
        analytics_data["latest_feedback"]["profile"] = profile_files[-1]["data"]["grading_explanation"]
    
    # Extract improvement areas and strengths from latest evaluations
    improvement_areas = set()
    strengths = set()
    
    if intro_files:
        latest_intro = intro_files[-1]["data"]
        if latest_intro.get("feedback"):
            improvement_areas.update(latest_intro["feedback"])
        if latest_intro.get("insights"):
            strengths.update(latest_intro["insights"])
    
    if profile_files:
        latest_profile = profile_files[-1]["data"]
        grading = latest_profile.get("grading_explanation", {})
        for key, value in grading.items():
            if "weak" in value.lower() or "needs" in value.lower() or "could" in value.lower():
                improvement_areas.add(f"{key.replace('_', ' ').title()}: {value}")
            elif "excellent" in value.lower() or "strong" in value.lower() or "good" in value.lower():
                strengths.add(f"{key.replace('_', ' ').title()}: {value}")
    
    analytics_data["improvement_areas"] = list(improvement_areas)[:5]  # Limit to top 5
    analytics_data["strengths"] = list(strengths)[:5]  # Limit to top 5
    
    return analytics_data

@router.get("/api/student/ratings/{roll_number}")
async def get_student_ratings(
    request: Request,
    roll_number: str,
    current_teacher: dict = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    # Verify teacher has access to this student
    student_mapping = db.query(TeacherStudentMap).filter(
        TeacherStudentMap.teacher_username == current_teacher["username"],
        TeacherStudentMap.student_roll == roll_number
    ).first()
    
    if not student_mapping:
        raise HTTPException(status_code=403, detail="Not authorized to view this student's data")    # Get all JSON files from student's rating directory
    student_ratings_dir = Path(f"ratings/{roll_number}")
    rating_files = []
    
    if student_ratings_dir.exists():
        for file in student_ratings_dir.glob("*.json"):
            try:
                with open(file, "r") as f:
                    data = json.load(f)
                    rating_files.append({
                        "filename": file.name,
                        "data": data
                    })
            except json.JSONDecodeError:
                continue

    return {"ratings": rating_files}

@router.get("/api/notes/{roll_number}")
async def get_student_notes(
    request: Request,
    roll_number: str,
    current_teacher: dict = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    # Verify teacher has access to this student
    student_mapping = db.query(TeacherStudentMap).filter(
        TeacherStudentMap.teacher_username == current_teacher["username"],
        TeacherStudentMap.student_roll == roll_number
    ).first()
    
    if not student_mapping:
        raise HTTPException(status_code=403, detail="Not authorized to view this student's notes")

    notes = db.query(Note).filter(
        Note.student_roll == roll_number
    ).order_by(Note.timestamp.desc()).all()

    return {
        "notes": [
            {
                "id": note.id,
                "teacher_username": note.teacher_username,
                "json_filename": note.json_filename,
                "note": note.note,
                "timestamp": note.timestamp.isoformat()
            }
            for note in notes
        ]
    }

@router.post("/api/notes/")
async def add_note(
    request: Request,
    current_teacher: dict = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    data = await request.json()
    required_fields = ["student_roll", "json_filename", "note"]
    
    if not all(field in data for field in required_fields):
        raise HTTPException(status_code=400, detail="Missing required fields")

    # Verify teacher has access to this student
    student_mapping = db.query(TeacherStudentMap).filter(
        TeacherStudentMap.teacher_username == current_teacher["username"],
        TeacherStudentMap.student_roll == data["student_roll"]
    ).first()
    
    if not student_mapping:
        raise HTTPException(status_code=403, detail="Not authorized to add notes for this student")

    new_note = Note(
        teacher_username=current_teacher["username"],
        student_roll=data["student_roll"],
        json_filename=data["json_filename"],
        note=data["note"]
    )
    
    db.add(new_note)
    db.commit()
    db.refresh(new_note)

    return {
        "id": new_note.id,
        "teacher_username": new_note.teacher_username,
        "json_filename": new_note.json_filename,
        "note": new_note.note,
        "timestamp": new_note.timestamp.isoformat()
    }

@router.post("/api/teacher/assign_student")
async def assign_student(
    request: Request,
    student_data: dict,
    current_teacher: dict = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    # Verify the student exists
    student = db.query(User).filter(
        User.roll_number == student_data["student_roll"]
    ).first()
    
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
        
    # Check if student is already assigned to this teacher
    existing_mapping = db.query(TeacherStudentMap).filter(
        TeacherStudentMap.teacher_username == current_teacher["username"],
        TeacherStudentMap.student_roll == student_data["student_roll"]
    ).first()
    
    if existing_mapping:
        raise HTTPException(status_code=400, detail="Student is already assigned to you")
        
    # Create new mapping
    new_mapping = TeacherStudentMap(
        teacher_username=current_teacher["username"],
        student_roll=student_data["student_roll"]
    )
    
    try:
        db.add(new_mapping)
        db.commit()
        return {"message": f"Successfully assigned student {student.name}"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to assign student")

@router.get("/teacher/dashboard", response_class=HTMLResponse)
async def teacher_dashboard(
    request: Request,
    current_teacher: dict = Depends(get_current_teacher)
):
    return templates.TemplateResponse(
        "teacher_dashboard.html",
        {"request": request, "teacher_username": current_teacher["username"]}
    )

@router.get("/api/teacher/search_student/{roll_number}")
async def search_student(
    request: Request,
    roll_number: str,
    current_teacher: dict = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    student = db.query(User).filter(
        User.roll_number == roll_number
    ).first()
    
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
        
    return {
        "name": student.name,
        "roll_number": student.roll_number
    }
