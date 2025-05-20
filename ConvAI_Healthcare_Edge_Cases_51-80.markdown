# ConvAI Edge Cases: Healthcare Cases 51–80

This document details edge cases 51–80 for the *ConvAI Form Filler* AI, focusing on healthcare scenarios where the system collects patient data (e.g., name, symptoms, medical history) via voice input. Each case addresses a unique challenge, from minimal responses to ethical dilemmas, with hardcoded responses to simulate AI behavior. The system is tested locally on an NVIDIA RTX 4060 with Mistral-7B and Whisper, aligning with the demo app’s frontend.

## Healthcare Edge Cases

### 51. Minimal Answers
**Description**: User provides short, incomplete responses.  
**Why It’s an Issue**: Insufficient detail for accurate form completion.  
**How Human Acts**:  
```
AI: What symptoms do you have?  
User: Pain.  
```  
**How Hospital AI Should Respond**:  
```
AI: Got it. Where is the pain, and is there anything else, like fever?  
User: Stomach pain, no fever.  
```  
**How We Tackle**: Ask specific, closed-ended questions to extract details. Mistral-7B maps minimal inputs to form fields (e.g., “pain” → “Symptoms”).

### 52. Contradictory Medical History
**Description**: User reports conflicting past conditions.  
**Why It’s an Issue**: Risks incorrect medical records.  
**How Human Acts**:  
```
AI: Any past medical conditions?  
User: I have diabetes. No, I don’t.  
```  
**How Hospital AI Should Respond**:  
```
AI: Thanks for clarifying. To confirm, do you have diabetes or no past conditions?  
User: No conditions.  
```  
**How We Tackle**: Verify the latest statement. Log contradictions in MongoDB for nurse review.

### 53. Overly Excited Patient
**Description**: User is overly enthusiastic, sharing excessive details.  
**Why It’s an Issue**: Hard to focus on current symptoms.  
**How Human Acts**:  
```
AI: What’s bothering you today?  
User: I’m feeling great, just a little cough, but I ran a marathon last week, it was amazing!  
```  
**How Hospital AI Should Respond**:  
```
AI: Wow, a marathon? That’s impressive! Let’s focus on that cough — how long have you had it?  
User: About three days.  
```  
**How We Tackle**: Channel enthusiasm with targeted questions. Limit input to 500 tokens in Mistral-7B.

### 54. Dropped Connection
**Description**: Frontend-backend connection fails mid-conversation.  
**Why It’s an Issue**: Interrupts data collection, risks data loss.  
**How Human Acts**:  
```
AI: What’s your name?  
User: Emma.  
[Connection Drops]  
```  
**How Hospital AI Should Respond**:  
```
AI: Looks like we got disconnected. I have “Emma” — is that right? Any symptoms?  
User: Yes, Emma. I have a fever.  
```  
**How We Tackle**: Cache partial data in localStorage. Retry connection and confirm last input.

### 55. Low GPU Memory
**Description**: RTX 4060 runs out of VRAM for Mistral-7B.  
**Why It’s an Issue**: AI processing fails, stalling conversation.  
**How Human Acts**:  
```
AI: What symptoms do you have?  
User: Fever and cough.  
[GPU Error: Out of memory]  
```  
**How Hospital AI Should Respond**:  
```
AI: Sorry, I had a hiccup. You mentioned fever and cough, right? What’s your name?  
User: Liam.  
```  
**How We Tackle**: Fallback to CPU or quantized Mistral-7B (4-bit). Monitor VRAM with `nvidia-smi`.

### 56. Biased Assumptions
**Description**: User perceives AI’s question as biased (e.g., gender-based).  
**Why It’s an Issue**: Erodes trust, ethical violation.  
**How Human Acts**:  
```
AI: Are you a male patient?  
User: Why does that matter? I’m here for my symptoms!  
```  
**How Hospital AI Should Respond**:  
```
AI: My apologies, I don’t need that info. What symptoms are you experiencing?  
User: I have a headache.  
```  
**How We Tackle**: Use neutral prompts. Train Mistral-7B with unbiased datasets (e.g., Common Voice).

