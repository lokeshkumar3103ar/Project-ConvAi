import requests
import json
import datetime
import asyncio
from pathlib import Path
import re

# Import DISABLE_LLM from .utils
from .utils import DISABLE_LLM

# Import file organization functions
import sys
from pathlib import Path
if str(Path(__file__).parent.parent.parent) not in sys.path:
    sys.path.append(str(Path(__file__).parent.parent.parent))
from file_organizer import organize_path, log_file_operation

def get_extraction_prompt(transcript_text: str) -> str:
    """Creates and returns the prompt for extracting data from transcripts - optimized for college students"""
    return f"""
    You are a precise data extraction assistant that parses and structures information in JSON from college student self-introduction transcripts.    
    
    EXTRACTION RULES:
    1. Only extract information that is EXPLICITLY stated in the text - never infer or assume.
    2. If information for a field is not clearly mentioned, write exactly "Not Mentioned" - do not guess.
    3. Use direct quotes where possible, especially for technical terms, project names, and qualifications.
    4. Format consistently: use bullet points for lists and maintain original capitalization for proper nouns.
    5. For numerical values (age, CGPA, years), extract the exact number as mentioned.
    6. List multiple items separately and clearly when found in the text.
    7. Prioritize accuracy and completeness over brevity.
    8. If information is ambiguous, extract the literal statement rather than interpreting it.
    
    ### Personal Details 
    - Name (full name as mentioned)
    - Age (exact number only - if mentioned, but not required for evaluation)
    - Languages known (list all mentioned languages with proficiency levels if stated)
    - Hometown/Origin (where they're from - city, state, or region)

    ### Academic Focus
    - Current degree program (B.Tech, B.E., M.Tech, etc.)
    - Year of study (1st year, 2nd year, 3rd year, 4th year, final year)
    - Major/Specialization (Computer Science, Mechanical, Electronics, etc.)
    - College/University (full institution name)
    - CGPA (exact value with scale, e.g., "8.5/10" - only if mentioned proudly)
    - Academic projects (course projects, final year projects, semester projects)

    ### Practical Experience
    - Internships (summer internships, industry exposure, company names, duration)
    - Workshops and certifications (specific workshops attended, certifications earned)
    - College competitions (hackathons, coding competitions, technical events participated)
    - Research projects (projects with professors, research work, publications)
    - Applied learning experiences (practical implementations, real-world applications)

    ### Skills Development
    - Programming languages (all languages mentioned with proficiency if stated)
    - Tools & technologies (frameworks, software, platforms explored)
    - Technical skills (domain-specific technical capabilities)
    - Soft skills (communication, teamwork, leadership skills developed through group projects)
    - Leadership roles (positions in college clubs, events organized, team leadership)

    ### Personal Context & Motivation
    - Interests and hobbies (personal interests, recreational activities)
    - Career aspirations (what they want to become, future goals in their field)
    - Field of interest (specific areas within their domain they're passionate about)
    - What motivates them (driving factors, inspiration, passion areas)
    - Initiative in learning (self-learning efforts, extra-curricular technical activities)

    ### Current Projects & Work (if any)
    - Current projects (ongoing academic or personal projects)
    - Project name (exact project title)
    - Technology/tools used (list all technologies mentioned)
    - Problem statement (concise description of the problem addressed)
    - Solution implemented (specific approach or methodology used)
    - Your role (specific responsibilities in team projects)

    ### Work Experience (if any)
    - Company name (full organization name - internships or part-time work)
    - Role (exact position title)
    - Duration (time period or months worked)
    - Skills gained (specific skills acquired during this experience)
    - Key responsibilities (main duties and learning outcomes)

    ### Achievements & Extra-curricular Activities
    - Academic achievements (scholarships, academic awards, honors)
    - Technical achievements (competition wins, project recognitions)
    - Extra-curricular activities (clubs, societies, volunteering, organizing events)
    - Relevant hobbies (activities that complement their academic/career interests)

    ### Career Goals & Preferences
    - Target role/field (specific job roles or career paths they're interested in)
    - Short-term goals (immediate career objectives post-graduation)
    - Long-term aspirations (career vision, where they see themselves)
    - Professional interests (specific domains or technologies they want to work with)

    IMPORTANT: Extract information exactly as stated in the text. Focus on college-relevant experiences and academic journey. Do not add any interpretation or inferences.

    Text: {transcript_text}
    \"\"\""""

def extract_fields_from_transcript(transcript_text: str, roll_number: str = None) -> dict:
    """Returns the complete extracted fields from transcript as a dictionary
    
    Args:
        transcript_text (str): The transcript text to process
        roll_number (str, optional): Student roll number for file organization
    
    Returns:
        dict: Status and file path information
    """
    
    prompt = get_extraction_prompt(transcript_text)
    if DISABLE_LLM:
        print("[⚠️ LLM DISABLED] Skipping extract_fields_from_transcript LLM call.")
        return {
            "status": "disabled",
            "message": "LLM call skipped (safe edit mode)"
        }

    try:
        # Use non-streaming mode for cleaner queue operation
        print("📤 [QUEUE] Sending extraction request to LLM API...")
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
            print(f"📥 [QUEUE] Received extraction response from LLM API")
            
            response_json = response.json()
            extracted_text = response_json.get('response', '')
            
            # After streaming is complete, save the extracted data
            if not extracted_text.strip():
                print("❌ No data extracted from LLM response")
                return {"status": "error", "message": "No data returned from LLM"}
            
            print(f"\n✅ LLM extraction completed. Total response length: {len(extracted_text)} characters")
            
            # Use file organization system for saving extracted forms
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"form_{timestamp}.json"
            
            # Use organize_path to get the proper file path with roll number organization
            file_path = organize_path("filled_forms", filename, roll_number)
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            try:
                # Save the extracted data to a JSON file
                json_data = {
                    "timestamp": datetime.datetime.now().isoformat(),
                    "extracted_fields": extracted_text
                }
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(json_data, f, indent=2, ensure_ascii=False)
                
                print(f"✅ Saved extracted data to: {file_path}")
                log_file_operation("CREATE form", file_path, roll_number)
                
                # Return status information 
                return {
                    "status": "saved", 
                    "file": str(file_path)
                }
            
            except Exception as save_error:
                print(f"❌ Error saving JSON file: {str(save_error)}")
                return {"status": "error", "message": f"Error saving to file: {str(save_error)}"}
        else:
            print(f"Error calling LLM: {response.status_code}")
            return {"status": "error", "message": f"LLM API error: {response.status_code}"}
    
    except Exception as e:
        print(f"Exception calling LLM: {str(e)}")
        return {"status": "error", "message": f"Exception: {str(e)}"}


