# Laptop Life-Saver System

Predictive maintenance platform for the Nyanza District laptop fleet.

## Requirements

- **Python 3.10 or later** (uses modern type annotations)
- Windows 10/11 (for WMI temperature monitoring)
- Administrator rights recommended for full hardware access

## Project Structure

```
agent/           Python health agent (edge service)
supabase/        Database schema & SQL scripts
dashboard/       React.js admin panel (future)
```

## Quick Start — Python Agent

```bash
# 1. Activate the virtual environment
.venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Copy and edit the environment file
copy .env.example .env
# → Set your SUPABASE_URL and SUPABASE_KEY

# 4. Run the agent
python -m agent.agent
```

The agent will start collecting hardware telemetry every 30 seconds.
Without Supabase credentials it runs in **offline mode**, storing data in `agent/local_buffer.json`.

## Supabase Setup

1. Create a Supabase project at [supabase.com](https://supabase.com)
2. Open the SQL Editor and paste the contents of `supabase/schema.sql`
3. Copy your **Project URL** and **service_role key** into `.env`
