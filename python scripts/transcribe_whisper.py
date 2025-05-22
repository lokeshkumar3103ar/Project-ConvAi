import os
import whisper
rel_path = '.\speech_data' #relative path of speech_data folder
file_list = []

for file_name in os.listdir(rel_path):
    if os.path.isfile(os.path.join(rel_path, file_name)): #checks if the file exists 
        file_list.append(file_name)

open("./transcriptions.txt", "w") #open the file transcriptions if it doesn't exist or overwrites it if it exists

model = whisper.load_model("medium") #loads the whisper model (use small, medium,  large, turbo)
options = dict(language="en", beam_size=5, best_of=5, temperature=0.0) #fiddle with beam_size and best_of to get the best results (use 10 or 5 )

n=len(file_list)
for i in range(n):
    file_name = file_list[i]
    print("Transcribing"+file_name) #to show what file is being transcribed
    full_file = os.path.join(rel_path, file_name) #full path of the file

    result = model.transcribe(full_file, **options) #transcribes the audio file
    text = result["text"] #takes only the text from the result

    with open("./transcriptions.txt", "a") as f: #writing the text to a file
        f.write(f"{file_name}: {text}\n") 

print("TRANSCRIPTION COMPLETED") 