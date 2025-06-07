from models import Base, engine, SessionLocal, User, Teacher, TeacherStudentMap, Note
from argon2 import PasswordHasher

def init_db():
    # Create all tables
    Base.metadata.drop_all(bind=engine)  # Drop existing tables
    Base.metadata.create_all(bind=engine)
    
    # Create a session
    db = SessionLocal()
    
    try:
        # Create a sample teacher account
        ph = PasswordHasher()
        teacher = Teacher(
            username="teacher1",
            hashed_password=ph.hash("password123")
        )
        db.add(teacher)
        
        # Create some sample student accounts
        students = [
            User(
                username="student1",
                hashed_password=ph.hash("password123"),
                roll_number="R001"
            ),
            User(
                username="student2",
                hashed_password=ph.hash("password123"),
                roll_number="R002"
            )
        ]
        db.add_all(students)
        
        # Commit to save the users
        db.commit()
        
        # Create teacher-student mapping
        mapping = TeacherStudentMap(
            teacher_username="teacher1",
            student_roll="R001"
        )
        db.add(mapping)
        
        db.commit()
        print("✅ Database initialized successfully!")
        print("\nSample accounts created:")
        print("Teacher: username='teacher1', password='password123'")
        print("Student: username='student1', password='password123', roll='R001'")
        print("Student: username='student2', password='password123', roll='R002'")
        
    except Exception as e:
        print(f"❌ Error initializing database: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    init_db()
