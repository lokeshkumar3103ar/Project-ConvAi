"""
File Organization Module for ConvAI-IntroEval

This module provides centralized utilities for organizing files by roll numbers
into subdirectories within the existing directory structure.

Author: RTX System
Date: June 8, 2025
"""

import re
import json
from pathlib import Path
from typing import Optional, Tuple, Union, List
from datetime import datetime


def extract_roll_number_from_path(path: Union[str, Path]) -> Optional[str]:
    """
    Extract roll number from file path with validation to avoid false positives.
    
    Args:
        path: File path to analyze
        
    Returns:
        Roll number if found and valid, None otherwise
    """
    path_obj = Path(path)
    
    # Check parent directory names in order (most specific first)
    for parent in [path_obj.parent, path_obj.parent.parent]:
        if parent and parent.name:
            parent_name = parent.name
            
            # Skip common directory names that aren't roll numbers
            common_dirs = {
                'videos', 'transcription', 'filled_forms', 'ratings', 
                'static', 'templates', 'app', 'llm', 'extra scripts',
                'RTXlogs', 'Study Resources', 'extras', 'python scripts'
            }
            
            if parent_name.lower() in common_dirs:
                continue
                
            # Check if it looks like a roll number (starts with dept code + numbers)
            # Examples: STU001, CSE123, ECE456, IT789, etc.
            if re.match(r'^[A-Z]{2,4}\d{3,6}$', parent_name.upper()):
                return parent_name.upper()
                
            # Also check for simple alphanumeric patterns that could be roll numbers
            if re.match(r'^[A-Z0-9]{4,10}$', parent_name.upper()) and any(c.isdigit() for c in parent_name):
                return parent_name.upper()
    
    return None


def get_user_directory(base_dir: Path, roll_number: Optional[str]) -> Path:
    """
    Get user-specific directory, creating it if necessary.
    
    Args:
        base_dir: Base directory (e.g., videos, transcription, etc.)
        roll_number: User's roll number (optional)
        
    Returns:
        Path to user directory (subdirectory if roll_number provided, base_dir otherwise)
    """
    base_dir = Path(base_dir)
    
    if roll_number and roll_number.strip():
        user_dir = base_dir / roll_number.strip()
        user_dir.mkdir(parents=True, exist_ok=True)
        print(f"📁 Created/verified user directory: {user_dir}")
        return user_dir
    else:
        base_dir.mkdir(parents=True, exist_ok=True)
        return base_dir


def organize_path(base_path: Path, filename: str, roll_number: Optional[str]) -> Path:
    """
    Create full file path with roll number organization.
    
    Args:
        base_path: Base directory path
        filename: Name of the file
        roll_number: User's roll number (optional)
        
    Returns:
        Full file path with proper organization
    """
    user_dir = get_user_directory(base_path, roll_number)
    return user_dir / filename


def save_file_with_organization(
    content: Union[str, bytes, dict], 
    base_dir: Path, 
    filename: str, 
    roll_number: Optional[str],
    file_type: str = "text"
) -> Tuple[bool, Path, str]:
    """
    Save file with proper roll number organization.
    
    Args:
        content: Content to save (string, bytes, or dict for JSON)
        base_dir: Base directory for file type
        filename: Name of the file
        roll_number: User's roll number (optional)
        file_type: Type of file ("text", "binary", "json")
        
    Returns:
        Tuple of (success: bool, file_path: Path, status_message: str)
    """
    try:
        file_path = organize_path(base_dir, filename, roll_number)
        
        if file_type == "json":
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(content, f, indent=2, ensure_ascii=False)
        elif file_type == "binary":
            with open(file_path, 'wb') as f:
                f.write(content)
        else:  # text
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
        
        location_info = f"in {roll_number}/ subdirectory" if roll_number else "in root directory"
        status_message = f"File saved {location_info}: {file_path}"
        print(f"✅ {status_message}")
        
        return True, file_path, status_message
        
    except Exception as e:
        error_message = f"Failed to save file {filename}: {str(e)}"
        print(f"❌ {error_message}")
        return False, Path(), error_message


