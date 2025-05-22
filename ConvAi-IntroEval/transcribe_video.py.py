import whisper
from pathlib import Path

# Supported audio/video extensions
SUPPORTED_EXTENSIONS = [".mp3", ".mp4", ".wav", ".m4a", ".webm", ".flac", ".ogg", ".aac"]
model_size = "turbo"  # Change to "medium" or "large" if needed
# Load Whisper model
model = whisper.load_model(model_size)  # or "medium", "large" if you prefer

# Input/output directories
input_dir = Path("Project-ConvAi") / "ConvAi-IntroEval" / "videos" 
output_dir = Path("Project-ConvAi") / "ConvAi-IntroEval" / "transcription"
output_dir.mkdir(exist_ok=True)

# Format transcription as readable paragraphs
def format_transcription(segments):
    formatted = []
    for seg in segments:
        start = seg['start']
        end = seg['end']
        text = seg['text'].strip()
        timestamp = f"[{int(start)//60:02d}:{int(start)%60:02d} - {int(end)//60:02d}:{int(end)%60:02d}]"
        formatted.append(f"{timestamp} {text}")
    return "\n\n".join(formatted)

# Process each file
for file in input_dir.iterdir():
    if file.suffix.lower() in SUPPORTED_EXTENSIONS:
        print(f"Processing {file.name}...")
        result = model.transcribe(str(file), verbose=False, language="en")
        formatted_text = format_transcription(result.get("segments", []))
        #the output file name should also have the model we used like small, large etc
        output_file = output_dir / f"{file.stem}_transcription_{model_size}.txt"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(formatted_text)

        print(f"✅ Saved: {output_file}")
