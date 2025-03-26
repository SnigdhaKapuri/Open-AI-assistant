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
from Backend.ImageGeneration import GenerateImages
import psutil
import platform
import psutil
import time
from datetime import datetime


env_vars = dotenv_values(".env")
Username = env_vars.get("Username")
Assistantname = env_vars.get("Assistantname")

DefaultMessage = f'''{Username}: Hello {Assistantname}, How are you?
{Assistantname}: Welcome {Username}. I am doing well. How may I help you?'''

subprocesses = []
Functions = ["open", "close", "play", "system", "content", "google search", "youtube search"]



last_charge_status = None
last_battery_level = None
high_cpu_alerted = False
high_memory_alerted = False

def CheckSystemStatus(query):
    query = query.lower()  # Convert query to lowercase for easier matching

    # Battery/charger status with real-time updates
    if "battery" in query or "charger" in query or "charging" in query:
        if hasattr(psutil, "sensors_battery"):
            battery = psutil.sensors_battery()
            if battery:
                status = f"Battery is at {battery.percent}%"
                if battery.power_plugged:
                    status += " and charging"
                else:
                    status += " and not charging"
                if battery.percent < 20 and not battery.power_plugged:
                    status += ". Warning: Low battery! Please connect charger."
                return status
            else:
                return "Battery information not available."
        else:
            return "Battery information not supported on this system."

    elif "ram" in query or "memory" in query:
        memory_info = psutil.virtual_memory()
        status = f"RAM usage is {memory_info.percent}%"
        if memory_info.percent > 85:
            status += ". Warning: High memory usage!"
        return status

    elif "cpu" in query or "processor" in query:
        cpu_usage = psutil.cpu_percent(interval=1)
        status = f"CPU usage is {cpu_usage}%"
        if cpu_usage > 85:
            status += ". Warning: High CPU usage!"
        return status

    elif "disk" in query or "storage" in query:
        disk_info = psutil.disk_usage('/')
        status = f"Disk usage is {disk_info.percent}%"
        if disk_info.percent > 90:
            status += ". Warning: Disk space running low!"
        return status

    elif "system" in query or "status" in query:
        # Get all system info
        system_info = []
        
        # CPU info
        cpu_usage = psutil.cpu_percent(interval=1)
        cpu_info = f"CPU: {cpu_usage}% usage"
        if cpu_usage > 85:
            cpu_info += " (High usage!)"
        system_info.append(cpu_info)
        
        # Memory info
        memory_info = psutil.virtual_memory()
        mem_info = f"RAM: {memory_info.percent}% used"
        if memory_info.percent > 85:
            mem_info += " (High usage!)"
        system_info.append(mem_info)
        
        # Disk info
        disk_info = psutil.disk_usage('/')
        disk_info_str = f"Disk: {disk_info.percent}% full"
        if disk_info.percent > 90:
            disk_info_str += " (Low space!)"
        system_info.append(disk_info_str)
        
        # Battery info if available
        if hasattr(psutil, "sensors_battery"):
            battery = psutil.sensors_battery()
            if battery:
                batt_info = f"Battery: {battery.percent}%"
                if battery.power_plugged:
                    batt_info += " (Charging)"
                else:
                    batt_info += " (Not charging)"
                if battery.percent < 20 and not battery.power_plugged:
                    batt_info += " (Low battery!)"
                system_info.append(batt_info)
        
        return "System status:\n" + "\n".join(system_info)

    else:
        return "I can provide information about battery, RAM, CPU, or disk status. What would you like to know?"

        
