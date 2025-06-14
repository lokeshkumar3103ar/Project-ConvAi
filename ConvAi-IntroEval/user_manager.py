#!/usr/bin/env python3
"""
User and Teacher Management Script for ConvAi-IntroEval

This script provides comprehensive management functionality for users and teachers
including viewing, editing, password reset, and deletion operations.

Usage:
    python user_manager.py [command] [options]

Commands:
    list-users          List all users
    list-teachers       List all teachers
    view-user           View specific user details
    view-teacher        View specific teacher details
    create-user         Create a new user
    create-teacher      Create a new teacher
    update-user         Update user information
    update-teacher      Update teacher information
    reset-password      Reset user/teacher password
    delete-user         Delete a user
    delete-teacher      Delete a teacher
    map-student         Map student to teacher
    unmap-student       Unmap student from teacher
    view-mappings       View teacher-student mappings
    interactive         Start interactive mode

Author: ConvAi Team
Date: June 2025
"""

import argparse
import getpass
import sys
from datetime import datetime
from typing import Optional, List
from sqlalchemy.orm import Session
from argon2 import PasswordHasher
from tabulate import tabulate

# Import models and database setup
from models import User, Teacher, TeacherStudentMap, Note, SessionLocal, get_db
from auth import get_password_hash, verify_password

ph = PasswordHasher()

