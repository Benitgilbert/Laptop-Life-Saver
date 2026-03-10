# 🚜 Deployment Guide: Laptop Life-Saver
> *Official Setup Instructions for Nyanza District IT Staff*

This guide outlines the steps to deploy the Laptop Life-Saver system for monitoring educational laptops.

## 1. Supabase Backend Setup (Cloud)
The system uses **Supabase** as its real-time database and authentication provider.

1.  **Create Project:** Sign up at [supabase.com](https://supabase.com) and create a new project named `Nyanza-Fleet-Monitor`.
10. **Database Schema:**
    * Copy [schema.sql](./supabase/schema.sql) content and run it in the Supabase SQL Editor. This creates all necessary tables.
3.  **API Credentials:**
    *   Go to **Project Settings** > **API**.
    *   Note down your **Project URL** and the **service_role** key (used by agents) and **anon public** key (used by the dashboard).

---

## 2. Windows Agent Deployment
The agent is a smart executable that installs itself to `C:\Program Files\LaptopLifeSaver`.

### Installation Steps
1.  **Run Executable:** Simply launch `LaptopLifeSaver_Agent.exe` from any location (USB, Downloads, etc.).
2.  **Auto-Install:** The app will automatically ask for Admin rights to move itself to the official Program Files folder.
3.  **Configuration:** It will then launch the setup wizard to collect device and user information.
4.  **Run:** The agent is now installed and will minimize to the system tray.

---

---

## 3. Cloud Dashboard Deployment (Admin)
The dashboard provides fleet-wide visibility and can be hosted for free.

### Setup using Vercel
1.  **Repository:** Push your code to GitHub/GitLab.
2.  **Deploy:** Connect your repository to [Vercel](https://vercel.com).
3.  **Build Settings:**
    *   **Framework Preset:** Vite
    *   **Root Directory:** `dashboard`
    *   **Build Command:** `npm run build`
    *   **Output Directory:** `dist`
4.  **Environment Variables:** Add `VITE_SUPABASE_URL` and `VITE_SUPABASE_KEY` (use your **Public Anon** key).

---

## 4. Cloud ML Engine Deployment
To run Data Science models automatically (Anomaly Detection, Predictors), you need a cloud runner.

### Option A: GitHub Actions (Free & Automatic)
1.  **Secrets:** In your GitHub Repo, go to **Settings > Secrets > Actions**.
2.  **Add Secrets:** Add `SUPABASE_URL` and `SUPABASE_KEY` (use **Service Role** key).
3.  **Workflow:** The system includes a workflow in `.github/workflows/ml_pipeline.yml` that runs the analytics every 6 hours automatically.

### Option B: Render.com (Background Worker)
1.  **New Service:** Create a **Background Worker**.
2.  **Command:** `python cloud_ml_runner.py`
3.  **Environment:** Set `SUPABASE_URL` and `SUPABASE_KEY`.

## 4. Operational Best Practices
- **Alerting:** Ensure browser notifications are enabled to receive critical hardware alerts.
- **Maintenance:** Use the **Remote Actions** panel to trigger manual syncs if a device hasn't reported in over 24 hours.
- **Retention:** Data older than 30 days is automatically aggregated into hourly summaries to maintain database performance.
