import base64
import subprocess
import sys
import time
import os
import re

VBOX_ENV = os.environ.copy()
VBOX_ENV["VBOX_USER_HOME"] = "/var/lib/virtualbox"

def _run_vbox(args, capture_output=False):
    cmd = ["VBoxManage"] + args
    if os.environ.get("VBOX_FORCE_SUDO") == "1":
        cmd = ["sudo", "VBoxManage"] + args
        return subprocess.run(
            cmd,
            capture_output=capture_output,
            text=True,
            env=VBOX_ENV,
            timeout=20
        )
    try:
        result = subprocess.run(
            cmd,
            capture_output=capture_output,
            text=True,
            env=VBOX_ENV,
            timeout=5
        )
        if result.returncode == 0:
            return result
    except subprocess.TimeoutExpired:
        result = None
    cmd = ["sudo", "VBoxManage"] + args
    return subprocess.run(
        cmd,
        capture_output=capture_output,
        text=True,
        env=VBOX_ENV,
        timeout=20
    )

def _run_powershell(command):
    args = [
        "guestcontrol", "sandbox", "run",
        "--exe", r"C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe",
        "--username", "oem", "--password", "oem",
        "--wait-stdout", "--wait-stderr", "--timeout", "20000",
        "--", "powershell.exe", "-NoProfile", "-NonInteractive",
        "-ExecutionPolicy", "Bypass", "-Command", command
    ]
    # Guest execution service can be slow to initialize after boot.
    for attempt in range(5):
        result = _run_vbox(args, capture_output=True)
        if result.returncode == 0:
            return result
        if "guest execution service is not ready" not in (result.stderr or "").lower():
            return result
        time.sleep(3)
    return result

def _run_powershell_system(command):
    task_name = f"PurpleLabTmp_{int(time.time())}"
    start_time = time.strftime("%H:%M", time.localtime(time.time() + 60))
    encoded = base64.b64encode(command.encode("utf-16le")).decode("ascii")
    task_cmd = (
        f"$tr=\"powershell.exe -NoProfile -NonInteractive -ExecutionPolicy Bypass -EncodedCommand {encoded}\";"
        f"$argsCreate=@('/Create','/F','/SC','ONCE','/ST','{start_time}','/RL','HIGHEST','/RU','SYSTEM','/TN','{task_name}','/TR',$tr);"
        f"Start-Process schtasks -ArgumentList $argsCreate -NoNewWindow -Wait;"
        f"Start-Process schtasks -ArgumentList @('/Run','/TN','{task_name}') -NoNewWindow -Wait;"
        f"Start-Process schtasks -ArgumentList @('/Delete','/F','/TN','{task_name}') -NoNewWindow -Wait"
    )

    return _run_powershell(task_cmd)

def poweroff_vm():
    # Command to shut down the virtual machine
    _run_vbox(["controlvm", "sandbox", "poweroff"])

def restore_snapshot():
    # Command to restore Snapshot1
    _run_vbox(["snapshot", "sandbox", "restore", "Snapshot1"])

def start_vm_headless():
    # Command to start the virtual machine
    _run_vbox(["startvm", "sandbox", "--type", "headless"])

def reboot_vm():
    state = _get_vm_state()
    if state == "running":
        _run_vbox(["controlvm", "sandbox", "reset"])
    else:
        start_vm_headless()

def take_snapshot():
    snapshot_name = f"Snapshot_{int(time.time())}"
    _run_vbox(["snapshot", "sandbox", "take", snapshot_name])

