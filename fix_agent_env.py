import sys
import subprocess

def install_requirements():
    print("📦 Installing/Updating dependencies from requirements.txt...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Dependencies process finished.")
    except Exception as e:
        print(f"❌ Failed to install dependencies: {e}")
        # We continue to verify even if pip had a warning

def verify_imports():
    print("\n🔍 Verifying critical imports...")
    dependencies = [
        "psutil",
        "wmi",
        "supabase",
        "dotenv",
        "pystray",
        "PIL",
        "customtkinter"
    ]
    
    missing = []
    for dep in dependencies:
        try:
            __import__(dep)
            print(f"✅ {dep}")
        except ImportError:
            missing.append(dep)
            print(f"❌ {dep} (MISSING)")

    if missing:
        print(f"\n⚠️ Still missing: {', '.join(missing)}")
        if "wmi" in missing:
            print("\n💡 TIP: For 'wmi', try running this manual command:")
            print(f"   {sys.executable} -m pip install wmi pypiwin32")
        return False
    
    print("\n🎉 Environment is healthy and ready to run the agent!")
    return True

if __name__ == "__main__":
    install_requirements()
    if not verify_imports():
        print("\nTrying one last time to fix 'wmi' specifically...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "wmi", "pypiwin32"])
            verify_imports()
        except:
            pass
    print("\nIf 'wmi' is still missing, please restart your terminal and try again.")
