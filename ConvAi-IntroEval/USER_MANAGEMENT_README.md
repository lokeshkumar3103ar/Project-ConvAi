# User and Teacher Management Scripts

This directory contains comprehensive management tools for the ConvAi-IntroEval system users and teachers.

## Files

### 1. `user_manager.py` - Command Line Interface
A comprehensive command-line tool for managing users and teachers with all CRUD operations.

### 2. `web_user_manager.py` - Web Interface
A web-based interface for managing users and teachers with a user-friendly GUI.

## Installation

Make sure you have all required dependencies:

```powershell
pip install fastapi uvicorn sqlalchemy argon2-cffi jose tabulate jinja2 python-multipart
```

## Usage

### Command Line Interface (`user_manager.py`)

#### Interactive Mode (Recommended for beginners)
```powershell
python user_manager.py
# or
python user_manager.py interactive
```

#### Command Line Operations

**List operations:**
```powershell
# List all users
python user_manager.py list-users

# List all users with detailed information
python user_manager.py list-users --detailed

# List all teachers
python user_manager.py list-teachers

# List all teachers with detailed information
python user_manager.py list-teachers --detailed
```

**View specific records:**
```powershell
# View user by ID, username, or roll number
python user_manager.py view-user --identifier "john_doe"
python user_manager.py view-user --identifier "12345"
python user_manager.py view-user --identifier "1"

# View teacher by ID or username
python user_manager.py view-teacher --identifier "teacher1"
python user_manager.py view-teacher --identifier "1"
```

**Create new records:**
```powershell
# Create new user
python user_manager.py create-user --username "john_doe" --roll-number "2023001"

# Create new teacher
python user_manager.py create-teacher --username "teacher1"
```

**Update records:**
```powershell
# Update user information
python user_manager.py update-user --identifier "john_doe" --new-username "john_smith" --new-roll-number "2023002"

# Update teacher information
python user_manager.py update-teacher --identifier "teacher1" --new-username "prof_smith"
```

**Password management:**
```powershell
# Reset user password
python user_manager.py reset-password --user-type user --identifier "john_doe"

# Reset teacher password
python user_manager.py reset-password --user-type teacher --identifier "teacher1"
```

**Delete records:**
```powershell
# Delete user (with confirmation prompt)
python user_manager.py delete-user --identifier "john_doe"

# Delete user without confirmation
python user_manager.py delete-user --identifier "john_doe" --confirm

# Delete teacher
python user_manager.py delete-teacher --identifier "teacher1"
```

**Manage teacher-student relationships:**
```powershell
# Map student to teacher
python user_manager.py map-student --teacher-username "teacher1" --student-roll "2023001"

# Remove student from teacher
python user_manager.py unmap-student --teacher-username "teacher1" --student-roll "2023001"

# View all mappings
python user_manager.py view-mappings
```

### Web Interface (`web_user_manager.py`)

Start the web server:
```powershell
python web_user_manager.py
```

Then open your browser and go to: `http://localhost:8001`

The web interface provides:
- **Dashboard**: Overview of system statistics
- **User Management**: Create, view, edit, and delete users
- **Teacher Management**: Create, view, edit, and delete teachers
- **Relationship Management**: Create and manage teacher-student mappings
- **Password Reset**: Reset passwords for users and teachers

## Features

### User Management
- ✅ Create new users with username, password, and optional roll number
- ✅ View user details including assigned teachers and notes count
- ✅ Update username and roll number
- ✅ Reset passwords securely
- ✅ Delete users (with cascade deletion of related data)
- ✅ List all users with optional detailed view

### Teacher Management
- ✅ Create new teachers with username and password
- ✅ View teacher details including assigned students and notes count
- ✅ Update teacher username
- ✅ Reset passwords securely
- ✅ Delete teachers (with cascade deletion of related data)
- ✅ List all teachers with optional detailed view

### Relationship Management
- ✅ Map students to teachers
- ✅ Remove student-teacher mappings
- ✅ View all current mappings
- ✅ Prevent duplicate mappings

### Security Features
- ✅ Secure password hashing using Argon2
- ✅ Duplicate username/roll number prevention
- ✅ Safe deletion with confirmation prompts
- ✅ Input validation and error handling

### Data Integrity
- ✅ Cascade deletion (removing users/teachers removes related mappings and notes)
- ✅ Foreign key constraint checking
- ✅ Transaction rollback on errors
- ✅ Unique constraint enforcement

## Examples

### Common Workflow Examples

**Setting up a new class:**
```powershell
# 1. Create teacher
python user_manager.py create-teacher --username "prof_mathematics"

# 2. Create students
python user_manager.py create-user --username "alice_student" --roll-number "2023001"
python user_manager.py create-user --username "bob_student" --roll-number "2023002"

# 3. Map students to teacher
python user_manager.py map-student --teacher-username "prof_mathematics" --student-roll "2023001"
python user_manager.py map-student --teacher-username "prof_mathematics" --student-roll "2023002"

# 4. Verify setup
python user_manager.py view-teacher --identifier "prof_mathematics"
python user_manager.py view-mappings
```

**Bulk password reset (interactive mode):**
```powershell
python user_manager.py
# Choose option 9 (Reset password) multiple times
```

**User cleanup:**
```powershell
# Remove graduated students
python user_manager.py delete-user --identifier "2020001" --confirm
python user_manager.py delete-user --identifier "2020002" --confirm

# View remaining users
python user_manager.py list-users --detailed
```

## Database Schema

The scripts work with the following database tables:
- `users`: Student accounts with username, password, and roll number
- `teachers`: Teacher accounts with username and password
- `teacher_student_map`: Relationships between teachers and students
- `notes`: Teacher notes about students
- `password_reset_tokens`: Password reset functionality

## Error Handling

The scripts include comprehensive error handling for:
- Duplicate usernames/roll numbers
- Missing records
- Database connection issues
- Invalid input data
- Foreign key constraint violations

## Security Considerations

- Passwords are hashed using Argon2 (industry standard)
- No plain text passwords are stored
- Input validation prevents SQL injection
- Confirmation prompts for destructive operations
- Secure password input (hidden when typing)

## Troubleshooting

**Common Issues:**

1. **"User not found" error**: Make sure the identifier (ID, username, or roll number) is correct
2. **"Username already exists"**: Choose a different username
3. **Database locked error**: Make sure no other instances are running
4. **Permission denied**: Run with appropriate user permissions
5. **Module not found**: Install missing dependencies with pip

**Getting Help:**
- Use `python user_manager.py --help` for command reference
- Use interactive mode for guided operations
- Check the database file exists and is accessible
- Verify all dependencies are installed

## Integration with Main Application

These management scripts work alongside the main ConvAi-IntroEval application:
- They use the same database (`users.db`)
- They respect the same data models and constraints
- They can be run while the main application is running
- Changes are immediately reflected in the main application

## Backup Recommendations

Before performing bulk operations, consider backing up your database:
```powershell
copy users.db users_backup.db
```

This ensures you can recover if something goes wrong during management operations.
