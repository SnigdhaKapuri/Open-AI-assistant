from Frontend.GUI import (
    GraphicalUserInterface,
    SetAssistantStatus,
    ShowTextToScreen,
    TempDirectoryPath, 
    SetMicrophoneStatus,
    AnswerModifier,
    QueryModifier,
    GetMicrophoneStatus,
    GetAssistantStatus
)
from Backend.Model import FirstLayerDMM
from Backend.RealtimeSearchEngine import RealtimeSearchEngine
from Backend.Automation import Automation
from Backend.SpeechToText import SpeechRecognition
from Backend.Chatbot import ChatBot
from Backend.TextToSpeech import TextToSpeech
from dotenv import dotenv_values
from asyncio import run
from time import sleep
import subprocess
import threading
import json
import os
import psutil
from Backend.ImageGeneration import GenerateImages


env_vars = dotenv_values(".env")
Username = env_vars.get("Username")
Assistantname = env_vars.get("Assistantname")

DefaultMessage = f'''{Username}: Hello {Assistantname}, How are you?
{Assistantname}: Welcome {Username}. I am doing well. How may I help you?'''

subprocesses = []
Functions = ["open", "close", "play", "system", "content", "google search", "youtube search"]

def get_system_status():
    """Gather detailed system status information"""
    # CPU information
    cpu_usage = psutil.cpu_percent(interval=1)
    cpu_freq = psutil.cpu_freq()
    cpu_cores = psutil.cpu_count(logical=False)
    cpu_threads = psutil.cpu_count(logical=True)
    
    # Memory information
    mem = psutil.virtual_memory()
    total_mem = round(mem.total / (1024**3), 2)
    available_mem = round(mem.available / (1024**3), 2)
    used_mem = round(mem.used / (1024**3), 2)
    mem_percent = mem.percent
    
    # Battery information (if available)
    try:
        battery = psutil.sensors_battery()
        if battery:
            battery_percent = battery.percent
            power_plugged = "plugged in" if battery.power_plugged else "not plugged in"
            battery_info = f"{battery_percent}% ({power_plugged})"
        else:
            battery_info = "No battery detected"
    except:
        battery_info = "Battery information unavailable"
    
    # Disk information
    disk = psutil.disk_usage('/')
    total_disk = round(disk.total / (1024**3), 2)
    used_disk = round(disk.used / (1024**3), 2)
    free_disk = round(disk.free / (1024**3), 2)
    disk_percent = disk.percent
    
    # System uptime
    uptime = psutil.boot_time()
    from datetime import datetime
    uptime_str = datetime.fromtimestamp(uptime).strftime("%Y-%m-%d %H:%M:%S")
    
    # Create system status message
    system_status = f"""
    System Status Report:
    
    CPU:
    - Usage: {cpu_usage}%
    - Cores: {cpu_cores} physical, {cpu_threads} logical
    - Frequency: {cpu_freq.current:.2f} MHz (max: {cpu_freq.max:.2f} MHz)
    
    Memory:
    - Total: {total_mem} GB
    - Used: {used_mem} GB ({mem_percent}%)
    - Available: {available_mem} GB
    
    Storage:
    - Total: {total_disk} GB
    - Used: {used_disk} GB ({disk_percent}%)
    - Free: {free_disk} GB
    
    Battery: {battery_info}
    
    System Uptime: Since {uptime_str}
    """
    
    return system_status.strip()

def ShowDefaultChatIfNoChats():
    with open(r'Data\ChatLog.json', "r", encoding='utf-8') as File:
        if len(File.read()) < 5:
            with open(TempDirectoryPath('Database.data'), 'w', encoding='utf-8') as file:
                file.write("")
            with open(TempDirectoryPath('Responses.data'), 'w', encoding='utf-8') as file:
                file.write(DefaultMessage)

def ReadChatLogJson():
    with open(r'Data\ChatLog.json', 'r', encoding='utf-8') as file:  
        chatlog_data = json.load(file)
    return chatlog_data

def ChatLogIntegration():
    json_data = ReadChatLogJson()
    formatted_chatlog = ""
    for entry in json_data:
        if entry["role"] == "user":
            formatted_chatlog += f"User: {entry['content']}\n"
        elif entry["role"] == "assistant":  
            formatted_chatlog += f"Assistant: {entry['content']}\n"

    formatted_chatlog = formatted_chatlog.replace("User", Username + " ")
    formatted_chatlog = formatted_chatlog.replace("Assistant", Assistantname + " ")

    with open(TempDirectoryPath('Database.data'), 'w', encoding='utf-8') as file:
        file.write(AnswerModifier(formatted_chatlog))

