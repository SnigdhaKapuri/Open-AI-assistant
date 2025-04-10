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
from datetime import datetime
import GPUtil  # Install with: pip install gputil (for GPU status)
import socket  # For basic internet speed check

env_vars = dotenv_values(".env")
Username = env_vars.get("Username")
Assistantname = env_vars.get("Assistantname")

DefaultMessage = f'''{Username}: Hello {Assistantname}, How are you?
{Assistantname}: Welcome {Username}. I am doing well. How may I help you?'''

subprocesses = []
Functions = ["open", "close", "play", "system", "content", "google search", "youtube search"]

# Individual system status functions
def get_battery_status():
    """Get battery status"""
    try:
        battery = psutil.sensors_battery()
        if battery:
            plugged = "plugged in" if battery.power_plugged else "on battery"
            return f"Battery is at {battery.percent}% and {plugged}."
        return "No battery detected."
    except:
        return "Battery information unavailable."

def get_ram_status():
    """Get RAM usage"""
    mem = psutil.virtual_memory()
    total = round(mem.total / (1024**3), 2)
    used = round(mem.used / (1024**3), 2)
    available = round(mem.available / (1024**3), 2)
    return f"RAM: {used} GB used out of {total} GB ({mem.percent}%), {available} GB available."

def get_cpu_status():
    """Get CPU usage and details"""
    cpu_usage = psutil.cpu_percent(interval=1)
    cpu_cores = psutil.cpu_count(logical=False)
    cpu_threads = psutil.cpu_count(logical=True)
    cpu_freq = psutil.cpu_freq()
    return f"CPU: {cpu_usage}% usage, {cpu_cores} physical cores, {cpu_threads} threads, {cpu_freq.current:.2f} MHz."

def get_disk_status():
    """Get disk usage"""
    disk = psutil.disk_usage('/')
    total = round(disk.total / (1024**3), 2)
    used = round(disk.used / (1024**3), 2)
    free = round(disk.free / (1024**3), 2)
    return f"Disk: {used} GB used out of {total} GB ({disk.percent}%), {free} GB free."

def get_uptime_status():
    """Get system uptime"""
    uptime = psutil.boot_time()
    uptime_str = datetime.fromtimestamp(uptime).strftime("%Y-%m-%d %H:%M:%S")
    return f"System has been up since {uptime_str}."

def get_temperature_status():
    """Get system temperature (if available)"""
    try:
        temps = psutil.sensors_temperatures()
        if 'coretemp' in temps:  # Common for Intel CPUs
            core_temp = temps['coretemp'][0].current
            return f"CPU temperature is {core_temp}°C."
        elif 'nvme' in temps:  # For some NVMe drives
            return f"Drive temperature is {temps['nvme'][0].current}°C."
        return "Temperature data not available on this system."
    except:
        return "Error retrieving temperature data."

def get_network_status():
    """Get network I/O stats"""
    net = psutil.net_io_counters()
    sent = round(net.bytes_sent / (1024**2), 2)
    recv = round(net.bytes_recv / (1024**2), 2)
    return f"Network: {sent} MB sent, {recv} MB received since boot."

def get_gpu_status():
    """Get GPU usage (if available)"""
    try:
        gpus = GPUtil.getGPUs()
        if gpus:
            gpu = gpus[0]  # Assuming one GPU; adjust for multi-GPU systems
            return f"GPU: {gpu.name}, {gpu.load*100:.1f}% usage, {gpu.memoryUsed} MB used out of {gpu.memoryTotal} MB."
        return "No GPU detected."
    except:
        return "GPU information unavailable (install GPUtil or check GPU support)."

def get_process_count():
    """Get number of running processes"""
    process_count = len(psutil.pids())
    return f"There are {process_count} processes currently running."

