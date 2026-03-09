"""
notifications.py — Native Toast Notifications
Laptop Life-Saver System | Nyanza District

Wrapper around plyer to send non-intrusive background alerts to users.
"""

import logging
from plyer import notification

logger = logging.getLogger("notifications")

def show_toast(title: str, message: str, app_name: str = "Laptop Life-Saver"):
    """
    Display a native Windows toast notification.
    Safe to call; will log instead of crashing if notification service fails.
    """
    try:
        import os
        logger.info("📢 Showing notification: %s - %s", title, message)
        
        # Path to the branded icon
        base_dir = os.path.dirname(__file__)
        icon_path = os.path.join(base_dir, "Logo.ico")
        if not os.path.exists(icon_path):
            icon_path = None # Fallback to default
            
        notification.notify(
            title=title,
            message=message,
            app_name=app_name,
            app_icon=icon_path,
            timeout=10, # Seconds
        )
    except Exception as e:
        logger.error("Failed to show notification: %s", e)

def notify_low_battery(percent: int):
    show_toast(
        "Low Battery Warning",
        f"Your battery is at {percent}%. Please plug in to avoid data loss.",
    )

def notify_high_temp(temp: float):
    show_toast(
        "High Temperature Alert",
        f"Your laptop is running hot ({temp}°C). Close unused apps to cool it down.",
    )

def notify_disk_full(usage: float):
    show_toast(
        "Storage Almost Full",
        f"Disk usage is at {usage}%. Clean up files to maintain performance.",
    )
