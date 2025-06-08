import requests
import json
import datetime
from pathlib import Path
import asyncio

# Import helper functions from .utils
try:
    from .utils import get_latest_form_file, fix_json_and_rating_calculation, save_rating_to_file, DISABLE_LLM
except ImportError: # Fallback for direct execution if needed
    from utils import get_latest_form_file, fix_json_and_rating_calculation, save_rating_to_file, DISABLE_LLM


def get_profile_rating_prompt(form_data: dict) -> str:
    """Creates and returns the prompt for evaluating profile rating"""
    # Print the form data for debugging
    print("\n=== DEBUG: Form Data for Profile Rating ===")
    print(f"Form data type: {type(form_data)}")
    print(f"Form data keys: {list(form_data.keys()) if isinstance(form_data, dict) else 'Not a dictionary'}")
    
    # Try different ways to extract the fields depending on the structure
    extracted_fields = None
    
    # Case 1: Direct extracted_fields in the form_data
    if "extracted_fields" in form_data and form_data["extracted_fields"]:
        extracted_fields = form_data["extracted_fields"]
        print("✅ Found extracted_fields directly in form_data")
    
    # Case 2: Data might be nested in a data field
    elif "data" in form_data and isinstance(form_data["data"], dict):
        if "extracted_fields" in form_data["data"]:
            extracted_fields = form_data["data"]["extracted_fields"]
            print("✅ Found extracted_fields in form_data['data']")
    
    # Case 3: The form data itself might be a string containing the fields
    elif isinstance(form_data, str):
        extracted_fields = form_data
        print("✅ Form data is a string, using directly")
    
    # Fallback: if nothing else works, try to use the whole form_data as a string
    if not extracted_fields:
        print("⚠️ Could not find extracted_fields in the expected structure, using whole form_data")
        extracted_fields = str(form_data)
    
    print(f"Extracted fields type: {type(extracted_fields)}")
    print(f"Extracted fields preview: {str(extracted_fields)[:200]}...")
    print("=== END DEBUG ===\n")
    
    return f"""    You are an expert HR evaluator with extensive experience in candidate assessment and selection. Your task is to provide an objective, data-driven rating of candidate profiles based on specific evaluation criteria.
    
    PROFILE RATING INSTRUCTIONS:
    - Analyze the candidate profile data carefully and thoroughly
    - Apply the rubrics objectively and consistently
    - Base your assessment ONLY on information explicitly present in the profile
    - Do not make assumptions about unstated qualifications
    - Calculate scores precisely according to the formulas provided
      PROFILE RATING RUBRICS (out of 10 total points):    
    1. Completeness (max 3.0 points):
        - Count all fields that are **not empty or "Not Mentioned"**.
        - Use this formula exactly:  
            `completeness_score = min(3.0, (filled_fields / 35) * 3)`
        - NEVER exceed 3.0 points for this category even if calculation yields higher value.
        🔒 Your response must:
        - Follow the formula exactly.
        - Always cap the result at 3.0 even if the calculation yields a higher number.
        - Round the result to **2 decimal places**.
        - Always include the count of filled fields and the exact formula used.

       • The 35 fields are categorized as:
         - Personal Details (4 fields): Name, Age, Languages known, Professional Status
         - Education Background (5 fields): Degree & specialization, College/university, Year of graduation, CGPA, Notable achievements/certifications
         - Projects (6 fields): Project name, Technology/tools used, Problem statement, Solution implemented, Outcomes/accomplishments, Your role
         - Work Experience (6 fields): Company name, Role, Time period, Total years of experience, Skills gained, Key responsibilities & achievements
         - Skills (4 fields): Technical skills, Soft skills, Tools & technologies, Domain expertise
         - Achievements & Activities (3 fields): Professional achievements, Extracurricular activities, Relevant hobbies
         - Personal Traits (1 field): Personality Traits
         - Role Expectation (1 field): Target Job Role
         - Career Preferences (5 fields): Career goals, Preferred location, Willingness to relocate, Work environment preference, Expected Salary Range
       • MUST format as: "X.X/3 – X of 35 fields filled (X% completion)."

    2. Relevance to Target Role (0-2 points):
       • Examine skills, experience, and education against the stated target role
       • 2.0 = Strong alignment: Skills/experience directly match the target role (e.g., fullstack dev → HTML, JS, DB)
       • 1.5 = Good alignment: Most key skills present but missing some important elements
       • 1.0 = Partial alignment: Some relevant skills but significant gaps
       • 0.5 = Minimal alignment: Few relevant skills mentioned
       • 0.0 = No alignment: No relevance shown to target role or target role not mentioned
       • Provide specific examples of matching or missing skills in your explanation    
    3. Projects/Internships Quality (0-3 points):
    IMPORTANT: Look for ALL project mentions, not just detailed ones
       • 3.0 = Exceptional: Multiple (2+) well-described projects OR 1 exceptionally detailed project with technologies, clear problem/solution, and outcomes
       • 2.5 = Very good: 1 well-detailed project with technologies, problem statement, solution, and some outcomes
       • 2.0 = Good: 1+ projects with decent detail (technologies + problem/solution mentioned)
       • 1.5 = Adequate: 1+ projects mentioned with basic technologies or brief description
       • 1.0 = Minimal: Project(s) mentioned but very vague description (just project name or basic mention)
       • 0.5 = Very minimal: Unclear project references or academic assignments only
       • 0.0 = None: No projects or internships mentioned at all
       • SCORING TIP: Multiple projects should score higher even if individually less detailed

    4. Achievements and Extra-curricular Value (0-2 points):
       • 2.0 = Outstanding: Multiple significant achievements (certifications, awards, leadership roles)
       • 1.5 = Strong: Several achievements or activities with clear relevance to professional growth
       • 1.0 = Moderate: At least 1 meaningful achievement or activity mentioned
       • 0.5 = Limited: Vague mention of achievements without specifics
       • 0.0 = None: No achievements or activities mentioned
       • Consider the relevance and significance of achievements to the target role

    FORM DATA TO EVALUATE:
    {extracted_fields}      Return your evaluation as a JSON object with this exact structure:
    {{
      "profile_rating": X.X,
      "grading_explanation": {{
        "completeness": "X.X/3 – X of 35 fields filled (X% completion).",
        "relevance": "X/2 – [specific explanation with examples of matching/missing skills]",
        "projects_or_internships": "X/3 – [detailed assessment with examples]",
        "extra_achievements": "X/2 – [specific achievements and their relevance]"
      }},
      "grading_debug": {{
        "completeness_score": X.X,
        "relevance_score": X.X,
        "projects_score": X.X,
        "achievements_score": X.X,
        "calculated_sum": X.X,
        "sum_check": {{
          "profile_expected": 10,
          "profile_reported": X.X
        }},
        "notes": "[any observations about strengths/weaknesses and improvement areas]"
      }}
    }}
      IMPORTANT FINAL CHECKS:
      1. Ensure completeness_score is NEVER greater than 3.0, regardless of the calculation result
      2. Double-check that profile_rating equals completeness_score + relevance_score + projects_score + achievements_score
      3. Respond ONLY with the JSON object, no additional text.
    """

