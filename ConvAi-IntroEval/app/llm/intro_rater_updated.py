import requests
import json
import datetime
import asyncio
from pathlib import Path

# Import helper functions from .utils
from .utils import (
    get_latest_transcript_file, 
    enhance_info_coverage_calculation, 
    generate_default_feedback, 
    preprocess_llm_json_response, # Added, though fix_json_and_rating_calculation uses it internally
    fix_json_and_rating_calculation, 
    save_rating_to_file,
    DISABLE_LLM
)


def get_intro_rating_prompt(transcript_text: str) -> str:
    """Creates and returns the prompt for evaluating intro rating"""
    return f"""
    You are an expert communication coach specializing in evaluating professional self-introductions. Your task is to provide an objective, data-driven rating of a candidate's introduction based on the provided transcript and specific evaluation criteria.

    INTRO RATING INSTRUCTIONS:
    - Analyze the transcript carefully and thoroughly.
    - Apply the rubrics objectively and consistently.
    - Base your assessment ONLY on information explicitly present in the transcript.
    - Do not make assumptions about unstated qualities or information.
    - Calculate scores precisely according to the rubric.

    INTRO RATING RUBRICS (out of 10 total points):

    1. Grammar & Clarity (0-3.0 points):
       - 3.0: Fluent, grammatically perfect, clear and coherent sentences throughout.
       - 2.5: Mostly fluent and clear, minor grammatical errors or occasional awkward phrasing that doesn't hinder understanding.
       - 2.0: Understandable, but with noticeable grammatical errors or clarity issues.
       - 1.5: Several errors in grammar or unclear sentences, making it somewhat difficult to follow.
       - 1.0: Significant grammatical issues and lack of clarity, making comprehension difficult.
       - 0.5: Mostly incoherent or grammatically incorrect.
       - 0.0: Completely unintelligible.
       - Provide specific examples of errors or well-phrased sentences.

    2. Structure (0-1.5 points):
       - 1.5: Excellent logical flow (e.g., clear past-present-future progression, or thematic coherence), easy to follow.       
       - 1.0: Generally logical flow, but might have minor jumps or could be more organized.
       - 0.5: Some attempt at structure, but lacks clear organization or is difficult to follow.
       - 0.0: No discernible structure, rambling or chaotic.       - Briefly describe the observed structure or lack thereof.
    3. Information Coverage (0-3.5 points) Check how well the introduction covers key professional information:
       - 3.5: Comprehensively covers ALL key information areas: name/introduction, education, skills/expertise, work/projects, career goals, and personal qualities.
       - 3.0: Covers 5 out of 6 key areas thoroughly, missing only one minor aspect.
       - 2.5: Covers 4 out of 6 key areas well, with noticeable omissions in 1-2 areas.
       - 2.0: Covers 3 out of 6 key areas adequately, sparse information in others.
       - 1.5: Covers 2 out of 6 key areas, very limited information overall.
       - 1.0: Covers only 1 key area well, mostly generic statements.
       - 0.5: Minimal information, touches on aspects superficially.
       - 0.0: No relevant professional information provided.
       - SCORING GUIDE: Check each area (name/intro, education, skills, work/projects, goals, personal qualities) and count how many are well-covered.

    4. Relevance to Role (0-2.0 points):
       - 2.0: Clearly and effectively connects strengths, experiences, or goals to a typical desired job role in their field (even if not explicitly stated, infer based on context like "software engineer", "data analyst").
       - 1.5: Attempts to connect strengths/goals to a role, but the connection could be stronger or more explicit.
       - 1.0: Some mention of skills or goals that might be relevant, but no clear connection made to a professional role.
       - 0.5: Vague or very weak connection to any professional role.
       - 0.0: No attempt to connect their introduction to a job role, or information is irrelevant.
       - Explain how well they connected their profile to a potential job role.

    5. INSIGHTS (Provide 2-3 brief, specific observations about the speaker based on what you actually heard):
    - Tone: [Describe the specific tone you observed - confident, nervous, enthusiastic, etc.]
    - Style: [Describe the specific speaking style - formal, conversational, structured, rambling, etc.]
    - Fluency: [Describe the specific fluency and pacing - smooth, hesitant, fast-paced, well-paced, etc.]

    6. FEEDBACK (Provide 2-3 specific, actionable suggestions for improvement based on gaps you identified):
        - [Specific suggestion for delivery improvement based on what you observed]
        - [Specific suggestion for content enhancement based on what was missing or unclear]
        - [Specific suggestion for structure improvement if needed]    IMPORTANT: For Information Coverage (info_coverage), carefully evaluate these 6 key areas:
        1. Name or introduction of self - Does the speaker identify themselves?
        2. Educational background or qualifications - Do they mention their studies, degree, institution?
        3. Skills, expertise, or strengths - Do they describe their technical/professional capabilities?
        4. Work experience, projects, or achievements - Do they mention any practical experience?
        5. Goals, aspirations, or what they're seeking - Do they explain their career objectives?
        6. Personal interests or unique qualities - Do they share anything that makes them distinctive?
    
    Score based on how many areas are well-covered (not just mentioned briefly). Each area covered well = approximately 0.6 points.

    Return your evaluation as a JSON object with this exact structure:
    {{
      "intro_rating": X.X, // Total score out of 10, sum of all subcategories
      "grading_explanation": {{
        "grammar_and_clarity": "X.X/3.0 – [Brief explanation with specific examples]",
        "structure": "X.X/1.5 – [Brief explanation of observed structure]",
        "info_coverage": "X.X/3.5 – [Brief explanation, mention key info present/missing]",
        "relevance_to_role": "X.X/2.0 – [Brief explanation of how well they connected to a role]"
      }},      "insights": [
        "Tone: [Describe the specific tone you observed]",
        "Style: [Describe the specific speaking style you heard]",
        "Fluency: [Describe the specific fluency and pacing you noticed]"
      ],
      "feedback": [
        "[Specific actionable suggestion for improvement #1]",
        "[Specific actionable suggestion for improvement #2]",
        "[Specific actionable suggestion for improvement #3]"
      ],
      "grading_debug": {{
        "grammar_clarity_score": X.X,
        "structure_score": X.X,
        "info_coverage_score": X.X,
        "relevance_score": X.X,
        "calculated_sum": X.X, // Sum of the four X.X scores above
        "sum_check": {{
          "intro_expected": 10.0,
          "intro_reported": X.X // This should match intro_rating and calculated_sum
        }},
        "notes": "explain any observed strengths/weaknesses and areas for improvement"
      }}
    }}
    TRANSCRIPT TO EVALUATE:
    ---BEGIN TRANSCRIPT---
    {transcript_text}
    ---END TRANSCRIPT---    

    IMPORTANT: Respond ONLY with the JSON object, no additional text. Ensure the sum of all category scores (grammar_and_clarity + structure + info_coverage + relevance_to_role) matches the intro_rating value and the calculated_sum in grading_debug.
    """

