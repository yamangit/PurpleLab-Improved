# Vagrant Ubuntu 22.04 (bridged via eth0)

## Prereqs (host)

- VirtualBox installed
- Vagrant installed

## Bring it up

```bash
cd vagrant_box
vagrant up
```

If your host interface is not named `eth0`, edit `vagrant_box/Vagrantfile` and replace the `bridge: "eth0"` value.

## Connect

```bash
cd vagrant_box
vagrant ssh
```