def evaluate_profile_rating(form_path=None) -> dict:
    """
    Evaluates a profile rating based on the form data
    
    Args:
        form_path (str, optional): Path to specific form file. Defaults to None (uses latest).
    
    Returns:
        dict: Rating results
    """
    try:
        # Load the form data
        file_path, form_data = get_latest_form_file(form_path)
        if not form_data:
            return {"status": "error", "message": "Failed to load form data"}
          # Generate the evaluation prompt
        prompt = get_profile_rating_prompt(form_data)
    
        if DISABLE_LLM:
            print("[⚠️ LLM DISABLED] Skipping evaluate_profile_rating LLM call.")
            return {
                "status": "disabled",
                "message": "LLM call skipped (safe edit mode)"
        }

        # Call the LLM with streaming enabled
        print("📤 [CONSOLE] Sending profile rating request to LLM API...")
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "mistral",
                "prompt": prompt,
                "stream": True,  # Enable streaming
                "temperature": 0.0,  # Remove randomness for consistent output
                "top_p": 1.0,        # Set top_p to 1.0 for deterministic sampling
                "top_k": 40,         # Limit token selection to top 40 tokens
                "seed": 42,          # Fixed seed for reproducible results
                "stop": ["\n\n"]     # Stop token for clean output termination
            },
            stream=True  # Stream the HTTP response
        )
        
        if response.status_code == 200:
            # Process the streaming response line by line
            print(f"📥 [CONSOLE] Receiving streaming profile rating response from LLM API")
            
            rating_text = ""
            
            for line in response.iter_lines():
                if line:
                    # Parse the streaming line
                    json_line = json.loads(line.decode('utf-8'))
                    
                    if 'response' in json_line:
                        chunk = json_line['response']
                        rating_text += chunk
                        
                        # Print the chunk to the console immediately
                        print(chunk, end='', flush=True)
                    
                    # Check if the stream is done
                    if json_line.get('done', False):
                        print()  # New line after completion
                        break
            
            try:
                # Parse the JSON response
                # rating_data = json.loads(rating_text) # Old parsing
                
                # Use the utility function to parse and fix JSON
                rating_data = fix_json_and_rating_calculation(
                    rating_text,
                    rating_type="profile" 
                    # No need to pass enhance_info_coverage or generate_default_feedback for profile
                )

                if rating_data.get("status") == "error":
                    print(f"❌ Error processing LLM response for profile rating: {rating_data.get('message')}")
                    return rating_data # Return the error structure

                # ---- START: Fix and verify profile rating calculation ----
                # This section is now largely handled by fix_json_and_rating_calculation
                # We can keep a simplified check or remove if confident in the util.
                # For now, let's assume fix_json_and_rating_calculation handles it.
                # If specific logic for profile rating sum check beyond the util is needed, it can be added here.
                # Example:
                # Ensure profile_rating key exists after util processing
                if "profile_rating" not in rating_data:
                    print("⚠️ 'profile_rating' key missing after fix_json_and_rating_calculation. Attempting to recalculate.")
                    # Fallback recalculation if needed, though util should handle this
                    debug_info = rating_data.get("grading_debug", {})
                    completeness = float(debug_info.get("completeness_score", 0.0))
                    relevance = float(debug_info.get("relevance_score", 0.0))
                    projects = float(debug_info.get("projects_score", 0.0))
                    achievements = float(debug_info.get("achievements_score", 0.0))
                    calculated_sum_by_python = round(completeness + relevance + projects + achievements, 1)
                    rating_data["profile_rating"] = calculated_sum_by_python
                    if "grading_debug" not in rating_data: rating_data["grading_debug"] = {}
                    rating_data["grading_debug"]["calculated_sum"] = calculated_sum_by_python
                    if "sum_check" not in rating_data["grading_debug"]: rating_data["grading_debug"]["sum_check"] = {}
                    rating_data["grading_debug"]["sum_check"]["profile_reported"] = calculated_sum_by_python
                    rating_data["grading_debug"]["sum_check"]["profile_expected"] = 10.0                # ---- END: Fix and verify profile rating calculation ----
                
                # Add metadata about the evaluated file
                rating_data["evaluated_file"] = str(file_path)
                rating_data["evaluation_timestamp"] = datetime.datetime.now().isoformat()
                
                # NOTE: File saving is now handled by the background process in main.py
                # This eliminates duplicate file saving and ensures proper file organization
                print(f"✅ Profile rating evaluation completed for {file_path}")
                print("📁 File will be saved by background process with proper organization")
                
                # Print the final profile rating for debugging
                print(f"Profile rating result: {rating_data}")
                
                return rating_data
            
            except Exception as e: # Catch any other unexpected error during processing
                print(f"❌ Unexpected error after attempting to fix JSON in profile_rater (sync): {str(e)}")
                return {
                    "status": "error", 
                    "message": f"Unexpected error processing response: {str(e)}",
                    "raw_response": rating_text
                }
    
    except Exception as e:
        print(f"Exception in profile rating evaluation: {str(e)}")
        return {"status": "error", "message": f"Exception: {str(e)}"}

