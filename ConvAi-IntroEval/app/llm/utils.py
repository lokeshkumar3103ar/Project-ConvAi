import json
import re
from pathlib import Path
import glob
import sys

# Add parent directory to path to import file_organizer
sys.path.append(str(Path(__file__).parent.parent.parent))
from file_organizer import glob_with_roll_number

DISABLE_LLM = False # ✅ Set to False to enable LLM calls

# Moved from call_llm.py
def preprocess_llm_json_response(response_text):
    """
    Preprocesses and fixes common JSON format issues in LLM responses
    
    Args:
        response_text (str): Raw response text from LLM
        
    Returns:
        str: Preprocessed and cleaned text ready for JSON parsing
    """
    # Check if the response is empty
    if not response_text or response_text.isspace():
        return "{}"
    
    # Remove any non-JSON content at the beginning and end (e.g., markdown code block markers)
    response_text = re.sub(r'^```json\s*', '', response_text)
    response_text = re.sub(r'^```\s*', '', response_text)
    response_text = re.sub(r'\s*```$', '', response_text)
    
    # Fix missing commas between elements in arrays/objects
    response_text = re.sub(r'(["\d])\s*\n\s*"', r'\1,\n"', response_text)
    
    # Fix incorrect comment syntax in JSON (common LLM mistake)
    response_text = re.sub(r'//.*?$', '', response_text, flags=re.MULTILINE)
    
    # Fix double/triple/etc. commas
    response_text = re.sub(r',\s*,+', ',', response_text)
    
    # Fix trailing commas in objects and arrays
    response_text = re.sub(r',(\s*[}\]])', r'\1', response_text)
    
    # Make sure we have valid JSON opening and closing
    if not response_text.strip().startswith('{') and not response_text.strip().startswith('['):
        response_text = '{' + response_text + '}'
    
    # Fix truncated or incomplete JSON - try to balance brackets
    open_braces = response_text.count('{')
    close_braces = response_text.count('}')
    open_brackets = response_text.count('[')
    close_brackets = response_text.count(']')
    
    # Add missing closing braces/brackets
    if open_braces > close_braces:
        response_text += '}' * (open_braces - close_braces)
    if open_brackets > close_brackets:
        response_text += ']' * (open_brackets - close_brackets)
    
    # Remove any text after the last closing bracket/brace that would make it invalid JSON
    last_close_brace = response_text.rfind('}')
    last_close_bracket = response_text.rfind(']')
    last_close = max(last_close_brace, last_close_bracket)
    
    if last_close > 0:
        response_text = response_text[:last_close+1]
    
    # Try to parse it - if it fails, try a more aggressive cleaning
    try:
        json.loads(response_text)
    except json.JSONDecodeError as e:
        print(f"Initial JSON preprocessing couldn't fix all issues: {e}. Attempting more aggressive cleaning...")
        
        # Try more aggressive cleaning - e.g., if there's a specific pattern that's consistently problematic
        # Fix missing quotes around keys (a common LLM error)
        response_text = re.sub(r'([{,]\s*)(\w+)(\s*:)', r'\1"\2"\3', response_text)
        
        # Fix the common error with grading_debug comments
        response_text = re.sub(r'("intro_reported":\s*)"([0-9.]+)"\s*//.*', r'\1"\2"', response_text)
        response_text = re.sub(r'("profile_reported":\s*)"([0-9.]+)"\s*//.*', r'\1"\2"', response_text)
    
    return response_text

