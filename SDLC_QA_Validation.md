# SDLC Phase QA Activities Validation
> **Project:** Laptop Life-Saver System (FYP)

This document verifies how the development of the Laptop Life-Saver system successfully adhered to standard Software Development Life Cycle (SDLC) Quality Assurance activities.

| SDLC Phase | QA Activity | Application in This Project |
| :--- | :--- | :--- |
| **Requirements** | Review and validate requirements | We validated that the system must provide real-time hardware telemetry and predictive maintenance. We refined the "Fleet Management" phase to include S.M.A.R.T health and Asset tagging. |
| **Design** | Evaluate architecture/security | Implemented a decoupled architecture (Agent-DB-Dashboard) for scalability. Ensured security by moving all sensitive Supabase credentials to `.env` files and verifying Vite's environment isolation. |
| **Implementation** | Code reviews and standards | Conducted code cleanup to remove 10+ obsolete scripts. Followed modular design for the `prediction_engine` and used standardized hardware polling via `psutil`. |
| **Testing** | identify and fix defects | Verified the Dashboard rendering via local build tests. Debugged and resolved the "Blank Screen" issue by identifying missing environment variables. Run agent tests via `pytest`. |
| **Deployment** | Verify production runtime | Created a standalone `LaptopLifeSaver_Agent.exe` and verified its runtime. Documented the Vercel (Frontend) and GitHub Actions (Cloud ML) production pipelines. |
| **Maintenance** | Monitor and fix/update | Built a `cloud_ml_runner.py` system for automated monitoring. Configured GitHub Actions for continuous analytics to ensure the system evolves as more laptop data is collected. |

### Summary
The system is fully compliant with the requested QA activities, ensuring a robust, secure, and maintainable platform for the Nyanza District laptop fleet.
