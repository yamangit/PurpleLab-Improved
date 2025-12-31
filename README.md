# PurpleLab-Improved

PurpleLab-Improved is a turnkey cybersecurity lab to build and validate detection rules, simulate attacks, and train analysts. It deploys a complete stack with a web UI, OpenSearch, PostgreSQL, Flask API, and a Windows sandbox VM managed by VirtualBox.

## Highlights
- Web UI for hunting, rules, and lab management
- Windows sandbox with Sysmon + Winlogbeat + Atomic Red Team
- OpenSearch for search and dashboards
- PostgreSQL for application data
- Flask backend API and automation scripts
- Ansible-based installation and VM orchestration
- Optional Vagrant setup for a reproducible Ubuntu 22.04 host

## Quick Start (Ubuntu 22.04)
1) Clone the repo:
```bash
git clone https://github.com/yamangit/PurpleLab-Improved.git
cd PurpleLab-Improved
```

2) Run the installer:
```bash
sudo bash install.sh
```

3) Open the web UI:
```
http://<host-ip>/
```

The installer provisions OpenSearch, PostgreSQL, Flask, and the Windows sandbox VM.

## Quick Start (Vagrant + VirtualBox)
A ready Vagrant setup exists in `vagrant_box/` with bridged networking.

```bash
cd vagrant_box
vagrant up
vagrant ssh
```

Inside the VM, the repo is mounted at `/purplelab_host`.

## Credentials
- Default admin user is written to `~/admin.txt` during install.
- Windows sandbox VM credentials: `oem / oem`.

## Services and Ports
- Web UI: `http://<host-ip>/`
- Flask API: `http://<host-ip>:5000/`
- OpenSearch: `http://<host-ip>:9200/`
- OpenSearch Dashboards: `http://<host-ip>:5601/`
- PostgreSQL: `5432` (local only by default)

## Documentation
- System requirements: `SYSTEM_REQUIREMENTS.md`
- Architecture overview: `ARCHITECTURE.md`

## Security Notice
This lab is not hardened. Do not expose it directly to the internet without proper network controls and authentication hardening.

## License
MIT License. See `LICENSE`.