def evaluate_intro_rating_sync(transcript_path=None) -> dict:
    """
    Evaluates an intro rating based on the transcript data (synchronous version)
    
    Args:
        transcript_path (str, optional): Path to specific transcript file. Defaults to None (uses latest).
    
    Returns:
        dict: Rating results
    """
    try:
        # Load the transcript data
        file_path, transcript_text = get_latest_transcript_file(transcript_path)
        if not transcript_text:
            return {"status": "error", "message": "Failed to load transcript data"}
        
        # Generate the evaluation prompt
        prompt = get_intro_rating_prompt(transcript_text)
        
        if DISABLE_LLM:
            print("[⚠️ LLM DISABLED] Skipping evaluate_intro_rating_sync LLM call.")
            return {
                "status": "disabled",
                "message": "LLM call skipped (safe edit mode)"
            }
        
        # Call the LLM with streaming enabled
        print("📤 [CONSOLE] Sending intro rating evaluation request to LLM API...")
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
            print(f"📥 [CONSOLE] Receiving streaming intro rating response from LLM API")
            
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
                # Parse and fix the JSON response using the utility function
                # Pass the specific functions for enhancing and generating feedback for intro rating
                rating_data = fix_json_and_rating_calculation(
                    rating_text, 
                    rating_type="intro",
                    enhance_info_coverage_calculation_func=enhance_info_coverage_calculation,
                    generate_default_feedback_func=generate_default_feedback
                )

                if rating_data.get("status") == "error":
                    print(f"❌ Error processing LLM response: {rating_data.get('message')}")
                    # Return the error structure from fix_json_and_rating_calculation
                    return rating_data                # Add metadata about the evaluated file
                rating_data["evaluated_file"] = str(file_path)
                rating_data["evaluation_timestamp"] = datetime.datetime.now().isoformat()
                
                # NOTE: File saving is now handled by the background process in main.py
                # This eliminates duplicate file saving and ensures proper file organization
                print(f"✅ Intro rating evaluation completed for {file_path}")
                print("📁 File will be saved by background process with proper organization")
                
                return rating_data
                
                return rating_data
            
            except Exception as e: # Catch any other unexpected error during processing after fix_json
                print(f"❌ Unexpected error after attempting to fix JSON in intro_rater: {str(e)}")
                return {
                    "status": "error", 
                    "message": f"Unexpected error processing response: {str(e)}",
                    "raw_response": rating_text
                }
        else:
            print(f"Error calling LLM: {response.status_code}")
            return {"status": "error", "message": f"LLM API error: {response.status_code}"}
    
    except Exception as e:
        print(f"Exception in intro rating evaluation: {str(e)}")
        return {"status": "error", "message": f"Exception: {str(e)}"}