def get_system_load():
    """Get system load averages (not available on all OSes)"""
    try:
        load = psutil.getloadavg()  # Returns 1, 5, 15-minute averages (Linux/Unix only)
        return f"System load averages: {load[0]:.2f} (1 min), {load[1]:.2f} (5 min), {load[2]:.2f} (15 min)."
    except:
        return "System load averages not available on this OS (Windows not supported)."

def get_internet_status():
    """Basic internet connectivity check"""
    try:
        socket.create_connection(("www.google.com", 80), timeout=2)
        return "Internet connection is active."
    except:
        return "No internet connection detected."

def get_system_status():
    """Full system status report"""
    return "\n".join([
        get_cpu_status(),
        get_ram_status(),
        get_disk_status(),
        get_battery_status(),
        get_uptime_status(),
        get_temperature_status(),
        get_network_status(),
        get_gpu_status(),
        get_process_count(),
        get_system_load(),
        get_internet_status()
    ])

# Mapping of system-related queries to functions
system_metrics = {
    "battery": get_battery_status,
    "ram": get_ram_status,
    "cpu": get_cpu_status,
    "disk": get_disk_status,
    "storage": get_disk_status,
    "uptime": get_uptime_status,
    "temperature": get_temperature_status,
    "temp": get_temperature_status,  # Alias
    "network": get_network_status,
    "gpu": get_gpu_status,
    "processes": get_process_count,
    "load": get_system_load,
    "internet": get_internet_status,
    "system": get_system_status  # Full report
}

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
    print(f"Chat Data Being Loaded:\n{Data}")
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

    print(f"Decision {Decision}")

    G = any(i.startswith("general") for i in Decision)
    R = any(i.startswith("realtime") for i in Decision)

    Merged_query = " and ".join(
        ["".join(i.split()[1:]) for i in Decision if i.startswith("general") or i.startswith("realtime")]
    )

    for queries in Decision:
        if "generate " in queries:
            ImageGenerationQuery = str(queries)
            ImageExecution = True

    # Handle system-related queries
    for queries in Decision:
        if not TaskExecution:
            if any(queries.startswith(func) for func in Functions):
                query_lower = queries.lower()
                for metric, func in system_metrics.items():
                    if metric in query_lower:
                        status = func()
                        ShowTextToScreen(f"{Assistantname}: Here's the {metric} status:\n{status}")
                        SetAssistantStatus("Answering...")
                        TextToSpeech(f"Here's the {metric} status: {status}")
                        SetMicrophoneStatus("False")
                        return True
                # Non-system function calls
                if "system" not in query_lower:
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
        SetMicrophoneStatus("False")
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
                SetMicrophoneStatus("False")
                return True
            elif "realtime" in Queries:
                SetAssistantStatus("Searching...")
                QueryFinal = Queries.replace("realtime ", "")
                Answer = RealtimeSearchEngine(QueryModifier(QueryFinal))
                ShowTextToScreen(f"{Assistantname}: {Answer}")  
                SetAssistantStatus("Answering...")
                TextToSpeech(Answer)
                SetMicrophoneStatus("False")
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
    last_input_time = time.time()
    timeout_seconds = 60

    while True:
        CurrentStatus = GetMicrophoneStatus()
        print(f"Microphone Status: {CurrentStatus}, Last Input Time: {last_input_time}")
        
        if CurrentStatus == "True":
            print("User input detected, running MainExecution...")
            MainExecution()
            last_input_time = time.time()
            print(f"Timer reset to: {last_input_time}")
        else:
            current_time = time.time()
            elapsed_time = current_time - last_input_time
            print(f"Elapsed time since last input: {elapsed_time:.2f} seconds")
            
            if elapsed_time >= timeout_seconds:
                print("No user input for 60 seconds. Exiting program...")
                SetAssistantStatus("Exiting due to inactivity...")
                ShowTextToScreen(f"{Assistantname}: Goodbye, exiting due to 60 seconds of inactivity.")
                TextToSpeech("Goodbye, exiting due to 60 seconds of inactivity.")
                sleep(1)
                os._exit(1)
            
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
    SecondThread()