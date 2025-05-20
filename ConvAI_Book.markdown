# Build Your Own Conversational AI From Scratch: A Beginner's Guide to ConvAI Form Automation

## Introduction
Welcome, aspiring coder! This book is your step-by-step guide to building a *Conversational AI (ConvAI)* system from scratch using just your laptop. Imagine creating an AI that chats with people naturally, like a friendly interviewer or a caring nurse, and magically fills out forms for HR interviews or hospital patient intake. Whether you're a student or a curious beginner, this book will hold your hand through every step — from installing tools to deploying a web app that companies or hospitals could use. Let's dive in!

---

## Chapter 1: What is Conversational AI?

### What is ConvAI?
Conversational AI is like a super-smart chatbot that talks to people naturally, understands their words, and does useful tasks. Unlike a regular chatbot that follows rigid scripts, ConvAI uses *Natural Language Processing (NLP)* and *Large Language Models (LLMs)* to have human-like conversations. Think of it as a digital assistant that listens, thinks, and responds intelligently.

### Why ConvAI in HR and Healthcare?
In HR, ConvAI can interview job candidates by asking questions like "Tell me about yourself" and automatically extract details like their name, skills, and experience to fill out a form. In healthcare, it can talk to patients, ask "What happened?", and fill out intake forms with symptoms and medical history. This saves time, reduces mistakes, and makes interactions feel friendly.

### What Will Our Project Do?
By the end of this book, you'll build a web app that:
- Takes voice input from users (job seekers or patients).
- Holds a natural conversation, asking follow-up questions if needed.
- Extracts structured data (e.g., name, skills, symptoms).
- Fills out HR or hospital forms automatically.
- Runs online, ready for real-world use.

### Real-World Impact
- **HR**: Faster interviews, less bias, and auto-generated candidate profiles.
- **Healthcare**: Quick patient intake, fewer errors, and happier patients.
- **You**: A cool project to show off in your portfolio!

---

## Chapter 2: Tools and Tech Stack Setup

### Minimum Laptop Specs
- **OS**: Windows, macOS, or Linux.
- **RAM**: 8GB (16GB recommended).
- **Storage**: 20GB free space.
- **Internet**: For downloading tools and cloud deployment.

### Step-by-Step Setup
Let’s set up everything you need. Follow these steps carefully, and you’ll have a coding environment ready in no time!

