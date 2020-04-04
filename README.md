# vSandbox
## Requirements
python 3
## Setup environment
download folder vm/ (including qemu images) and put it into folder vSandbox/ \
link: \

sudo apt-get update\
sudo apt-get install -y qemu-kvm qemu virt-manager virt-viewer libvirt-bin\
sudo apt-get install sshpass\
sudo apt-get install uml-utilities bridge-utils\

sudo gedit /etc/network/interfaces
```
# interfaces(5) file used by ifup(8) and ifdown(8)
auto lo
iface lo inet loopback

auto br0
iface br0 inet dhcp
 bridge_ports <interface>
 bridge_maxwait 0
```

sudo groupadd -r tuntap\
sudo usermod -a -G tuntap <hostname>\
sudo ifup br0\
sudo cp qemu-ifup /etc/\
sudo chmod 755 /etc/qemu-ifup\
sudo mkdir /usr/share/openbios\
sudo cp openbios-ppc /usr/share/openbios\
sudo chmod +x sandbox/*.sh
sudo chmod +x lib/*/*

pip3 install paramiko\
pip3 install scapy

sudo visudo
```
Defaults    timestamp_timeout=-1\
```
nano ~/.ssh/config
```
host 192.168.122.*
    StrictHostKeyChecking no
    UserKnownHostsFile=/dev/null
```
## Run sandbox
python3 run.py <file_or_folder>