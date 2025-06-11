# a script to clean up video files in the /videos directory, but keep subfolders of rollnumber, only delete videos/audio files inside the roll number subfolders
# the /videos directory is expected to be in the ConvAi-IntroEval project root directory
# videos directory=Project-ConvAi\ConvAi-IntroEval\videos

import os
import glob

def cleanup_videos():
    # Navigate to the ConvAi-IntroEval directory from the current script location
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)  # Go up one level from 'python scripts'
    convai_dir = os.path.join(project_root, 'ConvAi-IntroEval')
    videos_dir = os.path.join(convai_dir, 'videos')
    
    if not os.path.exists(videos_dir):
        print(f"Directory {videos_dir} does not exist.")
        return

    # Get all subdirectories in the videos directory (roll number folders)
    subdirs = [d for d in os.listdir(videos_dir) if os.path.isdir(os.path.join(videos_dir, d))]

    # Iterate through each subdirectory (roll number folder)
    for subdir in subdirs:
        subdir_path = os.path.join(videos_dir, subdir)
        # Get all video and audio files in the subdirectory
        video_files = (glob.glob(os.path.join(subdir_path, '*.[Mm][Pp]4')) + 
                      glob.glob(os.path.join(subdir_path, '*.[Mm][Kk][Vv]')) + 
                      glob.glob(os.path.join(subdir_path, '*.[Aa][Vv][Ii]')) + 
                      glob.glob(os.path.join(subdir_path, '*.[Mm][Pp][Ee][Gg]')) + 
                      glob.glob(os.path.join(subdir_path, '*.[Ww][Aa][Vv]')) + 
                      glob.glob(os.path.join(subdir_path, '*.[Mm][Pp][3]')))

        # Delete each video and audio file
        for file in video_files:
            try:
                os.remove(file)
                print(f"Deleted file: {file}")
            except Exception as e:
                print(f"Error deleting file {file}: {e}")
    
    print("Cleanup completed.")

if __name__ == "__main__":
    cleanup_videos()