def show_vm_info():
    # Command to display virtual machine information
    result = _run_vbox(["showvminfo", "sandbox", "--machinereadable"], capture_output=True)
    if result.returncode != 0:
        print(result.stderr.strip(), file=sys.stderr)
        sys.exit(1)
    info = {}
    snapshot_count = 0
    for line in result.stdout.splitlines():
        if line.startswith("name="):
            info["name"] = line.split("=", 1)[1].strip().strip('"')
        elif line.startswith("VMState="):
            info["state"] = line.split("=", 1)[1].strip().strip('"')
        elif line.startswith("SnapshotCount="):
            info["snapshots"] = line.split("=", 1)[1].strip().strip('"')
        elif line.startswith("SnapshotName=") or line.startswith("SnapshotName-"):
            snapshot_count += 1
    if "snapshots" not in info:
        info["snapshots"] = str(snapshot_count)
    print(f"Name: {info.get('name', 'unknown')}")
    print(f"State: {info.get('state', 'unknown')}")
    print(f"Snapshots: {info.get('snapshots', '0')}")

def _get_vm_state():
    result = _run_vbox(["showvminfo", "sandbox", "--machinereadable"], capture_output=True)
    if result.returncode != 0:
        return ""
    for line in result.stdout.splitlines():
        if line.startswith("VMState="):
            return line.split("=", 1)[1].strip().strip('"')
    return ""

def get_vm_ip():
    # Command to get the IP address of the virtual machine
    state = _get_vm_state()
    if state != "running":
        print("IP =")
        return
    result = _run_vbox(["guestproperty", "enumerate", "sandbox"], capture_output=True)
    if result.returncode != 0:
        print(result.stderr.strip(), file=sys.stderr)
        sys.exit(1)
    ips = re.findall(r"/VirtualBox/GuestInfo/Net/\d+/V4/IP, value: ([0-9.]+)", result.stdout)
    ip = next((ip for ip in ips if ip and ip != "0.0.0.0"), "")
    if not ip:
        print("IP =")
        return
    print(ip)

def upload_to_vm():
    # Upload files individually from malware_upload folder
    source_directory = "/var/www/html/Downloaded/malware_upload"
    destination_directory = "C:\\Users\\oem\\Documents\\samples"
    
    if not os.path.exists(source_directory):
        print(f"Source directory {source_directory} does not exist")
        return
    
    # List all files in the source folder
    for file in os.listdir(source_directory):
        full_file_path = os.path.join(source_directory, file)
        if os.path.isfile(full_file_path):
            # Build the VBoxManage command for each file
            destination_file = f"{destination_directory}\\{file}"
            command = f'sudo VBoxManage guestcontrol "sandbox" copyto --username oem --password oem "{full_file_path}" "{destination_file}"'
            
            print(f"Uploading {file} to VM...")
            result = subprocess.run(command, shell=True)
            if result.returncode == 0:
                print(f"Successfully uploaded {file}")
            else:
                print(f"Failed to upload {file}")

def api_upload_to_vm():
    # Upload files individually from upload folder for API uploads
    source_directory = "/var/www/html/Downloaded/upload"
    destination_directory = "C:\\Users\\oem\\Documents\\samples"
    
    if not os.path.exists(source_directory):
        print(f"Source directory {source_directory} does not exist")
        return
    
    # List all files in the source folder
    for file in os.listdir(source_directory):
        full_file_path = os.path.join(source_directory, file)
        if os.path.isfile(full_file_path):
            # Build the VBoxManage command for each file
            destination_file = f"{destination_directory}\\{file}"
            command = f'sudo VBoxManage guestcontrol "sandbox" copyto --username oem --password oem "{full_file_path}" "{destination_file}"'
            
            print(f"Uploading {file} to VM...")
            result = subprocess.run(command, shell=True)
            if result.returncode == 0:
                print(f"Successfully uploaded {file}")
            else:
                print(f"Failed to upload {file}")

