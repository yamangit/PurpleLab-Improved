# Architecture

## High-Level Flow

User Browser
   |
   v
Web UI (PHP/HTML/CSS)
   |
   v
Flask API (app.py)
   |
   +--> PostgreSQL (app data)
   |
   +--> OpenSearch (logs/search)
   |
   +--> VirtualBox (sandbox VM)
           |
           +--> Windows Server sandbox
                - Sysmon
                - Winlogbeat -> OpenSearch
                - Atomic Red Team

## Key Components
- Web UI: `Web/`
- Flask API: `app.py` and `Web/app.py`
- Automation scripts: `scripts/`
- Ansible roles: `ansible/roles/`
- Vagrant environment: `vagrant_box/`

## VM Control
Flask invokes `scripts/manageVM.py`, which interacts with VirtualBox to:
- Start/stop headless VM
- Restore or create snapshots
- Fetch VM state/IP
- Run WinRM actions inside the sandbox

## Data Flow
- Windows logs -> Winlogbeat -> OpenSearch
- Web UI queries OpenSearch for hunting/visualization
- Web UI uses Flask for actions and health checks
