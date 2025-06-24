"""
ConvAi LLM Utilities Module

This module provides essential utilities for the ConvAi introduction evaluation system:
- LLM response preprocessing and JSON extraction (Mistral LLM specific)
- Form and transcript file loading with roll number directory support
- Rating calculation validation and correction logic
- File saving operations for evaluation results

Key Functions:
- preprocess_llm_json_response(): Cleans and extracts JSON from Mistral LLM responses
- get_latest_form_file(): Loads student form data from filled_forms directory
- get_latest_transcript_file(): Loads interview transcripts from transcription directory
- fix_json_and_rating_calculation(): Validates and corrects rating scores
- save_rating_to_file(): Saves evaluation results to JSON files

Note: This module is optimized for Mistral LLM and ConvAi's file organization system.
"""
import json
import re
from pathlib import Path
import sys

# Add parent directory to path to import file_organizer
sys.path.append(str(Path(__file__).parent.parent.parent))
from file_organizer import glob_with_roll_number

DISABLE_LLM = False # ✅ Set to False to enable LLM calls

def preprocess_llm_json_response(response_text):
    """
    Preprocessing for Mistral LLM JSON responses
    Cleans and extracts JSON content from Mistral's response format
    
    Args:
        response_text (str): Raw response text from Mistral LLM
        
    Returns:
        str: Preprocessed and cleaned text ready for JSON parsing
    """
    if not response_text or not response_text.strip():
        return "{}"
    
    # Step 1: Handle common Mistral format (explanatory text followed by JSON)
    lines = response_text.split('\n')
    json_started = False
    json_lines = []
    
    for line in lines:
        # Skip explanatory text until we hit the first backtick or opening brace
        if not json_started:
            if line.strip().startswith('```') or line.strip().startswith('{'):
                json_started = True
                if line.strip().startswith('{'):
                    json_lines.append(line)
            continue
        
        # Stop collecting when we hit closing backticks
        if line.strip() == '```':
            break
            
        # Skip opening backticks line
        if line.strip().startswith('```'):
            continue
            
        json_lines.append(line)
    
    # Reconstruct the JSON
    cleaned_response = '\n'.join(json_lines)
      # Step 2: Basic fallback regex extraction if line parsing didn't work
    if not cleaned_response.strip():
        cleaned_response = response_text
        
        # Remove explanatory text before JSON - find first { or [
        json_start = -1
        for i, char in enumerate(cleaned_response):
            if char in '{[':
                json_start = i
                break
        
        if json_start > 0:
            cleaned_response = cleaned_response[json_start:]
        
        # Remove markdown code blocks
        cleaned_response = re.sub(r'```(?:json)?\s*', '', cleaned_response, flags=re.IGNORECASE)
        cleaned_response = re.sub(r'Here is.*?:\s*', '', cleaned_response, flags=re.IGNORECASE)
        
    # Step 3: Extract JSON content
    json_match = re.search(r'\{.*\}', cleaned_response, re.DOTALL)
    if json_match:
        cleaned_response = json_match.group(0)    # Step 4: Basic JSON cleaning
    # Fix missing commas between basic elements first
    cleaned_response = re.sub(r'(["\d}])\s*\n\s*"', r'\1,\n"', cleaned_response)
    cleaned_response = re.sub(r'(["\d}])\s+"', r'\1,"', cleaned_response)
    
    # Fix the specific case: quoted string ending with period, space, comma, then newline and quote
    # Pattern: "text." ,\n"next_key" should become "text.",\n"next_key"
    cleaned_response = re.sub(r'(\."\s*),\s*\n\s*"([^"]*":\s*)', r'\1,\n"\2', cleaned_response)
    
    # Fix missing commas after quoted strings with various endings
    cleaned_response = re.sub(r'([".!?])\s*\n\s*"([^"]*":\s*)', r'\1,\n"\2', cleaned_response)
    
    # Fix missing commas after numbers followed by newlines and quotes
    cleaned_response = re.sub(r'(\d)\s*\n\s*"([^"]*":\s*)', r'\1,\n"\2', cleaned_response)
    
    # Remove comments (common LLM mistake)
    cleaned_response = re.sub(r'//.*?$', '', cleaned_response, flags=re.MULTILINE)
    
    # Fix multiple commas and trailing commas
    cleaned_response = re.sub(r',\s*,+', ',', cleaned_response)
    cleaned_response = re.sub(r',(\s*[}\]])', r'\1', cleaned_response)
    
    # Fix structural issues - ensure proper brace matching
    open_braces = cleaned_response.count('{')
    close_braces = cleaned_response.count('}')
    if open_braces > close_braces:
        # Add missing closing braces
        missing_braces = open_braces - close_braces
        cleaned_response = cleaned_response.rstrip() + '\n' + '}' * missing_braces
    elif close_braces > open_braces:
        # Remove extra closing braces from the end
        extra_braces = close_braces - open_braces
        for _ in range(extra_braces):
            # Remove the last occurrence of }
            last_brace_idx = cleaned_response.rfind('}')
            if last_brace_idx != -1:
                cleaned_response = cleaned_response[:last_brace_idx] + cleaned_response[last_brace_idx+1:]
    
    # Clean up whitespace
    cleaned_response = cleaned_response.strip()
    
    # Ensure valid JSON structure
    if not cleaned_response.startswith('{') and not cleaned_response.startswith('['):
        cleaned_response = '{' + cleaned_response + '}'
    
    # Final validation and fix common errors
    try:
        json.loads(cleaned_response)
    except json.JSONDecodeError:
        # Fix unquoted keys
        cleaned_response = re.sub(r'([{,]\s*)(\w+)(\s*:)', r'\1"\2"\3', cleaned_response)
    
    return cleaned_response

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
    Enhance information coverage calculation based on rating data and debug info.
    Validates the score and ensures it's within the expected range for intro evaluation.
    
    Args:
        rating_data (dict): The rating data containing evaluation results
        debug_info (dict): Debug information from the rating process
        info_coverage (float): Current information coverage score
        
    Returns:
        float: Enhanced/validated information coverage score
    """
    try:
        # Ensure info_coverage is within valid range (0.0 to 2.5 for intro evaluation)
        if info_coverage < 0.0:
            info_coverage = 0.0
        elif info_coverage > 2.5:
            info_coverage = 2.5
            
        # Round to one decimal place for consistency
        return round(info_coverage, 1)
        
    except (ValueError, TypeError):
        # If there's an error, return a safe default
        return 0.0

def generate_default_feedback(rating_data):
    """
    Generate default feedback if LLM doesn't provide adequate feedback.
    Ensures the rating data contains meaningful feedback for the user.
    
    Args:
        rating_data (dict): The rating data that may need default feedback
        
    Returns:
        dict: Updated rating data with proper feedback
    """
    # Ensure 'feedback' key exists and has meaningful content
    if "feedback" not in rating_data or not rating_data["feedback"]:
        rating_data["feedback"] = [
            "Please review your introduction for clarity and completeness.",
            "Ensure all key personal and professional details are included.",
            "Consider improving the structure and flow of your introduction."
        ]
    elif isinstance(rating_data["feedback"], list) and len(rating_data["feedback"]) == 0:
        rating_data["feedback"] = [
            "No specific feedback was generated. Please review your introduction.",
            "Consider re-evaluating the content for completeness and clarity."
        ]
    
    # Ensure feedback is always a list
    if isinstance(rating_data["feedback"], str):
        rating_data["feedback"] = [rating_data["feedback"]]
        
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
        if "profile_rating" in rating_data:
            profile_rating_str = str(rating_data["profile_rating"])
            if "/" in profile_rating_str:
                cleaned_rating = profile_rating_str.split("/")[0].strip()
                print(f"⚠️ Fixing profile_rating format from '{profile_rating_str}' to '{cleaned_rating}'")
                rating_data["profile_rating"] = cleaned_rating
        
        if "intro_rating" in rating_data:
            intro_rating_str = str(rating_data["intro_rating"])
            if "/" in intro_rating_str:
                cleaned_rating = intro_rating_str.split("/")[0].strip()
                print(f"⚠️ Fixing intro_rating format from '{intro_rating_str}' to '{cleaned_rating}'")
                rating_data["intro_rating"] = cleaned_rating
        
        # Clean grading_explanation values
        if "grading_explanation" in rating_data and isinstance(rating_data["grading_explanation"], dict):
            print(f"✅ Found grading_explanation - ensuring category values are properly formatted")
            for category, value in rating_data["grading_explanation"].items():
                if not isinstance(value, str):
                    rating_data["grading_explanation"][category] = str(value)
                    print(f"  ⚠️ Converted {category} value to string: {value}")
                
                # Fix completeness format if it exceeds max score
                if category == "completeness" and "/" in value:
                    parts = value.split("/", 1)
                    score_part = parts[0].strip()
                    try:
                        score_value = float(score_part)
                        if score_value > 3.0:
                            corrected_value = "3.0/" + parts[1]
                            rating_data["grading_explanation"]["completeness"] = corrected_value
                            print(f"  ⚠️ Fixed completeness in grading_explanation: {value} -> {corrected_value}")
                    except ValueError:
                        pass          # Validate and correct scores based on rating type
        if rating_type == "profile":
            debug_info = rating_data.get("grading_debug", {})
            try:
                # Check for new field names first (updated prompt structure)
                if "practical_foundation_score" in debug_info:
                    # New field names (updated prompt)
                    practical_foundation = extract_numeric_score(debug_info.get("practical_foundation_score", 0.0))
                    technical_competency = extract_numeric_score(debug_info.get("technical_competency_score", 0.0))
                    hands_on_experience = extract_numeric_score(debug_info.get("hands_on_experience_score", 0.0))
                    growth_potential = extract_numeric_score(debug_info.get("growth_potential_score", 0.0))
                    
                    # Fix practical foundation score if it exceeds max 3.0 points
                    if practical_foundation > 3.0:
                        print(f"⚠️ Practical foundation score {practical_foundation} exceeds max 3.0, capping to 3.0")
                        practical_foundation = 3.0
                        debug_info["practical_foundation_score"] = "3.0"                    
                    calculated_sum = round(practical_foundation + technical_competency + hands_on_experience + growth_potential, 1)
                    
                    # Store the calculated sum in debug info
                    debug_info["calculated_sum"] = str(calculated_sum)
                    
                else:
                    # Old field names (legacy support)
                    completeness_score = min(3.0, extract_numeric_score(debug_info.get("completeness_score", 0.0)))
                    relevance_score = extract_numeric_score(debug_info.get("relevance_score", 0.0))
                    projects_score = extract_numeric_score(debug_info.get("projects_score", 0.0))
                    achievements_score = extract_numeric_score(debug_info.get("achievements_score", 0.0))
                    calculated_sum = round(completeness_score + relevance_score + projects_score + achievements_score, 1)
                    
                    # Store the calculated sum in debug info
                    debug_info["calculated_sum"] = str(calculated_sum)
                    
            except (ValueError, TypeError) as e:
                print(f"⚠️ Error extracting profile scores: {e}")
                calculated_sum = 0.0
              # Correct the rating if there's a discrepancy or if it's 0.0
            try:
                llm_reported_rating = extract_numeric_score(rating_data.get("profile_rating", 0.0))
            except (ValueError, TypeError) as e:
                print(f"⚠️ Error converting profile_rating to float: {e}. Using calculated sum instead.")
                llm_reported_rating = calculated_sum

            if abs(llm_reported_rating - calculated_sum) > 0.01 or llm_reported_rating == 0.0:
                print(f"⚠️ Correcting profile sum. LLM: {llm_reported_rating}, Calculated: {calculated_sum}")
                rating_data["profile_rating"] = str(calculated_sum)
                if "grading_debug" not in rating_data:
                    rating_data["grading_debug"] = {}
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
            
            # Store the calculated sum in debug info
            debug_info["calculated_sum"] = str(calculated_sum)            # Safe conversion of intro_rating to float and correct if needed
            try:
                llm_reported_rating = extract_numeric_score(rating_data.get("intro_rating", 0.0))
            except (ValueError, TypeError) as e:
                print(f"⚠️ Error converting intro_rating to float: {e}. Using calculated sum instead.")
                llm_reported_rating = calculated_sum

            if abs(llm_reported_rating - calculated_sum) > 0.01 or llm_reported_rating == 0.0:
                print(f"⚠️ Correcting intro sum. LLM: {llm_reported_rating}, Calculated: {calculated_sum}")
                rating_data["intro_rating"] = str(calculated_sum)
                if "grading_debug" not in rating_data:
                    rating_data["grading_debug"] = {}
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
