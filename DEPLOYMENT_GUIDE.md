# 🚜 Deployment Guide: Laptop Life-Saver
> *Official Setup Instructions for Nyanza District IT Staff*

This guide outlines the steps to deploy the Laptop Life-Saver system for monitoring educational laptops.

## 1. Supabase Backend Setup (Cloud)
The system uses **Supabase** as its real-time database and authentication provider.

1.  **Create Project:** Sign up at [supabase.com](https://supabase.com) and create a new project named `Nyanza-Fleet-Monitor`.
2.  **Database Schema:**
    *   Navigate to the **SQL Editor** in the side menu.
    *   Click **New Query**.
    *   Copy [schema.sql](file:///c:/FYP/supabase/schema.sql) content and run it. This creates the `devices`, `telemetry`, `alerts`, `threshold_settings`, and `remote_actions` tables.
3.  **API Credentials:**
    *   Go to **Project Settings** > **API**.
    *   Note down your **Project URL** and the **service_role** key (used by agents) and **anon public** key (used by the dashboard).

---

## 2. Python Agent Deployment (Endpoint)
The agent should be installed on every Windows laptop in the fleet.

### Prerequisites
- Python 3.10 or later.
- Internet connectivity (or local caching will be used).

### Installation Steps
1.  **Clone/Copy Files:** Copy the `agent/` folder to `C:\Program Files\LaptopLifeSaver\`.
2.  **Configuration:**
    *   Create a `.env` file in the root directory.
    *   Add following keys:
        ```env
        SUPABASE_URL=your_project_url
        SUPABASE_KEY=your_service_role_key
        POLL_INTERVAL=30
        ```
3.  **Run Agent:**
    ```bash
    python -m agent.agent
    ```

---

## 3. Dashboard Deployment (Admin)
The dashboard provides fleet-wide visibility for IT managers.

### Setup
1.  **Environment:** Create `dashboard/.env` with your `VITE_SUPABASE_URL` and `VITE_SUPABASE_ANON_KEY`.
2.  **Build:**
    ```bash
    cd dashboard
    npm install
    npm run build
    ```
3.  **Hosting:** Deploy the `dist/` folder to Vercel, Netlify, or your preferred static site hosting.

---

## 4. Operational Best Practices
- **Alerting:** Ensure browser notifications are enabled to receive critical hardware alerts.
- **Maintenance:** Use the **Remote Actions** panel to trigger manual syncs if a device hasn't reported in over 24 hours.
- **Retention:** Data older than 30 days is automatically aggregated into hourly summaries to maintain database performance.
