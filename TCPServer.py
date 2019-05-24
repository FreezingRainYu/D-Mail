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

HOST = ''
PORT = 23333
BUFSIZE = 1024
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind((HOST, PORT))
s.listen(5)

while True:
    print('waiting for connection...')

    (c, addr) = s.accept()
    print('receive a file from', addr[0], ':')

    try:
        fname = c.recv(BUFSIZE).decode('utf-8')
        print('received file name :', fname)

        fsize = int(str(c.recv(BUFSIZE).decode('utf-8')))
        print('received file size :', suffix(fsize))

        fhash0 = c.recv(BUFSIZE).decode('utf-8')
        print('received file SHA-1 :', fhash0)

    except (ValueError, ConnectionError):
        print('transmission failed')
        c.close()
        print()
        continue

    fpath = filedialog.askdirectory(title='Save', initialdir=os.getcwd()) + '/' + fname
    f = open(fpath, 'wb')
    print('save as :', fpath)

    rsize = 0
    per = 0
    t0 = time.perf_counter()

    try:
        while not rsize == fsize:
            if fsize - rsize > BUFSIZE:
                data = c.recv(BUFSIZE)
                f.write(data)
            else:
                data = c.recv(fsize - rsize)
                f.write(data)
            rsize += len(data)
            print('\r', '{:.2f}'.format(rsize / fsize * 100), '%', end='')

    except ConnectionError:
        print()
        f.close()
        os.remove(fpath)
        print('transmission failed')
        c.close()
        print()
        continue

    print()
    t1 = time.perf_counter()
    dt = t1 - t0
    rate = fsize / dt
    print('time :', dt, 's')
    print('average rate :', suffix(rate), '/ s')
    f.close()

    f = open(fpath, 'rb')
    fhash1 = hashlib.sha1()
    while True:
        data = f.read(BUFSIZE)
        if not data:
            break
        fhash1.update(data)
    fhash1 = str(fhash1.hexdigest())
    print('calculated file SHA-1 :', fhash1)
    f.close()
    if fhash0 == fhash1:
        print('data check succeeded')
    else:
        os.remove(fpath)
        print('data check failed')

    c.close()
    print()
