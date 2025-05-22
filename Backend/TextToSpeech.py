import random
import asyncio
import edge_tts
import os
import pygame
import time
import threading
from dotenv import dotenv_values

env_vars = dotenv_values(".env")
AssistantVoice = env_vars.get("AssistantVoice")
Username = env_vars.get("Username")

# Global variables for audio management
audio_lock = threading.Lock()
current_audio_file = None
mixer_initialized = False

def initialize_mixer():
    global mixer_initialized
    if not mixer_initialized:
        try:
            pygame.mixer.init()
            mixer_initialized = True
        except pygame.error as e:
            print(f"Mixer initialization error: {e}")

def cleanup_resources():
    """Clean up all audio resources"""
    global mixer_initialized, current_audio_file
    
    with audio_lock:
        try:
            if pygame.mixer.get_init():
                if pygame.mixer.music.get_busy():
                    pygame.mixer.music.stop()
                pygame.mixer.quit()
        except:
            pass
        
        mixer_initialized = False
        current_audio_file = None

async def generate_audio_file(text, file_path):
    """Generate audio file with retry logic"""
    max_retries = 3
    for attempt in range(max_retries):
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
            
            communicate = edge_tts.Communicate(text, AssistantVoice, pitch='+5Hz', rate='+13%')
            await communicate.save(file_path)
            return True
        except PermissionError:
            if attempt < max_retries - 1:
                await asyncio.sleep(0.5 * (attempt + 1))
                continue
            raise
    return False

def play_audio(file_path, interrupt_check):
    """Play audio with proper resource management"""
    try:
        pygame.mixer.music.load(file_path)
        pygame.mixer.music.play()
        
        while pygame.mixer.music.get_busy():
            if interrupt_check() == False:
                pygame.mixer.music.stop()
                return False
            time.sleep(0.1)
        return True
    except pygame.error as e:
        print(f"Audio playback error: {e}")
        return False

def TTS(text, interrupt_check=lambda: True):
    """Main TTS function with comprehensive error handling"""
    global current_audio_file
    
    # Create Data directory if it doesn't exist
    os.makedirs("Data", exist_ok=True)
    
    # Generate unique filename for each TTS request
    timestamp = str(int(time.time()))
    temp_file = f"Data/speech_{timestamp}.mp3"
    
    with audio_lock:
        try:
            # Stop any currently playing audio
            if pygame.mixer.get_init() and pygame.mixer.music.get_busy():
                pygame.mixer.music.stop()
            
            # Initialize mixer if needed
            initialize_mixer()
            
            # Generate audio file
            if not asyncio.run(generate_audio_file(text, temp_file)):
                return False
            
            # Play the audio
            success = play_audio(temp_file, interrupt_check)
            
            # Clean up the temporary file
            try:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
            except:
                pass
                
            return success
            
        except Exception as e:
            print(f"TTS error: {e}")
            return False

def TextToSpeech(text, interrupt_check=lambda: True):
    """Wrapper function for handling long texts"""
    responses = [
        f"That is a lot of text to read!! The rest of the result is being displayed on the chat screen, kindly check it out {Username}.",
        f"The rest of the text is now on the chat screen, {Username} please check it.",
        # ... (your existing responses)
    ]

    sentences = text.split(".")
    if len(sentences) > 4 and len(text) >= 250:
        short_version = " ".join(sentences[0:2]) + "." + random.choice(responses)
        TTS(short_version, interrupt_check)
    else:
        TTS(text, interrupt_check)

# Clean up when the module is unloaded
import atexit
atexit.register(cleanup_resources)