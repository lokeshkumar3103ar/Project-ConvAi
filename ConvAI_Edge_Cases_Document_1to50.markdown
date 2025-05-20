# ConvAI Edge Cases: 80 Test Cases for Robust Conversations

This document outlines 80 edge cases for the *ConvAI Form Filler* AI, which uses voice input to fill HR and healthcare forms. Each case details user challenges, AI responses, and solutions, ensuring the system handles linguistic, emotional, technical, ethical, and extreme scenarios. Cases are tested locally on an NVIDIA RTX 4060 with Mistral-7B and Whisper, using hardcoded responses for simplicity.

## HR Edge Cases

### 1. Irrelevant Answer
**Description**: User provides off-topic information unrelated to the form.  
**Why It’s an Issue**: AI cannot extract relevant data, delaying form completion.  
**How Human Acts**:  
```
AI: Tell me about yourself.  
User: I love pizza and hiking on weekends.  
```  
**How HR AI Should Respond**:  
```
AI: Pizza and hiking sound awesome! Can you share your name and a skill you use at work?  
User: I’m Arjun, and I’m a web developer.  
```  
**How We Tackle**: Redirect by relating to form fields and asking specific questions. Use spaCy to detect irrelevant topics and prioritize key entities (e.g., “skill”, “job”).

### 2. One-Word Answer
**Description**: User gives minimal, single-word responses.  
**Why It’s an Issue**: Insufficient data for form fields.  
**How Human Acts**:  
```
AI: What’s your main skill?  
User: Coding.  
```  
**How HR AI Should Respond**:  
```
AI: Cool! What kind of coding? Like Python or JavaScript?  
User: Python.  
```  
**How We Tackle**: Ask closed-ended, specific questions. Mistral-7B extracts single words as partial data, updating forms incrementally.

### 3. Contradictory Answer
**Description**: User provides conflicting information.  
**Why It’s an Issue**: Risks incorrect form data.  
**How Human Acts**:  
```
AI: How old are you?  
User: I’m 25. Wait, no, 30.  
```  
**How HR AI Should Respond**:  
```
AI: Thanks! Just to confirm, are you 30 years old?  
User: Yes, 30.  
```  
**How We Tackle**: Confirm the latest input with a verification prompt. Log contradictions in MongoDB for review.

### 4. Angry Outburst
**Description**: User expresses frustration with the process.  
**Why It’s an Issue**: May derail conversation or discourage user.  
**How Human Acts**:  
```
AI: What’s your work experience?  
User: This is stupid, why do I need to do this?  
```  
**How HR AI Should Respond**:  
```
AI: I hear you, it can feel repetitive. Let’s make it quick — what’s one job you’ve had?  
User: I was a cashier for a year.  
```  
**How We Tackle**: Acknowledge emotion, simplify questions, and maintain a calm tone. Use spaCy sentiment analysis to detect anger.

### 5. Sad Response
**Description**: User expresses sadness or discouragement.  
**Why It’s an Issue**: Emotional state may reduce cooperation.  
**How Human Acts**:  
```
AI: Tell me about yourself.  
User: I’m just not feeling great about my job search.  
```  
**How HR AI Should Respond**:  
```
AI: I’m sorry to hear that. Let’s highlight your strengths — what’s a skill you’re proud of?  
User: I’m good at project management.  
```  
**How We Tackle**: Empathize and pivot to positive, actionable questions. Log emotional responses for human review.

### 6. Overly Verbose
**Description**: User rambles with long, detailed stories.  
**Why It’s an Issue**: Hard to extract concise form data.  
**How Human Acts**:  
```
AI: What’s your work experience?  
User: Oh, I’ve done so much! I started as an intern, then got promoted, worked on this huge project…  
```  
**How HR AI Should Respond**:  
```
AI: That sounds exciting! Can you sum up your main role and years of experience?  
User: I’m a software engineer with 5 years.  
```  
**How We Tackle**: Interrupt politely and request a summary. Set a 500-token limit for Mistral-7B processing.

