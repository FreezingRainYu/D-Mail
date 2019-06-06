import hashlib
import os
import socket
import time
from tkinter import Tk
from tkinter import filedialog


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

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

try:
    s.connect((HOST, PORT))
    print('send a file to', HOST, ':')

    fpath = filedialog.askopenfilename(title='Open', initialdir=os.getcwd())
    f = open(fpath, 'rb')
    print('source path :', fpath)

    fname = os.path.basename(fpath)
    s.sendall(fname.encode('utf-8'))
    print('sent file name :', fname)
    time.sleep(0.1)

    fsize = os.path.getsize(fpath)
    s.sendall(str(fsize).encode('utf-8'))
    print('sent file size :', suffix(fsize))
    time.sleep(0.1)

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
        data = f.read(BUFSIZE)
        if not data:
            break
        s.sendall(data)
        if fsize - ssize > BUFSIZE:
            ssize += BUFSIZE
        else:
            ssize = fsize
        t3 = time.perf_counter()
        dt = t3 - t2
        s0 = speed
        speed = len(data) / dt
        if s0 and abs((speed - s0) / s0) > SPEEDRATE:
            speed = s0
        print('\r', '{:.2f}'.format(ssize / fsize * 100), '%', suffix(speed), '/ s', end='')

    print()
    t1 = time.perf_counter()
    dt = t1 - t0
    speed = fsize / dt
    print('total time :', '{:.6f}'.format(dt), 's')
    print('average speed :', suffix(speed), '/ s')
    f.close()
    fstat = s.recv(BUFSIZE).decode('utf-8')
    print(fstat)

    s.close()

except (ConnectionError, FileNotFoundError, KeyboardInterrupt):
    print()
    print('transmission failed or cancelled')
    s.close()
    exit()
