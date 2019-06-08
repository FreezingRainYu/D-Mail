import hashlib
import os
import socket
import time
from tkinter import Tk
from tkinter import filedialog


# 文件大小单位换算
def suffix(size):
    kilo = 1024
    mega = 1024 * kilo
    giga = 1024 * mega
    if size < kilo:
        return str(size) + ' B'
    elif size < mega:
        return '{:.2f}'.format(size / kilo) + ' KB'
    elif size < giga:
        return '{:.2f}'.format(size / mega) + ' MB'
    else:
        return '{:.2f}'.format(size / giga) + ' GB'


root = Tk()
root.withdraw()

HOST = ''
PORT = 23333
BACKLOG = 1
BUFSIZE = 1024
SPEEDRATE = 0.333

# 创建 TCP Socket
# socket.AF_INET == IPv4
# socket.SOCK_STREAM == TCP
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# 绑定 Server 地址到 Socket
s.bind((HOST, PORT))
# 监听连接请求
s.listen(BACKLOG)

try:
    while True:
        print('waiting for connection...')

        # 被动接受 Client 连接，并用新的 Socket 与 Client 建立连接
        (c, addr) = s.accept()
        print('receive a file from', addr[0], ':')

        try:
            # 接收文件名
            fname = c.recv(BUFSIZE).decode('utf-8')
            print('received file name :', fname)

            # 接收文件大小
            fsize = int(str(c.recv(BUFSIZE).decode('utf-8')))
            print('received file size :', suffix(fsize))

            # 接收文件 SHA-1 值
            recvhash = c.recv(BUFSIZE).decode('utf-8')
            print('received file SHA-1 :', recvhash)

        except (ConnectionError, ValueError):
            print('transmission failed : argument initialization failed')
            c.close()
            print()
            continue

        try:
            fpath = filedialog.askdirectory(title='Save', initialdir=os.getcwd()) + '/' + fname

        except TypeError:
            print('transmission failed : path choice closed')
            c.close()
            print()
            continue

        # 新建文件并写入
        f = open(fpath, 'wb')
        print('destination path :', fpath)

        rsize = 0
        per = 0
        speed = 0
        t0 = time.perf_counter()

        try:
            while not rsize == fsize:
                t2 = time.perf_counter()
                # 接收文件数据
                if fsize - rsize > BUFSIZE:
                    data = c.recv(BUFSIZE)
                    f.write(data)
                else:
                    data = c.recv(fsize - rsize)
                    f.write(data)
                rsize += len(data)
                t3 = time.perf_counter()
                # 计算瞬时传输速度与传输百分比
                dt = t3 - t2
                s0 = speed
                speed = len(data) / dt
                if s0 and abs((speed - s0) / s0) > SPEEDRATE:
                    speed = s0
                print('\r', '{:.2f}'.format(rsize / fsize * 100), '%', suffix(speed), '/ s', end='')

        except ConnectionError:
            print()
            f.close()
            os.remove(fpath)
            print('transmission failed : client connection interrupted')
            c.close()
            print()
            continue

        print()
        t1 = time.perf_counter()
        # 计算文件传输时间与平均传输速度
        dt = t1 - t0
        speed = fsize / dt
        print('total time :', '{:.6f}'.format(dt), 's')
        print('average speed :', suffix(speed), '/ s')
        f.close()

        # 计算本地文件 SHA-1 值并比较
        f = open(fpath, 'rb')
        calchash = hashlib.sha1()
        while True:
            data = f.read(BUFSIZE)
            if not data:
                break
            calchash.update(data)
        calchash = str(calchash.hexdigest())
        print('calculated file SHA-1 :', calchash)
        f.close()
        # 发送传输结果
        if recvhash == calchash:
            print('data check succeeded')
            print('transmission succeeded')
            c.sendall('transmission succeeded'.encode('utf-8'))
        else:
            os.remove(fpath)
            print('transmission failed : data check failed')
            c.sendall('transmission failed : data check failed'.encode('utf-8'))

        c.close()
        print()

except KeyboardInterrupt:
    print()
    print('server closed')
    s.close()
    exit()
