import sys
import os
import re
import subprocess

VBOX_ENV = os.environ.copy()
VBOX_ENV["VBOX_USER_HOME"] = "/var/lib/virtualbox"

def _run_vbox(args):
    cmd = ["VBoxManage"] + args
    if os.environ.get("VBOX_FORCE_SUDO") == "1":
        cmd = ["sudo", "-n", "VBoxManage"] + args
        return subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            env=VBOX_ENV,
            timeout=60
        )
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            env=VBOX_ENV,
            timeout=20
        )
        if result.returncode == 0:
            return result
    except subprocess.TimeoutExpired:
        result = None
    cmd = ["sudo", "-n", "VBoxManage"] + args
    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        env=VBOX_ENV,
        timeout=60
    )

def _get_vm_disk_path(vm_name):
    result = _run_vbox(["showvminfo", vm_name, "--machinereadable"])
    if result.returncode != 0:
        return None, result.stderr.strip()
    paths = []
    for line in result.stdout.splitlines():
        match = re.match(r'^"[^"]+"="(.+\.(?:vmdk|vdi))"$', line)
        if match:
            paths.append(match.group(1))
    if not paths:
        return None, "No disk path found in VM info"
    for path in paths:
        if "/Snapshots/" not in path and "\\Snapshots\\" not in path:
            return path, None
    return paths[0], None

def main(acquisition_type):
    vm_name = "sandbox"
    output_dir = "/tmp/forensic"

    os.makedirs(output_dir, exist_ok=True)

    if acquisition_type == "memory":
        output_file = os.path.join(output_dir, f"{vm_name}.dmp")
        args = ["debugvm", vm_name, "dumpvmcore", f"--filename={output_file}"]
    elif acquisition_type == "disk":
        vdi_path, err = _get_vm_disk_path(vm_name)
        if err:
            print(f"Error: {err}", file=sys.stderr)
            sys.exit(1)
        output_file = os.path.join(output_dir, f"{vm_name}.vdi")
        args = ["clonemedium", "disk", vdi_path, output_file, "--format", "VDI", "--variant", "Standard"]
    else:
        print("Invalid argument. Use 'memory' or 'disk'.")
        sys.exit(1)

    # Check if file exists and remove it if it does
    if os.path.exists(output_file):
        os.remove(output_file)

    # Execute the command
    try:
        result = _run_vbox(args)
        if result.returncode != 0:
            print(f"Error: {result.stderr.strip()}", file=sys.stderr)
            sys.exit(1)
        try:
            os.chmod(output_file, 0o644)
            subprocess.run(["sudo", "-n", "/bin/chown", "www-data:www-data", output_file], check=False)
            subprocess.run(["sudo", "-n", "/bin/chmod", "0644", output_file], check=False)
        except Exception:
            pass
        print(result.stdout.strip())
    except subprocess.TimeoutExpired:
        print("Error: VBoxManage command timed out", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python forensic_acquisition.py <memory|disk>")
        sys.exit(1)

    acquisition_type = sys.argv[1]
    main(acquisition_type)
