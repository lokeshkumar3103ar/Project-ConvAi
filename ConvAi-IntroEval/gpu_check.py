#!/usr/bin/env python3
"""
GPU Detection and PyTorch CUDA Verification Script
This script checks if GPU is available and properly configured for STT processing.
"""

import torch
import sys
import platform

def check_gpu_availability():
    """Comprehensive GPU availability check"""
    print("=" * 60)
    print("🔍 GPU DETECTION AND PYTORCH CUDA VERIFICATION")
    print("=" * 60)
    
    # System Info
    print(f"🖥️  System: {platform.system()} {platform.release()}")
    print(f"🐍 Python: {sys.version}")
    print(f"🔥 PyTorch: {torch.__version__}")
    
    # CUDA Availability
    print(f"\n📊 CUDA STATUS:")
    print(f"   CUDA Available: {torch.cuda.is_available()}")
    
    if torch.cuda.is_available():
        print(f"   CUDA Version: {torch.version.cuda}")
        print(f"   cuDNN Version: {torch.backends.cudnn.version()}")
        print(f"   GPU Count: {torch.cuda.device_count()}")
        
        # GPU Details
        for i in range(torch.cuda.device_count()):
            gpu_props = torch.cuda.get_device_properties(i)
            memory_gb = gpu_props.total_memory / (1024**3)
            print(f"   GPU {i}: {gpu_props.name} ({memory_gb:.1f} GB)")
            
        # Current Device
        current_device = torch.cuda.current_device()
        print(f"   Current Device: {current_device}")
        
        # Memory Info
        if torch.cuda.is_available():
            allocated = torch.cuda.memory_allocated() / (1024**3)
            cached = torch.cuda.memory_reserved() / (1024**3)
            print(f"   Memory Allocated: {allocated:.2f} GB")
            print(f"   Memory Cached: {cached:.2f} GB")
            
        # Test GPU Tensor Operations
        print(f"\n🧪 GPU TENSOR TEST:")
        try:
            # Create test tensor on GPU
            test_tensor = torch.randn(1000, 1000, device='cuda')
            result = torch.matmul(test_tensor, test_tensor)
            print(f"   ✅ GPU tensor operations working")
            print(f"   ✅ Test tensor shape: {result.shape}")
            print(f"   ✅ Tensor device: {result.device}")
            
            # Clean up
            del test_tensor, result
            torch.cuda.empty_cache()
            
        except Exception as e:
            print(f"   ❌ GPU tensor test failed: {e}")
            
    else:
        print("   ❌ CUDA not available - will use CPU")
        print("   💡 Possible reasons:")
        print("      - NVIDIA GPU drivers not installed")
        print("      - CUDA toolkit not installed")
        print("      - PyTorch installed without CUDA support")
        print("      - Incompatible CUDA version")

def test_whisper_gpu():
    """Test Whisper model GPU usage"""
    print(f"\n🎤 WHISPER GPU TEST:")
    try:
        import whisper
        
        device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"   Target device: {device}")
        
        # Load small model for testing
        print(f"   Loading Whisper 'tiny' model on {device}...")
        model = whisper.load_model("tiny", device=device)
        
        print(f"   ✅ Whisper model loaded successfully")
        print(f"   ✅ Model device: {next(model.parameters()).device}")
        
        # Test with dummy audio (1 second of silence)
        print(f"   Testing transcription...")
        dummy_audio = torch.zeros(16000, dtype=torch.float32)  # 1 second at 16kHz
        
        with torch.no_grad():
            result = model.transcribe(dummy_audio.numpy(), verbose=False)
            
        print(f"   ✅ Transcription test successful")
        print(f"   ✅ Result: {result.get('text', 'No text')}")
        
        # Memory cleanup
        del model
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            
    except ImportError:
        print(f"   ❌ Whisper not installed")
    except Exception as e:
        print(f"   ❌ Whisper GPU test failed: {e}")

def recommend_fixes():
    """Provide recommendations if GPU is not working"""
    print(f"\n💡 RECOMMENDATIONS:")
    
    if not torch.cuda.is_available():
        print("   🔧 To enable GPU for STT:")
        print("      1. Install NVIDIA GPU drivers")
        print("      2. Install CUDA toolkit (version 12.1 recommended)")
        print("      3. Reinstall PyTorch with CUDA:")
        print("         pip uninstall torch torchaudio torchvision")
        print("         pip install torch torchaudio torchvision --index-url https://download.pytorch.org/whl/cu121")
        print("      4. Restart your application")
    else:
        print("   ✅ GPU is properly configured!")
        print("   🚀 Your STT processing should use GPU acceleration")
        
def main():
    """Main function to run all checks"""
    check_gpu_availability()
    test_whisper_gpu()
    recommend_fixes()
    
    print("\n" + "=" * 60)
    print("🏁 GPU CHECK COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    main()
