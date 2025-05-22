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

def transcribe_file(file_path: Path, output_dir: Path) -> tuple[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)

    # Ensure we're working with the file in videos directory, not copying it
    if not str(file_path).lower().startswith(str(Path(file_path).parent).lower()):
        print(f"⚠️ Warning: File path should be in the videos directory")

    result = model.transcribe(str(file_path), verbose=False, language="en")
    formatted_text = format_transcription(result.get("segments", []))

    output_file = output_dir / f"{file_path.stem}_transcription_{model_size}.txt"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(formatted_text)

    print(f"✅ Transcription saved: {output_file}")
    return formatted_text, output_file