### 57. Non-Human Input
**Description**: Non-human sounds (e.g., pet barking) detected.  
**Why It’s an Issue**: Whisper misinterprets as speech, causing errors.  
**How Human Acts**:  
```
AI: What’s your name?  
[Whisper Output]: [Dog barking]  
```  
**How Hospital AI Should Respond**:  
```
AI: Sounds like a furry friend! Can you speak clearly with your name?  
User: John.  
```  
**How We Tackle**: Use `librosa` for frequency analysis to filter non-human audio. Prompt for retry.

### 58. Long Pause
**Description**: User pauses for an extended period mid-response.  
**Why It’s an Issue**: Disrupts conversation flow, risks timeout.  
**How Human Acts**:  
```
AI: What symptoms do you have?  
User: I have… [30-second pause]  
```  
**How Hospital AI Should Respond**:  
```
AI: No rush! When you’re ready, what symptoms are you feeling?  
User: Fever.  
```  
**How We Tackle**: Set a 30-second timeout in `pyaudio`. Offer a gentle nudge to continue.

### 59. Repetitive Complaints
**Description**: User repeats the same symptom multiple times.  
**Why It’s an Issue**: Redundant data, delays other fields.  
**How Human Acts**:  
```
AI: What symptoms do you have?  
User: I have a cough, a bad cough, really coughing a lot.  
```  
**How Hospital AI Should Respond**:  
```
AI: Got it, a cough. Any other symptoms, like fever or pain?  
User: No, just the cough.  
```  
**How We Tackle**: Acknowledge the symptom once and pivot to other fields. Deduplicate in form data.

### 60. Slang-Heavy Input
**Description**: User uses medical slang or informal terms.  
**Why It’s an Issue**: AI may not map slang to clinical terms.  
**How Human Acts**:  
```
AI: What’s bothering you?  
User: My tummy’s acting up, yo.  
```  
**How Hospital AI Should Respond**:  
```
AI: Sorry your stomach’s off! Is it pain, nausea, or something else?  
User: Pain.  
```  
**How We Tackle**: Maintain a slang-to-clinical dictionary (e.g., “tummy” → “stomach”). Fine-tune Mistral-7B on informal datasets.

### 61. Sarcastic Response
**Description**: User responds with sarcasm, obscuring intent.  
**Why It’s an Issue**: Hard to extract genuine symptoms.  
**How Human Acts**:  
```
AI: What symptoms do you have?  
User: Oh, I’m just *perfect*, thanks for asking.  
```  
**How Hospital AI Should Respond**:  
```
AI: Glad you’re keeping spirits up! Seriously, any issues like pain or fever?  
User: I have a headache.  
```  
**How We Tackle**: Ignore sarcasm, ask direct questions. Use spaCy sentiment analysis to detect tone.

### 62. Requesting Human Agent
**Description**: User demands to speak to a human.  
**Why It’s an Issue**: AI cannot proceed without escalation path.  
**How Human Acts**:  
```
AI: What’s your name?  
User: I want a real person, not a robot!  
```  
**How Hospital AI Should Respond**:  
```
AI: I understand. I’ll note your request. For now, can you share your name to start?  
User: Emma.  
```  
**How We Tackle**: Offer escalation option. Log request in MongoDB for nurse follow-up.

### 63. Fast Speech
**Description**: User speaks too quickly, overwhelming Whisper.  
**Why It’s an Issue**: Transcription errors or missed words.  
**How Human Acts**:  
```
AI: What symptoms do you have?  
[Whisper Output]: Fevercoughheadache [garbled].  
```  
**How Hospital AI Should Respond**:  
```
AI: You’re quick! I caught fever, cough, headache. Is that right?  
User: Yes.  
```  
**How We Tackle**: Adjust Whisper’s frame rate for faster speech. Confirm partial transcriptions.

### 64. Slow Speech
**Description**: User speaks very slowly, causing delays.  
**Why It’s an Issue**: Risks timeout or incomplete transcription.  
**How Human Acts**:  
```
AI: What’s your name?  
User: L… i… a… m… [slowly].  
```  
**How Hospital AI Should Respond**:  
```
AI: Thanks, I got Liam. Any symptoms you’re experiencing?  
User: Fever.  
```  
**How We Tackle**: Extend Whisper’s buffer time. Be patient with response timing.

