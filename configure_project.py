import os
import sys

def update_env_files(url, key):
    # Normalize URL (remove trailing slashes)
    url = url.strip().rstrip('/')
    key = key.strip()

    # 1. Update Root .env (for Agent)
    root_env_path = os.path.join(os.getcwd(), '.env')
    root_lines = [
        "PYTHONPATH=.",
        "POLL_INTERVAL=30",
        f"SUPABASE_URL={url}",
        f"SUPABASE_KEY={key}"
    ]
    with open(root_env_path, 'w') as f:
        f.write('\n'.join(root_lines) + '\n')
    print(f"✓ Updated {root_env_path}")

    # 2. Update Dashboard .env
    dashboard_env_path = os.path.join(os.getcwd(), 'dashboard', '.env')
    # Dashboard typically uses the 'anon' key for security, 
    # but some setups use the same for testing. 
    # IMPORTANT: We'll assume the URL must match. 
    # Note: Vite needs the VITE_ prefix.
    
    # We'll ask if they also want to update the dashboard key
    # (Usually dashboard uses the Public Anon key, while Agent uses Service Role)
    dashboard_lines = [
        f"VITE_SUPABASE_URL={url}",
        f"VITE_SUPABASE_KEY={key} # WARNING: Use Service Role only for Agent setup"
    ]
    
    # If the file exists, we try to preserve it but update the URL
    if os.path.exists(dashboard_env_path):
        print("Note: Dashboard .env exists. Updating URL...")
    
    with open(dashboard_env_path, 'w') as f:
        f.write('\n'.join(dashboard_lines) + '\n')
    print(f"✓ Updated {dashboard_env_path}")

if __name__ == "__main__":
    print("═══ Supabase Project Configurator ═══")
    url = input("Enter Supabase URL (e.g., https://xyz.supabase.co): ")
    key = input("Enter Supabase Service Role Key: ")
    
    if not url or not key:
        print("Error: Both URL and Key are required.")
        sys.exit(1)
        
    update_env_files(url, key)
    print("Done! You can now run the agent or the dashboard.")
