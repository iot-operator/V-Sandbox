import os
import sys
import subprocess
import time
from threading import Timer


def proc_file(path):
    p = subprocess.Popen('python3 controller/main.py ' + path, shell=True)
    p.wait()


def proc_folder(path):
    with open('list_benign.csv', 'r') as f:
        old_elf = f.read().split('\n')[:-1]

    for _, _, files in os.walk(path):
        for file in files:
            print(file)
            # Check analysis status
            if file in old_elf:
                print('Already run successful')
                continue

            if path.endswith('/'):
                file_path = sys.argv[1] + file
            else:
                file_path = sys.argv[1] + '/' + file
            output = os.popen('file ' + file_path)
            ret = output.read()

            if 'ARM' not in ret and 'MIPS' not in ret:
                print('Not supported yet')
                continue

            continue_fl = False
            for _, dirs, _ in os.walk('final_report'):
                for dir in dirs:
                    if str(file) in dir:
                        print('Already analyzed')
                        continue_fl = True
            for _, dirs, _ in os.walk('report'):
                for dir in dirs:
                    if str(file) in dir:
                        print('Already analyzed')
                        continue_fl = True

            if not continue_fl:
                proc_file(file_path)
            k = subprocess.Popen('sudo pkill qemu-system-', shell=True)
            k.wait()
    return 0


if __name__ == "__main__":
    # Create_report folder
    if not os.path.exists('final_report/'):
        os.makedirs('final_report/')
    if not os.path.exists('report/'):
        os.makedirs('report/')

    path = sys.argv[1]
    if os.path.isdir(path):
        proc_folder(path)
    elif os.path.isfile(path):
        proc_file(path)
    else:
        print('Input is not a directory or normal file')