def get_latest_form_file(form_path=None):
    """
    Gets the latest form JSON file from the filled_forms directory
    or loads a specific form if path is provided.
    Uses file organization system to search across roll number subdirectories.
    
    Args:
        form_path (str, optional): Path to a specific form file. Defaults to None.
    
    Returns:
        tuple: (file_path, form_data)
    """
    try:
        if form_path:
            # Use the provided path
            file_path = Path(form_path)
            if not file_path.exists():
                print(f"❌ Specified form file not found: {form_path}")
                return None, None
        else:
            # Find the latest file using file organization system
            json_files = glob_with_roll_number("filled_forms", "*.json")
            if not json_files:
                print("❌ No form files found in the filled_forms directory or subdirectories")
                return None, None
            
            # Sort by modified time (newest first)
            file_path = max(json_files, key=lambda x: x.stat().st_mtime)
        
        # Load the JSON data
        print(f"📂 Attempting to load form file: {file_path}")
        with open(file_path, 'r', encoding='utf-8') as f:
            form_data = json.load(f)
        
        print(f"✅ Loaded form file: {file_path}")
        print(f"📊 Form data keys: {list(form_data.keys() if isinstance(form_data, dict) else [])}")
        
        # Check if this is a reference file that points to the actual form
        if isinstance(form_data, dict) and "file" in form_data and isinstance(form_data.get("file"), str):
            referenced_file = form_data.get("file")
            print(f"📄 This is a reference file pointing to: {referenced_file}")
            
            # Load the actual form file that's referenced
            ref_file_path = Path(referenced_file)
            if ref_file_path.exists():
                print(f"📂 Attempting to load referenced form file: {ref_file_path}")
                with open(ref_file_path, 'r', encoding='utf-8') as f:
                    actual_form_data = json.load(f)
                print(f"✅ Successfully loaded referenced form file: {ref_file_path}")
                print(f"📊 Referenced form data keys: {list(actual_form_data.keys() if isinstance(actual_form_data, dict) else [])}")
                return ref_file_path, actual_form_data
            else:
                print(f"❌ Referenced form file not found: {referenced_file}")
        
        return file_path, form_data
    
    except Exception as e:
        print(f"❌ Error loading form file: {str(e)}")
        import traceback
        traceback.print_exc()  # Print the full stack trace for better debugging
        return None, None

def get_latest_transcript_file(transcript_path: str = None):
    """
    Gets the latest transcript file from the transcription directory
    or loads a specific transcript if path is provided.
    Uses file organization system to search across roll number subdirectories.

    Args:
        transcript_path (str, optional): Path to a specific transcript file. Defaults to None.

    Returns:
        tuple: (file_path, transcript_content)
    """
    try:
        if transcript_path:
            # Use the provided path
            file_path = Path(transcript_path)
            if not file_path.exists():
                print(f"❌ Specified transcript file not found: {transcript_path}")
                return None, None
        else:
            # Find the latest file using file organization system
            txt_files = glob_with_roll_number("transcription", "*.txt")
            if not txt_files:
                print("❌ No transcript files found in the transcription directory or subdirectories")
                return None, None
            
            # Sort by modified time (newest first)
            file_path = max(txt_files, key=lambda x: x.stat().st_mtime)

        # Load the transcript content
        with open(file_path, 'r', encoding='utf-8') as f:
            transcript_content = f.read()

        print(f"✅ Loaded transcript file: {file_path}")
        return file_path, transcript_content

    except Exception as e:
        print(f"❌ Error loading transcript file: {str(e)}")
        return None, None

# Functions moved from call_llm.py's fallback implementations
# You may need to replace these with the original, more robust implementations

def enhance_info_coverage_calculation(rating_data, debug_info, info_coverage):
    """
    Placeholder for enhancing information coverage calculation.
    This was a fallback in call_llm.py.
    """
    print("[⚠️ WARNING] Using placeholder enhance_info_coverage_calculation function in utils.py")
    # Basic pass-through, replace with actual logic if needed
    return info_coverage

def generate_default_feedback(rating_data):
    """
    Placeholder for generating default feedback if LLM doesn't provide it.
    This was a fallback in call_llm.py.
    """
    print("[⚠️ WARNING] Using placeholder generate_default_feedback function in utils.py")
    # Basic pass-through, replace with actual logic if needed
    # Example: Ensure 'feedback' key exists
    if "feedback" not in rating_data or not rating_data["feedback"]:
        rating_data["feedback"] = ["No specific feedback generated by LLM. Consider re-evaluating or checking LLM output.", "Ensure all sections of the introduction are well-covered."]
    return rating_data