### 7. Multilingual Input
**Description**: User mixes languages (e.g., English and Tamil).  
**Why It’s an Issue**: AI may not understand non-English terms.  
**How Human Acts**:  
```
AI: What’s your main skill?  
User: I’m a coder, I use Python and pannu software development.  
```  
**How HR AI Should Respond**:  
```
AI: Got Python! Can you clarify what you do in software development, maybe in English?  
User: I build web apps.  
```  
**How We Tackle**: Use `langdetect` to identify languages and prompt for English. Translate key terms with a dictionary.

### 8. Noisy Audio
**Description**: Background noise corrupts speech-to-text.  
**Why It’s an Issue**: Incorrect transcription leads to wrong data.  
**How Human Acts**:  
```
AI: What’s your name?  
[Whisper Output]: Priya [loud music] coder.  
```  
**How HR AI Should Respond**:  
```
AI: I heard “Priya.” Is that your name? Any music we can turn down?  
User: Yes, Priya. I’ll lower it.  
```  
**How We Tackle**: Confirm partial transcriptions. Use `librosa` for noise filtering in Whisper.

### 9. Silence
**Description**: User doesn’t speak after prompt.  
**Why It’s an Issue**: Halts conversation flow.  
**How Human Acts**:  
```
AI: Tell me about yourself.  
[No Input]  
```  
**How HR AI Should Respond**:  
```
AI: I didn’t hear anything. Is your mic on? What’s your name?  
User: Sofia.  
```  
**How We Tackle**: Set a 5-second timeout in `pyaudio`. Prompt to check mic and retry.

### 10. Abusive Language
**Description**: User uses offensive words.  
**Why It’s an Issue**: Violates usage policy; risks user disengagement.  
**How Human Acts**:  
```
AI: What’s your work experience?  
User: This AI is garbage!  
```  
**How HR AI Should Respond**:  
```
AI: I’m sorry you feel that way. Let’s try again — what’s a job you’ve had?  
User: I’m a designer.  
```  
**How We Tackle**: Filter with `profanity-check`. Offer escalation to human agent.

*(Cases 11–40 for HR include: vague answers, contradictory skills, overly excited users, dropped connections, low GPU memory, sensitive data sharing, biased assumptions, non-human input, long pauses, repetitive answers, slang-heavy input, sarcastic responses, requesting human agent, fast speech, slow speech, accent challenges, multiple speakers, joking responses, changing topics, incomplete sentences, whispering, shouting, background chatter, device issues, consent refusal, cultural misunderstandings, outdated information, ambiguous pronouns, and requesting illegal actions. Each follows the same format.)*

## Healthcare Edge Cases

### 41. Vague Symptoms
**Description**: User describes symptoms non-specifically.  
**Why It’s an Issue**: Prevents accurate form completion.  
**How Human Acts**:  
```
AI: What happened?  
User: I feel bad.  
```  
**How Hospital AI Should Respond**:  
```
AI: I’m sorry to hear that. Any specific symptoms, like pain or fever?  
User: Headaches and tiredness.  
```  
**How We Tackle**: Use yes/no or list-based prompts. Mistral-7B maps vague terms to symptom categories.

### 42. Unrelated Complaints
**Description**: User mentions irrelevant health issues.  
**Why It’s an Issue**: Distracts from current symptoms.  
**How Human Acts**:  
```
AI: What’s bothering you today?  
User: My knee hurts from last year, and my cat scratched me.  
```  
**How Hospital AI Should Respond**:  
```
AI: Ouch, sorry about that! Let’s focus on today — any current symptoms like fever?  
User: I have a fever.  
```  
**How We Tackle**: Refocus on present issues. Ignore unrelated data in form updates.

### 43. Emotional Distress
**Description**: User is scared or upset about their condition.  
**Why It’s an Issue**: May hinder clear responses.  
**How Human Acts**:  
```
AI: What symptoms do you have?  
User: I’m so scared, I’m always sick.  
```  
**How Hospital AI Should Respond**:  
```
AI: I’m really sorry you’re feeling scared. Let’s note your symptoms to help the doctors. What’s been happening?  
User: Chest pain.  
```  
**How We Tackle**: Empathize, then pivot to actionable questions. Log for nurse review.