def monitor_system_status():
    global last_charge_status, last_battery_level, high_cpu_alerted, high_memory_alerted
    global last_network_status, last_disk_usage, last_temperatures
    
    # Initialize tracking variables
    last_charge_status = None
    last_battery_level = None
    high_cpu_alerted = False
    high_memory_alerted = False
    last_network_status = None
    last_disk_usage = None
    last_temperatures = {}
    last_process_count = None
    last_boot_time = None
    last_users = None
    
    while True:
        try:
            # 1. Battery Monitoring (Laptops/Portable Devices)
            if hasattr(psutil, "sensors_battery"):
                battery = psutil.sensors_battery()
                if battery:
                    current_charge_status = battery.power_plugged
                    current_battery_level = battery.percent
                    
                    # Charger connection/disconnection
                    if last_charge_status is not None and current_charge_status != last_charge_status:
                        if current_charge_status:
                            message = "🔌 Charger connected. Battery is now charging."
                        else:
                            remaining = f"{battery.secsleft//3600}h {(battery.secsleft%3600)//60}m" if battery.secsleft > 0 else "unknown"
                            message = f"🔋 Charger disconnected. Running on battery power. Estimated remaining: {remaining}"
                        notify_user(message)
                    
                    # Battery level changes
                    if last_battery_level is not None and abs(current_battery_level - last_battery_level) >= 5:
                        message = f"🔋 Battery level: {current_battery_level}%"
                        if current_battery_level <= 20 and not current_charge_status:
                            message += " ⚠️ Low battery! Please connect charger."
                        elif current_battery_level <= 10 and not current_charge_status:
                            message += " 🚨 Critical battery level! Connect charger immediately!"
                        notify_user(message)
                    
                    # Full charge notification
                    if current_charge_status and current_battery_level >= 95 and last_battery_level is not None and last_battery_level < 95:
                        notify_user("🔋 Battery is fully charged. You may unplug the charger.")
                    
                    last_charge_status = current_charge_status
                    last_battery_level = current_battery_level

            # 2. CPU Monitoring
            cpu_usage = psutil.cpu_percent(interval=5)
            cpu_freq = psutil.cpu_freq().current if hasattr(psutil, "cpu_freq") else None
            cpu_count = psutil.cpu_count(logical=False)
            
            if cpu_usage > 90:
                if not high_cpu_alerted:
                    notify_user(f"🔥 CPU Usage Critical: {cpu_usage}% at {cpu_freq}MHz")
                    high_cpu_alerted = True
            elif cpu_usage > 75:
                if not high_cpu_alerted:
                    notify_user(f"⚠️ High CPU Usage: {cpu_usage}%")
                    high_cpu_alerted = True
            else:
                high_cpu_alerted = False

            # 3. Memory Monitoring
            memory = psutil.virtual_memory()
            swap = psutil.swap_memory()
            
            if memory.percent > 90:
                if not high_memory_alerted:
                    notify_user(f"🚨 Critical Memory Usage: {memory.percent}% (Available: {memory.available//(1024**2)}MB)")
                    high_memory_alerted = True
            elif memory.percent > 80:
                if not high_memory_alerted:
                    notify_user(f"⚠️ High Memory Usage: {memory.percent}%")
                    high_memory_alerted = True
            else:
                high_memory_alerted = False

            # 4. Disk Monitoring
            disks = {}
            for part in psutil.disk_partitions(all=False):
                try:
                    usage = psutil.disk_usage(part.mountpoint)
                    disks[part.device] = usage.percent
                    
                    # Disk space alerts
                    if usage.percent > 90:
                        notify_user(f"🚨 Disk {part.device} at {usage.percent}% capacity!")
                    elif usage.percent > 80 and (last_disk_usage is None or last_disk_usage.get(part.device, 0) <= 80):
                        notify_user(f"⚠️ Disk {part.device} at {usage.percent}% capacity")
                    
                except Exception as e:
                    print(f"Disk monitoring error: {e}")
            
            last_disk_usage = disks

            # 5. Network Monitoring
            # net_io = psutil.net_io_counters()
            # current_network = {
            #     'bytes_sent': net_io.bytes_sent,
            #     'bytes_recv': net_io.bytes_recv,
            #     'connections': len(psutil.net_connections())
            # }
            
            # if last_network_status:
            #     sent_diff = (current_network['bytes_sent'] - last_network_status['bytes_sent'])/1024
            #     recv_diff = (current_network['bytes_recv'] - last_network_status['bytes_recv'])/1024
                
            #     if sent_diff > 1024 or recv_diff > 1024:  # More than 1MB transferred
            #         notify_user(f"🌐 Network Activity: Sent {sent_diff:.1f}KB, Received {recv_diff:.1f}KB")
            
            # last_network_status = current_network

            # 6. Temperature Monitoring (if available)
            if hasattr(psutil, "sensors_temperatures"):
                temps = psutil.sensors_temperatures()
                for name, entries in temps.items():
                    for entry in entries:
                        if entry.current > 80:
                            notify_user(f"🌡️ High Temperature Alert: {entry.label or name} at {entry.current}°C")

            # 7. Process Monitoring
            current_process_count = len(psutil.pids())
            if last_process_count and abs(current_process_count - last_process_count) > 10:
                notify_user(f"🔄 Process count changed significantly: {last_process_count} → {current_process_count}")
            last_process_count = current_process_count

            # 8. Boot Time Monitoring
            current_boot_time = psutil.boot_time()
            if last_boot_time and current_boot_time != last_boot_time:
                notify_user("🔄 System was rebooted")
            last_boot_time = current_boot_time

            # 9. User Sessions Monitoring
            current_users = len(psutil.users())
            if last_users and current_users != last_users:
                notify_user(f"👤 User sessions changed: {last_users} → {current_users}")
            last_users = current_users

            # 10. System Uptime Notification
            uptime = time.time() - psutil.boot_time()
            if uptime > 86400 and int(uptime) % 86400 < 5:  # Daily notification if uptime > 1 day
                days = int(uptime // 86400)
                notify_user(f"⏳ System uptime: {days} day{'s' if days != 1 else ''}")

            sleep(5)  # Check every 5 seconds
            
        except Exception as e:
            print(f"System monitoring error: {e}")
            sleep(10)


def notify_user(message):
    """Helper function to notify the user with both text and speech"""

    try:
        ShowTextToScreen(f"{Assistantname}: {message}")
        SetAssistantStatus("Notifying...")
        TextToSpeech(message)
        SetAssistantStatus("Available...")
    except Exception as e:
        print(f"Notification error: {e}")

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

# def InitialExecution():
#     SetMicrophoneStatus("False")
#     ShowTextToScreen(" ")
#     ShowDefaultChatIfNoChats()
#     ChatLogIntegration()
#     ShowChatsOnGUI()



def InitialExecution():
    SetMicrophoneStatus("False")
    ShowTextToScreen(" ")
    ShowDefaultChatIfNoChats()
    ChatLogIntegration()
    ShowChatsOnGUI()
    
    # Start system monitoring thread
    monitor_thread = threading.Thread(target=monitor_system_status, daemon=True)
    monitor_thread.start()


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
                run(Automation(list(Decision)))
                TaskExecution = True

    if ImageExecution:
        GenerateImages(ImageGenerationQuery)  # Direct function call

    # Check if the query contains system-related keywords
    system_keywords = ["battery", "ram", "memory", "cpu", "disk", "storage", "notifications", "system", "status"]
    if any(keyword in Query.lower() for keyword in system_keywords):
        system_status = CheckSystemStatus(Query)
        ShowTextToScreen(f"{Assistantname}: {system_status}")
        SetAssistantStatus("Answering...")
        TextToSpeech(system_status)
        return True

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
    while True:
        CurrentStatus = GetMicrophoneStatus()

        if CurrentStatus == "True":
            MainExecution()
        else:
            AIStatus = GetAssistantStatus()
            if "Available..." in AIStatus:
                sleep(0.1)
            else:
                SetAssistantStatus("Available...")

def SecondThread():
    GraphicalUserInterface()

if __name__ == "__main__":
    InitialExecution()
    thread2 = threading.Thread(target=FirstThread, daemon=True)
    thread2.start()
    SecondThread()
