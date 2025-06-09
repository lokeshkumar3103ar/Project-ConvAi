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
    """Creates and returns the prompt for extracting data from transcripts"""
    return f"""
    You are a precise data extraction assistant that parses and structures information from professional self-introduction transcripts.    EXTRACTION RULES:
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
    - Age (exact number only)
    - Languages known (list all mentioned languages with proficiency levels if stated)
    - Professional Status (exactly as stated: "Fresher", "Experienced", or specific experience level)

    ### Education Background
    - Degree & specialization (complete degree name with field/major)
    - College/university (full institution name)
    - Year of graduation (exact year, if mentioned)
    - CGPA (exact value with scale, e.g., "8.5/10")
    - Notable achievements/certifications (list specific qualifications with dates if mentioned)

    ### Projects
    - Project name (exact project title)
    - Technology/tools used (list all technologies mentioned)
    - Problem statement (concise description of the problem addressed)
    - Solution implemented (specific approach or methodology used)
    - Outcomes/accomplishments (quantifiable results or impacts, if mentioned)
    - Your role (specific responsibilities in team projects)

    ### Work Experience
    - Company name (full organization name)
    - Role (exact job title)
    - Time period (start and end dates or duration)
    - Total years of experience (exact value, e.g., "2 years 3 months")
    - Skills gained (specific skills acquired during this experience)
    - Key responsibilities & achievements (bullet points of main duties and accomplishments)

    ### Skills
    - Technical skills (programming languages, frameworks, methodologies)
    - Soft skills (communication, teamwork, etc.)
    - Tools & technologies (software, platforms, systems) 
    - Domain expertise (industry-specific knowledge areas)

    ### Achievements & Activities
    - Professional achievements (awards, recognitions, certifications)
    - Extracurricular activities (clubs, volunteering, competitions)
    - Relevant hobbies (activities related to professional interests)

    ### Personal Traits
    - Personality Traits: List specific character traits mentioned (e.g., adaptive, leader, quick learner)

    ### Role Expectation
    - Target Job Role: Exact position or role mentioned (e.g., Full Stack Developer, Data Analyst)

    ### Career Preferences
    - Career goals (short or long-term professional objectives)
    - Preferred location (specific cities/regions/countries)
    - Willingness to relocate (explicit yes/no statement with any conditions)
    - Work environment preference (exact preference: remote/hybrid/on-site)
    - Expected Salary Range (exact figures with currency, if mentioned)

    IMPORTANT: Extract information exactly as stated in the text. Do not add any interpretation or inferences.

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
        # Use streaming mode for console output but still return complete result
        print("📤 [CONSOLE] Sending extraction request to LLM API...")
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
            print(f"📥 [CONSOLE] Receiving streaming extraction response from LLM API")
            
            extracted_text = ""
            
            for line in response.iter_lines():
                if line:
                    # Parse the streaming line
                    json_line = json.loads(line.decode('utf-8'))
                    
                    if 'response' in json_line:
                        chunk = json_line['response']
                        extracted_text += chunk
                        # Print the chunk to the console immediately
                        print(chunk, end='', flush=True)
                    
                    # Check if the stream is done
                    if json_line.get('done', False):
                        print()  # New line after completion
                        break
            
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
                
                # Return status information (ratings will be triggered separately via streaming)
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

async def extract_fields_from_transcript_stream(transcript_text: str, roll_number: str = None):
    """Streaming version of field extraction from transcript

    Args:
        transcript_text (str): The transcript text to process
        roll_number (str, optional): Student roll number for file organization

    Yields:
        str: Server-sent events data with extraction progress
    """
    try:
        yield f"data: {json.dumps({'status': 'progress', 'message': 'Generating extraction prompt...'})}\n\n"
        await asyncio.sleep(0.1)
        
        prompt = get_extraction_prompt(transcript_text)
        
        if DISABLE_LLM:
            print("[⚠️ LLM DISABLED] Skipping extract_fields_from_transcript_stream LLM call.")
            yield f"data: {json.dumps({'status': 'disabled', 'message': 'LLM call skipped (safe edit mode)'})}\n\n"
            return

        yield f"data: {json.dumps({'status': 'progress', 'message': 'Calling LLM for field extraction...'})}\n\n"
        await asyncio.sleep(0.1)
        
        # Call the LLM in streaming mode
        print(f"📤 [CONSOLE] Sending extraction request to LLM API...")
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
                "stop": ["\n\n"]
            },
            stream=True  # Stream the HTTP response
        )
        
        extracted_text = ""
        
        if response.status_code == 200:
            # Process the streaming response line by line
            print(f"📥 [CONSOLE] Receiving streaming extraction response from LLM API")
            
            for line in response.iter_lines():
                if line:
                    # Parse the streaming line
                    json_line = json.loads(line.decode('utf-8'))
                    
                    if 'response' in json_line:
                        chunk = json_line['response']
                        extracted_text += chunk
                        
                        # Print to console immediately
                        print(chunk, end='', flush=True)
                        
                        # Send individual token to the client
                        # NOTE: We're not streaming this to the web UI per the requirements
                        # "Note: the form extraction should not streamed to web"
                        # So we just send progress updates
                        if len(chunk) > 0 and (len(extracted_text) % 100 < len(chunk)):
                            yield f"data: {json.dumps({'status': 'extracting', 'message': 'Receiving data...', 'text_length': len(extracted_text)})}\n\n"
                    
                    # Check if the stream is done                    if json_line.get('done', False):
                        print()  # New line after completion
                        break
                
                # Use file organization system for saving extracted forms
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"form_{timestamp}.json"
                
                # Use organize_path to get the proper file path with roll number organization
                file_path = organize_path("filled_forms", filename, roll_number)
                file_path.parent.mkdir(parents=True, exist_ok=True)
                
                try:
                    # Tell the client we're saving the data
                    yield f"data: {json.dumps({'status': 'progress', 'message': 'Saving extracted fields...'})}\n\n"
                    await asyncio.sleep(0.1)
                      # Save the extracted data to a JSON file
                    json_data = {
                        "timestamp": datetime.datetime.now().isoformat(),
                        "extracted_fields": extracted_text
                    }
                    with open(file_path, "w", encoding="utf-8") as f:
                        json.dump(json_data, f, indent=2, ensure_ascii=False)
                    
                    print(f"✅ [CONSOLE] Saved extracted data to: {file_path}")
                    log_file_operation("CREATE form", file_path, roll_number)
                    
                    # Send completion message
                    completion_data = {
                        "status": "complete",
                        "file": str(file_path),
                        "message": "Extraction completed successfully"
                    }
                    yield f"data: {json.dumps(completion_data)}\n\n"
                
                except Exception as save_error:
                    error_msg = f"Error saving JSON file: {str(save_error)}"
                    print(f"❌ [CONSOLE] {error_msg}")
                    yield f"data: {json.dumps({'status': 'error', 'message': error_msg})}\n\n"
        else:
            error_msg = f"LLM API error for extraction: {response.status_code}"
            print(f"❌ [CONSOLE] {error_msg}")
            yield f"data: {json.dumps({'status': 'error', 'message': error_msg})}\n\n"
    
    except Exception as e:
        error_msg = f"Exception in extraction stream: {str(e)}"
        print(f"❌ [CONSOLE] {error_msg}")
        yield f"data: {json.dumps({'status': 'error', 'message': error_msg})}\n\n"

