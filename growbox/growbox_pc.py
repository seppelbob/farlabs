import socket
import time
import re

HOST = 'raspberrypi.local'
PORT = 50002

def extract_data(data):
    regex = r"T(\d+\.?\d+)H(\d+\.?\d+)I(\d+\.?\d+)"
    match = re.match(regex, data)
    
    if match is None:
        return None, None, None

    temp = match[1]
    hum = match[2]
    intensity = match[3]

    return temp, hum, intensity


with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    
    s.connect((HOST, PORT))
    print("connected!")
    while True:

        s.sendall(b'S0/D/0')
        data = s.recv(1024).decode()
        T, H, I = extract_data(data)
        print(f"{time.asctime()}   :   T = {T} deg,  H = {H} %,  I = {I} lux")
        #print(data)

        #time.sleep()

