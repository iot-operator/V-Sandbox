from __future__ import print_function
import subprocess
import signal
import sys
import os
import threading
import time
import shutil
import queue
import json

import paramiko

from qemu_ctl import *
from server import server
from pcap_analyzer import process_pcap
from utils import *


vm_ip_dict = {
    'arm': '192.168.122.100',
    'mips': '192.168.122.101',
    'mipsel': '192.168.122.101',
    'i386': '192.168.122.102',
    'amd64': '192.168.122.103',
    'ppc': '192.168.122.104',
}
server_ip = '192.168.122.1:12345'


def pre_analyze(elf):
    print(sys.argv[1])

    print('CPU architecture...', end=' ')
    info = check_file_arch(sys.argv[1])
    with open('info.json', 'w') as f:
        json.dump(info, f)

    arch = info['arch']
    lib = info['linked-libs']

    if arch == 'Unsupported':
        print('Unsupported CPU architecture')
        exit(0)

    print('Starting VM...')
    start_vm(arch)

    vm_ip = vm_ip_dict[arch]

    print('Copying ELF to VM...', end=' ')
    if scp_to_vm(sys.argv[1], 'root', vm_ip, '/root/qemu') == 1:
        shutdown_vm(arch)
        exit(0)

    if lib == 'dynamic':
        print('Checking requested libs...', end=' ')
        cmd = 'cd qemu/ && chmod +x ' + elf + ' && ldd ' + elf
        exit_status, output = paramiko_client(vm_ip, cmd)
        if 'not found' in output:
            print('\nFound missing libs...', end=' ')
            src_lib = os.getcwd() + '/lib_repo/' + arch + '/'
            dst_lib = '/lib/'
            rsync('root', vm_ip, dst_lib, src_lib)
        else:
            print('OK')
    else:
        print('Static, no need to check requested libs')

    print('Analyzing...')
    cmd = 'cd qemu/ && chmod +x ' + elf + ' && python main.py ' + elf + ' 10'
    exit_status, output = paramiko_client(vm_ip, cmd)
    if exit_status == 0:
        print('Receiving report...', end=' ')
        output = output.split('\n')
        report_dir = output[-2][2:]
        scp_to_host('root', vm_ip, '/root/qemu/' +
                    report_dir, './report/', r=True)
    else:
        print('Failed\n' + str(output).strip())
        shutdown_vm(arch)
        exit(0)

    print('Shutting down VM...', end=' ')
    shutdown_vm(arch)
    return arch, lib, report_dir


def analyze_ccserver(elf, arch, lib, report_dir):
    ip_list = process_pcap('./report/' + report_dir + 'tcpdump.pcap')
    print('C&C Server detected... ' + str(len(ip_list)) + ' IP(s)')
    if len(ip_list) == 0:
        print('Finalizing report...', end=' ')
        shutil.move('report/' + report_dir, 'final_report/')
        shutil.move('info.json', 'final_report/' + report_dir)
        print('Done')
        return 0

    print('Starting VM...')
    start_vm(arch)

    vm_ip = vm_ip_dict[arch]

    print('Copying ELF to VM...', end=' ')
    if scp_to_vm(sys.argv[1], 'root', vm_ip, '/root/qemu') == 1:
        shutdown_vm(arch)
        exit(0)

    if lib == 'dynamic':
        cmd = 'cd qemu/ && chmod +x ' + elf + ' && ldd ' + elf
        exit_status, output = paramiko_client(vm_ip, cmd)
        if 'not found' in output:
            print('Moving libs...', end=' ')
            src_lib = os.getcwd() + '/lib_repo/' + arch + '/'
            dst_lib = '/lib/'
            rsync('root', vm_ip, dst_lib, src_lib)
        else:
            print('OK')

    with open('ip_list.txt', 'w') as f:
        for ip in ip_list:
            f.write(ip + '\n')
    paramiko_client_ipt(vm_ip)

    que = queue.Queue()
    serverThread = threading.Thread(
        target=lambda q, arg: q.put(server(arg)), args=(que, '', ))
    serverThread.start()

    cmd = 'cd qemu/ && chmod +x ' + elf + ' && python main.py ' + elf + ' 90'
    exit_status, output = paramiko_client(vm_ip, cmd, serverThread, que)

    if exit_status == 0:
        print('Receiving report...', end=' ')
        output = output.split('\n')
        report_dir = output[-2][2:]
        scp_to_host('root', vm_ip, '/root/qemu/' +
                    report_dir, './final_report/', r=True)
    else:
        if exit_status != 'timeout':
            print('Failed\n' + str(output).strip())
        print('Finalizing report...', end=' ')
        shutil.move('report/' + report_dir, 'final_report/')
        print('Done')

    shutil.move('info.json', 'final_report/' + report_dir)
    shutil.move('ip_list.txt', 'final_report/' + report_dir)

    print('Shutting down VM...', end=' ')
    shutdown_vm(arch)
    return 0


if __name__ == "__main__":
    t = time.time()
    print('__________vSandbox__________')
    elf = '.' + sys.argv[1][sys.argv[1].rfind('/'):]

    print('Stage 1: Pre-analyze')
    arch, lib, report_dir = pre_analyze(elf)
    # arch, report_dir = 'i386', '467b70c57106d6031ca1fca76c302ec4d07da253f7d4043b60bdafd7b4d33390_1585795870/'

    print('-'*24 + '\nStage 2: Analyzing with C&C Server')
    analyze_ccserver(elf, arch, lib, report_dir)
    print('Analyzing done in ' + str(int(time.time()-t)) + '\n')