async def evaluate_intro_rating_stream(transcript_path=None):
    """
    Streaming version of intro rating evaluation
    
    Args:
        transcript_path (str, optional): Path to specific transcript file. Defaults to None (uses latest).
    
    Yields:
        str: Server-sent events data with intro rating progress
    """
    try:
        yield f"data: {json.dumps({'status': 'progress', 'message': 'Loading transcript...'})}\n\n"
        await asyncio.sleep(0.1)
        
        # Load the transcript data
        file_path, transcript_text = get_latest_transcript_file(transcript_path)
        if not transcript_text:
            yield f"data: {json.dumps({'status': 'error', 'message': 'Failed to load transcript data'})}\n\n"
            return
        
        yield f"data: {json.dumps({'status': 'progress', 'message': 'Generating evaluation prompt...'})}\n\n"
        await asyncio.sleep(0.1)
        
        prompt = get_intro_rating_prompt(transcript_text)
        
        if DISABLE_LLM:
            print("[⚠️ LLM DISABLED] Skipping evaluate_intro_rating_stream LLM call.")
            yield f"data: {json.dumps({'status': 'disabled', 'message': 'LLM call skipped (safe edit mode)'})}\n\n"
            return
        
        yield f"data: {json.dumps({'status': 'progress', 'message': 'Calling LLM for intro rating...'})}\n\n"
        await asyncio.sleep(0.1)
        
        # Call the LLM in streaming mode
        print(f"📤 [CONSOLE] Sending intro rating request to LLM API...")
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
        
        rating_text = ""
        
        if response.status_code == 200:
            # Process the streaming response line by line
            print(f"📥 [CONSOLE] Receiving streaming intro rating response from LLM API")
            
            for line in response.iter_lines():
                if line:
                    # Parse the streaming line
                    json_line = json.loads(line.decode('utf-8'))
                    
                    if 'response' in json_line:
                        chunk = json_line['response']
                        rating_text += chunk
                        
                        # Print to console immediately
                        print(chunk, end='', flush=True)
                        
                        # Send tokens to the web UI in real-time (token-by-token)
                        yield f"data: {json.dumps({'status': 'token', 'token': chunk})}\n\n"
                        
                        # Also send a progress update every ~100 chars for clients that might not handle token streaming
                        if len(chunk) > 0 and (len(rating_text) % 100 < len(chunk)):
                            yield f"data: {json.dumps({'status': 'evaluating', 'message': 'Receiving evaluation...', 'text_length': len(rating_text)})}\n\n"
                    
                    # Check if the stream is done
                    if json_line.get('done', False):
                        print()  # New line after completion
                        break
            
            try:
                # Tell the client we're processing the response
                yield f"data: {json.dumps({'status': 'progress', 'message': 'Processing intro rating...'})}\n\n"
                await asyncio.sleep(0.1)
                
                # Parse and fix the JSON response using the utility function
                rating_data = fix_json_and_rating_calculation(
                    rating_text,
                    rating_type="intro",
                    enhance_info_coverage_calculation_func=enhance_info_coverage_calculation,
                    generate_default_feedback_func=generate_default_feedback
                )

                if rating_data.get("status") == "error":
                    error_msg = f"Error processing LLM response: {rating_data.get('message')}"
                    print(f"❌ [CONSOLE] {error_msg}")
                    yield f"data: {json.dumps({'status': 'error', 'message': error_msg, 'raw_response': rating_data.get('raw_response', rating_text)})}\n\n"
                    return                # Add metadata about the evaluated file
                rating_data["evaluated_file"] = str(file_path)
                rating_data["evaluation_timestamp"] = datetime.datetime.now().isoformat()
                
                # NOTE: File saving is now handled by the background process in main.py
                # This eliminates duplicate file saving and ensures proper file organization
                yield f"data: {json.dumps({'status': 'progress', 'message': 'Intro rating evaluation completed'})}\n\n"
                await asyncio.sleep(0.1)
                
                # Send the final rating data to the client
                completion_data = {
                    "status": "complete",
                    "rating": rating_data.get("intro_rating"),
                    "data": rating_data,
                    "message": "Intro rating evaluation completed successfully. File will be saved by background process."
                }
                yield f"data: {json.dumps(completion_data)}\n\n"
            
            except json.JSONDecodeError as e:
                error_msg = f"Error parsing LLM response as JSON: {str(e)}"
                print(f"❌ [CONSOLE] {error_msg}")
                yield f"data: {json.dumps({'status': 'error', 'message': error_msg, 'raw_response': rating_text})}\n\n"
            
            except Exception as process_error: # Catch any other unexpected error
                error_msg = f"Error processing intro rating: {str(process_error)}"
                print(f"❌ [CONSOLE] {error_msg}")
                yield f"data: {json.dumps({'status': 'error', 'message': error_msg})}\n\n"
        else:
            error_msg = f"LLM API error for intro rating: {response.status_code}"
            print(f"❌ [CONSOLE] {error_msg}")
            yield f"data: {json.dumps({'status': 'error', 'message': error_msg})}\n\n"
    
    except Exception as e:
        error_msg = f"Exception in intro rating stream: {str(e)}"
        print(f"❌ [CONSOLE] {error_msg}")
        yield f"data: {json.dumps({'status': 'error', 'message': error_msg})}\n\n"