def ShowChatsOnGUI():
    File = open(TempDirectoryPath('Database.data'), "r", encoding='utf-8')
    Data = File.read()
    print(f"Chat Data Being Loaded:\n{Data}")  # Debugging print
    if len(str(Data)) > 0:
        lines = Data.split('\n')
        result = '\n'.join(lines)
        File.close()
        File = open(TempDirectoryPath('Responses.data'), "w", encoding='utf-8')
        File.write(result)
        File.close()

def InitialExecution():
    SetMicrophoneStatus("False")
    ShowTextToScreen(" ")
    ShowDefaultChatIfNoChats()
    ChatLogIntegration()
    ShowChatsOnGUI()

InitialExecution()

def MainExecution():
    TaskExecution = False
    ImageExecution = False
    ImageGenerationQuery = ""

    SetAssistantStatus("Listening...")
    Query = SpeechRecognition()
    ShowTextToScreen(f"{Username}: {Query}")
    SetAssistantStatus("Thinking...")
    Decision = FirstLayerDMM(Query)

    print("")
    print(f"Decision {Decision}")
    print("")

    G = any(i.startswith("general") for i in Decision)
    R = any(i.startswith("realtime") for i in Decision)

    Merged_query = " and ".join(
        ["".join(i.split()[1:]) for i in Decision if i.startswith("general") or i.startswith("realtime")]
    )

    for queries in Decision:
        if "generate " in queries:
            ImageGenerationQuery = str(queries)
            ImageExecution = True

    for queries in Decision:
        if not TaskExecution:
            if any(queries.startswith(func) for func in Functions):
                if "system" in queries.lower():
                    # Handle system status request
                    system_status = get_system_status()
                    ShowTextToScreen(f"{Assistantname}: Here's the system status:\n{system_status}")
                    SetAssistantStatus("Answering...")
                    TextToSpeech(f"Here's the system status: CPU usage is {psutil.cpu_percent()} percent. Memory usage is {psutil.virtual_memory().percent} percent.")
                    return True
                else:
                    run(Automation(list(Decision)))
                TaskExecution = True

    if ImageExecution:
        GenerateImages(ImageGenerationQuery)

    if G and R or R:
        SetAssistantStatus("Searching...")
        Answer = RealtimeSearchEngine(QueryModifier(Merged_query))
        ShowTextToScreen(f"{Assistantname}: {Answer}")
        SetAssistantStatus("Answering...")
        TextToSpeech(Answer)
        return True
    else:
        for Queries in Decision:
            if "general" in Queries:
                SetAssistantStatus("Thinking...")
                QueryFinal = Queries.replace("general", "")
                Answer = ChatBot(QueryModifier(QueryFinal))
                ShowTextToScreen(f"{Assistantname}: {Answer}")
                SetAssistantStatus("Answering...")
                TextToSpeech(Answer)
                return True
            elif "realtime" in Queries:
                SetAssistantStatus("Searching...")
                QueryFinal = Queries.replace("realtime ", "")
                Answer = RealtimeSearchEngine(QueryModifier(QueryFinal))
                ShowTextToScreen(f"{Assistantname}: {Answer}")  
                SetAssistantStatus("Answering...")
                TextToSpeech(Answer)
                return True
            elif "exit" in Queries:
                QueryFinal = "Okay, Bye!"
                Answer = ChatBot(QueryModifier(QueryFinal))
                ShowTextToScreen(f"{Assistantname}: {Answer}")
                SetAssistantStatus("Answering...")
                TextToSpeech(Answer)
                os._exit(1)


def FirstThread():
    import time
    last_input_time = time.time()  # Track the last time input was processed
    timeout_seconds = 10  # Set timeout to 30 seconds

    while True:
        CurrentStatus = GetMicrophoneStatus()
        print(f"Microphone Status: {CurrentStatus}, Last Input Time: {last_input_time}")  # Debugging
        if CurrentStatus == "True":
            print("User input detected, running MainExecution...")
            MainExecution()
            last_input_time = time.time()  # Reset timer after user input
            print(f"Timer reset to: {last_input_time}")
        else:
            current_time = time.time()
            elapsed_time = current_time - last_input_time
            print(f"Elapsed time since last input: {elapsed_time:.2f} seconds")
            if elapsed_time >= timeout_seconds:
                print("No user input for 30 seconds. Exiting program...")
                SetAssistantStatus("Exiting due to inactivity...")
                ShowTextToScreen(f"{Assistantname}: Goodbye, exiting due to 30 seconds of inactivity.")
                sleep(1)  # Brief delay to allow GUI update
                os._exit(1)  # Exit the entire program
            AIStatus = GetAssistantStatus()
            if "Available..." not in AIStatus:
                SetAssistantStatus("Available...")
            sleep(0.1)



def SecondThread():
    GraphicalUserInterface()

if __name__ == "__main__":
    InitialExecution()
    thread1 = threading.Thread(target=FirstThread, daemon=True)
    thread1.start()
    SecondThread()  # This runs in the main thread