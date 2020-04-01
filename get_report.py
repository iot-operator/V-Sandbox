import os
import sys
import shutil


def gen_label(path):
    b = m = o = be = 0
    with open('/home/ais/Desktop/label.txt', 'w') as f:
        for _, dirs, _ in os.walk(path):
            for dir in dirs:
                if dir is not 'fgt':
                    for _, _, files in os.walk(path + dir):
                        for file in files:
                            f.write(str(file))
                            if 'bashlite' in dir:
                                f.write(' 0\n')
                                b += 1
                            elif 'mirai' in dir:
                                f.write(' 1\n')
                                m += 1
                            elif 'others' in dir:
                                f.write(' 2\n')
                                o += 1
                            elif 'benign' in dir:
                                f.write(' -1\n')
                                be += 1
    print(b,m,o,be)


def check(path):
    ret = True
    for _, _, files in os.walk(path):
        count = 0
        strace_file = ''
        for file in files:
            if 'strace' in file:
                count += 1
                strace_file = file
        if count == 1:
            strace_path = path + '/' + strace_file
            if os.path.getsize(strace_path) < 1024:
                ret = False
        else:
            return ret
    ldd_path = path + '/ldd.txt'
    if os.path.getsize(ldd_path) == 0:
        ret = False
    with open(ldd_path, 'r') as f:
        lib = f.read()
        if 'not found' in lib:
            ret = False
    return ret


def gen_final_report(path, path2):
    s = d = 0
    arch = path[path.rfind('_')+1:]
    print(arch)
    for _, dirs, _ in os.walk(path):
        for dir in dirs:
            name = dir[:dir.find('_')]
            # print(name)
            output = os.popen('file ~/Downloads/botnet_arch/' + arch + name)
            ret = output.read()
            if 'static' in ret and check(path+dir):
                try:
                    s += 1
                    shutil.copytree(path+dir, '/home/ais/Desktop/reports/'+dir)
                except Exception as e:
                    pass

    for _, dirs, _ in os.walk(path2):
        for dir in dirs:
            name = dir[:dir.find('_')]
            # print(name)
            output = os.popen('file ~/Downloads/botnet_arch/' + arch + name)
            ret = output.read()
            if 'dynamic' in ret and check(path2+dir):
                try:
                    d += 1
                    shutil.copytree(path2+dir, '/home/ais/Desktop/reports/'+dir)
                except Exception as e:
                    pass
    print(s,d)


if __name__ == "__main__":
    # gen_label(sys.argv[1])
    gen_final_report(sys.argv[1], sys.argv[2])