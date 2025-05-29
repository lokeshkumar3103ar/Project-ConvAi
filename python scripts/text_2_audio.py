# write a program to convert text to audio and save it in a folder named text_to_audio in same directory
import os
text='''# Self Introduction - Aravindakshan R

"Hello everyone! I'm Aaaravindakshan R, a 20-year-old second-year B.Tech Computer Science Engineering student at Hindustan Institute of Technology and Science in Chennai. I'm fluent in Tamil as my native language, professionally proficient in English, and have elementary knowledge of Hindi and Korean.

I began my academic journey at D.A.V. Public School, graduating in March 2023, and I'm currently pursuing my Bachelor's degree which I'll complete in August 2027. During my education, I've earned a MATLAB certification that has enhanced my technical capabilities.

My passion lies in web development. During my internships at CodSoft and ApexPlanet Software from October to November 2024, I gained valuable experience building responsive websites. At CodSoft, I created a personal portfolio, designed landing pages, and built a complete portfolio website using HTML and CSS. Simultaneously at ApexPlanet, I expanded my skills by developing dynamic applications with JavaScript, including a to-do list app with task management functionality and responsive contact forms with validation features.

My technical skills include proficiency in C++, C, and GitHub version control, alongside web technologies like HTML, CSS, and JavaScript. Through my internships and coursework, I've also developed strong time management, problem-solving, and adaptability skills that complement my technical abilities.

I've participated in several hackathons and completed additional courses in web development and AI to supplement my formal education. I consider myself detail-oriented, adaptive, and quick to learn new technologies.

My goal is to secure a position as a Web Developer or Front-End Developer where I can apply my skills while continuing to grow. I'm based in Chennai but open to relocating for the right opportunity, and I'm flexible regarding work environments, whether remote, hybrid, or on-site.

I'm eager to continue learning and contributing to innovative projects in the tech industry. Thank you for this opportunity to introduce myself!"
'''
#the audio should save in "C:\Users\lokes\Downloads\KAMPYUTER\College Projects\Project ConvAi\Project-ConvAi\extras\text_to_audio"

import pyttsx3

def text_to_audio(text, filename='introduction.mp3'):
    # Initialize the text-to-speech engine
    engine = pyttsx3.init()
    
    # Set properties before adding anything to speak
    engine.setProperty('rate', 150)  # Speed of speech
    engine.setProperty('volume', 1)  # Volume (0.0 to 1.0)

    # Create a directory for audio files if it doesn't exist
    output_dir = r"C:\Users\lokes\Downloads\KAMPYUTER\College Projects\Project ConvAi\Project-ConvAi\extras\text_to_audio"
    os.makedirs(output_dir, exist_ok=True)
    
    # Save the audio file
    audio_path = os.path.join(output_dir, filename)
    engine.save_to_file(text, audio_path)
    
    # Run the engine to process the speech
    engine.runAndWait()
    
    print(f"Audio saved as {audio_path}")
# get text from user
if __name__ == "__main__":
    # Uncomment the next line to get text from user input
    # text = input("Enter the text you want to convert to audio: ")
    
    # Call the function to convert text to audio
    text_to_audio(text, 'introduction.mp3')