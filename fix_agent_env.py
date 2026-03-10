import sys
import subprocess

def install_requirements():
    print("📦 Installing missing dependencies from requirements.txt...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ All dependencies installed successfully!")
    except Exception as e:
        print(f"❌ Failed to install dependencies: {e}")
        sys.exit(1)

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
        return False
    
    print("\n🎉 Environment is healthy and ready to run the agent!")
    return True

if __name__ == "__main__":
    install_requirements()
    if verify_imports():
        print("\nYou can now run the agent or rebuild the EXE.")
