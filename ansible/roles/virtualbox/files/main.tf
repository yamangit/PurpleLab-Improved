terraform {
  required_version = ">= 0.12"
  required_providers {
    null = {
      source  = "hashicorp/null"
      version = "~> 3.0"
    }
  }
}

variable "vm_name" {
  type        = string
  description = "Nom de la machine virtuelle"
  default     = "sandbox"
}

variable "vm_cpus" {
  type        = number
  description = "Nombre de CPU pour la VM"
  default     = 2
}

variable "vm_memory" {
  type        = string
  description = "Quantité de mémoire RAM pour la VM"
  default     = "4096"
}

variable "vm_disk_size" {
  type        = number
  description = "Taille du disque en MB"
  default     = 40960
}

variable "vm_network_interface" {
  type        = string
  description = "Interface réseau à utiliser"
}

variable "vagrant_home" {
  type        = string
  description = "Vagrant home directory (where boxes are stored)"
}

variable "vm_basefolder" {
  type        = string
  description = "VirtualBox base folder for VM storage"
}

resource "null_resource" "windows_vm" {
  triggers = {
    vm_name           = var.vm_name
    vm_network_iface  = var.vm_network_interface
    vagrant_home      = var.vagrant_home
    vm_basefolder     = var.vm_basefolder
  }

  provisioner "local-exec" {
    command = <<-EOT
      # Vérifie si la VM existe déjà
      if VBoxManage list vms | grep -q "\"${var.vm_name}\""; then
        echo "VM ${var.vm_name} déjà existante. Aucune action."
        exit 0
      fi

      echo "Création de la VM ${var.vm_name}..." >> terraform.log
      VBoxManage import "${var.vagrant_home}/boxes/StefanScherer-VAGRANTSLASH-windows_2019/2021.05.15/virtualbox/box.ovf" \
        --vsys 0 \
        --vmname "${var.vm_name}" \
        --basefolder "${var.vm_basefolder}" || exit 1

      echo "Configuration des ressources de la VM..." >> terraform.log
      VBoxManage modifyvm "${var.vm_name}" --cpus ${var.vm_cpus} --memory ${var.vm_memory} --acpi on --boot1 disk || exit 1

      echo "Configuration du réseau..." >> terraform.log
      VBoxManage modifyvm "${var.vm_name}" --nic1 bridged --bridgeadapter1 "${var.vm_network_interface}" || exit 1

      echo "Redimensionnement du disque..." >> terraform.log
      DISK_PATH=$(VBoxManage showvminfo "${var.vm_name}" --machinereadable | awk -F'=' '/SATA-0-0|IDE-0-0/ {gsub(/\"/, "", $2); print $2; exit}')
      if [ -n "$${DISK_PATH}" ]; then
        if echo "$${DISK_PATH}" | grep -qE '\\.vmdk$'; then
          NEW_DISK="$${DISK_PATH%.vmdk}.vdi"
          VBoxManage clonemedium disk "$${DISK_PATH}" "$${NEW_DISK}" --format VDI || exit 1
          VBoxManage storageattach "${var.vm_name}" --storagectl "IDE Controller" --port 0 --device 0 --type hdd --medium "$${NEW_DISK}" || exit 1
          VBoxManage closemedium disk "$${DISK_PATH}" --delete || true
          DISK_PATH="$${NEW_DISK}"
        fi
        VBoxManage modifymedium disk "$${DISK_PATH}" --resize ${var.vm_disk_size} || exit 1
      fi

      echo "Démarrage de la VM..." >> terraform.log
      VBoxManage startvm "${var.vm_name}" --type headless || exit 1

      echo "Attente que la VM soit prête..." >> terraform.log
      sleep 60

      echo "Vérification de l'état de la VM..." >> terraform.log
      VBoxManage showvminfo "${var.vm_name}" | grep -q "running" || exit 1

      echo "VM ${var.vm_name} créée et démarrée avec succès" >> terraform.log
    EOT
  }

  # Optionnel : tu peux garder ce bloc, mais il est dangereux si relancé involontairement.
  # Je recommande de l'enlever complètement si tu veux pas supprimer la VM accidentellement.
}
