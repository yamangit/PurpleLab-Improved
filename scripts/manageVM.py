import subprocess
import sys
import time
import os
import re

VBOX_ENV = os.environ.copy()
VBOX_ENV["VBOX_USER_HOME"] = "/var/lib/virtualbox"

def _run_vbox(args, capture_output=False):
    cmd = ["VBoxManage"] + args
    result = subprocess.run(cmd, capture_output=capture_output, text=True, env=VBOX_ENV)
    if result.returncode != 0:
        cmd = ["sudo", "VBoxManage"] + args
        result = subprocess.run(cmd, capture_output=capture_output, text=True, env=VBOX_ENV)
    return result

def poweroff_vm():
    # Command to shut down the virtual machine
    _run_vbox(["controlvm", "sandbox", "poweroff"])

def restore_snapshot():
    # Command to restore Snapshot1
    _run_vbox(["snapshot", "sandbox", "restore", "Snapshot1"])

def start_vm_headless():
    # Command to start the virtual machine
    _run_vbox(["startvm", "sandbox", "--type", "headless"])

def show_vm_info():
    # Command to display virtual machine information
    result = _run_vbox(["showvminfo", "sandbox", "--machinereadable"], capture_output=True)
    if result.returncode != 0:
        print(result.stderr.strip(), file=sys.stderr)
        sys.exit(1)
    info = {}
    for line in result.stdout.splitlines():
        if line.startswith("name="):
            info["name"] = line.split("=", 1)[1].strip().strip('"')
        elif line.startswith("VMState="):
            info["state"] = line.split("=", 1)[1].strip().strip('"')
        elif line.startswith("SnapshotCount="):
            info["snapshots"] = line.split("=", 1)[1].strip().strip('"')
    print(f"Name: {info.get('name', 'unknown')}")
    print(f"State: {info.get('state', 'unknown')}")
    print(f"Snapshots: {info.get('snapshots', '0')}")

def get_vm_ip():
    # Command to get the IP address of the virtual machine
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
# Command to disable Windows Defender real-time monitoring
    powershell_command = (
    'VBoxManage guestcontrol "sandbox" run --exe '
    '"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" --username oem --password oem '
    '-- -Command "& {Start-Process powershell -ArgumentList \'Set-MpPreference -DisableRealtimeMonitoring \$true\' -Verb RunAs}"'
)

    # Run the command to disable Windows Defender real-time monitoring
    subprocess.run(powershell_command, shell=True, check=True)
    print("PowerShell command successfully executed on the VM.")

def enable_antivirus():
# Command to disable Windows Defender real-time monitoring
    powershell_command = (
    'VBoxManage guestcontrol "sandbox" run --exe '
    '"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" --username oem --password oem '
    '-- -Command "& {Start-Process powershell -ArgumentList \'Set-MpPreference -DisableRealtimeMonitoring \$false\' -Verb RunAs}"'
)

    # Run the command to disable Windows Defender real-time monitoring
    subprocess.run(powershell_command, shell=True, check=True)
    print("PowerShell command successfully executed on the VM.")

def restart_winlogbeat():
    # Command to restart the winlogbeat service
    command = (
        'VBoxManage guestcontrol "sandbox" run --exe '
        '"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" --username oem --password oem '
        '-- -Command "& {Start-Process powershell -ArgumentList \'Restart-Service winlogbeat\' -Verb RunAs}"'
    )
    subprocess.run(command, shell=True)

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
elif command_name == "disableav":
    disable_antivirus()
elif command_name == "enableav":
    enable_antivirus()
elif command_name == "restartwinlogbeat":
    restart_winlogbeat()
else:
    print("Command not recognized. Utilisation: python manageVM.py <commande>")