class UserManager:
    def __init__(self):
        self.db = SessionLocal()
    
    def __del__(self):
        if hasattr(self, 'db'):
            self.db.close()
    
    # ==================== USER OPERATIONS ====================
    
    def list_users(self, detailed: bool = False) -> None:
        """List all users in the system"""
        users = self.db.query(User).all()
        
        if not users:
            print("No users found in the system.")
            return
        
        if detailed:
            headers = ["Username", "Roll Number", "Assigned Teachers"]
            data = []
            for user in users:
                # Get assigned teachers
                mappings = self.db.query(TeacherStudentMap).filter(
                    TeacherStudentMap.student_roll == user.roll_number
                ).all()
                teachers = [mapping.teacher_username for mapping in mappings]
                
                data.append([
                    user.username,
                    user.roll_number or "Not Set",
                    ", ".join(teachers) if teachers else "None"
                ])
        else:
            headers = ["ID", "Username", "Roll Number"]
            data = [[user.id, user.username, user.roll_number or "Not Set"] for user in users]
        
        print(f"\n=== Users ({len(users)} total) ===")
        print(tabulate(data, headers=headers, tablefmt="grid"))
    
    def view_user(self, identifier: str) -> None:
        """View detailed information about a specific user"""
        user = self._get_user(identifier)
        if not user:
            return
        
        # Get assigned teachers
        mappings = self.db.query(TeacherStudentMap).filter(
            TeacherStudentMap.student_roll == user.roll_number
        ).all()
        teachers = [mapping.teacher_username for mapping in mappings]
        
        # Get notes count
        notes_count = self.db.query(Note).filter(Note.student_roll == user.roll_number).count()
        
        print(f"\n=== User Details ===")
        print(f"ID: {user.id}")
        print(f"Username: {user.username}")
        print(f"Roll Number: {user.roll_number or 'Not Set'}")
        print(f"Assigned Teachers: {', '.join(teachers) if teachers else 'None'}")
        print(f"Notes Count: {notes_count}")
    
    def create_user(self, username: str, password: str = None, roll_number: str = None) -> None:
        """Create a new user"""
        # Check if username already exists
        existing_user = self.db.query(User).filter(User.username == username).first()
        if existing_user:
            print(f"Error: User with username '{username}' already exists.")
            return
        
        # Check if roll number already exists
        if roll_number:
            existing_roll = self.db.query(User).filter(User.roll_number == roll_number).first()
            if existing_roll:
                print(f"Error: User with roll number '{roll_number}' already exists.")
                return
        
        # Get password if not provided
        if not password:
            password = getpass.getpass("Enter password for new user: ")
            confirm_password = getpass.getpass("Confirm password: ")
            if password != confirm_password:
                print("Error: Passwords do not match.")
                return
        
        # Create user
        hashed_password = get_password_hash(password)
        new_user = User(
            username=username,
            hashed_password=hashed_password,
            roll_number=roll_number
        )
        
        try:
            self.db.add(new_user)
            self.db.commit()
            print(f"User '{username}' created successfully.")
        except Exception as e:
            self.db.rollback()
            print(f"Error creating user: {e}")
    
    def update_user(self, identifier: str, new_username: str = None, new_roll_number: str = None) -> None:
        """Update user information"""
        user = self._get_user(identifier)
        if not user:
            return
        
        try:
            if new_username:
                # Check if new username already exists
                existing = self.db.query(User).filter(
                    User.username == new_username, User.id != user.id
                ).first()
                if existing:
                    print(f"Error: Username '{new_username}' already exists.")
                    return
                user.username = new_username
            
            if new_roll_number:
                # Check if new roll number already exists
                existing = self.db.query(User).filter(
                    User.roll_number == new_roll_number, User.id != user.id
                ).first()
                if existing:
                    print(f"Error: Roll number '{new_roll_number}' already exists.")
                    return
                user.roll_number = new_roll_number
            
            self.db.commit()
            print(f"User updated successfully.")
            self.view_user(str(user.id))
        except Exception as e:
            self.db.rollback()
            print(f"Error updating user: {e}")
    
    def delete_user(self, identifier: str, confirm: bool = False) -> None:
        """Delete a user and all related data"""
        user = self._get_user(identifier)
        if not user:
            return
        
        if not confirm:
            response = input(f"Are you sure you want to delete user '{user.username}'? This will also delete all related mappings and notes. (y/N): ")
            if response.lower() != 'y':
                print("Deletion cancelled.")
                return
        
        try:
            # Delete related data
            self.db.query(TeacherStudentMap).filter(
                TeacherStudentMap.student_roll == user.roll_number
            ).delete()
            
            self.db.query(Note).filter(Note.student_roll == user.roll_number).delete()
            
            # Delete user
            self.db.delete(user)
            self.db.commit()
            print(f"User '{user.username}' deleted successfully.")
        except Exception as e:
            self.db.rollback()
            print(f"Error deleting user: {e}")
    
    # ==================== TEACHER OPERATIONS ====================
    
    def list_teachers(self, detailed: bool = False) -> None:
        """List all teachers in the system"""
        teachers = self.db.query(Teacher).all()
        
        if not teachers:
            print("No teachers found in the system.")
            return
        
        if detailed:
            headers = ["ID", "Username", "Assigned Students", "Notes Count"]
            data = []
            for teacher in teachers:
                # Get assigned students
                mappings = self.db.query(TeacherStudentMap).filter(
                    TeacherStudentMap.teacher_username == teacher.username
                ).all()
                students = [mapping.student_roll for mapping in mappings]
                
                # Get notes count
                notes_count = self.db.query(Note).filter(
                    Note.teacher_username == teacher.username
                ).count()
                
                data.append([
                    teacher.id,
                    teacher.username,
                    ", ".join(students) if students else "None",
                    notes_count
                ])
        else:
            headers = ["ID", "Username"]
            data = [[teacher.id, teacher.username] for teacher in teachers]
        
        print(f"\n=== Teachers ({len(teachers)} total) ===")
        print(tabulate(data, headers=headers, tablefmt="grid"))
    
    def view_teacher(self, identifier: str) -> None:
        """View detailed information about a specific teacher"""
        teacher = self._get_teacher(identifier)
        if not teacher:
            return
        
        # Get assigned students
        mappings = self.db.query(TeacherStudentMap).filter(
            TeacherStudentMap.teacher_username == teacher.username
        ).all()
        students = [mapping.student_roll for mapping in mappings]
        
        # Get notes count
        notes_count = self.db.query(Note).filter(
            Note.teacher_username == teacher.username
        ).count()
        
        print(f"\n=== Teacher Details ===")
        print(f"ID: {teacher.id}")
        print(f"Username: {teacher.username}")
        print(f"Assigned Students: {', '.join(students) if students else 'None'}")
        print(f"Notes Count: {notes_count}")
    
    def create_teacher(self, username: str, password: str = None) -> None:
        """Create a new teacher"""
        # Check if username already exists
        existing_teacher = self.db.query(Teacher).filter(Teacher.username == username).first()
        if existing_teacher:
            print(f"Error: Teacher with username '{username}' already exists.")
            return
        
        # Get password if not provided
        if not password:
            password = getpass.getpass("Enter password for new teacher: ")
            confirm_password = getpass.getpass("Confirm password: ")
            if password != confirm_password:
                print("Error: Passwords do not match.")
                return
        
        # Create teacher
        hashed_password = get_password_hash(password)
        new_teacher = Teacher(
            username=username,
            hashed_password=hashed_password
        )
        
        try:
            self.db.add(new_teacher)
            self.db.commit()
            print(f"Teacher '{username}' created successfully.")
        except Exception as e:
            self.db.rollback()
            print(f"Error creating teacher: {e}")
    
    def update_teacher(self, identifier: str, new_username: str = None) -> None:
        """Update teacher information"""
        teacher = self._get_teacher(identifier)
        if not teacher:
            return
        
        try:
            if new_username:
                # Check if new username already exists
                existing = self.db.query(Teacher).filter(
                    Teacher.username == new_username, Teacher.id != teacher.id
                ).first()
                if existing:
                    print(f"Error: Username '{new_username}' already exists.")
                    return
                
                old_username = teacher.username
                teacher.username = new_username
                
                # Update related mappings
                mappings = self.db.query(TeacherStudentMap).filter(
                    TeacherStudentMap.teacher_username == old_username
                ).all()
                for mapping in mappings:
                    mapping.teacher_username = new_username
            
            self.db.commit()
            print(f"Teacher updated successfully.")
            self.view_teacher(str(teacher.id))
        except Exception as e:
            self.db.rollback()
            print(f"Error updating teacher: {e}")
    
    def delete_teacher(self, identifier: str, confirm: bool = False) -> None:
        """Delete a teacher and all related data"""
        teacher = self._get_teacher(identifier)
        if not teacher:
            return
        
        if not confirm:
            response = input(f"Are you sure you want to delete teacher '{teacher.username}'? This will also delete all related mappings and notes. (y/N): ")
            if response.lower() != 'y':
                print("Deletion cancelled.")
                return
        
        try:
            # Delete related data
            self.db.query(TeacherStudentMap).filter(
                TeacherStudentMap.teacher_username == teacher.username
            ).delete()
            
            self.db.query(Note).filter(Note.teacher_username == teacher.username).delete()
            
            # Delete teacher
            self.db.delete(teacher)
            self.db.commit()
            print(f"Teacher '{teacher.username}' deleted successfully.")
        except Exception as e:
            self.db.rollback()
            print(f"Error deleting teacher: {e}")
    
    # ==================== PASSWORD OPERATIONS ====================
    
    def reset_password(self, user_type: str, identifier: str, new_password: str = None) -> None:
        """Reset password for user or teacher"""
        if user_type.lower() == 'user':
            entity = self._get_user(identifier)
        elif user_type.lower() == 'teacher':
            entity = self._get_teacher(identifier)
        else:
            print("Error: user_type must be 'user' or 'teacher'")
            return
        
        if not entity:
            return
        
        # Get new password if not provided
        if not new_password:
            new_password = getpass.getpass("Enter new password: ")
            confirm_password = getpass.getpass("Confirm new password: ")
            if new_password != confirm_password:
                print("Error: Passwords do not match.")
                return
        
        try:
            entity.hashed_password = get_password_hash(new_password)
            self.db.commit()
            print(f"Password reset successfully for {user_type} '{entity.username}'.")
        except Exception as e:
            self.db.rollback()
            print(f"Error resetting password: {e}")
    
    # ==================== MAPPING OPERATIONS ====================
    
    def map_student_to_teacher(self, teacher_username: str, student_roll: str) -> None:
        """Map a student to a teacher"""
        # Verify teacher exists
        teacher = self.db.query(Teacher).filter(Teacher.username == teacher_username).first()
        if not teacher:
            print(f"Error: Teacher '{teacher_username}' not found.")
            return
        
        # Verify student exists
        student = self.db.query(User).filter(User.roll_number == student_roll).first()
        if not student:
            print(f"Error: Student with roll number '{student_roll}' not found.")
            return
        
        # Check if mapping already exists
        existing_mapping = self.db.query(TeacherStudentMap).filter(
            TeacherStudentMap.teacher_username == teacher_username,
            TeacherStudentMap.student_roll == student_roll
        ).first()
        
        if existing_mapping:
            print(f"Error: Student '{student_roll}' is already mapped to teacher '{teacher_username}'.")
            return
        
        try:
            new_mapping = TeacherStudentMap(
                teacher_username=teacher_username,
                student_roll=student_roll
            )
            self.db.add(new_mapping)
            self.db.commit()
            print(f"Student '{student_roll}' mapped to teacher '{teacher_username}' successfully.")
        except Exception as e:
            self.db.rollback()
            print(f"Error creating mapping: {e}")
    
    def unmap_student_from_teacher(self, teacher_username: str, student_roll: str) -> None:
        """Unmap a student from a teacher"""
        mapping = self.db.query(TeacherStudentMap).filter(
            TeacherStudentMap.teacher_username == teacher_username,
            TeacherStudentMap.student_roll == student_roll
        ).first()
        
        if not mapping:
            print(f"Error: No mapping found between teacher '{teacher_username}' and student '{student_roll}'.")
            return
        
        try:
            self.db.delete(mapping)
            self.db.commit()
            print(f"Student '{student_roll}' unmapped from teacher '{teacher_username}' successfully.")
        except Exception as e:
            self.db.rollback()
            print(f"Error removing mapping: {e}")
    
    def view_mappings(self) -> None:
        """View all teacher-student mappings"""
        mappings = self.db.query(TeacherStudentMap).all()
        
        if not mappings:
            print("No teacher-student mappings found.")
            return
        
        headers = ["Teacher", "Student Roll", "Student Username"]
        data = []
        
        for mapping in mappings:
            student = self.db.query(User).filter(User.roll_number == mapping.student_roll).first()
            student_username = student.username if student else "Unknown"
            data.append([mapping.teacher_username, mapping.student_roll, student_username])
        
        print(f"\n=== Teacher-Student Mappings ({len(mappings)} total) ===")
        print(tabulate(data, headers=headers, tablefmt="grid"))
    
    # ==================== HELPER METHODS ====================
    
    def _get_user(self, identifier: str) -> Optional[User]:
        """Get user by ID, username, or roll number"""
        try:
            # Try by ID first
            if identifier.isdigit():
                user = self.db.query(User).filter(User.id == int(identifier)).first()
                if user:
                    return user
            
            # Try by username
            user = self.db.query(User).filter(User.username == identifier).first()
            if user:
                return user
            
            # Try by roll number
            user = self.db.query(User).filter(User.roll_number == identifier).first()
            if user:
                return user
            
            print(f"Error: User '{identifier}' not found.")
            return None
        except Exception as e:
            print(f"Error finding user: {e}")
            return None
    
    def _get_teacher(self, identifier: str) -> Optional[Teacher]:
        """Get teacher by ID or username"""
        try:
            # Try by ID first
            if identifier.isdigit():
                teacher = self.db.query(Teacher).filter(Teacher.id == int(identifier)).first()
                if teacher:
                    return teacher
            
            # Try by username
            teacher = self.db.query(Teacher).filter(Teacher.username == identifier).first()
            if teacher:
                return teacher
            
            print(f"Error: Teacher '{identifier}' not found.")
            return None
        except Exception as e:
            print(f"Error finding teacher: {e}")
            return None
    
    # ==================== INTERACTIVE MODE ====================
    
    def interactive_mode(self) -> None:
        """Start interactive management mode"""
        print("\n" + "="*50)
        print("ConvAi User & Teacher Management System")
        print("="*50)
        
        while True:
            print("\nAvailable commands:")
            print("1.  List users")
            print("2.  List teachers")
            print("3.  View user details")
            print("4.  View teacher details")
            print("5.  Create user")
            print("6.  Create teacher")
            print("7.  Update user")
            print("8.  Update teacher")
            print("9.  Reset password")
            print("10. Delete user")
            print("11. Delete teacher")
            print("12. Map student to teacher")
            print("13. Unmap student from teacher")
            print("14. View mappings")
            print("0.  Exit")
            
            try:
                choice = input("\nEnter your choice (0-14): ").strip()
                
                if choice == "0":
                    print("Goodbye!")
                    break
                elif choice == "1":
                    detailed = input("Show detailed view? (y/N): ").lower() == 'y'
                    self.list_users(detailed)
                elif choice == "2":
                    detailed = input("Show detailed view? (y/N): ").lower() == 'y'
                    self.list_teachers(detailed)
                elif choice == "3":
                    identifier = input("Enter user ID, username, or roll number: ").strip()
                    self.view_user(identifier)
                elif choice == "4":
                    identifier = input("Enter teacher ID or username: ").strip()
                    self.view_teacher(identifier)
                elif choice == "5":
                    username = input("Enter username: ").strip()
                    roll_number = input("Enter roll number (optional): ").strip() or None
                    self.create_user(username, roll_number=roll_number)
                elif choice == "6":
                    username = input("Enter username: ").strip()
                    self.create_teacher(username)
                elif choice == "7":
                    identifier = input("Enter user ID, username, or roll number: ").strip()
                    new_username = input("Enter new username (or press Enter to skip): ").strip() or None
                    new_roll_number = input("Enter new roll number (or press Enter to skip): ").strip() or None
                    self.update_user(identifier, new_username, new_roll_number)
                elif choice == "8":
                    identifier = input("Enter teacher ID or username: ").strip()
                    new_username = input("Enter new username (or press Enter to skip): ").strip() or None
                    self.update_teacher(identifier, new_username)
                elif choice == "9":
                    user_type = input("Reset password for (user/teacher): ").strip()
                    identifier = input("Enter ID or username: ").strip()
                    self.reset_password(user_type, identifier)
                elif choice == "10":
                    identifier = input("Enter user ID, username, or roll number: ").strip()
                    self.delete_user(identifier)
                elif choice == "11":
                    identifier = input("Enter teacher ID or username: ").strip()
                    self.delete_teacher(identifier)
                elif choice == "12":
                    teacher_username = input("Enter teacher username: ").strip()
                    student_roll = input("Enter student roll number: ").strip()
                    self.map_student_to_teacher(teacher_username, student_roll)
                elif choice == "13":
                    teacher_username = input("Enter teacher username: ").strip()
                    student_roll = input("Enter student roll number: ").strip()
                    self.unmap_student_from_teacher(teacher_username, student_roll)
                elif choice == "14":
                    self.view_mappings()
                else:
                    print("Invalid choice. Please try again.")
                    
            except KeyboardInterrupt:
                print("\n\nGoodbye!")
                break
            except Exception as e:
                print(f"Error: {e}")