### 65. Accent Challenges
**Description**: User’s accent affects transcription accuracy.  
**Why It’s an Issue**: Misinterpreted words lead to wrong data.  
**How Human Acts**:  
```
AI: What symptoms do you have?  
[Whisper Output]: I have “fever” [heard as “fiber”].  
```  
**How Hospital AI Should Respond**:  
```
AI: Did you say fever? Can you confirm your symptoms?  
User: Yes, fever.  
```  
**How We Tackle**: Fine-tune Whisper on diverse accents (e.g., Common Voice dataset). Confirm ambiguous terms.

### 66. Multiple Speakers
**Description**: Multiple voices detected in audio input.  
**Why It’s an Issue**: AI cannot isolate the primary speaker.  
**How Human Acts**:  
```
AI: What’s your name?  
[Whisper Output]: John [second voice: “Tell them, honey!”].  
```  
**How Hospital AI Should Respond**:  
```
AI: I heard “John.” Can the main speaker confirm their name?  
User: Yes, John.  
```  
**How We Tackle**: Use `librosa` for speaker separation. Prompt for single speaker.

### 67. Joking Response
**Description**: User makes jokes instead of providing data.  
**Why It’s an Issue**: Delays form completion.  
**How Human Acts**:  
```
AI: What symptoms do you have?  
User: I’m allergic to mornings!  
```  
**How Hospital AI Should Respond**:  
```
AI: Ha, mornings can be tough! Any real symptoms, like pain or fever?  
User: I have a cough.  
```  
**How We Tackle**: Acknowledge humor, redirect to serious questions. Use spaCy to detect playful intent.

### 68. Changing Topics
**Description**: User shifts to unrelated health topics.  
**Why It’s an Issue**: Distracts from current form fields.  
**How Human Acts**:  
```
AI: Any current symptoms?  
User: My knee hurt last year, now my diet’s off.  
```  
**How Hospital AI Should Respond**:  
```
AI: Thanks for sharing. Let’s focus on today — any symptoms now?  
User: I have a fever.  
```  
**How We Tackle**: Refocus on present issues. Ignore irrelevant topics in form updates.

### 69. Incomplete Sentences
**Description**: User stops mid-sentence, leaving partial data.  
**Why It’s an Issue**: Incomplete information for form.  
**How Human Acts**:  
```
AI: What symptoms do you have?  
User: I have a fever and… [stops].  
```  
**How Hospital AI Should Respond**:  
```
AI: I caught “fever.” Anything else, like cough or pain?  
User: Cough.  
```  
**How We Tackle**: Confirm partial input and prompt for completion. Log partial data.

### 70. Whispering
**Description**: User speaks too softly, affecting transcription.  
**Why It’s an Issue**: Whisper may miss or misinterpret input.  
**How Human Acts**:  
```
AI: What’s your name?  
[Whisper Output]: [Faint] Liam.  
```  
**How Hospital AI Should Respond**:  
```
AI: I barely heard that. Can you speak a bit louder with your name?  
User: Liam.  
```  
**How We Tackle**: Adjust Whisper’s sensitivity. Prompt for louder speech.

### 71. Shouting
**Description**: User speaks too loudly, distorting audio.  
**Why It’s an Issue**: Causes transcription errors or clipping.  
**How Human Acts**:  
```
AI: What symptoms do you have?  
[Whisper Output]: FEVER! [distorted].  
```  
**How Hospital AI Should Respond**:  
```
AI: Wow, loud and clear! Did you say fever? Any other symptoms?  
User: Yes, fever and cough.  
```  
**How We Tackle**: Normalize audio levels in `librosa`. Confirm distorted inputs.

### 72. Background Chatter
**Description**: Background voices interfere with primary speaker.  
**Why It’s an Issue**: Whisper picks up irrelevant speech.  
**How Human Acts**:  
```
AI: What’s your name?  
[Whisper Output]: Emma [background: “Dinner’s ready!”].  
```  
**How Hospital AI Should Respond**:  
```
AI: I heard “Emma.” Can you speak in a quieter spot?  
User: Yes, Emma.  
```  
**How We Tackle**: Use noise suppression in Whisper. Request quieter environment.

### 73. Device Issues
**Description**: User’s microphone or device malfunctions.  
**Why It’s an Issue**: Prevents audio input, halting conversation.  
**How Human Acts**:  
```
AI: What symptoms do you have?  
[No Audio: Mic Muted]  
```  
**How Hospital AI Should Respond**:  
```
AI: I’m not hearing you. Can you check if your mic is muted or connected?  
User: [Fixes mic] I have a fever.  
```  
**How We Tackle**: Detect no audio in `pyaudio`. Guide user to troubleshoot device.

