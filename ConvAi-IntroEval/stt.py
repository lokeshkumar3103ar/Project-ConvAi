import whisper
from pathlib import Path

SUPPORTED_EXTENSIONS = [".mp3", ".mp4", ".wav", ".m4a", ".webm", ".flac", ".ogg", ".aac"]
model_size = "turbo"
model = whisper.load_model(model_size)

def format_transcription(segments):
    formatted = []
    for seg in segments:
        start = seg['start']
        end = seg['end']
        text = seg['text'].strip()
        timestamp = f"[{int(start)//60:02d}:{int(start)%60:02d} - {int(end)//60:02d}:{int(end)%60:02d}]"
        formatted.append(f"{timestamp} {text}")
    return "\n\n".join(formatted)

def transcribe_file(file_path: Path, output_dir: Path, roll_number: str = None) -> tuple[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Create roll_number subdirectory if roll_number is provided
    if roll_number:
        user_output_dir = output_dir / roll_number
        user_output_dir.mkdir(parents=True, exist_ok=True)
        print(f"📁 Using user directory for roll {roll_number}: {user_output_dir}")
    else:
        user_output_dir = output_dir

    # Ensure we're working with the file in videos directory, not copying it
    if "videos" not in str(file_path).lower():
        print(f"⚠️ Warning: Expected file to be inside videos directory: {file_path}")

    result = model.transcribe(str(file_path), verbose=False, language="en")
    formatted_text = format_transcription(result.get("segments", []))

    output_file = user_output_dir / f"{file_path.stem}_transcription_{model_size}.txt"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(formatted_text)

    location_info = f" (roll: {roll_number})" if roll_number else " (root)"
    print(f"✅ Transcription ({model_size}) saved{location_info}: {output_file}")
    return formatted_text, output_file