def main():
    parser = argparse.ArgumentParser(description="ConvAi User & Teacher Management System")
    parser.add_argument("command", nargs="?", help="Command to execute")
    parser.add_argument("--username", help="Username")
    parser.add_argument("--roll-number", help="Roll number")
    parser.add_argument("--password", help="Password")
    parser.add_argument("--new-username", help="New username")
    parser.add_argument("--new-roll-number", help="New roll number")
    parser.add_argument("--teacher-username", help="Teacher username")
    parser.add_argument("--student-roll", help="Student roll number")
    parser.add_argument("--user-type", choices=["user", "teacher"], help="User type for password reset")
    parser.add_argument("--identifier", help="User/Teacher identifier (ID, username, or roll number)")
    parser.add_argument("--detailed", action="store_true", help="Show detailed view")
    parser.add_argument("--confirm", action="store_true", help="Skip confirmation prompts")
    
    args = parser.parse_args()
    
    manager = UserManager()
    
    try:
        if not args.command or args.command == "interactive":
            manager.interactive_mode()
        elif args.command == "list-users":
            manager.list_users(args.detailed)
        elif args.command == "list-teachers":
            manager.list_teachers(args.detailed)
        elif args.command == "view-user":
            if not args.identifier:
                args.identifier = input("Enter user ID, username, or roll number: ").strip()
            manager.view_user(args.identifier)
        elif args.command == "view-teacher":
            if not args.identifier:
                args.identifier = input("Enter teacher ID or username: ").strip()
            manager.view_teacher(args.identifier)
        elif args.command == "create-user":
            if not args.username:
                args.username = input("Enter username: ").strip()
            manager.create_user(args.username, args.password, args.roll_number)
        elif args.command == "create-teacher":
            if not args.username:
                args.username = input("Enter username: ").strip()
            manager.create_teacher(args.username, args.password)
        elif args.command == "update-user":
            if not args.identifier:
                args.identifier = input("Enter user ID, username, or roll number: ").strip()
            manager.update_user(args.identifier, args.new_username, args.new_roll_number)
        elif args.command == "update-teacher":
            if not args.identifier:
                args.identifier = input("Enter teacher ID or username: ").strip()
            manager.update_teacher(args.identifier, args.new_username)
        elif args.command == "reset-password":
            if not args.user_type:
                args.user_type = input("Reset password for (user/teacher): ").strip()
            if not args.identifier:
                args.identifier = input("Enter ID or username: ").strip()
            manager.reset_password(args.user_type, args.identifier, args.password)
        elif args.command == "delete-user":
            if not args.identifier:
                args.identifier = input("Enter user ID, username, or roll number: ").strip()
            manager.delete_user(args.identifier, args.confirm)
        elif args.command == "delete-teacher":
            if not args.identifier:
                args.identifier = input("Enter teacher ID or username: ").strip()
            manager.delete_teacher(args.identifier, args.confirm)
        elif args.command == "map-student":
            if not args.teacher_username:
                args.teacher_username = input("Enter teacher username: ").strip()
            if not args.student_roll:
                args.student_roll = input("Enter student roll number: ").strip()
            manager.map_student_to_teacher(args.teacher_username, args.student_roll)
        elif args.command == "unmap-student":
            if not args.teacher_username:
                args.teacher_username = input("Enter teacher username: ").strip()
            if not args.student_roll:
                args.student_roll = input("Enter student roll number: ").strip()
            manager.unmap_student_from_teacher(args.teacher_username, args.student_roll)
        elif args.command == "view-mappings":
            manager.view_mappings()
        else:
            print(f"Unknown command: {args.command}")
            print("Use --help for available commands")
    
    except KeyboardInterrupt:
        print("\nOperation cancelled.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
