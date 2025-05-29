# ConvAi-IntroEval Project Overview

This is a self-introduction evaluation system that processes audio/video introductions through a three-stage pipeline. Here's a breakdown of each file and the workflow:

## File Descriptions

### Core Processing Files

**stt.py** - Speech-to-Text Module
- Uses OpenAI Whisper (turbo model) for audio transcription
- Converts audio/video files to timestamped text transcripts
- Supports multiple formats: mp3, mp4, wav, m4a, webm, flac, ogg, aac
- Outputs formatted transcripts with timestamps

**main.py** - FastAPI Web Application
- Main application entry point with REST API endpoints
- Handles file uploads, processing coordination, and streaming responses
- Manages directories for videos, transcripts, forms, and ratings
- Provides real-time Server-Sent Events (SSE) for frontend updates

### LLM Processing Module (`app/llm/`)

**`form_extractor.py`** - Field Extraction
- Extracts structured information from transcripts using LLM
- Identifies personal details, background, skills, goals from spoken introductions
- Supports both synchronous and streaming processing

**`profile_rater_updated.py`** - Profile Rating
- Evaluates the completeness and quality of extracted profile information
- Provides scoring and feedback on personal introduction content

**`intro_rater_updated.py`** - Introduction Rating
- Analyzes the overall quality of the spoken introduction
- Evaluates delivery, structure, clarity, and engagement

**`utils.py`** - Utility Functions
- Helper functions for file management and LLM operations
- Handles latest file retrieval and data processing utilities

### Frontend Files

**Templates:** `index.html` - Main web interface
**CSS:** `styles.css`, `rating-styles.css` - Styling
**JavaScript:** `app.js`, `rating-utils.js` - Frontend logic

## Workflow Diagram

```mermaid
graph TD
    A[User Uploads Audio/Video] --> B[File Validation & Storage]
    B --> C[Speech-to-Text Processing<br/>Whisper Turbo]
    C --> D[Transcript Generation<br/>with Timestamps]
    
    D --> E{Extract Fields?}
    E -->|Yes| F[LLM Field Extraction<br/>Personal Info, Skills, Goals]
    E -->|No| J[Return Transcript Only]
    
    F --> G[Save Filled Form JSON]
    G --> H{Generate Ratings?}
    
    H -->|Yes| I1[Background Task:<br/>Profile Rating]
    H -->|Yes| I2[Background Task:<br/>Intro Rating]
    H -->|No| K[Return Form Data]
    
    I1 --> L1[Profile Rating JSON]
    I2 --> L2[Introduction Rating JSON]
    
    L1 --> M[Frontend Polling<br/>for Completion]
    L2 --> M
    K --> M
    J --> M
    
    M --> N[Display Results<br/>with Ratings]
    
    style A fill:#e1f5fe
    style C fill:#f3e5f5
    style F fill:#e8f5e8
    style I1 fill:#fff3e0
    style I2 fill:#fff3e0
    style N fill:#e0f2f1
```

## Data Flow

### Directories Structure
- **`videos/`** - Uploaded audio/video files
- **`transcription/`** - Generated transcript files
- **`filled_forms/`** - Extracted structured data (JSON)
- **`ratings/`** - Generated rating files (JSON)

### API Endpoints
- **`POST /transcribe`** - Main processing endpoint
- **`GET /extract-fields-stream`** - Streaming field extraction
- **`GET /profile-rating-stream`** - Streaming profile rating
- **`GET /intro-rating-stream`** - Streaming intro rating
- **`GET /ratings/check_status`** - Poll for rating completion

### Processing Flow
1. **Upload & Transcribe** - Convert audio to text using Whisper
2. **Extract Fields** - Use LLM to structure transcript into form data
3. **Generate Ratings** - Parallel evaluation of profile and introduction quality
4. **Stream Results** - Real-time updates to frontend via Server-Sent Events

The system is designed for asynchronous processing with background tasks for time-consuming LLM operations, while providing immediate feedback through streaming responses.