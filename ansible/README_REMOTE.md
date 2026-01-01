# PurpleLab Ansible (remote host)

This repo includes an Ansible playbook to install PurpleLab and (optionally) OpenSearch + Dashboards on a remote Linux host.

## Prereqs

- Ansible on your control machine
- SSH access to the target host (user with sudo)
- Target host is Ubuntu 22.04 (playbook assumptions)

## 1) Create a remote inventory

Create a new inventory file (example: `ansible/inventory/remote/hosts`).

```ini
[purplelab]
<REMOTE_IP> ansible_user=<SSH_USER> ansible_ssh_private_key_file=~/.ssh/id_ed25519

[opensearch_nodes]
<REMOTE_IP> ansible_user=<SSH_USER> ansible_ssh_private_key_file=~/.ssh/id_ed25519

[opensearch_dashboards_nodes]
<REMOTE_IP> ansible_user=<SSH_USER> ansible_ssh_private_key_file=~/.ssh/id_ed25519
```

Notes:
- Replace `<REMOTE_IP>` and `<SSH_USER>`.
- If you use password auth, remove `ansible_ssh_private_key_file` and add `-k` to the ansible command.
- If OpenSearch/Dashboards should be on a separate host, split the groups accordingly.

## 2) Run the full install

From the repo root:

```bash
cd ansible
ansible-playbook -i inventory/remote/hosts playbook.yml -K
```

`-K` prompts for sudo password on the remote host.

## 3) Run only specific parts

Only base install (web + db + VM):

```bash
cd ansible
ansible-playbook -i inventory/remote/hosts playbook.yml -K --tags common,webserver,database,virtualbox
```

Only OpenSearch + Dashboards:

```bash
cd ansible
ansible-playbook -i inventory/remote/hosts playbook.yml -K --tags opensearch
```

Only VM configuration tasks:

```bash
cd ansible
ansible-playbook -i inventory/remote/hosts playbook.yml -K --tags configure_vm
```

## 4) Common issues

- **Sudo prompts fail**: use `-K` or ensure passwordless sudo for the SSH user.
- **SSH auth fails**: verify `ansible_user`, key path, and host firewall.
- **OpenSearch fails**: ensure enough RAM (8–12 GB recommended).

## 5) Quick variables

You can override defaults via `-e`:

```bash
ansible-playbook -i inventory/remote/hosts playbook.yml -K \
  -e "db_user=toor db_pass=root db_name=purplelab"
```
