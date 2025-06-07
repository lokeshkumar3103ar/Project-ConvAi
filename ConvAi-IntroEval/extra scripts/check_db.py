from models import SessionLocal, Teacher

def check_teachers():
    db = SessionLocal()
    try:
        teachers = db.query(Teacher).all()
        print("\nTeachers in database:")
        for teacher in teachers:
            print(f"Username: {teacher.username}")
    finally:
        db.close()

if __name__ == "__main__":
    check_teachers()