async def evaluate_profile_rating_stream(form_path=None):
    """
    Streaming version of profile rating evaluation
    
    Args:
        form_path (str, optional): Path to specific form file. Defaults to None (uses latest).
    
    Yields:
        str: Server-sent events data with profile rating progress
    """
    try:
        yield f"data: {json.dumps({'status': 'progress', 'message': 'Loading form data...'})}\\n\\n"
        await asyncio.sleep(0.1)
        
        # Load the form data
        file_path, form_data = get_latest_form_file(form_path)
        if not form_data:
            yield f"data: {json.dumps({'status': 'error', 'message': 'Failed to load form data'})}\\n\\n"
            return
        
        yield f"data: {json.dumps({'status': 'progress', 'message': 'Generating evaluation prompt...'})}\\n\\n"
        await asyncio.sleep(0.1)
        
        prompt = get_profile_rating_prompt(form_data)
        
        if DISABLE_LLM:
            print("[⚠️ LLM DISABLED] Skipping evaluate_profile_rating_stream LLM call.")
            yield f"data: {json.dumps({'status': 'disabled', 'message': 'LLM call skipped (safe edit mode)'})}\\n\\n"
            return
        
        yield f"data: {json.dumps({'status': 'progress', 'message': 'Calling LLM for profile rating...'})}\\n\\n"
        await asyncio.sleep(0.1)
        
        # Call the LLM in streaming mode
        print(f"📤 [CONSOLE] Sending profile rating request to LLM API...")
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "mistral",
                "prompt": prompt,
                "stream": True,  # Enable streaming
                "temperature": 0.0,
                "top_p": 1.0,
                "top_k": 40,
                "seed": 42,
                "stop": ["\\n\\n"]
            },
            stream=True  # Stream the HTTP response
        )
        
        rating_text = ""
        
        if response.status_code == 200:
            # Process the streaming response line by line
            print(f"📥 [CONSOLE] Receiving streaming profile rating response from LLM API")
            
            for line in response.iter_lines():
                if line:
                    # Parse the streaming line
                    json_line = json.loads(line.decode('utf-8'))
                    
                    if 'response' in json_line:
                        chunk = json_line['response']
                        rating_text += chunk
                        
                        # Send a progress update every ~100 chars or so
                        if len(chunk) > 0 and (len(rating_text) % 100 < len(chunk)):
                            yield f"data: {json.dumps({'status': 'evaluating', 'message': 'Receiving evaluation...', 'text_length': len(rating_text)})}\\n\\n"
                    
                    # Check if the stream is done
                    if json_line.get('done', False):
                        break
            
            # Tell the client we're processing the response
            yield f"data: {json.dumps({'status': 'progress', 'message': 'Processing profile rating...'})}\\n\\n"
            await asyncio.sleep(0.1)
            
            try:
                # Parse the JSON response
                # rating_data = json.loads(rating_text) # Old parsing

                # Use the utility function to parse and fix JSON
                rating_data = fix_json_and_rating_calculation(
                    rating_text,
                    rating_type="profile"
                )

                if rating_data.get("status") == "error":
                    error_msg = f"Error processing LLM response for profile rating (stream): {rating_data.get('message')}"
                    print(f"❌ [CONSOLE] {error_msg}")
                    yield f"data: {json.dumps({'status': 'error', 'message': error_msg, 'raw_response': rating_data.get('raw_response', rating_text)})}\\n\\n"
                    return

                # ---- START: Fix and verify profile rating calculation ----
                # As with the sync version, this is largely handled by the utility.
                # We can keep a simplified check or remove if confident in the util.
                if "profile_rating" not in rating_data:
                    print("⚠️ 'profile_rating' key missing after fix_json_and_rating_calculation (stream). Attempting to recalculate.")
                    # Fallback recalculation if needed
                    debug_info = rating_data.get("grading_debug", {})
                    completeness = float(debug_info.get("completeness_score", 0.0))
                    relevance = float(debug_info.get("relevance_score", 0.0))
                    projects = float(debug_info.get("projects_score", 0.0))
                    achievements = float(debug_info.get("achievements_score", 0.0))
                    calculated_sum_by_python = round(completeness + relevance + projects + achievements, 1)
                    rating_data["profile_rating"] = calculated_sum_by_python
                    if "grading_debug" not in rating_data: rating_data["grading_debug"] = {}
                    rating_data["grading_debug"]["calculated_sum"] = calculated_sum_by_python
                    if "sum_check" not in rating_data["grading_debug"]: rating_data["grading_debug"]["sum_check"] = {}
                    rating_data["grading_debug"]["sum_check"]["profile_reported"] = calculated_sum_by_python
                    rating_data["grading_debug"]["sum_check"]["profile_expected"] = 10.0
                # ---- END: Fix and verify profile rating calculation ----
                  # Add metadata about the evaluated file
                rating_data["evaluated_file"] = str(file_path)
                rating_data["evaluation_timestamp"] = datetime.datetime.now().isoformat()
                
                # NOTE: File saving is now handled by the background process in main.py
                # This eliminates duplicate file saving and ensures proper file organization
                yield f"data: {json.dumps({'status': 'progress', 'message': 'Profile rating evaluation completed'})}\\n\\n"
                await asyncio.sleep(0.1)
                
                # Send the final rating data to the client
                completion_data = {
                    "status": "complete",
                    "rating": rating_data.get("profile_rating"),
                    "data": rating_data,
                    "message": "Profile rating evaluation completed successfully. File will be saved by background process."
                }
                yield f"data: {json.dumps(completion_data)}\\n\\n"
            
            except Exception as process_error: # Catch any other unexpected error
                error_msg = f"Error processing profile rating (stream): {str(process_error)}"
                print(f"❌ [CONSOLE] {error_msg}")
                yield f"data: {json.dumps({'status': 'error', 'message': error_msg})}\\n\\n"
        else:
            error_msg = f"LLM API error for profile rating: {response.status_code}"
            print(f"❌ [CONSOLE] {error_msg}")
            yield f"data: {json.dumps({'status': 'error', 'message': error_msg})}\\n\\n"
    except Exception as e:
        error_msg = f"Exception in profile rating stream: {str(e)}"
        print(f"❌ [CONSOLE] {error_msg}")
        yield f"data: {json.dumps({'status': 'error', 'message': error_msg})}\\n\\n"