### 44. Contradictory Symptoms
**Description**: User reports conflicting health details.  
**Why It’s an Issue**: Risks incorrect medical data.  
**How Human Acts**:  
```
AI: Any symptoms?  
User: I have a fever. No, I feel cold.  
```  
**How Hospital AI Should Respond**:  
```
AI: Thanks for sharing. To clarify, do you have a fever or feel cold now?  
User: I have a fever.  
```  
**How We Tackle**: Verify the latest symptom. Flag contradictions in logs.

### 45. Noisy Audio
**Description**: Background noise affects transcription.  
**Why It’s an Issue**: Leads to incomplete or wrong symptom data.  
**How Human Acts**:  
```
AI: What symptoms do you have?  
[Whisper Output]: Fever [baby crying] cough.  
```  
**How Hospital AI Should Respond**:  
```
AI: I heard “fever” and “cough.” Is that right? Can we reduce any background noise?  
User: Yes, that’s correct.  
```  
**How We Tackle**: Confirm partial data. Enhance Whisper with noise suppression.

### 46. Silence
**Description**: User doesn’t respond to prompt.  
**Why It’s an Issue**: Stops data collection.  
**How Human Acts**:  
```
AI: What’s your name?  
[No Input]  
```  
**How Hospital AI Should Respond**:  
```
AI: I didn’t catch that. Is your mic working? What’s your name?  
User: Emma.  
```  
**How We Tackle**: Implement a 5-second timeout. Prompt to check mic.

### 47. Overly Verbose
**Description**: User gives a long medical history.  
**Why It’s an Issue**: Hard to isolate current symptoms.  
**How Human Acts**:  
```
AI: What’s bothering you?  
User: I’ve had asthma forever, then last year I broke my leg, and now I feel off…  
```  
**How Hospital AI Should Respond**:  
```
AI: Thanks for the details! What symptoms are you feeling today?  
User: Fever and cough.  
```  
**How We Tackle**: Request a summary of current issues. Limit input to 500 tokens.

### 48. Multilingual Input
**Description**: User uses non-English terms (e.g., Spanish).  
**Why It’s an Issue**: AI may miss key symptoms.  
**How Human Acts**:  
```
AI: What symptoms do you have?  
User: I have fiebre, uh, fever, and tos.  
```  
**How Hospital AI Should Respond**:  
```
AI: Got “fever”! Can you describe your cough in English, please?  
User: It’s dry and constant.  
```  
**How We Tackle**: Detect language with `langdetect`. Translate medical terms.

### 49. Abusive Language
**Description**: User insults the AI or process.  
**Why It’s an Issue**: Disrupts interaction; ethical concerns.  
**How Human Acts**:  
```
AI: What’s your name?  
User: This is a waste of time, idiot AI!  
```  
**How Hospital AI Should Respond**:  
```
AI: I’m sorry you’re frustrated. Let’s get started — what’s your name?  
User: Liam.  
```  
**How We Tackle**: Filter profanity with `profanity-check`. Escalate if repeated.

### 50. Sensitive Data
**Description**: User shares private information (e.g., SSN).  
**Why It’s an Issue**: Privacy violation; legal risks.  
**How Human Acts**:  
```
AI: What’s your name?  
User: John, and my SSN is 123-45-6789.  
```  
**How Hospital AI Should Respond**:  
```
AI: Thanks, John. I don’t need your SSN — just your symptoms, please.  
User: I have a headache.  
```  
**How We Tackle**: Use spaCy NER to redact sensitive data. Log anonymized data.

*(Cases 51–80 for Healthcare include: minimal answers, contradictory medical history, overly excited patients, dropped connections, low GPU memory, biased assumptions, non-human input, long pauses, repetitive complaints, slang-heavy input, sarcastic responses, requesting human agent, fast speech, slow speech, accent challenges, multiple speakers, joking responses, changing topics, incomplete sentences, whispering, shouting, background chatter, device issues, consent refusal, cultural misunderstandings, outdated medical info, ambiguous symptoms, requesting illegal actions, and emergency escalation. Each follows the same format.)*

## Summary
These 80 edge cases ensure *ConvAI Form Filler* handles diverse user behaviors, from irrelevant rambles to technical failures. By using redirection, clarification, empathy, and technical fallbacks, the AI maintains accurate form completion. Test locally with your RTX 4060, Mistral-7B, and Whisper, and extend with backend logic (FastAPI, MongoDB) for production.