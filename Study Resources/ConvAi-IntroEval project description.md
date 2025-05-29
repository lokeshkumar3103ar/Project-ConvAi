
> **Folder: `ConvAi-IntroEval`**
> 
> This folder contains the core application logic for the ConvAI Introduction Evaluator project.
> 
> ---
> 
> 1.  **main.py**
>     *   **Purpose**: This is the main entry point for the FastAPI web application. It defines the API endpoints, handles HTTP requests, and orchestrates the overall workflow of transcribing audio, extracting information, and rating profiles/introductions.
>     *   **Key Functions/Endpoints**:
>         *   `get_html("/")`: Serves the main HTML page (`index.html`).
>         *   `transcribe_endpoint("/transcribe")`:
>             *   **Input**: Audio/video file uploaded by the user.
>             *   **Process**: Saves the uploaded file, calls stt.py to transcribe it, then calls form_extractor.py to extract structured data from the transcript. It also schedules background tasks to generate profile and intro ratings.
>             *   **Output**: JSON response containing the path to the transcription file and the extracted fields (or an initial status indicating ratings are being generated).
>         *   `profile_rating_endpoint("/profile-rating")`:
>             *   **Input**: Optional `form_path` (query parameter). If not provided, uses the latest form.
>             *   **Process**: Calls profile_rater.py to evaluate the profile based on a form file.
>             *   **Output**: JSON response with the profile rating.
>         *   `profile_rating_stream_endpoint("/profile-rating-stream")`:
>             *   **Input**: Optional `form_path`.
>             *   **Process**: Calls profile_rater.py to get a streaming profile rating.
>             *   **Output**: Server-Sent Events (SSE) stream with profile rating progress.
>         *   `intro_rating_endpoint("/intro-rating")`:
>             *   **Input**: Optional `transcript_path` (query parameter). If not provided, uses the latest transcript.
>             *   **Process**: Calls intro_rater.py to evaluate the introduction based on a transcript file.
>             *   **Output**: JSON response with the intro rating.
>         *   `intro_rating_stream_endpoint("/intro-rating-stream")`:
>             *   **Input**: Optional `transcript_path`.
>             *   **Process**: Calls intro_rater.py to get a streaming intro rating.
>             *   **Output**: SSE stream with intro rating progress.
>         *   `extract_fields_stream_endpoint("/extract-fields-stream")`:
>             *   **Input**: Optional `transcript_path`.
>             *   **Process**: Loads transcript, calls form_extractor.py to stream field extraction. Schedules background tasks for ratings once extraction is complete.
>             *   **Output**: SSE stream with field extraction progress and completion status.
>         *   `list_ratings("/ratings")`:
>             *   **Input**: None.
>             *   **Process**: Lists all rating files found in the `ratings` directory.
>             *   **Output**: JSON response with a list of available rating files.
>         *   `get_rating_file("/rating/{filename}")`:
>             *   **Input**: `filename` (path parameter).
>             *   **Process**: Reads and returns the content of a specific rating file.
>             *   **Output**: JSON response with the content of the rating file.
>     *   **Connected To**:
>         *   stt.py: For audio transcription.
>         *   call_llm.py (and through it, the modules in `app/llm/`): For form extraction and rating functionalities.
>         *   `templates/index.html`: Serves the frontend.
>         *   File system: Reads/writes video files, transcription files, form files, and rating files in `videos/`, `transcription/`, `filled_forms/`, and `ratings/` directories respectively.
>     *   **Role**: Acts as the central controller of the application, exposing APIs for the frontend to interact with and managing the backend processes.
> 
> ---
>  Okay, here's a breakdown of the files in the `ConvAi-IntroEval` folder:
> 
> **1. main.py**
> 
> *   **Process and Function:** This is the main FastAPI application file. It defines the API endpoints for handling file uploads, transcription, LLM-based evaluations (form extraction, profile rating, intro rating), and serving the frontend. It orchestrates the overall workflow of the application.
> *   **Inputs:**
>     *   HTTP requests to its defined endpoints (e.g., `/transcribe`, `/profile-rating`, `/intro-rating`, `/extract-fields-stream`).
>     *   Uploaded audio/video files for transcription.
>     *   Query parameters specifying file paths for ratings (optional).
> *   **Outputs:**
>     *   JSON responses containing transcription text, extracted form data, evaluation ratings, and status messages.
>     *   Streaming responses for real-time updates during LLM processing.
>     *   Serves the `index.html` file for the frontend.
> *   **Connected to:**
>     *   stt.py: Calls `transcribe_file` to convert audio/video to text.
>     *   call_llm.py (and through it, the `app/llm` modules): Uses functions for form extraction and various ratings.
>     *   `templates/index.html`: Serves this file as the main UI.
>     *   `static/` (css, js): Implicitly, as `index.html` will link to these.
>     *   Reads from and writes to `videos/`, `transcription/`, `filled_forms/`, and `ratings/` directories.
> *   **Contribution & Role:** Acts as the central controller and entry point for all application functionalities. It manages user interactions (via HTTP), delegates tasks to specialized modules, and handles data flow between different components.
> 
> **2. stt.py**
> 
> *   **Process and Function:** Handles Speech-To-Text (STT) conversion. It uses the `whisper` library to transcribe audio/video files into text.
> *   **Inputs:**
>     *   `file_path` (Path object): The absolute path to the audio/video file to be transcribed.
>     *   `output_dir` (Path object): The directory where the transcription text file should be saved.
> *   **Outputs:**
>     *   A tuple containing:
>         *   `formatted_text` (str): The transcribed text with timestamps.
>         *   `output_file` (Path object): The path to the saved transcription file.
>     *   Saves the transcription to a `.txt` file in the `transcription/` directory.
> *   **Connected to:**
>     *   main.py: main.py calls the `transcribe_file` function.
>     *   Reads from the `videos/` directory (where uploaded files are initially stored).
>     *   Writes to the `transcription/` directory.
> *   **Contribution & Role:** Provides the core speech-to-text functionality, converting spoken introductions into a text format that can be processed by the LLM modules.
> 
> **3. call_llm.py**
> 
> *   **Process and Function:** This file acts as a central import hub for all functions related to Large Language Model (LLM) interactions. It previously contained direct LLM call logic, but after refactoring, it primarily imports and re-exports functions from the `app/llm` package.
> *   **Inputs:** None directly (it doesn't define functions that take external inputs itself in its current refactored state).
> *   **Outputs:** None directly (it doesn't define functions that return values itself).
> *   **Connected to:**
>     *   main.py: main.py imports various LLM-related functions from this file (which are, in turn, imported from the `app/llm` modules).
>     *   form_extractor.py: Imports functions for form field extraction.
>     *   profile_rater.py: Imports functions for profile rating.
>     *   intro_rater.py: Imports functions for introduction rating.
>     *   utils.py: Imports utility functions and the `DISABLE_LLM` flag.
> *   **Contribution & Role:** Simplifies imports in main.py by providing a single point of access for all LLM-related functionalities. It promotes a cleaner separation of concerns by delegating the actual LLM logic to the `app/llm` package.
> 
> **4. utils.py**
> 
> *   **Process and Function:** This is a utility module for LLM-related tasks. It centralizes common helper functions and global flags used across different LLM modules.
>     *   `DISABLE_LLM`: A global boolean flag to enable/disable actual LLM API calls (useful for testing or development).
>     *   `preprocess_llm_json_response()`: Cleans and fixes common formatting issues in raw JSON responses from the LLM.
>     *   `get_latest_form_file()`: Retrieves the path and content of the most recent form JSON file or a specific one if a path is provided.
>     *   `get_latest_transcript_file()`: Retrieves the path and content of the most recent transcript text file or a specific one.
>     *   `enhance_info_coverage_calculation()`: Placeholder for logic to refine information coverage scores (currently a basic pass-through).
>     *   `generate_default_feedback()`: Placeholder for generating default feedback if the LLM doesn't provide it.
>     *   `fix_json_and_rating_calculation()`: A crucial function that takes raw LLM output, preprocesses it, parses it as JSON, and recalculates/validates rating scores to ensure consistency.
>     *   `save_rating_to_file()`: Saves processed rating data to a JSON file in the `ratings/` directory.
> *   **Inputs:**
>     *   `preprocess_llm_json_response()`: Raw LLM response text.
>     *   `get_latest_form_file()` / `get_latest_transcript_file()`: Optional file path.
>     *   `fix_json_and_rating_calculation()`: Raw LLM rating text, rating type.
>     *   `save_rating_to_file()`: Rating data, file path, rating type.
> *   **Outputs:**
>     *   `preprocess_llm_json_response()`: Cleaned JSON string.
>     *   `get_latest_form_file()` / `get_latest_transcript_file()`: Tuple of (file path, content).
>     *   `fix_json_and_rating_calculation()`: Processed rating data as a dictionary.
>     *   `save_rating_to_file()`: Tuple of (success boolean, message/filepath string).
>     *   Modifies files in `ratings/` directory.
> *   **Connected to:**
>     *   form_extractor.py
>     *   intro_rater.py
>     *   profile_rater.py
>     *   call_llm.py (imports `DISABLE_LLM` and other utils)
>     *   Reads from `filled_forms/` and `transcription/` directories.
>     *   Writes to `ratings/` directory.
> *   **Contribution & Role:** Provides essential, reusable utility functions that support the LLM modules, promoting code reuse, consistency in JSON handling and file operations, and easier management of global settings like `DISABLE_LLM`.
> 
> **5. form_extractor.py**
> 
> *   **Process and Function:** Responsible for extracting structured information (fields like name, education, skills, etc.) from the raw text of a candidate's introduction transcript using an LLM.
>     *   `get_extraction_prompt()`: Generates the specific prompt to instruct the LLM on how to extract fields.
>     *   `extract_fields_from_transcript()`: Sends the transcript and prompt to the LLM (non-streaming for the final result, but uses streaming for console output during the call) and saves the extracted fields to a JSON file.
>     *   `extract_fields_from_transcript_stream()`: A streaming version that yields progress updates and the final extracted data (though the UI requirement was not to stream the actual extracted text token-by-token to the web UI, but rather progress and completion).
> *   **Inputs:**
>     *   `transcript_text` (str): The raw text from the candidate's introduction.
> *   **Outputs:**
>     *   `extract_fields_from_transcript()`: A dictionary indicating the status and path to the saved form file.
>     *   `extract_fields_from_transcript_stream()`: Yields Server-Sent Events (SSE) data with progress and completion status, including the path to the saved form file.
>     *   Saves the extracted data to a JSON file in the `filled_forms/` directory.
> *   **Connected to:**
>     *   call_llm.py (which re-exports its functions).
>     *   utils.py (uses `DISABLE_LLM`).
>     *   Makes HTTP requests to the LLM API (e.g., `http://localhost:11434/api/generate`).
>     *   Writes to the `filled_forms/` directory.
> *   **Contribution & Role:** Converts unstructured transcript text into a structured JSON format (a "form") that can be used for subsequent profile evaluation. This is the first step in the LLM processing pipeline after transcription.
> 
> **6. intro_rater.py**
> 
> *   **Process and Function:** Evaluates the quality of a candidate's introduction based on the transcript, using an LLM. It assesses aspects like grammar, clarity, structure, information coverage, and relevance to a role.
>     *   `get_intro_rating_prompt()`: Generates the detailed prompt with rubrics to guide the LLM in evaluating the introduction.
>     *   `evaluate_intro_rating_sync()`: Sends the transcript and prompt to the LLM, processes the response (including fixing JSON and recalculating scores using utils.py), and saves the rating.
>     *   `evaluate_intro_rating_stream()`: A streaming version that yields progress updates and the final rating data to the client in real-time.
> *   **Inputs:**
>     *   `transcript_path` (str, optional): Path to a specific transcript file. If None, uses the latest.
> *   **Outputs:**
>     *   `evaluate_intro_rating_sync()`: A dictionary containing the detailed intro rating.
>     *   `evaluate_intro_rating_stream()`: Yields SSE data with tokens, progress, and the final rating.
>     *   Saves the rating to a JSON file in the `ratings/` directory.
> *   **Connected to:**
>     *   call_llm.py (which re-exports its functions).
>     *   utils.py (uses `get_latest_transcript_file`, `fix_json_and_rating_calculation`, `save_rating_to_file`, `DISABLE_LLM`, and placeholder feedback/enhancement functions).
>     *   Makes HTTP requests to the LLM API.
>     *   Reads from the `transcription/` directory.
>     *   Writes to the `ratings/` directory.
> *   **Contribution & Role:** Provides an automated assessment of the candidate's spoken introduction, offering scores and qualitative feedback on various communication aspects.
> 
> **7. profile_rater.py**
> 
> *   **Process and Function:** Evaluates a candidate's overall profile based on the structured data extracted into a form (from form_extractor.py), using an LLM. It assesses completeness, relevance to a target role, project quality, and achievements.
>     *   `get_profile_rating_prompt()`: Generates the detailed prompt with rubrics to guide the LLM in evaluating the profile form.
>     *   `evaluate_profile_rating()`: Sends the form data and prompt to the LLM, processes the response (using utils.py), and saves the rating.
>     *   `evaluate_profile_rating_stream()`: A streaming version that yields progress updates and the final rating data.
> *   **Inputs:**
>     *   `form_path` (str, optional): Path to a specific form JSON file. If None, uses the latest.
> *   **Outputs:**
>     *   `evaluate_profile_rating()`: A dictionary containing the detailed profile rating.
>     *   `evaluate_profile_rating_stream()`: Yields SSE data with progress and the final rating.
>     *   Saves the rating to a JSON file in the `ratings/` directory.
> *   **Connected to:**
>     *   call_llm.py (which re-exports its functions).
>     *   utils.py (uses `get_latest_form_file`, `fix_json_and_rating_calculation`, `save_rating_to_file`, `DISABLE_LLM`).
>     *   Makes HTTP requests to the LLM API.
>     *   Reads from the `filled_forms/` directory.
>     *   Writes to the `ratings/` directory.
> *   **Contribution & Role:** Provides an automated assessment of the candidate's overall professional profile based on the extracted information, offering scores and feedback on their qualifications and experience.
> 
> **Other Files/Folders in `ConvAi-IntroEval/`:**
> 
> *   **`index.html` (deprecated, now in `templates/`)**: Was the main HTML file for the frontend. (Now correctly served from `templates/index.html` by main.py).
> *   **`__pycache__/`**: Contains cached bytecode files (`.pyc`) automatically generated by Python to speed up loading of modules. Not directly part of the project's logic.
> *   **`app/`**: A package directory.
>     *   **`llm/`**: A sub-package containing all LLM-related modules, as detailed above.
> *   **`filled_forms/`**: Directory where JSON files containing data extracted from transcripts by form_extractor.py are stored.
> *   **`ratings/`**: Directory where JSON files containing evaluation ratings (both intro and profile) generated by intro_rater.py and profile_rater.py are stored.
> *   **`static/`**: Contains static assets for the frontend.
>     *   `css/style.css`: Stylesheets for the HTML frontend.
>     *   `js/script.js`: JavaScript code for frontend interactivity (handling uploads, displaying results, etc.).
> *   **`templates/`**: Contains HTML templates.
>     *   `index.html`: The main HTML file for the user interface.
> *   **`transcription/`**: Directory where text files (`.txt`) containing transcriptions generated by stt.py are stored.
> *   **`videos/`**: Directory where uploaded audio/video files are temporarily stored before transcription.
> 
> This structure promotes a modular and organized codebase, separating concerns for API handling, speech-to-text, LLM interactions, and utility functions.
