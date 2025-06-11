# models.py

from sqlalchemy import Column, Integer, String, create_engine, ForeignKey, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime, timedelta

DATABASE_URL = "sqlite:///./users.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    roll_number = Column(String, unique=True, nullable=True, index=True)

class Teacher(Base):
    __tablename__ = "teachers"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    roll_number = Column(String, unique=True, nullable=True, index=True)  # Add roll_number for consistency

class TeacherStudentMap(Base):
    __tablename__ = "teacher_student_map"
    id = Column(Integer, primary_key=True, index=True)
    teacher_username = Column(String, ForeignKey("teachers.username"))
    student_roll = Column(String, ForeignKey("users.roll_number"))

class Note(Base):
    __tablename__ = "notes"
    id = Column(Integer, primary_key=True, index=True)
    teacher_username = Column(String, ForeignKey("teachers.username"))
    student_roll = Column(String, ForeignKey("users.roll_number"))
    json_filename = Column(String)
    note = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)

class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    token = Column(String, unique=True, index=True)
    expires_at = Column(DateTime)

Base.metadata.create_all(bind=engine)
