# 💻 Laptop Life-Saver System
> *Predictive Maintenance & Fleet Management for Nyanza District*

Laptop Life-Saver is a comprehensive platform designed to monitor the health and reliability of educational laptop fleets. It combines a lightweight Python-based monitoring agent with a powerful real-time React dashboard.

## 🚀 Key Features

### 🛠️ Real-time Monitoring (Agent)
- **Performance:** CPU Temperature, Load, RAM Usage, Disk Space, Battery Health.
- **Health Classification:** Real-time green/yellow/red status indicators based on configurable thresholds.
- **Offline Resilience:** Local JSON buffering ensure data survives network outages.

### 🏢 Advanced Fleet Management (Phase 1)
- **Inventory Tracking:** Automatic detection of CPU Model, RAM capacity, and Disk types (SSD vs HDD).
- **Metadata Management:** Assign laptops to specific **Schools/Departments**, track **Asset Tags**, and **Assigned Users**.
- **S.M.A.R.T. Health:** Deep disk failure prediction monitoring.
- **Remote Maintenance:** Trigger maintenance actions like `FORCE_SYNC` directly from the dashboard.

### 📊 Real-time Dashboard
- **Fleet Overview:** Global health distribution and alert summary.
- **Predictive Scoring:** Health scores (0-100) based on historical telemetry.
- **Live Notifications:** Browser push alerts for critical hardware failures.

## 🏗️ Architecture

```mermaid
graph LR
    A[Python Agent] -- Telemetry --> B[Supabase Cloud]
    B -- Realtime Hooks --> C[React Dashboard]
    C -- Remote Actions --> B
    B -- Poll/Sync --> A
```

## 🛠️ Tech Stack
- **Agent:** Python 3.10+, `psutil`, `wmi`, `requests`.
- **Dashboard:** React 19, Vite, TailwindCSS, Lucide-React.
- **Backend:** Supabase (PostgreSQL, Realtime, Auth, RLS).

## 🚦 Quick Start

### Python Agent Setup
```bash
# 1. Activate the environment
.venv\Scripts\activate

# 2. Run the agent
python -m agent.agent
```

### Dashboard Setup
```bash
cd dashboard
npm install
npm run dev
```

## 🧪 Automated Testing
Run the full test suite to ensure system reliability:
- **Agent:** `python -m pytest agent/tests/`
- **Dashboard:** `cd dashboard && npm test`

## 📖 Documentation
- [Detailed Deployment Guide](file:///c:/FYP/DEPLOYMENT_GUIDE.md)
- [Supabase Schema Documentation](file:///c:/FYP/supabase/schema.sql)
