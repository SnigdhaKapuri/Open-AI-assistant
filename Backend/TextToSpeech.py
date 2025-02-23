import pygame
import random
import asyncio
import edge_tts
import os
from dotenv import dotenv_values

# Load environment variables
env_vars = dotenv_values(".env")
AssistantVoice = env_vars.get("AssistantVoice", "en-US-JennyNeural")  # Default voice

# Define file path for audio
AUDIO_FILE_PATH = os.path.join("Data", "speech.mp3")

async def TextToAudioFile(text):
    """
    Converts text to speech and saves as an audio file.
    """
    try:
        # Remove existing file
        if os.path.exists(AUDIO_FILE_PATH):
            os.remove(AUDIO_FILE_PATH)

        # Convert text to speech
        communicate = edge_tts.Communicate(text, AssistantVoice, pitch='+5Hz', rate='+13%')
        await communicate.save(AUDIO_FILE_PATH)

    except Exception as e:
        print(f"Error generating audio file: {e}")

def play_audio():
    """
    Plays the generated audio file using pygame.
    """
    pygame.mixer.init()
    try:
        pygame.mixer.music.load(AUDIO_FILE_PATH)
        pygame.mixer.music.play()

        # Wait for audio to finish playing
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)

    except Exception as e:
        print(f"Error playing audio: {e}")

    finally:
        pygame.mixer.music.stop()
        pygame.mixer.quit()

def TTS(Text):
    """
    Converts text to speech and plays the generated audio.
    """
    try:
        asyncio.run(TextToAudioFile(Text))  # Generate speech
        play_audio()  # Play the speech
        return True

    except Exception as e:
        print(f"Error in TTS function: {e}")
        return False

def TextToSpeech(Text):
    """
    Splits long text and plays the first part along with a random message,
    while displaying the rest on the screen.
    """
    responses = [
        "The rest of the result has been printed to the chat screen, kindly check it out.",
        "The rest of the text is now on the chat screen, please check it.",
        "You can see the rest of the text on the chat screen.",
        "The remaining part of the text is now on the chat screen.",
        "You'll find more text on the chat screen for you to see.",
        "The rest of the answer is now on the chat screen.",
        "Please look at the chat screen for the rest of the answer.",
        "You'll find the complete answer on the chat screen.",
        "The next part of the text is on the chat screen.",
        "Please check the chat screen for more information."
    ]

    text_parts = Text.split(".")

    # If the text is long, play the first two sentences and inform the user
    if len(text_parts) > 4 and len(Text) >= 250:
        TTS(" ".join(text_parts[:2]) + ". " + random.choice(responses))
    else:
        TTS(Text)

if __name__ == "__main__":
    while True:
        user_input = input("Enter the text: ")
        if user_input.lower() == "exit":
            break
        TextToSpeech(user_input)
