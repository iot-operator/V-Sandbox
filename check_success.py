import os
import sys


def check_success(report_dir):
    success_num = 0
    dyn_num = 0
    strace_num = 0
    for _, dirs, _ in os.walk(report_dir):
        for dir in dirs:
            # print(dir)

            success_flag = None
            ldd_path = report_dir + dir + '/ldd.txt'
            with open(ldd_path, 'r') as f:
                data = f.read()
                if 'not found' in data and not success_flag:
                    success_flag = 'Error: dynamic libs missing'
                    dyn_num += 1

            if not success_flag:
                for _, _, files in os.walk(report_dir + dir):
                    count = 0
                    strace_file = ''
                    for file in files:
                        if 'strace' in file:
                            count += 1
                            strace_file = file
                    if count == 1:
                        strace_path = report_dir + dir + '/' + strace_file
                        if os.path.getsize(strace_path) == 593:
                            success_flag = 'Error: strace log too small'
                            strace_num += 1
                            print(dir)

            # print('\t' + str(success_flag))
            if not success_flag:
                success_num += 1
                print(dir + '\tsuccess')
    return success_num,  dyn_num, strace_num


if __name__ == "__main__":
    report_dir = sys.argv[1] 
    print(check_success(report_dir))
