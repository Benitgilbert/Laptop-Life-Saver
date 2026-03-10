import sys
import os

def get_resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

def get_install_path():
    """ Returns the standard installation path on Windows """
    return os.path.join(os.environ.get("ProgramFiles", "C:\\Program Files"), "LaptopLifeSaver")

def is_running_from_install_path():
    """ Checks if the current executable is running from the install directory """
    exe_path = sys.executable
    return exe_path.lower().startswith(get_install_path().lower())
