# Project Maintenance & Update Guide

This guide explains how to update each part of the Laptop Life-Saver system as your requirements evolve.

## 1. Updating the Windows Agent
If you change the Python code in the `agent/` folder:
1.  **Re-bundle the EXE:** Open a terminal in the root directory and run:
    ```powershell
    .\.venv\Scripts\pyinstaller.exe --onefile --windowed --name LaptopLifeSaver --icon agent/Logo.ico --add-data "Logo.png;." agent/agent.py
    ```
2.  **Distribute:** Replace the old `LaptopLifeSaver_Agent.exe` with the new one found in the `dist/` folder (then you can delete the `build/` and `dist/` folders again).

## 2. Updating the Dashboard
If you modify the React code in `dashboard/src`:
-   **Local Development:** The changes will show up instantly if `npm run dev` is running.
-   **Production (Vercel):** Simply push your changes to your GitHub repository. Vercel will automatically detect the change, rebuild, and redeploy the live site.

## 3. Updating the AI / ML Engine
If you improve your models in `prediction_engine/` or `cloud_ml_runner.py`:
-   **GitHub Actions:** Push the code to GitHub. The next scheduled run (every 6 hours) will use the updated logic automatically.
-   **Manual Run:** Run `python cloud_ml_runner.py` locally to test your changes immediately.

## 4. Database Changes
If you need to add new data fields (e.g., tracking laptop temperature history):
1.  Go to the **Supabase Dashboard** > **Table Editor**.
2.  Add the new columns to the relevant table.
3.  Update the `agent` or `dashboard` code to send/receive the new data.

---
**Tip:** Always keep a backup of your `.env` files, as they contain your project's "secret keys" to connect to the database.
