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

# HOST = '127.0.0.1'
HOST = '192.168.160.129'
PORT = 23333
BUFSIZE = 1024
SPEEDRATE = 0.333

# 创建 TCP Socket
# socket.AF_INET == IPv4
# socket.SOCK_STREAM == TCP
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

try:
    # 向 Server 主动发起连接
    s.connect((HOST, PORT))
    print('send a file to', HOST, ':')

    # 打开文件并读取
    fpath = filedialog.askopenfilename(title='Open', initialdir=os.getcwd())
    f = open(fpath, 'rb')
    print('source path :', fpath)

    # 发送文件名
    fname = os.path.basename(fpath)
    s.sendall(fname.encode('utf-8'))
    print('sent file name :', fname)
    time.sleep(0.1)

    # 发送文件大小
    fsize = os.path.getsize(fpath)
    s.sendall(str(fsize).encode('utf-8'))
    print('sent file size :', suffix(fsize))
    time.sleep(0.1)

    # 计算并发送文件 SHA-1 值
    fhash = hashlib.sha1()
    while True:
        data = f.read(BUFSIZE)
        if not data:
            break
        fhash.update(data)
    fhash = str(fhash.hexdigest())
    s.sendall(fhash.encode('utf-8'))
    print('sent file SHA-1 :', fhash)
    time.sleep(0.1)
    f.close()

    ssize = 0
    per = 0
    speed = 0
    t0 = time.perf_counter()

    f = open(fpath, 'rb')
    while True:
        t2 = time.perf_counter()
        # 发送文件数据
        data = f.read(BUFSIZE)
        if not data:
            break
        s.sendall(data)
        # 计算发送进度
        if fsize - ssize > BUFSIZE:
            ssize += BUFSIZE
        else:
            ssize = fsize
        t3 = time.perf_counter()
        # 计算瞬时传输速度与传输百分比
        dt = t3 - t2
        s0 = speed
        speed = len(data) / dt
        if s0 and abs((speed - s0) / s0) > SPEEDRATE:
            speed = s0
        print('\r', '{:.2f}'.format(ssize / fsize * 100), '%', suffix(speed), '/ s', end='')

    print()
    t1 = time.perf_counter()
    # 计算文件传输时间与平均传输速度
    dt = t1 - t0
    speed = fsize / dt
    print('total time :', '{:.6f}'.format(dt), 's')
    print('average speed :', suffix(speed), '/ s')
    f.close()
    # 接收传输结果
    fstat = s.recv(BUFSIZE).decode('utf-8')
    print(fstat)

    s.close()

except (ConnectionError, FileNotFoundError, KeyboardInterrupt):
    print()
    print('transmission failed or cancelled')
    s.close()
    exit()
