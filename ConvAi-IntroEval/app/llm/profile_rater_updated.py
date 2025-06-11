# filepath: c:\Users\lokes\Downloads\KAMPYUTER\College Projects\Project ConvAi\Project-ConvAi\ConvAi-IntroEval\app\llm\profile_rater_updated.py
import requests
import json
import datetime
from pathlib import Path

# Import helper functions from .utils
try:
    from .utils import get_latest_form_file, fix_json_and_rating_calculation, DISABLE_LLM
except ImportError:  # Fallback for direct execution if needed
    from utils import get_latest_form_file, fix_json_and_rating_calculation, DISABLE_LLM


def get_profile_rating_prompt(form_data: dict) -> str:
    """Creates and returns the prompt for evaluating profile rating"""
    # Extract the fields from the form data structure
    extracted_fields = None
    
    if "extracted_fields" in form_data and form_data["extracted_fields"]:
        extracted_fields = form_data["extracted_fields"]
    elif "data" in form_data and isinstance(form_data["data"], dict):
        if "extracted_fields" in form_data["data"]:
            extracted_fields = form_data["data"]["extracted_fields"]
    elif isinstance(form_data, str):
        extracted_fields = form_data
    else:
        extracted_fields = str(form_data)
    
    return f"""You are an expert HR evaluator with extensive experience in candidate assessment and selection. Your task is to provide an objective, data-driven rating of candidate profiles based on specific evaluation criteria.

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
    {extracted_fields}

    Return your evaluation as a JSON object with this exact structure:
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
        
        # Call the LLM with non-streaming mode for cleaner queue operation
        print("📤 [QUEUE] Sending profile rating request to Mistral API...")
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "mistral",
                "prompt": prompt,
                "stream": False,  # Disable streaming for queue mode
                "temperature": 0.0,  # Remove randomness for consistent output
                "top_p": 1.0,        # Set top_p to 1.0 for deterministic sampling
                "top_k": 40,         # Limit token selection to top 40 tokens
                "seed": 42,          # Fixed seed for reproducible results
                "stop": ["\n\n"]     # Stop token for clean output termination
            }
        )
        
        if response.status_code == 200:
            # Process the complete response
            print(f"📥 [QUEUE] Received profile rating response from LLM API")
            
            response_json = response.json()
            rating_text = response_json.get('response', '')
            
            try:
                # Use the utility function to parse and fix JSON
                rating_data = fix_json_and_rating_calculation(
                    rating_text,
                    rating_type="profile"
                )

                if rating_data.get("status") == "error":
                    print(f"❌ Error processing LLM response for profile rating: {rating_data.get('message')}")
                    return rating_data

                # Add metadata about the evaluated file
                rating_data["evaluated_file"] = str(file_path)
                rating_data["evaluation_timestamp"] = datetime.datetime.now().isoformat()
                
                # NOTE: File saving is now handled by the background process in main.py
                print(f"✅ Profile rating evaluation completed for {file_path}")
                print("📁 File will be saved by background process with proper organization")
                
                return rating_data
            
            except Exception as e:
                print(f"❌ Unexpected error after attempting to fix JSON in profile_rater: {str(e)}")
                return {
                    "status": "error", 
                    "message": f"Unexpected error processing response: {str(e)}",
                    "raw_response": rating_text
                }
        else:
            print(f"Error calling LLM: {response.status_code}")
            return {"status": "error", "message": f"LLM API error: {response.status_code}"}
    
    except Exception as e:
        print(f"Exception in profile rating evaluation: {str(e)}")
        return {"status": "error", "message": f"Exception: {str(e)}"}

# Streaming function removed as requested
