import socket
import threading
import time


def send_bashlite(c):
    with open('../command_list', 'r') as f:
        lines = f.readlines()
    for line in lines:
        try:
            c.send(line.encode())
            print('\033[91msend: \033[00m', line.encode())
            time.sleep(1)
        except Exception as e:
            print('Exception: ' + str(e))
            break
        try:
            c.settimeout(1)
            data = c.recv(1024)
            print('\033[92mrecv: \033[00m', data)
        except:
            pass
    c.close()


def send_mirai(c):
    ping = b'\x00\x00'
    while True:
        data = b''
        try:
            c.settimeout(1)
            data = c.recv(1024)
            print('\033[92mrecv: \033[00m', data)
        except:
            pass
        if data == ping:
            try:
                c.send(ping)
                print('\033[91msend: \033[00m', ping)
            except Exception as e:
                print('Exception: ' + str(e))
                break


def send(c):
    data = b''
    try:
        c.settimeout(5)
        data = c.recv(1024)
        print('\033[92mrecv: \033[00m', data)
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

    print("Server is listening...")

    while True:
        try:
            s.settimeout(10)
            c, addr = s.accept()
        except:
            print('Server timeout...')
            return -1

        print('Connected to ' + str(addr[0]) + ':' + str(addr[1]))

        sendThread = threading.Thread(target=send, args=(c,))
        sendThread.start()
        sendThread.join()
        s.close()
        print('\nServer closed. Waiting VM...')
        return 0


if __name__ == '__main__':
    server("")
