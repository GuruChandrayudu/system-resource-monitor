
import os
import time
import csv
from datetime import datetime, timedelta

import psutil

CPU_THRESHOLD = 80
RAM_THRESHOLD = 80
DISK_THRESHOLD = 90
CHECK_INTERVAL = 5

LOG_FILE = "resource_log.csv"


def get_system_uptime():
    uptime_seconds = time.time() - psutil.boot_time()
    return str(timedelta(seconds=int(uptime_seconds)))


def initialize_log():
    if not os.path.exists(LOG_FILE):
        with open(LOG_FILE, "w", newline="") as file:
            writer = csv.writer(file)
            writer.writerow([
                "Timestamp",
                "CPU Usage (%)",
                "RAM Usage (%)",
                "Disk Usage (%)",
                "Uptime"
            ])


def monitor_system():
    disk_path = os.path.abspath(os.sep)
    initialize_log()

    print("\n========== SYSTEM RESOURCE MONITOR ==========\n")
    print(f"{'Timestamp':<22}{'CPU':>8}{'RAM':>10}{'Disk':>10}")
    print("-" * 50)
    print("Press Ctrl+C to stop monitoring.\n")

    try:
        while True:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            cpu = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage(disk_path)
            uptime = get_system_uptime()

            print(
                f"{timestamp:<22}"
                f"{cpu:>7.1f}%"
                f"{memory.percent:>9.1f}%"
                f"{disk.percent:>9.1f}%"
            )

            if cpu >= CPU_THRESHOLD:
                print("WARNING: High CPU usage!")

            if memory.percent >= RAM_THRESHOLD:
                print("WARNING: High RAM usage!")

            if disk.percent >= DISK_THRESHOLD:
                print("WARNING: High disk usage!")

            with open(LOG_FILE, "a", newline="") as file:
                writer = csv.writer(file)
                writer.writerow([
                    timestamp,
                    cpu,
                    memory.percent,
                    disk.percent,
                    uptime
                ])

            time.sleep(CHECK_INTERVAL)

    except KeyboardInterrupt:
        print("-" * 50)
        print(f"\nSystem Uptime: {get_system_uptime()}")
        print("Monitoring stopped.")
        print(f"History saved to {LOG_FILE}")


if __name__ == "__main__":
    monitor_system()
