import psutil
import time
from datetime import datetime
import platform
from Frontend.GUI import notify_user  # Make sure this import matches your project structure

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
    
    # Notification cooldowns to prevent spamming
    last_notification_time = {}
    
    def can_notify(notification_type, cooldown=60):
        """Prevents notification spamming"""
        current_time = time.time()
        if notification_type not in last_notification_time or \
           (current_time - last_notification_time[notification_type]) >= cooldown:
            last_notification_time[notification_type] = current_time
            return True
        return False
    
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
                        if can_notify("charger_status"):
                            notify_user(message)
                    
                    # Battery level changes
                    if last_battery_level is not None and abs(current_battery_level - last_battery_level) >= 5:
                        message = f"🔋 Battery level: {current_battery_level}%"
                        if current_battery_level <= 20 and not current_charge_status:
                            message += " ⚠️ Low battery! Please connect charger."
                        elif current_battery_level <= 10 and not current_charge_status:
                            message += " 🚨 Critical battery level! Connect charger immediately!"
                        if can_notify("battery_level"):
                            notify_user(message)
                    
                    # Full charge notification
                    if current_charge_status and current_battery_level >= 95 and last_battery_level is not None and last_battery_level < 95:
                        if can_notify("full_charge"):
                            notify_user("🔋 Battery is fully charged. You may unplug the charger.")
                    
                    last_charge_status = current_charge_status
                    last_battery_level = current_battery_level

            # 2. CPU Monitoring
            cpu_usage = psutil.cpu_percent(interval=5)
            cpu_freq = psutil.cpu_freq().current if hasattr(psutil, "cpu_freq") else None
            
            if cpu_usage > 90 and can_notify("high_cpu"):
                notify_user(f"🔥 CPU Usage Critical: {cpu_usage}% at {cpu_freq or 'unknown'}MHz")
                high_cpu_alerted = True
            elif cpu_usage > 75 and can_notify("high_cpu", 300):  # 5 minute cooldown
                notify_user(f"⚠️ High CPU Usage: {cpu_usage}%")
                high_cpu_alerted = True
            elif cpu_usage < 50:
                high_cpu_alerted = False

            # 3. Memory Monitoring
            memory = psutil.virtual_memory()
            
            if memory.percent > 90 and can_notify("high_memory"):
                notify_user(f"🚨 Critical Memory Usage: {memory.percent}% (Available: {memory.available//(1024**2)}MB)")
                high_memory_alerted = True
            elif memory.percent > 80 and can_notify("high_memory", 300):  # 5 minute cooldown
                notify_user(f"⚠️ High Memory Usage: {memory.percent}%")
                high_memory_alerted = True
            elif memory.percent < 60:
                high_memory_alerted = False

            # 4. Disk Monitoring
            for part in psutil.disk_partitions(all=False):
                try:
                    usage = psutil.disk_usage(part.mountpoint)
                    
                    # Disk space alerts
                    if usage.percent > 90 and can_notify(f"disk_{part.device}"):
                        notify_user(f"🚨 Disk {part.device} at {usage.percent}% capacity!")
                    elif usage.percent > 80 and can_notify(f"disk_{part.device}", 3600):  # 1 hour cooldown
                        notify_user(f"⚠️ Disk {part.device} at {usage.percent}% capacity")
                    
                except Exception as e:
                    print(f"Disk monitoring error for {part.device}: {e}")

            # 5. Network Monitoring
            net_io = psutil.net_io_counters()
            current_connections = len(psutil.net_connections())
            
            if current_connections > 100 and can_notify("network_connections"):
                notify_user(f"🌐 High Network Connections: {current_connections} active connections")

            # 6. System Uptime Notification
            uptime = time.time() - psutil.boot_time()
            if uptime > 86400 and int(uptime) % 86400 < 5 and can_notify("uptime", 86400):  # Daily notification
                days = int(uptime // 86400)
                notify_user(f"⏳ System uptime: {days} day{'s' if days != 1 else ''}")

            # 7. System Summary (once per hour)
            if int(time.time()) % 3600 < 5 and can_notify("hourly_summary", 3600):
                cpu = psutil.cpu_percent()
                mem = psutil.virtual_memory()
                notify_user(
                    f"📊 System Summary:\n"
                    f"• CPU: {cpu}%\n"
                    f"• Memory: {mem.percent}%\n"
                    f"• Disk: {psutil.disk_usage('/').percent}%\n"
                    f"• Processes: {len(psutil.pids())}"
                )

            sleep(5)  # Check every 5 seconds
            
        except Exception as e:
            print(f"System monitoring error: {e}")
            sleep(10)

# Start the monitoring thread
monitor_thread = threading.Thread(target=monitor_system_status, daemon=True)
monitor_thread.start()