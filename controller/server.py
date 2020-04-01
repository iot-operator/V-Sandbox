import socket
import threading


def send(c):
    with open('./command_list', 'r') as f:
        lines = f.readlines()
    for line in lines:
        try:
            c.settimeout(1)
            data = c.recv(1024)
            print('recv: ' + data.decode(), end='')
        except:
            pass

        try:
            c.send(line.encode())
            print('send: ' + line, end=''),
            time.sleep(1)
        except:
            print('Lost connection...')
            break
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
        print('Server closed. Waiting VM...')
        return 0


if __name__ == '__main__':
    server()
