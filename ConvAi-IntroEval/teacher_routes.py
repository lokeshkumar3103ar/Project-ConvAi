from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import List
import json
import os
from datetime import datetime
from pathlib import Path

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
                "username": student.username,
                "roll_number": student.roll_number
            })

    return {"students": students}

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
        raise HTTPException(status_code=403, detail="Not authorized to view this student's data")

    # Get all JSON files from ratings directory
    ratings_dir = Path("ratings")
    rating_files = []
    
    if ratings_dir.exists():
        for file in ratings_dir.glob("*.json"):
            try:
                with open(file, "r") as f:
                    data = json.load(f)
                    # Check if this rating belongs to the student
                    if data.get("roll_number") == roll_number:
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
        return {"message": f"Successfully assigned student {student.username}"}
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
        "username": student.username,
        "roll_number": student.roll_number
    }
