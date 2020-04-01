from __future__ import print_function
import os
import paramiko
import time


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