def disable_antivirus():
    # Disable Windows Defender real-time monitoring.
    result = _run_powershell_system(
        "Set-MpPreference -DisableRealtimeMonitoring $true;"
        "Get-MpComputerStatus | Select -ExpandProperty RealTimeProtectionEnabled -ErrorAction SilentlyContinue;"
        "Get-MpComputerStatus | Select -ExpandProperty IsTamperProtected -ErrorAction SilentlyContinue"
    )
    if result.returncode != 0:
        print(result.stderr.strip(), file=sys.stderr)
        sys.exit(1)
    status = _run_powershell(
        "Get-MpComputerStatus | Select -ExpandProperty RealTimeProtectionEnabled -ErrorAction SilentlyContinue;"
        "Get-MpComputerStatus | Select -ExpandProperty IsTamperProtected -ErrorAction SilentlyContinue"
    )
    if status.returncode == 0:
        print(status.stdout.strip())
    print("PowerShell command successfully executed on the VM.")

def enable_rdp():
    result = _run_powershell_system(
        "Set-ItemProperty -Path 'HKLM:\\System\\CurrentControlSet\\Control\\Terminal Server' -Name fDenyTSConnections -Value 0;"
        "Enable-NetFirewallRule -DisplayGroup \"Remote Desktop\";"
        "Start-Service TermService"
    )
    if result.returncode != 0:
        print(result.stderr.strip(), file=sys.stderr)
        sys.exit(1)

def enable_antivirus():
    # Enable Windows Defender real-time monitoring.
    result = _run_powershell_system(
        "Set-MpPreference -DisableRealtimeMonitoring $false;"
        "Get-MpComputerStatus | Select -ExpandProperty RealTimeProtectionEnabled -ErrorAction SilentlyContinue;"
        "Get-MpComputerStatus | Select -ExpandProperty IsTamperProtected -ErrorAction SilentlyContinue"
    )
    if result.returncode != 0:
        print(result.stderr.strip(), file=sys.stderr)
        sys.exit(1)
    status = _run_powershell(
        "Get-MpComputerStatus | Select -ExpandProperty RealTimeProtectionEnabled -ErrorAction SilentlyContinue;"
        "Get-MpComputerStatus | Select -ExpandProperty IsTamperProtected -ErrorAction SilentlyContinue"
    )
    if status.returncode == 0:
        print(status.stdout.strip())
    enable_rdp()
    print("PowerShell command successfully executed on the VM.")

def restart_winlogbeat():
    # Command to restart the winlogbeat service
    result = _run_powershell("Restart-Service winlogbeat")
    if result.returncode != 0:
        print(result.stderr.strip(), file=sys.stderr)
        sys.exit(1)

def av_status():
    result = _run_powershell(
        "Get-MpComputerStatus | Select -ExpandProperty RealTimeProtectionEnabled -ErrorAction SilentlyContinue;"
        "Get-MpComputerStatus | Select -ExpandProperty IsTamperProtected -ErrorAction SilentlyContinue"
    )
    if result.returncode != 0:
        print(result.stderr.strip(), file=sys.stderr)
        sys.exit(1)
    print(result.stdout.strip())

if len(sys.argv) != 2:
    print("Utilisation: python manageVM.py <commande>")
    sys.exit(1)

command_name = sys.argv[1]

if command_name == "restore":
    poweroff_vm()
    restore_snapshot()
    time.sleep(1)
    start_vm_headless()
elif command_name == "state":
    show_vm_info()
elif command_name == "upload":
    upload_to_vm()
elif command_name == "apiupload":  
    api_upload_to_vm()
elif command_name == "ip":
    get_vm_ip()
elif command_name == "poweroff":
    poweroff_vm()
elif command_name == "startheadless":
    start_vm_headless()
elif command_name == "reboot":
    reboot_vm()
elif command_name == "snapshot":
    take_snapshot()
elif command_name == "disableav":
    disable_antivirus()
elif command_name == "enableav":
    enable_antivirus()
elif command_name == "restartwinlogbeat":
    restart_winlogbeat()
elif command_name == "enablerdp":
    enable_rdp()
elif command_name == "avstatus":
    av_status()
else:
    print("Command not recognized. Utilisation: python manageVM.py <commande>")