1. **Install Python 3.10+**
   - Download from [python.org](https://www.python.org/downloads/).
   - During installation, check "Add Python to PATH."
   - Verify: Open a terminal and run `python --version`. You should see something like `Python 3.10.12`.

2. **Install Node.js and npm**
   - Download from [nodejs.org](https://nodejs.org/en/download/) (LTS version).
   - Verify: Run `node --version` and `npm --version` in terminal.

3. **Install Git**
   - Download from [git-scm.com](https://git-scm.com/downloads).
   - Verify: Run `git --version`.

4. **Install VS Code**
   - Download from [code.visualstudio.com](https://code.visualstudio.com/).
   - Install extensions: Python, JavaScript, Prettier.

5. **Create Project Folder**
   - Create a folder called `ConvAI`.
   - Open it in VS Code: `File > Open Folder`.

6. **Set Up Virtual Environment**
   - In terminal, navigate to `ConvAI` folder: `cd path/to/ConvAI`.
   - Run: `python -m venv venv`.
   - Activate: 
     - Windows: `venv\Scripts\activate`
     - macOS/Linux: `source venv/bin/activate`
   - You’ll see `(venv)` in your terminal.

7. **Install Python Libraries**
   - Run:
     ```bash
     pip install openai-whisper openai fastapi uvicorn python-dotenv spacy
     ```
   - Install Whisper dependencies: `pip install torch` (ensure your laptop supports it; if not, use Google Colab for Whisper).

8. **Install Node.js Dependencies**
   - Initialize a Node project: `npm init -y`.
   - Install React: 
     ```bash
     npx create-react-app frontend
     cd frontend
     npm install axios
     ```

9. **Sample Folder Structure**
   ```
   ConvAI/
   ├── backend/              # FastAPI server
   │   ├── main.py
   │   ├── requirements.txt
   │   └── .env
   ├── frontend/             # React web app
   │   ├── src/
   │   └── package.json
   ├── venv/                 # Python virtual env
   └── README.md
   ```

### Common Mistake
- **Python not in PATH**: If `python` command doesn’t work, reinstall Python and ensure "Add to PATH" is checked.
- **Wrong folder**: Always run commands in the correct project folder.

---

## Chapter 3: Speech to Text (Voice Input Setup)

### How Speech Recognition Works
Speech-to-text (STT) converts spoken words into text. We’ll use *OpenAI Whisper*, a powerful open-source model that works locally.

### Step 1: Record Audio
We’ll use a simple Python script with `pyaudio` to record audio. Install it:
```bash
pip install pyaudio
```

### Step 2: Convert Audio to Text
Create a file `backend/stt.py` with this code:

```python
import pyaudio
import wave
import whisper

# Record audio
def record_audio(filename="input.wav", duration=5):
    chunk = 1024
    format = pyaudio.paInt16
    channels = 1
    rate = 44100

    p = pyaudio.PyAudio()
    stream = p.open(format=format, channels=channels, rate=rate, input=True, frames_per_buffer=chunk)
    
    print("Recording...")
    frames = []
    for _ in range(0, int(rate / chunk * duration)):
        data = stream.read(chunk)
        frames.append(data)
    
    print("Done recording.")
    stream.stop_stream()
    stream.close()
    p.terminate()

    wf = wave.open(filename, 'wb')
    wf.setnchannels(channels)
    wf.setsampwidth(p.get_sample_size(format))
    wf.setframerate(rate)
    wf.writeframes(b''.join(frames))
    wf.close()

# Convert to text
def speech_to_text(filename="input.wav"):
    model = whisper.load_model("base")  # Use 'tiny' for faster results
    result = model.transcribe(filename, fp16=False)
    return result["text"]

if __name__ == "__main__":
    record_audio()
    text = speech_to_text()
    print("You said:", text)
```

### Step 3: Test It
- Run `python stt.py`.
- Speak something like "Hi, I’m Priya, a software engineer."
- Check the output: It should print your spoken words as text.

### Diagram: STT Flow
```
[User Speaks] → [Microphone] → [PyAudio Records WAV] → [Whisper Converts to Text] → [Text Output]
```

### Common Mistake
- **No microphone**: Ensure your laptop has a working mic.
- **Whisper too slow**: Use the `tiny` model (`model = whisper.load_model("tiny")`) for faster processing.

---

## Chapter 4: NLP and LLMs — The Brain of ConvAI

### What is NLP?
Natural Language Processing (NLP) helps computers understand human language. We’ll use *OpenAI’s GPT-4 Turbo* to extract structured data (e.g., name, skills) from text.

### Step 1: Set Up OpenAI API
- Sign up at [platform.openai.com](https://platform.openai.com/) and get an API key.
- Create a `.env` file in `backend/`:
  ```
  OPENAI_API_KEY=your-api-key-here
  ```

### Step 2: Extract Structured Data
Create `backend/nlp.py`:

```python
import openai
from dotenv import load_dotenv
import os

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

def extract_data(text, domain="hr"):
    prompt = f"""
    You are a conversational AI extracting structured data from user responses.
    Domain: {domain}
    Input: "{text}"
    
    Extract the following fields (if available):
    - Name
    - Age
    - Skills (for HR) or Symptoms (for healthcare)
    - Experience (for HR) or Medical History (for healthcare)
    
    Output as JSON. If a field is missing, set it to null.
    """
    response = openai.ChatCompletion.create(
        model="gpt-4-turbo",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=200
    )
    return eval(response.choices[0].message.content.strip("```json\n```"))

if __name__ == "__main__":
    sample_text = "Hi, I’m Priya, a software engineer with 4 years of experience in Python and Java."
    result = extract_data(sample_text, "hr")
    print(result)
```

### Step 3: Test It
- Run `python nlp.py`.
- Output should be:
  ```json
  {
    "Name": "Priya",
    "Age": null,
    "Skills": ["Python", "Java"],
    "Experience": "4 years"
  }
  ```

### Prompt Design Tip
- Be specific in prompts (e.g., list exact fields).
- Use JSON format for structured output.

### Common Mistake
- **Invalid API key**: Double-check your `.env` file.
- **Overloaded prompt**: Keep prompts concise to avoid confusing the LLM.

---

## Chapter 5: Designing the Dynamic Q&A Logic

### How Q&A Works
The AI starts with an open-ended question (e.g., "Tell me about yourself"), extracts data, checks for missing fields, and asks follow-ups. We’ll use a state machine to track the conversation.

### Step 1: Define Question Logic
Create `backend/conversation.py`:

```python
class Conversation:
    def __init__(self, domain="hr"):
        self.domain = domain
        self.state = {
            "Name": None,
            "Age": None,
            "Skills" if domain == "hr" else "Symptoms": None,
            "Experience" if domain == "hr" else "Medical History": None
        }
        self.history = []
        self.initial_question = "Please tell me about yourself." if domain == "hr" else "Can you tell me what happened?"

    def get_next_question(self, user_response=None):
        if not self.history:
            self.history.append({"role": "ai", "content": self.initial_question})
            return self.initial_question
        
        # Update state with user response
        if user_response:
            extracted = extract_data(user_response, self.domain)
            for key, value in extracted.items():
                if value:
                    self.state[key] = value
            self.history.append({"role": "user", "content": user_response})

        # Check for missing fields
        for field, value in self.state.items():
            if not value:
                question = f"Can you tell me your {field.lower()}?"
                self.history.append({"role": "ai", "content": question})
                return question
        
        return "Thank you! I have all the information I need."

if __name__ == "__main__":
    conv = Conversation("hr")
    print(conv.get_next_question())  # Initial question
    print(conv.get_next_question("I’m Priya, 4 years in Python."))  # Follow-up
    print(conv.get_next_question("I’m 28 years old."))  # Another follow-up
```

### Step 2: Test It
- Run `python conversation.py`.
- Output:
  ```
  Please tell me about yourself.
  Can you tell me your age?
  Thank you! I have all the information I need.
  ```

### Diagram: Q&A Flow
```
[Initial Question] → [User Response] → [Extract Data] → [Check Missing Fields] → [Ask Follow-Up or End]
```

### Common Mistake
- **Infinite loops**: Ensure the conversation ends when all fields are filled.
- **Vague follow-ups**: Make questions specific to missing fields.

---

## Chapter 6: Form Mapping Engine

### What is Form Mapping?
This module takes extracted data and fills a form template (e.g., HR or hospital intake form).

### Step 1: Define Form Template
Create `backend/form_template.json`:

```json
{
  "hr": {
    "Name": null,
    "Age": null,
    "Skills": [],
    "Experience": null
  },
  "healthcare": {
    "Name": null,
    "Age": null,
    "Symptoms": [],
    "Medical History": null
  }
}
```

### Step 2: Form Filler
Create `backend/form.py`:

```python
import json

def fill_form(extracted_data, domain="hr"):
    with open("form_template.json", "r") as f:
        templates = json.load(f)
    
    form = templates[domain]
    for key, value in extracted_data.items():
        if key in form and value:
            form[key] = value
    
    return form

if __name__ == "__main__":
    data = {
        "Name": "Priya",
        "Age": 28,
        "Skills": ["Python", "Java"],
        "Experience": "4 years"
    }
    filled_form = fill_form(data, "hr")
    print(filled_form)
```

### Step 3: Test It
- Run `python form.py`.
- Output:
  ```json
  {
    "Name": "Priya",
    "Age": 28,
    "Skills": ["Python", "Java"],
    "Experience": "4 years"
  }
  ```

### Common Mistake
- **Mismatched fields**: Ensure extracted data keys match form template keys.
- **Empty forms**: Add validation to check if critical fields are filled.

---

## Chapter 7: UI/UX Frontend (Web App)

### Building the Web App
We’ll use *React* to create a simple web interface where users can record audio, see the conversation, and preview the filled form.

### Step 1: Set Up React
- In `frontend/`, ensure you’ve run `npx create-react-app frontend`.
- Install `axios` for API calls: `npm install axios`.

### Step 2: Create UI
Replace `frontend/src/App.js` with:

```javascript
import React, { useState } from 'react';
import axios from 'axios';
import './App.css';

function App() {
  const [conversation, setConversation] = useState([]);
  const [form, setForm] = useState({});
  const [recording, setRecording] = useState(false);

  const startRecording = async () => {
    setRecording(true);
    // Note: Browser-based recording requires WebRTC; for simplicity, assume backend handles it
    try {
      const response = await axios.post('http://localhost:8000/record');
      const { text, next_question, form_data } = response.data;
      setConversation([...conversation, { role: 'user', text }, { role: 'ai', text: next_question }]);
      setForm(form_data);
    } catch (error) {
      console.error('Error:', error);
    }
    setRecording(false);
  };

  return (
    <div className="App">
      <h1>ConvAI Form Filler</h1>
      <div className="chat-box">
        {conversation.map((msg, index) => (
          <p key={index} className={msg.role}>
            <strong>{msg.role === 'ai' ? 'AI:' : 'You:'}</strong> {msg.text}
          </p>
        ))}
      </div>
      <button onClick={startRecording} disabled={recording}>
        {recording ? 'Recording...' : 'Speak'}
      </button>
      <div className="form-preview">
        <h2>Filled Form</h2>
        <pre>{JSON.stringify(form, null, 2)}</pre>
      </div>
    </div>
  );
}

export default App;
```

Add `frontend/src/App.css`:

```css
.App {
  text-align: center;
  padding: 20px;
  font-family: Arial, sans-serif;
}

.chat-box {
  border: 1px solid #ccc;
  padding: 10px;
  max-width: 600px;
  margin: 20px auto;
  height: 300px;
  overflow-y: scroll;
}

.chat-box p {
  margin: 5px 0;
}

.ai { color: blue; }
.user { color: green; }

button {
  padding: 10px 20px;
  font-size: 16px;
  cursor: pointer;
}

.form-preview {
  margin-top: 20px;
  text-align: left;
  max-width: 600px;
  margin: 20px auto;
}
```

### Step 3: Test It
- Run `npm start` in `frontend/`.
- Open `http://localhost:3000` in your browser.
- Click "Speak" (backend integration comes next).

### Diagram: UI Flow
```
[User Clicks Speak] → [Records Audio] → [Sends to Backend] → [Displays AI Response + Form]
```

### Common Mistake
- **CORS issues**: Ensure backend allows frontend requests (handled in Chapter 8).
- **No mic access**: Grant browser permission for microphone.

---

## Chapter 8: Backend API with FastAPI

### Setting Up the Backend
We’ll use *FastAPI* to create APIs that handle voice input, process conversations, and fill forms.

### Step 1: Create FastAPI Server
Create `backend/main.py`:

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from stt import record_audio, speech_to_text
from nlp import extract_data
from conversation import Conversation
from form import fill_form

app = FastAPI()

# Allow CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class DomainRequest(BaseModel):
    domain: str = "hr"

conv = None

@app.post("/start")
async def start_conversation(request: DomainRequest):
    global conv
    conv = Conversation(request.domain)
    return {"next_question": conv.get_next_question()}

@app.post("/record")
async def process_audio():
    record_audio()
    text = speech_to_text()
    extracted = extract_data(text, conv.domain)
    filled_form = fill_form(extracted, conv.domain)
    next_question = conv.get_next_question(text)
    return {"text": text, "next_question": next_question, "form_data": filled_form}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

### Step 2: Run the Backend
- Run `uvicorn main:app --reload` in `backend/`.
- Test APIs at `http://localhost:8000/docs`.

### Step 3: Connect Frontend
- The frontend’s `axios.post` calls `/record` to process audio and update the UI.

### Common Mistake
- **Port conflict**: Ensure no other app uses port 8000.
- **CORS error**: Verify CORS middleware is correctly set.

---

## Chapter 9–15: Summaries (To Be Expanded in Full Book)

### Chapter 9: Model Training (Optional)
- Collect sample HR/healthcare dialogues from open datasets (e.g., [Hugging Face Datasets](https://huggingface.co/datasets)).
- Fine-tune a smaller LLM like LLaMA2 using Hugging Face’s Transformers.
- Use spaCy for custom entity extraction (e.g., symptoms, skills).
- Deploy fine-tuned model locally or on cloud.

### Chapter 10: Self-Learning and Feedback Loop
- Store conversation logs in MongoDB.
- Analyze failed sessions (e.g., missing fields, vague answers).
- Update prompt templates based on failure patterns.
- Implement a feedback form in the UI.

### Chapter 11: Deployment
- Host backend on [Render](https://render.com/) or AWS.
- Host frontend on [Vercel](https://vercel.com/) or Netlify.
- Use Docker: Create a `Dockerfile` for backend.
- Set up HTTPS with Let’s Encrypt.
- Monitor with Prometheus or Render’s built-in tools.

### Chapter 12: Consent, Ethics & Security
- Add a consent checkbox in the React UI.
- Store data in PostgreSQL with anonymization.
- Use `python-dotenv` for secure API keys.
- Encrypt API calls with HTTPS.
- Follow GDPR/HIPAA: Delete voice data after processing.

### Chapter 13: Testing and Edge Cases
- Test with diverse accents using sample audio from [Common Voice](https://commonvoice.mozilla.org/).
- Handle background noise: Preprocess audio with noise reduction.
- Write unit tests for NLP and form-filling logic using `pytest`.
- Simulate vague answers: "I feel bad" → Follow-up question.

### Chapter 14: Future Upgrades
- Add text-to-speech with [ElevenLabs](https://elevenlabs.io/) for voice output.
- Build a mobile app with Flutter.
- Support multilingual input with Whisper’s language detection.
- Deploy a local LLM for offline use (e.g., LLaMA2 on a powerful laptop).

### Chapter 15: Appendix
- **Datasets**: Common Voice, Hugging Face HR/medical datasets.
- **Code Repo**: Host on GitHub (create one during setup).
- **Prompt Examples**:
  - HR: "Extract name, skills, experience from: '{text}'"
  - Healthcare: "Extract symptoms, medical history from: '{text}'"
- **Tools**: Python, Node.js, Whisper, FastAPI, React, PostgreSQL.
- **Forums**: Stack Overflow, Hugging Face Community, Reddit.

---

## Final Goal Achieved
By following this book, you’ve built a *ConvAI Form Automation Web App* that:
- Takes voice input via a web interface.
- Holds smart, natural conversations using GPT-4 Turbo and Whisper.
- Extracts structured data and fills HR or hospital forms.
- Runs online, ready for clients to use.
- Includes a feedback loop for continuous improvement.

Now, deploy it, share it with the world, and keep tinkering to make it even better!