from __future__ import print_function
import os
import paramiko
import time
from qemu_ctl import scp_to_vm


def check_file_arch(file):
    output = os.popen('file ' + file)
    ret = output.read()
    arch = ''
    if 'ELF' in ret:
        if 'ARM' in ret:
            arch = 'arm'
            print('ARM')
        elif 'MIPS' in ret:
            if 'MSB' in ret:
                arch = 'mips'
            else:
                arch = 'mipsel'
            print('MIPS (' + arch + ')')
        elif 'Intel' in ret:
            arch = 'i386'
            print('Intel 80386 (i386)')
        elif 'x86-64' in ret:
            arch = 'amd64'
            print('x86-64')
        elif 'PowerPC' in ret:
            arch = 'ppc'
            print('PowerPC')
        else:
            print('Unsupported')
            print(ret)
    else:
        print('Unsupported!')
        print(ret)
    return arch


def paramiko_client(vm_ip, cmd, thread=None, que=None):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(vm_ip, username='root', password='root')
    _, stdout, _ = client.exec_command(cmd)

    server_output = 0
    if thread:
        thread.join()
        server_output = que.get()

    if server_output == -1:
        exit_status = 'timeout'
        output = None
    else:
        exit_status = stdout.channel.recv_exit_status()
        output = stdout.read().decode('utf-8')
    client.close()
    return exit_status, output


def paramiko_client_ipt(vm_ip, ip_list):
    with open('ip_list', 'w') as f:
        for ip in ip_list:
            f.write(ip + '\n')

    print('Moving ip_list...', end=' ')
    if scp_to_vm('ip_list', 'root', vm_ip, '/root/') == 1:
        print('Failed to move list of C&C IPs')
        exit(0)

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(vm_ip, username='root', password='root')
    server_ip = '192.168.122.1:12345'
    cmd = 'for IP in $(cat ip_list); do iptables -t nat -A OUTPUT -p tcp -d $IP -j DNAT --to-destination ' + \
        server_ip + '; done'
    _, stdout, _ = client.exec_command(cmd)
    exit_status = stdout.channel.recv_exit_status()
    print('Redirect... OK')
    client.close()
