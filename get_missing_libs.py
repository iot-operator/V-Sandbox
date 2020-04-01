from __future__ import print_function
import os
import sys


def check_success(report_dir):
    count = 0
    missing_libs = dict()
    for _, dirs, _ in os.walk(report_dir):
        for dir in dirs:
            lib_path = report_dir + dir + '/ldd.txt'
            with open(lib_path, 'r') as f:
                data = f.readlines()
                for line in data:
                    if 'not found' in line:
                        lib = line[:line.find(' =>')]
                        missing_libs[lib] = missing_libs.get(lib, 0) + 1
                        count += 1
    missing_libs = sorted(missing_libs.items(), key=lambda x: x[1], reverse=True)
    print(count)
    for lib in missing_libs:
        print(lib)


if __name__ == "__main__":
    report_dir = sys.argv[1]
    check_success(report_dir)
