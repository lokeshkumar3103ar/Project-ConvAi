import whisper
from pathlib import Path
import threading
import os
import gc
import torch

SUPPORTED_EXTENSIONS = [".mp3", ".mp4", ".wav", ".m4a", ".webm", ".flac", ".ogg", ".aac"]
model_size = "turbo"

# Thread-safe model loading with proper isolation
_model_lock = threading.RLock()  # Re-entrant lock for better thread safety
_model_cache = {}
_device_locks = {}  # Per-device locks to prevent CUDA conflicts

def get_whisper_model():
    """Get a thread-safe Whisper model instance with proper CUDA isolation"""
    thread_id = threading.get_ident()
    
    # Determine the device
    device = "cuda" if torch.cuda.is_available() else "cpu"
    
    with _model_lock:
        # Create device lock if it doesn't exist
        if device not in _device_locks:
            _device_locks[device] = threading.Lock()
        
        # Use device-specific lock for CUDA operations
        with _device_locks[device]:
            # Create unique key for thread and device
            cache_key = f"{thread_id}_{device}"
            
            if cache_key not in _model_cache:
                print(f"🎤 Loading Whisper model '{model_size}' for thread {thread_id} on {device}")
                
                try:
                    # Clear CUDA cache before loading if using GPU
                    if device == "cuda":
                        torch.cuda.empty_cache()
                        # Set CUDA context for this thread
                        torch.cuda.set_device(0)
                    
                    # Load model with specific device
                    model = whisper.load_model(model_size, device=device)
                    
                    # Ensure model is in eval mode for thread safety
                    model.eval()
                    
                    _model_cache[cache_key] = model
                    print(f"✅ Whisper model loaded successfully for thread {thread_id} on {device}")
                    
                except Exception as e:
                    print(f"❌ Failed to load Whisper model for thread {thread_id}: {e}")
                    # Fallback to CPU if CUDA fails
                    if device == "cuda":
                        print("🔄 Falling back to CPU...")
                        try:
                            model = whisper.load_model(model_size, device="cpu")
                            model.eval()
                            _model_cache[f"{thread_id}_cpu"] = model
                            print(f"✅ Whisper model loaded on CPU for thread {thread_id}")
                            return model
                        except Exception as cpu_e:
                            print(f"❌ CPU fallback also failed: {cpu_e}")
                            raise
                    raise
            
            return _model_cache[cache_key]


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
    """
    Transcribe audio/video file using Whisper with thread-safe model loading.
    
    Args:
        file_path: Path to the audio/video file
        output_dir: Directory to save transcription
        roll_number: Optional roll number for user-specific subdirectory
    
    Returns:
        tuple: (transcription_text, output_file_path)
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Ensure file_path is a Path object
    if isinstance(file_path, str):
        file_path = Path(file_path)
    
    # Create roll_number subdirectory if roll_number is provided
    if roll_number:
        user_output_dir = output_dir / roll_number
        user_output_dir.mkdir(parents=True, exist_ok=True)
        print(f"📁 Using user directory for roll {roll_number}: {user_output_dir}")
    else:
        user_output_dir = output_dir

    # Ensure we're working with the file in videos directory, not copying it
    if "videos" not in str(file_path).lower():
        print(f"⚠️ Warning: Expected file to be inside videos directory: {file_path}")    # Get thread-safe model instance with proper isolation
    model = get_whisper_model()
    
    try:
        print(f"🎤 Starting transcription for thread {threading.get_ident()}: {file_path}")
        
        # Use torch.no_grad() to prevent memory leaks and ensure thread safety
        with torch.no_grad():
            # Ensure we're on the right device
            device = "cuda" if torch.cuda.is_available() else "cpu"
            
            # Transcribe with explicit parameters for consistency
            result = model.transcribe(
                str(file_path), 
                verbose=False, 
                language="en",
                task="transcribe",
                temperature=0.0,  # Deterministic output
                beam_size=1,      # Fastest beam search
                best_of=1         # Single attempt for speed
            )
            
            # Clean up intermediate tensors if on CUDA
            if device == "cuda":
                torch.cuda.empty_cache()
        
        formatted_text = format_transcription(result.get("segments", []))
        
        output_file = user_output_dir / f"{file_path.stem}_transcription_{model_size}.txt"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(formatted_text)

        location_info = f" (roll: {roll_number})" if roll_number else " (root)"
        print(f"✅ Transcription ({model_size}) saved{location_info}: {output_file}")
        return formatted_text, output_file
        
    except Exception as e:
        print(f"❌ Transcription failed for thread {threading.get_ident()}: {e}")
        
        # Clean up CUDA memory on error
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        
        # Re-raise the exception for proper error handling
        raise RuntimeError(f"STT processing failed: {e}") from e