### 74. Consent Refusal
**Description**: User refuses to consent to data processing.  
**Why It’s an Issue**: Blocks conversation start, legal requirement.  
**How Human Acts**:  
```
AI: Please consent to data processing.  
User: No way, I don’t trust this!  
```  
**How Hospital AI Should Respond**:  
```
AI: I respect your choice. Consent is needed to proceed. Want to read our privacy policy?  
User: Okay, I’ll consent.  
```  
**How We Tackle**: Enforce consent modal. Provide privacy policy link placeholder.

### 75. Cultural Misunderstandings
**Description**: User uses culturally specific terms or expectations.  
**Why It’s an Issue**: AI may misinterpret or offend.  
**How Human Acts**:  
```
AI: What symptoms do you have?  
User: I have “hot stomach” from spicy food.  
```  
**How Hospital AI Should Respond**:  
```
AI: Thanks for sharing. By “hot stomach,” do you mean pain or burning?  
User: Burning.  
```  
**How We Tackle**: Maintain a cultural term dictionary. Fine-tune Mistral-7B on diverse datasets.

### 76. Outdated Medical Info
**Description**: User provides old or irrelevant health data.  
**Why It’s an Issue**: Risks incorrect form data.  
**How Human Acts**:  
```
AI: Any past medical conditions?  
User: I had a cold in 2010.  
```  
**How Hospital AI Should Respond**:  
```
AI: Thanks, but let’s focus on recent conditions. Any current or ongoing issues?  
User: I have asthma.  
```  
**How We Tackle**: Prompt for recent data. Filter outdated info in form updates.

### 77. Ambiguous Symptoms
**Description**: User describes symptoms vaguely or metaphorically.  
**Why It’s an Issue**: Hard to map to clinical terms.  
**How Human Acts**:  
```
AI: What’s bothering you?  
User: My heart feels heavy.  
```  
**How Hospital AI Should Respond**:  
```
AI: I hear you. Does “heavy” mean pain, pressure, or something else?  
User: It’s pressure.  
```  
**How We Tackle**: Clarify with clinical options. Use spaCy to parse metaphors.

### 78. Requesting Illegal Actions
**Description**: User asks for non-medical services (e.g., prescriptions).  
**Why It’s an Issue**: Violates legal and ethical boundaries.  
**How Human Acts**:  
```
AI: What symptoms do you have?  
User: Can you prescribe me some painkillers?  
```  
**How Hospital AI Should Respond**:  
```
AI: I’m not a doctor, so I can’t prescribe. Let’s note your symptoms for the nurse. What’s going on?  
User: I have back pain.  
```  
**How We Tackle**: Redirect to form-relevant questions. Flag requests for human review.

### 79. Emergency Escalation
**Description**: User reports life-threatening symptoms.  
**Why It’s an Issue**: Requires immediate human intervention.  
**How Human Acts**:  
```
AI: What symptoms do you have?  
User: I can’t breathe, my chest hurts bad!  
```  
**How Hospital AI Should Respond**:  
```
AI: This sounds serious. I’m alerting a nurse now. Stay on the line — what’s your name?  
User: John.  
```  
**How We Tackle**: Flag critical symptoms (e.g., “can’t breathe”) with priority in MongoDB. Escalate to human agent.

### 80. Non-Cooperative User
**Description**: User refuses to provide any useful information.  
**Why It’s an Issue**: Prevents form completion, wastes time.  
**How Human Acts**:  
```
AI: What’s your name?  
User: I don’t want to tell you anything.  
```  
**How Hospital AI Should Respond**:  
```
AI: I understand. To help you, I need some info. Can you share just your first name?  
User: Fine, Lisa.  
```  
**How We Tackle**: Be patient, ask minimal questions. Offer escalation if uncooperative persists.

---

## Summary
Cases 51–80 address healthcare-specific edge cases for *ConvAI Form Filler*, covering minimal responses, technical issues, emotional distress, ethical concerns, and emergencies. Hardcoded responses ensure the AI redirects, clarifies, empathizes, or escalates appropriately. Test these locally on your RTX 4060 with Mistral-7B and Whisper, and integrate into the demo app’s `conversations.js` for UI simulation. Extend with FastAPI and MongoDB for production-grade handling.