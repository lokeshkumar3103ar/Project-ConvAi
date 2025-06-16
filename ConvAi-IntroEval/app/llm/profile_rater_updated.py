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
    """Creates and returns the prompt for evaluating profile rating with strong employability focus"""
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
    
    return f"""You are an expert HR evaluator with extensive experience in candidate assessment and hiring decisions. Your task is to provide an objective, data-driven rating that directly predicts EMPLOYABILITY and likelihood of being hired by companies.

    ⚡ CRITICAL: This profile rating score directly determines the candidate's employability potential. Higher scores indicate candidates who are most likely to be hired and succeed in professional roles.

    PROFILE RATING INSTRUCTIONS:
    - Analyze the candidate profile with a hiring manager's perspective
    - Focus on practical skills, real-world experience, and industry readiness
    - Apply the rubrics objectively based on what employers actually value
    - Base your assessment ONLY on information explicitly present in the profile
    - Remember: Academic credentials alone do not guarantee employability
    - Calculate scores precisely according to the formulas provided

    PROFILE RATING RUBRICS (out of 10 total points) - EMPLOYABILITY FOCUSED:
    
    1. Practical Foundation & Completeness (max 3.0 points):
        EMPLOYABILITY INSIGHT: Comprehensive profiles demonstrate thoroughness and self-awareness - key traits employers seek.
        
        - Count all fields that are **not empty or "Not Mentioned"**.
        - Use this formula exactly:  
            `completeness_score = min(3.0, (filled_fields / 35) * 3)`
        - NEVER exceed 3.0 points for this category even if calculation yields higher value.
        
        🔒 Enhanced Field Categories for College Students:
         - Personal Details (4 fields): Name, Age (optional), Languages known, Hometown/Origin
         - Academic Focus (5 fields): Current degree program, Year of study, Major/specialization, University, CGPA (if mentioned)
         - Practical Experience (8 fields): Internships, Workshops & certifications, College competitions, Research projects, Applied learning experiences, Current projects, Work experience, Project technologies
         - Skills Development (6 fields): Programming languages, Tools & technologies, Technical skills, Soft skills, Leadership roles, Initiative in learning
         - Personal Context & Growth (7 fields): Interests & hobbies, Career aspirations, Field of interest, What motivates them, Personal qualities, Academic projects, Target role
         - Professional Readiness (5 fields): Skills gained, Key responsibilities, Professional achievements, Extra-curricular activities, Industry readiness indicators

       • MUST format as: "X.X/3 – X of 35 fields filled (X% completion). Higher completion indicates better self-awareness and thoroughness."

    2. Industry Relevance & Technical Competency (0-2 points):
       EMPLOYABILITY INSIGHT: Technical skills aligned with target roles are the primary hiring criteria in today's market.
       
       • Examine programming languages, technical skills, tools, and domain knowledge against industry standards
       • 2.0 = Highly employable: Strong technical foundation with relevant skills for target field (e.g., web dev → React, Node.js, databases)
       • 1.5 = Good employability: Solid technical skills with minor gaps that can be quickly filled
       • 1.0 = Moderate employability: Basic technical foundation but needs significant skill development
       • 0.5 = Limited employability: Minimal technical skills, extensive training required
       • 0.0 = Not industry-ready: No relevant technical competency demonstrated
       • Consider modern industry requirements and emerging technologies
       • Provide specific examples of technical strengths and gaps in your explanation  

    3. Hands-On Experience & Project Portfolio (0-3 points):
    EMPLOYABILITY INSIGHT: Practical experience is the strongest predictor of job performance and hiring success.
    
    IMPORTANT: Look for ALL practical experience - internships, projects, competitions, research
       • 3.0 = Highly hireable: Multiple substantial experiences (2+ internships OR 3+ detailed projects OR research + competition experience)
       • 2.5 = Strong candidate: 1 solid internship + projects OR 2+ well-described projects with real-world applications
       • 2.0 = Good potential: 1+ internships OR 2+ projects with decent technical detail and problem-solving evidence
       • 1.5 = Developing candidate: Some practical experience (1+ projects or workshops) but limited depth
       • 1.0 = Entry-level: Basic project experience or academic assignments with minimal industry relevance
       • 0.5 = Very limited: Vague mentions of projects without clear technical implementation
       • 0.0 = No practical experience: Pure academic background with no hands-on work
       • CRITICAL: Prioritize internships and real-world projects over academic assignments

    4. Professional Growth & Leadership Potential (0-2 points):
       EMPLOYABILITY INSIGHT: Leadership, initiative, and continuous learning indicate high-potential employees who will grow with the company.
       
       • 2.0 = High potential: Multiple indicators of leadership (club roles, event organization, team projects) + career direction + learning initiative
       • 1.5 = Good potential: Some leadership experience OR strong career direction OR demonstrated learning initiative
       • 1.0 = Moderate potential: Basic extra-curricular involvement OR some career awareness
       • 0.5 = Limited indicators: Minimal evidence of leadership or professional development
       • 0.0 = No growth indicators: No evidence of leadership, initiative, or career planning
       • Consider: Leadership roles, competition participation, certifications, career goals, learning initiatives

    🎯 EMPLOYABILITY SCORING GUIDE:
    • 8.5-10.0: HIGHLY EMPLOYABLE - Top candidates likely to receive multiple job offers
    • 7.0-8.4: GOOD EMPLOYABILITY - Strong candidates with solid hiring potential
    • 5.5-6.9: MODERATE EMPLOYABILITY - Decent candidates who may need some skill development
    • 4.0-5.4: DEVELOPING POTENTIAL - Entry-level candidates requiring significant training
    • Below 4.0: LIMITED EMPLOYABILITY - Extensive development needed before industry readiness

    FORM DATA TO EVALUATE:
    {extracted_fields}

    Return your evaluation as a JSON object with this exact structure:
    {{
      "profile_rating": X.X,
      "employability_level": "[HIGHLY EMPLOYABLE/GOOD EMPLOYABILITY/MODERATE EMPLOYABILITY/DEVELOPING POTENTIAL/LIMITED EMPLOYABILITY]",
      "grading_explanation": {{
        "practical_foundation": "X.X/3 – X of 35 fields filled (X% completion). Higher completion indicates better self-awareness and thoroughness.",
        "technical_competency": "X.X/2 – [specific technical skills analysis and industry relevance]",
        "hands_on_experience": "X.X/3 – [detailed assessment of practical experience and project quality]",
        "growth_potential": "X.X/2 – [leadership, initiative, and professional development indicators]"
      }},
      "hiring_insights": {{
        "strongest_assets": "[Top 2-3 strengths that make this candidate attractive to employers]",
        "development_areas": "[Key areas that would improve employability]",
        "industry_readiness": "[Assessment of readiness for professional work]"
      }},
      "grading_debug": {{
        "practical_foundation_score": X.X,
        "technical_competency_score": X.X,
        "hands_on_experience_score": X.X,
        "growth_potential_score": X.X,
        "calculated_sum": X.X,
        "sum_check": {{
          "profile_expected": 10,
          "profile_reported": X.X
        }},
        "notes": "[observations about employability strengths/weaknesses and hiring potential]"
      }}
    }}

    IMPORTANT FINAL CHECKS:
    1. Ensure practical_foundation_score is NEVER greater than 3.0, regardless of the calculation result
    2. Double-check that profile_rating equals all four component scores
    3. Assign appropriate employability_level based on total score
    4. Focus hiring_insights on what employers actually care about
    5. Respond ONLY with the JSON object, no additional text.
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
                "temperature": 0.1,  # Remove randomness for consistent output
                "top_p": 0.95,        # Set top_p to 1.0 for deterministic sampling
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

