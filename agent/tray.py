"""
tray.py — System Tray Integration
Laptop Life-Saver System | Nyanza District

Provides a taskbar icon for controlling the agent and showing status.
"""

import os
import pystray
from PIL import Image
import threading
import logging

logger = logging.getLogger("tray")

class AgentTray:
    def __init__(self, logo_path: str, on_exit=None, on_show_logs=None):
        self.logo_path = logo_path
        self.on_exit_callback = on_exit
        self.on_show_logs_callback = on_show_logs
        self.icon = None

    def _create_menu(self):
        return pystray.Menu(
            pystray.MenuItem("Laptop Life-Saver", lambda: None, enabled=False),
            # pystray.Menu.SEPARATOR,
            pystray.MenuItem("Status: Monitoring", lambda: None, enabled=False),
            # pystray.MenuItem("Show Logs", self._on_show_logs),
            # pystray.Menu.SEPARATOR,
            pystray.MenuItem("Exit Agent", self._on_exit)
        )

    def _on_exit(self, icon, item):
        logger.info("Tray: Exit requested")
        if self.on_exit_callback:
            self.on_exit_callback()
        icon.stop()

    def _on_show_logs(self, icon, item):
        if self.on_show_logs_callback:
            self.on_show_logs_callback()

    def run(self):
        """Runs the tray icon. This is a blocking call if not in a thread."""
        try:
            if not os.path.exists(self.logo_path):
                logger.error(f"Tray: Logo not found at {self.logo_path}")
                # Fallback to a plain color if image missing
                image = Image.new('RGB', (64, 64), color=(99, 102, 241))
            else:
                image = Image.open(self.logo_path)

            self.icon = pystray.Icon(
                "laptop_life_saver",
                image,
                "Laptop Life-Saver Agent",
                menu=self._create_menu()
            )
            
            logger.info("Tray: Starting icon loop")
            self.icon.run()
        except Exception as e:
            logger.error(f"Tray: Failed to start icon: {e}")

def start_tray_in_thread(logo_path: str, on_exit=None):
    tray = AgentTray(logo_path, on_exit=on_exit)
    thread = threading.Thread(target=tray.run, daemon=True)
    thread.start()
    return tray
