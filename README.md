# 🧠 ConvAI – Conversational AI for HR Interview Automation

**ConvAI** (Conversational AI) is an AI-driven system that automates HR form filling and candidate profiling through a fully voice-enabled, natural conversation. It simulates a real-time HR interview using LLMs, speech recognition, and dynamic form mapping — removing the need for traditional form entry.

---

## 🚀 Demo Walkthrough

### 🔄 Interactive Workflow Guide
View the step-by-step process with animations and icons.

### 📊 Flowchart Visualization
Understand how user voice is transformed into structured data using NLP and backend mapping.

---

## 📦 Features

- ✅ Voice-to-Form Automation  
- ✅ Human-like Interviewing via LLM  
- ✅ Real-Time Speech Transcription  
- ✅ Intelligent Follow-up Questions  
- ✅ Automatic Entity Extraction  
- ✅ Structured Data Mapping (PDF/DB)  
- ✅ Fully Responsive UI + Walkthroughs

---

## 🧭 System Workflow Overview

Here’s how **ConvAI** works in a real-time setting:

| Step | Description |
|------|-------------|
| 1️⃣   | User enters the room (virtually or physically) |
| 2️⃣   | Microphone is activated, voice input begins |
| 3️⃣   | AI greets with *"Tell me about yourself"* |
| 4️⃣   | User responds freely |
| 5️⃣   | LLM detects missing info and asks follow-ups |
| 6️⃣   | STT transcribes speech, NLP extracts key info |
| 7️⃣   | Data auto-maps to backend fields (e.g., CGPA) |
| 8️⃣   | Final form is generated and submitted to HR |

📎 For a visual experience, visit the **ConvAI Workflow Page** *(Coming Soon)*.

---

## 🛠️ Tech Stack

| Layer       | Technology                                 |
|-------------|---------------------------------------------|
| 🧠 AI        | OpenAI LLM / Local LLMs                    |
| 🎙 Speech   | Web Speech API / Whisper / Google STT      |
| 📦 Backend  | Node.js / Firebase / Express               |
| 💻 Frontend | React + Tailwind + Framer Motion           |
| 🧾 NLP      | SpaCy / Transformers / LangChain           |
| 📋 Mapping  | Custom Handlers, Entity Extractors         |
| 📊 UI/Flow  | Mermaid.js / SVG / Framer Motion           |

---

## 🧪 Example Use Case

```plaintext
User: "Hi, I'm Lokesh from Coimbatore. I study at Hindustan University and my CGPA is 9.6..."
⬇️ AI → Transcribes voice → Extracts:
{
  "name": "Lokesh",
  "hometown": "Coimbatore",
  "college": "Hindustan University",
  "cgpa": "9.6"
}
⬇️ Form auto-fills and submits without any manual entry. 

🧩 Architecture Diagram
[Mic Input]
     ↓
[Speech-to-Text Engine]
     ↓
[LLM Analysis & Question Generator]
     ↓
[NLP Parser & Entity Extractor]
     ↓
[Form Auto-Mapping]
     ↓
[Form Output: PDF / Database / API]