def glob_with_roll_number(
    base_dir: Path, 
    pattern: str, 
    roll_number: Optional[str] = None
) -> List[Path]:
    """
    Search for files using glob pattern in both root and roll number subdirectories.
    
    Args:
        base_dir: Base directory to search in
        pattern: Glob pattern to match
        roll_number: Specific roll number to search in (optional)
        
    Returns:
        List of matching file paths
    """
    base_dir = Path(base_dir)
    matching_files = []
    
    if roll_number:
        # Search in specific roll number subdirectory
        user_dir = base_dir / roll_number
        if user_dir.exists():
            matching_files.extend(list(user_dir.glob(pattern)))
    else:
        # Search in root directory
        matching_files.extend(list(base_dir.glob(pattern)))
        
        # Also search recursively in all subdirectories
        matching_files.extend(list(base_dir.glob(f"**/{pattern}")))
    
    # Remove duplicates and sort by modification time (newest first)
    unique_files = list(set(matching_files))
    unique_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
    
    return unique_files


def find_latest_file_for_user(
    base_dir: Path, 
    pattern: str, 
    roll_number: Optional[str] = None
) -> Optional[Path]:
    """
    Find the most recent file matching pattern for a specific user or globally.
    
    Args:
        base_dir: Base directory to search in
        pattern: Glob pattern to match
        roll_number: User's roll number to search for (optional)
        
    Returns:
        Path to the most recent matching file, or None if not found
    """
    matching_files = glob_with_roll_number(base_dir, pattern, roll_number)
    
    if matching_files:
        latest_file = matching_files[0]  # Already sorted by modification time
        print(f"🔍 Found latest file: {latest_file}")
        return latest_file
    
    print(f"⚠️ No files found matching pattern '{pattern}' for roll number '{roll_number}'")
    return None


def log_file_operation(operation: str, file_path: Path, roll_number: Optional[str] = None):
    """
    Log file operations with timestamp and organization details.
    
    Args:
        operation: Description of the operation
        file_path: Path of the file involved
        roll_number: User's roll number (optional)
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    organization = f" (roll: {roll_number})" if roll_number else " (root)"
    print(f"[{timestamp}] {operation}: {file_path}{organization}")


def validate_roll_number(roll_number: str) -> bool:
    """
    Validate if a string is a valid roll number format.
    
    Args:
        roll_number: String to validate
        
    Returns:
        True if valid roll number format, False otherwise
    """
    if not roll_number or not isinstance(roll_number, str):
        return False
        
    # Allow common patterns: STU001, CSE123, ECE456, IT789, etc.
    return bool(re.match(r'^[A-Z]{2,4}\d{3,6}$', roll_number.upper()))


def get_directory_info(base_dir: Path) -> dict:
    """
    Get information about directory structure and file organization.
    
    Args:
        base_dir: Directory to analyze
        
    Returns:
        Dictionary with directory structure information
    """
    base_dir = Path(base_dir)
    info = {
        "base_directory": str(base_dir),
        "exists": base_dir.exists(),
        "subdirectories": [],
        "root_files": 0,
        "organized_files": 0
    }
    
    if base_dir.exists():
        # Count files in root
        info["root_files"] = len([f for f in base_dir.iterdir() if f.is_file()])
        
        # Analyze subdirectories
        for subdir in base_dir.iterdir():
            if subdir.is_dir():
                roll_number = extract_roll_number_from_path(subdir)
                subdir_info = {
                    "name": subdir.name,
                    "is_roll_number": roll_number is not None,
                    "validated_roll": roll_number,
                    "file_count": len([f for f in subdir.iterdir() if f.is_file()])
                }
                info["subdirectories"].append(subdir_info)
                
                if roll_number:
                    info["organized_files"] += subdir_info["file_count"]
    
    return info


def migration_helper(base_dir: Path, dry_run: bool = True) -> dict:
    """
    Helper function to analyze files that could be migrated to roll number organization.
    
    Args:
        base_dir: Directory to analyze
        dry_run: If True, only analyze without moving files
        
    Returns:
        Dictionary with migration analysis results
    """
    base_dir = Path(base_dir)
    results = {
        "total_files": 0,
        "migratable_files": [],
        "non_migratable_files": [],
        "errors": []
    }
    
    if not base_dir.exists():
        results["errors"].append(f"Directory does not exist: {base_dir}")
        return results
    
    # Analyze files in root directory
    for file_path in base_dir.iterdir():
        if file_path.is_file():
            results["total_files"] += 1
            
            # Try to extract roll number from filename or other context
            extracted_roll = extract_roll_number_from_path(file_path)
            
            if extracted_roll:
                results["migratable_files"].append({
                    "file": str(file_path),
                    "suggested_roll": extracted_roll,
                    "target_location": str(base_dir / extracted_roll / file_path.name)
                })
            else:
                results["non_migratable_files"].append(str(file_path))
    
    return results