def fix_json_and_rating_calculation(rating_text, rating_type="profile", enhance_info_coverage_calculation_func=None, generate_default_feedback_func=None):
    """
    Fixes JSON issues and validates/recalculates rating scores.
    
    Args:
        rating_text (str): Raw JSON text from LLM
        rating_type (str): Type of rating ("profile" or "intro")
        enhance_info_coverage_calculation_func (function, optional): Function to enhance info coverage calculation
        generate_default_feedback_func (function, optional): Function to generate default feedback if missing
        
    Returns:
        dict: Processed and validated rating data
    """
    print(f"[🔄] Validating and fixing {rating_type} rating JSON and calculation")
    processed_text = preprocess_llm_json_response(rating_text)
    
    def extract_numeric_score(score_str):
        """Extract numeric value from strings like '2.8/3.0' or '7.20/10'"""
        if isinstance(score_str, (int, float)):
            return float(score_str)
        
        score_str = str(score_str).strip()
        if '/' in score_str:
            # Extract the part before the '/'
            numeric_part = score_str.split('/')[0].strip()
            return float(numeric_part)
        else:
            return float(score_str)
    
    try:
        rating_data = json.loads(processed_text)
        
        # Clean rating values that might be in format like "2.61/10"
        # Profile rating cleanup
        if "profile_rating" in rating_data:
            profile_rating_str = str(rating_data["profile_rating"])
            if "/" in profile_rating_str:
                # Extract just the number before the slash
                cleaned_rating = profile_rating_str.split("/")[0].strip()
                print(f"⚠️ Fixing profile_rating format from '{profile_rating_str}' to '{cleaned_rating}'")
                rating_data["profile_rating"] = cleaned_rating
        
        # Intro rating cleanup
        if "intro_rating" in rating_data:
            intro_rating_str = str(rating_data["intro_rating"])
            if "/" in intro_rating_str:
                # Extract just the number before the slash
                cleaned_rating = intro_rating_str.split("/")[0].strip()
                print(f"⚠️ Fixing intro_rating format from '{intro_rating_str}' to '{cleaned_rating}'")
                rating_data["intro_rating"] = cleaned_rating            # Clean category values in grading_explanation (they're fine to display with slashes)
            # No need to remove the slash format as it's part of the explanation
            if "grading_explanation" in rating_data and isinstance(rating_data["grading_explanation"], dict):
                print(f"✅ Found grading_explanation - ensuring category values are properly formatted")
                # We don't remove slashes from grading_explanation values as they're descriptive text
                # Just ensure they're all strings
                for category, value in rating_data["grading_explanation"].items():
                    if not isinstance(value, str):
                        rating_data["grading_explanation"][category] = str(value)
                        print(f"  ⚠️ Converted {category} value to string: {value}")
                      # Check for completeness format in grading_explanation
                    if category == "completeness" and "/" in value:
                        parts = value.split("/", 1)  # Split at first slash
                        score_part = parts[0].strip()
                        try:
                            score_value = float(score_part)
                            if score_value > 3.0:
                                # Fix the completeness value in the explanation
                                corrected_value = "3.0/" + parts[1]
                                rating_data["grading_explanation"]["completeness"] = corrected_value
                                print(f"  ⚠️ Fixed completeness in grading_explanation: {value} -> {corrected_value}")
                        except ValueError:
                            pass# Basic sum check and correction
        if rating_type == "profile":
            debug_info = rating_data.get("grading_debug", {})
            try:                # Fix completeness score if it exceeds max 3.0 points
                if "completeness_score" in debug_info:
                    original_completeness = extract_numeric_score(debug_info.get("completeness_score", 0.0))
                    if original_completeness > 3.0:
                        print(f"⚠️ Completeness score {original_completeness} exceeds max 3.0, capping to 3.0")
                        debug_info["completeness_score"] = "3.0"
                
                # Recalculate with proper completeness capping
                completeness_score = min(3.0, extract_numeric_score(debug_info.get("completeness_score", 0.0)))
                relevance_score = extract_numeric_score(debug_info.get("relevance_score", 0.0))
                projects_score = extract_numeric_score(debug_info.get("projects_score", 0.0))
                achievements_score = extract_numeric_score(debug_info.get("achievements_score", 0.0))
                calculated_sum = round(completeness_score + relevance_score + projects_score + achievements_score, 1)
            except (ValueError, TypeError) as e:
                print(f"⚠️ Error extracting profile scores: {e}")
                calculated_sum = 0.0
            
            # Safe conversion of profile_rating to float
            try:
                llm_reported_rating = extract_numeric_score(rating_data.get("profile_rating", 0.0))
            except (ValueError, TypeError) as e:
                print(f"⚠️ Error converting profile_rating to float: {e}. Using calculated sum instead.")
                llm_reported_rating = calculated_sum

            if abs(llm_reported_rating - calculated_sum) > 0.01:
                print(f"⚠️ Correcting {rating_type} sum. LLM: {llm_reported_rating}, Calculated: {calculated_sum}")
                rating_data["profile_rating"] = str(calculated_sum)
                # Also ensure debug info is consistent
                if "grading_debug" not in rating_data:
                    rating_data["grading_debug"] = {}
                rating_data["grading_debug"]["calculated_sum"] = str(calculated_sum)
                if "sum_check" in rating_data["grading_debug"]:
                     rating_data["grading_debug"]["sum_check"]["profile_reported"] = str(calculated_sum)
        
        elif rating_type == "intro":
            debug_info = rating_data.get("grading_debug", {})
            try:
                grammar_clarity = extract_numeric_score(debug_info.get("grammar_clarity_score", 0.0))
                structure = extract_numeric_score(debug_info.get("structure_score", 0.0))
                info_coverage = extract_numeric_score(debug_info.get("info_coverage_score", 0.0))
                relevance = extract_numeric_score(debug_info.get("relevance_score", 0.0))
            except (ValueError, TypeError) as e:
                print(f"⚠️ Error extracting intro scores: {e}")
                grammar_clarity = structure = info_coverage = relevance = 0.0
            
            if enhance_info_coverage_calculation_func:
                info_coverage = enhance_info_coverage_calculation_func(rating_data, debug_info, info_coverage)
                debug_info["info_coverage_score"] = info_coverage
            
            calculated_sum = round(grammar_clarity + structure + info_coverage + relevance, 1)
            
            # Safe conversion of intro_rating to float
            try:
                llm_reported_rating = extract_numeric_score(rating_data.get("intro_rating", 0.0))
            except (ValueError, TypeError) as e:
                print(f"⚠️ Error converting intro_rating to float: {e}. Using calculated sum instead.")
                llm_reported_rating = calculated_sum

            if abs(llm_reported_rating - calculated_sum) > 0.01:
                print(f"⚠️ Correcting {rating_type} sum. LLM: {llm_reported_rating}, Calculated: {calculated_sum}")
                rating_data["intro_rating"] = str(calculated_sum)
                if "grading_debug" in rating_data:
                    rating_data["grading_debug"]["calculated_sum"] = str(calculated_sum)
                    if "sum_check" in rating_data["grading_debug"]:
                        rating_data["grading_debug"]["sum_check"]["intro_reported"] = str(calculated_sum)
        
        # Ensure the score is within valid range (0-10)
        score_key = f"{rating_type}_rating"
        if score_key in rating_data:
            try:
                current_score = extract_numeric_score(rating_data[score_key])
                if current_score < 0:
                    print(f"⚠️ Score {current_score} is below 0, correcting to 0.0")
                    rating_data[score_key] = "0.0"
                elif current_score > 10:
                    print(f"⚠️ Score {current_score} is above 10, correcting to 10.0")
                    rating_data[score_key] = "10.0"
            except (ValueError, TypeError) as e:
                print(f"⚠️ Error validating score range: {e}")
        
        # Generate default feedback if missing and function provided
        if generate_default_feedback_func:
            rating_data = generate_default_feedback_func(rating_data)
            
        # Log validation result
        print(f"✅ Successfully validated and fixed {rating_type} rating calculation")
            
        return rating_data
    except json.JSONDecodeError as e:
        print(f"❌ Error parsing JSON in fix_json_and_rating_calculation (utils.py): {e}")
        return {"status": "error", "message": f"Failed to parse JSON: {e}", "raw_response": rating_text}
    except Exception as e:
        print(f"❌ Unexpected error in fix_json_and_rating_calculation (utils.py): {e}")
        return {"status": "error", "message": f"Unexpected error: {e}", "raw_response": rating_text}

def save_rating_to_file(rating_data, file_path_str, rating_type):
    """
    Saves the rating data to a JSON file.
    
    Args:
        rating_data (dict): The rating data to save
        file_path_str (str): Path to save the file to
        rating_type (str): Type of rating ("profile" or "intro")
        
    Returns:
        tuple: (success, message) where success is a boolean and message is a string
    """
    try:
        # Ensure the directory exists
        file_path = Path(file_path_str)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(rating_data, f, indent=2, ensure_ascii=False)
        
        # Log success with the complete file path
        log_msg = f"✅ {rating_type.capitalize()} rating saved to {file_path} ({file_path.stat().st_size} bytes)"
        print(log_msg)
        
        return True, str(file_path)
    except Exception as e:
        # Log error with detailed information
        error_msg = f"❌ Error saving {rating_type} rating to file {file_path_str}: {str(e)}"
        print(error_msg)
        return False, str(e)
