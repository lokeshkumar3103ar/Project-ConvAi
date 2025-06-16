import requests
import json
import datetime
from pathlib import Path

# Import helper functions from .utils
from .utils import (
    get_latest_transcript_file, 
    enhance_info_coverage_calculation, 
    generate_default_feedback, 
    fix_json_and_rating_calculation, 
    DISABLE_LLM
)


def get_intro_rating_prompt(transcript_text: str) -> str:
    """Creates and returns the prompt for evaluating intro rating with improved flexibility"""
    return f"""
    You are an expert communication coach specializing in evaluating college student self-introductions for interview preparation. Your task is to provide an objective, data-driven rating based on the provided transcript and specific evaluation criteria.

    INTRO RATING INSTRUCTIONS:
    - Analyze the transcript carefully and thoroughly.
    - Apply the rubrics objectively and consistently for pre-final year college students.
    - Base your assessment ONLY on information explicitly present in the transcript.
    - Do not make assumptions about unstated qualities or information.
    - Calculate scores precisely according to the rubric.
    - Recognize that effective introductions can take many forms and structures.
    - Focus on communication effectiveness and practical readiness rather than adherence to specific formats.

    INTRO RATING RUBRICS (out of 10 total points):

    1. Grammar & Clarity (0-3.0 points):
       - 3.0: Fluent, grammatically appropriate, clear and coherent sentences throughout.
       - 2.5: Mostly fluent and clear, minor grammatical errors or occasional awkward phrasing that doesn't hinder understanding.
       - 2.0: Understandable, but with noticeable grammatical errors or clarity issues.
       - 1.5: Several errors in grammar or unclear sentences, making it somewhat difficult to follow.
       - 1.0: Significant grammatical issues and lack of clarity, making comprehension difficult.
       - 0.5: Mostly incoherent or grammatically incorrect.
       - 0.0: Completely unintelligible.
       - For non-native speakers, focus more on clarity and comprehensibility rather than perfect grammar.
       - Provide specific examples of errors or well-phrased sentences.    
       
    2. Structure (0-1.5 points):
       - 1.5: Effective organization that creates a coherent impression, regardless of specific format (not limited to past-present-future progression).
       - 1.0: Generally logical flow, but might have minor jumps or could be more organized.
       - 0.5: Some attempt at structure, but lacks clear organization or is difficult to follow.
       - 0.0: No discernible structure, rambling or chaotic.
       - Recognize that effective structure can take many forms (chronological, thematic, narrative, etc.).
       - Evaluate based on whether the structure effectively serves the communication purpose.

    3. Information Coverage (0-3.5 points) Check how well the introduction covers key areas for college students preparing for interviews:
       - 3.5: Comprehensively covers ALL key areas: name/introduction, academic background, practical experience/projects, technical skills, and career direction.
       - 3.0: Covers 4-5 key areas thoroughly, with good balance of academic and practical elements.
       - 2.5: Covers 3-4 key areas well, but may lack depth in practical experience or technical skills.
       - 2.0: Covers 2-3 key areas adequately, limited practical experience mentioned.
       - 1.5: Covers basic academic information but minimal practical or technical content.
       - 1.0: Only covers basic identification and academic details, no practical elements.
       - 0.5: Minimal information, mostly generic statements.
       - 0.0: No relevant information provided.
       - Focus on the presence and quality of information rather than the specific order presented.
       - SCORING GUIDE: Check each area (name/intro, academic background, practical experience/projects, technical skills, career goals) and evaluate depth of coverage.
       - Give higher weight to practical experience, projects, internships, and technical skills as these demonstrate readiness.

    4. Relevance to Professional Context (0-2.0 points):
       - 2.0: Clearly demonstrates practical readiness and connects their experience, skills, or projects to professional work context.
       - 1.5: Shows some practical preparation and makes connections to professional roles, but could be more specific.
       - 1.0: Mentions relevant skills or projects but doesn't clearly connect to professional context.
       - 0.5: Vague about practical applications or professional readiness.
       - 0.0: No indication of practical skills or professional preparation.
       - Consider how well they demonstrate value they can bring to employers through practical experience.
       - Focus on readiness for professional work rather than just academic achievement.

    5. INSIGHTS (Provide 2-3 brief, specific observations about the speaker based on what you actually heard):
       - Tone: [Describe the specific tone you observed - confident, nervous, enthusiastic, etc.]
       - Style: [Describe the specific speaking style - formal, conversational, structured, rambling, etc.]
       - Fluency: [Describe the specific fluency and pacing - smooth, hesitant, fast-paced, well-paced, etc.]
       - Consider cultural differences in communication styles when assessing tone and style.

    6. FEEDBACK (Provide 2-3 specific, actionable suggestions for improvement based on gaps you identified):
       - [Specific suggestion for delivery improvement based on what you observed]
       - [Specific suggestion for content enhancement based on what was missing or unclear]
       - [Specific suggestion for structure improvement if needed]
       - Focus on the most impactful improvements for interview preparation.
       - Provide suggestions that help them better demonstrate their practical readiness and skills.

    IMPORTANT: For Information Coverage (info_coverage), carefully evaluate these key areas for college students:
        1. Name and personal introduction - Does the speaker clearly identify themselves?
        2. Academic background - Do they mention their degree, major, university, and year of study?
        3. Practical experience and projects - Do they discuss internships, projects, competitions, or hands-on work?
        4. Technical skills and competencies - Do they mention relevant technical skills, programming languages, or tools?
        5. Career direction and goals - Do they express clear career interests or professional aspirations?
    
    Score generously when students demonstrate practical experience and technical skills. Academic information alone should not score highly - practical readiness and demonstrated skills are crucial for interview success.

    Return your evaluation as a JSON object with this exact structure:
    {{
      "intro_rating": X.X, // Total score out of 10, sum of all subcategories
      "grading_explanation": {{
        "grammar_and_clarity": "X.X/3.0 – [Brief explanation with specific examples]",
        "structure": "X.X/1.5 – [Brief explanation of observed structure]",
        "info_coverage": "X.X/3.5 – [Brief explanation, emphasize practical experience and technical skills coverage]",
        "relevance_to_role": "X.X/2.0 – [Brief explanation of practical readiness and professional context]"
      }},
      "insights": [
        "Tone: [Describe the specific tone you observed]",
        "Style: [Describe the specific speaking style you heard]",
        "Fluency: [Describe the specific fluency and pacing you noticed]"
      ],
      "feedback": [
        "[Specific actionable suggestion for interview preparation #1]",
        "[Specific actionable suggestion for interview preparation #2]",
        "[Specific actionable suggestion for interview preparation #3]"
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
        "notes": "explain any observed strengths/weaknesses and areas for improvement focusing on interview readiness"
      }}
    }}
    
    TRANSCRIPT TO EVALUATE:
    ---BEGIN TRANSCRIPT---
    {transcript_text}
    ---END TRANSCRIPT---

    IMPORTANT: Respond ONLY with the JSON object, no additional text. Ensure the sum of all category scores (grammar_and_clarity + structure + info_coverage + relevance_to_role) matches the intro_rating value and the calculated_sum in grading_debug.
    """

def evaluate_intro_rating(transcript_path=None) -> dict:
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
        
        # Call the LLM with non-streaming mode for cleaner queue operation
        print("📤 [QUEUE] Sending intro rating evaluation request to Mistral API...")
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
            }        )
        
        if response.status_code == 200:
            # Process the complete response
            print(f"📥 [QUEUE] Received intro rating response from LLM API")
            
            response_json = response.json()
            rating_text = response_json.get('response', '')
            
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
                    return rating_data

                # Add metadata about the evaluated file
                rating_data["evaluated_file"] = str(file_path)
                rating_data["evaluation_timestamp"] = datetime.datetime.now().isoformat()
                
                # NOTE: File saving is now handled by the background process in main.py
                # This eliminates duplicate file saving and ensures proper file organization
                print(f"✅ Intro rating evaluation completed for {file_path}")
                print("📁 File will be saved by background process with proper organization")
                
                return rating_data
            
            except Exception as e:
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

