import hashlib
import os
import socket
import time
from tkinter import Tk
from tkinter import filedialog


def suffix(size):
    k = 1024
    m = 1024 * k
    g = 1024 * m
    if size < k:
        return str(size) + ' B'
    elif size < m:
        return '{:.2f}'.format(size / k) + ' KB'
    elif size < g:
        return '{:.2f}'.format(size / m) + ' MB'
    else:
        return '{:.2f}'.format(size / g) + ' GB'


root = Tk()
root.withdraw()

# HOST = '127.0.0.1'
HOST = '192.168.160.129'
PORT = 23333
BUFSIZE = 1024
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

try:
    s.connect((HOST, PORT))
    print('send a file to', HOST, ':')

    fpath = filedialog.askopenfilename(title='Open', initialdir=os.getcwd())
    f = open(fpath, 'rb')
    print('source file :', fpath)

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
    f.close()

    ssize = 0
    per = 0
    t0 = time.perf_counter()

    f = open(fpath, 'rb')
    while True:
        data = f.read(BUFSIZE)
        if not data:
            break
        s.sendall(data)
        if fsize - ssize > BUFSIZE:
            ssize += BUFSIZE
        else:
            ssize = fsize
        print('\r', '{:.2f}'.format(ssize / fsize * 100), '%', end='')

    print()
    t1 = time.perf_counter()
    dt = t1 - t0
    rate = fsize / dt
    print('time :', dt, 's')
    print('average rate :', suffix(rate), '/ s')
    f.close()
    fstat = s.recv(BUFSIZE).decode('utf-8')
    print(fstat)

    s.close()

except (FileNotFoundError, ConnectionError):
    print()
    print('transmission failed')
    s.close()
    exit()
