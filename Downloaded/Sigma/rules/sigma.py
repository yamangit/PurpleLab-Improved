import datetime
import os
import subprocess
import sys
from pathlib import Path
import yaml

def _escape_qradar_value(value):
    return str(value).replace("'", "''")

def _build_qradar_fallback(rule_path):
    try:
        raw = Path(rule_path).read_text(encoding="utf-8")
        data = yaml.safe_load(raw)
    except Exception:
        return ""
    if not isinstance(data, dict):
        return ""
    detection = data.get("detection") or {}
    selection = detection.get("selection") or {}
    if not isinstance(selection, dict):
        return ""
    clauses = []
    for key, val in selection.items():
        if isinstance(val, list):
            values = ", ".join(f"'{_escape_qradar_value(v)}'" for v in val)
            clauses.append(f"\"{key}\" IN ({values})")
        else:
            clauses.append(f"\"{key}\"='{_escape_qradar_value(val)}'")
    if not clauses:
        return ""
    return "SELECT UTF8(payload) as search_payload from events where " + " AND ".join(clauses)

def convert_sigma_rule(rule_path, plugin):
    """
    :param rule_path: The path to the Sigma rule file (.yml).
    :param plugin: The plugin to use ('splunk' or 'eql' or 'qradar').
    """
    try:
     
        cache_dir = Path("/tmp/sigma-cache")
        cache_dir.mkdir(parents=True, exist_ok=True)
        env = os.environ.copy()
        env["XDG_CACHE_HOME"] = str(cache_dir)
        env["HOME"] = "/tmp"
        sigma_bin = "sigma"
        effective_rule_path = rule_path
        if plugin == "qradar":
            sigma_bin = "/var/www/html/Downloaded/Sigma/venv_qradar/bin/sigma"
            try:
                raw = Path(rule_path).read_text(encoding="utf-8")
                data = yaml.safe_load(raw)
                if isinstance(data, dict) and isinstance(data.get("date"), (datetime.date, datetime.datetime)):
                    data["date"] = data["date"].strftime("%Y/%m/%d")
                tmp_dir = Path("/tmp/sigma-qradar")
                tmp_dir.mkdir(parents=True, exist_ok=True)
                tmp_file = tmp_dir / Path(rule_path).name
                tmp_file.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
                effective_rule_path = str(tmp_file)
            except Exception:
                pass
        command = f"{sigma_bin} convert -t {plugin} {effective_rule_path} --without-pipeline"
        
       
        result = subprocess.run(command, shell=True, check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env)
        
    
        stdout = result.stdout.decode()
        stderr = result.stderr.decode().strip()
        lines = [line for line in stdout.splitlines() if line.strip() and line.strip() != "Parsing Sigma rules"]
        cleaned = "\n".join(lines).strip()
        if cleaned:
            print(cleaned)
        if stderr:
            # If QRadar backend can't map fields, fall back to payload search.
            if plugin == "qradar" and "supports only the following fields for process_creation" in stderr:
                fallback = _build_qradar_fallback(rule_path)
                if fallback:
                    print(fallback)
                    return
            print(stderr, file=sys.stderr)
        if result.returncode != 0 or (not cleaned and stderr):
            sys.exit(result.returncode or 1)
        
    except subprocess.CalledProcessError as e:
        print(f"Error during command execution : {e}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python script.py <path_to_rule.yml> <plugin>")
        sys.exit(1)
    
    rule_path = sys.argv[1]
    plugin = sys.argv[2]


    if plugin not in ['splunk', 'lucene', 'qradar']:
        print("The specified plugin must be 'splunk' or 'lucene' or 'qradar'.")
        sys.exit(1)
    
    convert_sigma_rule(rule_path, plugin)
