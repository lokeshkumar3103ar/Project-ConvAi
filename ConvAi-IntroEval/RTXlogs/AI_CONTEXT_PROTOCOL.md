# AI CONTEXT & PROTOCOL INSTRUCTIONS
**Critical Reference Document - Always Read First**

## 🚨 MANDATORY PROTOCOL: RTX LOGGING FIRST
**RULE #1: ALWAYS LOG BEFORE CODING**

### When User Says "RTX time" or Requests Logging:
1. **IMMEDIATELY** create/update RTX log file for current date
2. **DO NOT** proceed with any other tasks until logging is complete
3. **FORMAT**: `RTXlogs/rtx_[month]_[day]_[year].txt (or) md etc. what ever file is good for that particular entry`
4. **EXAMPLE**: `RTXlogs/rtx_june_8_2025`

### Before Making ANY Code Changes:
1. **FIRST**: Log what you're about to do in RTXlogs directory(Into respective Day's Subfolder)
2. **THEN**: Proceed with actual code modifications
3. **ALWAYS**: Update the log with results and status

## 📋 RTX LOG STRUCTURE TEMPLATE
```markdown
# RTX Log - [Month Day, Year]
**[Project/Feature Name] Development**

## Summary
[Brief description of what was accomplished]

## Files Created/Modified
- `filename.ext` - Description of changes

## Features Implemented
### [Category Name]
- ✅ Feature 1 description
- ✅ Feature 2 description
- ⚠️ Feature 3 (in progress/issues)

## Command Examples
```bash
# Example commands implemented
command --option value
```

## Testing Results
- ✅ Test 1 passed
- ✅ Test 2 passed
- ❌ Test 3 failed (with reason)

## Current System State
[Description of current project state]

## Dependencies Added/Modified
- package_name - Purpose

## Next Steps (if needed)
- [ ] Task 1
- [ ] Task 2

## Notes
[Important observations, warnings, or context]

**Status: [COMPLETED/IN-PROGRESS/BLOCKED]**
```

## 🎯 PROJECT CONTEXT: ConvAi-IntroEval

### Primary Project Location:
`c:\Users\lokes\Downloads\KAMPYUTER\College Projects\Project ConvAi\Project-ConvAi\ConvAi-IntroEval\`

### Key Files & Their Purposes:
- `main.py` - Main FastAPI application
- `models.py` - Database models (User, Teacher, TeacherStudentMap, Note)
- `auth.py` - Authentication and security
- `user_manager.py` - User/teacher management CLI tool
- `users.db` - SQLite database
- `RTXlogs/` - **CRITICAL**: All development logs stored here

### Database Schema:
- **users**: id, username, hashed_password, roll_number
- **teachers**: id, username, hashed_password
- **teacher_student_map**: id, teacher_username, student_roll
- **notes**: id, teacher_username, student_roll, json_filename, note, timestamp

### Current System State (as of June 8, 2025):
- **Users**: 3 total (Lokesh Kumar, 23112064, 23112011)
- **Teachers**: 1 total (dr_teacher)
- **Features**: Full CRUD user/teacher management system implemented

## 🔧 DEVELOPMENT PROTOCOLS

### Code Editing Rules:
1. **Read files first** before making changes
2. **Use appropriate tools**:
   - `insert_edit_into_file` for new code sections
   - `replace_string_in_file` for specific changes
3. **Include context** in replace operations (3-5 lines before/after)
4. **Avoid code repetition** - use `// ...existing code...` comments

### Security Requirements:
- **Password hashing**: Always use Argon2 via `get_password_hash()`
- **Input validation**: Validate all user inputs
- **Database transactions**: Use try/catch with rollback
- **Confirmation prompts**: For destructive operations

### User Environment:
- **OS**: Windows
- **Shell**: PowerShell
- **Python**: Available via `python` command
- **Database**: SQLite (`users.db`)

## 📝 LOGGING CATEGORIES

### Standard Log Sections:
1. **Summary** - What was accomplished
2. **Files Modified** - Complete list with descriptions
3. **Features Implemented** - Categorized with status checkmarks
4. **Commands/Examples** - Working code examples
5. **Testing Results** - What was tested and results
6. **Dependencies** - Any new packages or requirements
7. **Current State** - System status after changes
8. **Next Steps** - Future tasks or improvements needed
9. **Notes** - Important context, warnings, or observations

### Status Indicators:
- ✅ **Completed** - Feature working and tested
- ⚠️ **In Progress** - Partially implemented
- ❌ **Failed/Blocked** - Issue encountered
- 🔄 **Modified** - Updated existing feature
- 🆕 **New** - Brand new implementation

## 🚨 CRITICAL REMINDERS

### ALWAYS Remember:
1. **RTX LOG FIRST** - Never code without logging
2. **Read existing files** before editing
3. **Test commands** before considering complete
4. **Document everything** - Commands, results, issues
5. **Maintain backward compatibility** with existing system
6. **Follow established patterns** in the codebase

### NEVER Do:
- Make changes without logging first
- Skip error handling in database operations
- Store plain text passwords
- Break existing functionality
- Ignore user confirmation for destructive operations

## 🔄 SESSION CONTINUITY

### If AI Instance Resets:
1. **FIRST**: Read this file completely
2. **SECOND**: Check latest RTX log file for current project state
3. **THIRD**: Understand what was last accomplished
4. **FOURTH**: Continue following protocols from that point

### File Locations to Check:
- This file: `RTXlogs/AI_CONTEXT_PROTOCOL.md`
- Latest log: `RTXlogs/rtx_[current_date].md`
- Project status: Check database and main files

## 📋 QUICK REFERENCE COMMANDS

### User Management (Current System):
```powershell
# List users/teachers
python user_manager.py list-users --detailed
python user_manager.py list-teachers --detailed

# Create new records
python user_manager.py create-user --username "name" --roll-number "123"
python user_manager.py create-teacher --username "name"

# Interactive mode
python user_manager.py interactive
```

### Testing Database:
```powershell
# Check if database is accessible
python -c "from models import SessionLocal; print('DB accessible')"
```

## 🎯 CURRENT PROJECT PRIORITIES

### Completed (June 8, 2025):
- ✅ Full user/teacher CRUD operations
- ✅ Command-line interface with interactive mode
- ✅ Security implementation (Argon2 hashing)
- ✅ Database integration and validation
- ✅ Comprehensive documentation

### Potential Next Steps:
- Web interface for user management
- Bulk operations for user/teacher data
- Enhanced reporting and analytics
- User role management extensions
- Export/import functionality

---

**REMEMBER: This file is your memory. Always consult it first, log everything, then code.**

**Last Updated**: June 8, 2025
**Project**: ConvAi-IntroEval User Management System
**Status**: Production Ready(MVP)
