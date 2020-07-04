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
    print('\033[93mEMF  | \033[00mProcessing file: ' + sys.argv[1])
    info = check_file_arch(sys.argv[1])
    with open('info.json', 'w') as f:
        json.dump(info, f)

    arch = info['arch']
    lib = info['linked-libs']

    if arch == 'Unsupported':
        print('\033[93mEMF  | \033[00mCPU architecture is not supported. Exitting')
        exit(0)
    print('\033[93mEMF  | \033[00mCPU architecture: ' + arch)

    print('\033[92mSE   | \033[00mStarting QEMU virtual machine')
    start_vm(arch)

    vm_ip = vm_ip_dict[arch]

    print('\033[92mSE   | \033[00mTransfering ELF')
    if scp_to_vm(sys.argv[1], 'root', vm_ip, '/root/qemu') == 1:
        print('\033[92mSE   | \033[00mTransfering failed. Exitting')
        shutdown_vm(arch)
        exit(0)

    if lib == 'dynamic':
        print('\033[92mSE   | \033[00mChecking requested libs')
        cmd = 'cd qemu/ && chmod +x ' + elf + ' && ldd ' + elf
        exit_status, output = paramiko_client(vm_ip, cmd)
        if 'not found' in output:
            print('\033[92mSE   | \033[00mFound missing libs')
            src_lib = os.getcwd() + '/lib_repo/' + arch + '/'
            dst_lib = '/lib/'
            rsync('root', vm_ip, dst_lib, src_lib)
        else:
            print('\033[92mSE   | \033[00mRequested libs are OK')
    else:
        print('\033[92mSE   | \033[00mELF is statically-linked')

    print('\033[92mSE   | \033[00mAnalyzing')
    cmd = 'cd qemu/ && chmod +x ' + elf + ' && python main.py ' + elf + ' 10'
    exit_status, output = paramiko_client(vm_ip, cmd)
    if exit_status == 0:
        print('\033[94mRDP  | \033[00mGenerating report')
        output = output.split('\n')
        report_dir = output[-2][2:]
        scp_to_host('root', vm_ip, '/root/qemu/' +
                    report_dir, './report/', r=True)
        print('\033[94mRDP  | \033[00mComplete')
    else:
        print('\033[94mRDP  | \033[00mTransfering report failed\n' +
              str(output).strip())
        shutdown_vm(arch)
        exit(0)

    print('\033[92mSE   | \033[00mShutting down QEMU')
    shutdown_vm(arch)
    return arch, lib, report_dir


def analyze_ccserver(elf, arch, lib, report_dir):
    ip_list, fl = process_pcap('./report/' + report_dir + 'tcpdump.pcap')
    if not fl:
        print('\033[95mRDM  | \033[00mUnexpected error occured. Exitting')
        return 0

    if len(ip_list) == 0:
        print('\033[95mRDM  | \033[00mStopping analyzing')
        print('\033[95mRDM  | \033[00mFinalizing report')
        shutil.move('report/' + report_dir, 'final_report/')
        shutil.move('info.json', 'final_report/' + report_dir)
        print('\033[95mRDM  | \033[00mComplete')
        return 0

    print('\033[95mRDM  | \033[00mC&C IPs are found. Rerun Sannbox')
    print('\033[92mSE   | \033[00mStarting QEMU virtual machine')
    start_vm(arch)

    vm_ip = vm_ip_dict[arch]

    print('\033[92mSE   | \033[00mTransfering ELF')
    if scp_to_vm(sys.argv[1], 'root', vm_ip, '/root/qemu') == 1:
        print('\033[92mSE   | \033[00mTransfering failed. Exitting')
        shutdown_vm(arch)
        exit(0)

    if lib == 'dynamic':
        print('\033[92mSE   | \033[00mChecking requested libs')
        cmd = 'cd qemu/ && chmod +x ' + elf + ' && ldd ' + elf
        exit_status, output = paramiko_client(vm_ip, cmd)
        if 'not found' in output:
            print('\033[92mSE   | \033[00mFound missing libs')
            src_lib = os.getcwd() + '/lib_repo/' + arch + '/'
            dst_lib = '/lib/'
            rsync('root', vm_ip, dst_lib, src_lib)
        else:
            print('\033[92mSE   | \033[00mRequested libs are OK')
    else:
        print('\033[92mSE   | \033[00mELF is statically-linked')

    print('\033[92mSE   | \033[00mRedirecting')
    with open('ip_list.txt', 'w') as f:
        for ip in ip_list:
            f.write(ip + '\n')
    paramiko_client_ipt(vm_ip)

    print('\033[91mC&C  | \033[00mStarting C&C simulator')
    que = queue.Queue()
    serverThread = threading.Thread(
        target=lambda q, arg: q.put(server(arg)), args=(que, '', ))
    serverThread.start()

    print('\033[92mSE   | \033[00mAnalyzing')
    cmd = 'cd qemu/ && chmod +x ' + elf + ' && python main.py ' + elf + ' 90'
    exit_status, output = paramiko_client(vm_ip, cmd, serverThread, que)

    if exit_status == 0:
        print('\033[94mRDP  | \033[00mGenerating report')
        output = output.split('\n')
        final_report_dir = output[-2][2:]
        scp_to_host('root', vm_ip, '/root/qemu/' +
                    final_report_dir, './final_report/', r=True)
        print('\033[94mRDP  | \033[00mComplete')
    else:
        if exit_status != 'timeout':
            print(
                '\033[94mRDP  | \033[00mTransfering report failed\n' + str(output).strip())
        print('\033[94mRDP  | \033[00mFinalizing report')
        shutil.move('report/' + report_dir, 'final_report/')
        final_report_dir = report_dir
        print('\033[94mRDP  | \033[00mComplete')

    try:
        shutil.move('info.json', 'final_report/' + final_report_dir)
        shutil.move('ip_list.txt', 'final_report/' + final_report_dir)
    except Exception as e:
        print('\033[94mRDP  | \033[00mUnexpected error occured')

    if not os.path.exists('final_report/' + final_report_dir):
        print('\033[94mRDP  | \033[00mConnection error occured')
        shutil.move('report/' + report_dir, 'final_report/')
        shutil.move('info.json', 'final_report/' + report_dir)
        shutil.move('ip_list.txt', 'final_report/' + report_dir)

    print('\033[92mSE   | \033[00mShutting down QEMU')
    shutdown_vm(arch)
    return 0


if __name__ == "__main__":
    t = time.time()
    elf = '.' + sys.argv[1][sys.argv[1].rfind('/'):]

    arch, lib, report_dir = pre_analyze(elf)
    # arch, report_dir = 'i386', '467b70c57106d6031ca1fca76c302ec4d07da253f7d4043b60bdafd7b4d33390_1585795870/'
    analyze_ccserver(elf, arch, lib, report_dir)
    print('\033[93mINFO | \033[00mAnalyzing time: ' + str(time.time() - t))
