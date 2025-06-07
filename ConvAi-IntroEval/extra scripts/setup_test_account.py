from models import SessionLocal, Teacher
from auth import get_password_hash

def create_test_teacher():
    db = SessionLocal()
    try:
        # Check if test teacher exists
        teacher = db.query(Teacher).filter(Teacher.username == "testteacher").first()
        if teacher:
            print("\nTest teacher already exists.")
            return
        
        # Create test teacher with known password
        hashed_password = get_password_hash("testpass123")
        new_teacher = Teacher(
            username="testteacher",
            hashed_password=hashed_password
        )
        db.add(new_teacher)
        db.commit()
        print("\nCreated test teacher:")
        print("Username: testteacher")
        print("Password: testpass123")
    finally:
        db.close()

if __name__ == "__main__":
    create_test_teacher()
