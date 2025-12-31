# System Requirements

## Minimum (Functional)
- CPU: 8 vCPU (nested virtualization enabled)
- RAM: 12 GB
- Storage: 200 GB free
- OS: Ubuntu Server 22.04 LTS
- Virtualization: VT-x/AMD-V enabled in BIOS/UEFI

## Recommended
- CPU: 12 vCPU
- RAM: 16 GB+
- Storage: 250 GB+ (SSD recommended)
- Network: Bridged NIC for sandbox reachability

## Host Software
- VirtualBox (latest stable)
- Vagrant (optional, for `vagrant_box/`)
- Ansible (installed by `install.sh` if missing)

## Sandbox VM Requirements
- Disk: 100 GB
- RAM: 4 GB
- CPU: 3 vCPU

## Notes
- Nested virtualization must be enabled for VirtualBox to run inside the Ubuntu host.
- For Vagrant deployments, ensure the bridge interface is set to the correct NIC (e.g., `eth0`).
