import socketserver
import re
import time

import board
# import Adafruit_DHT
import adafruit_bh1750
from pigpio_dht import DHT11


HOST = ''
PORT = 50002




class Station:

    def __init__(self, DHT11_pin):

        # self.DHT11_sensor = Adafruit_DHT.DHT11
        # self.DHT11_pin = DHT11_pin
        self.DHT11_sensor = DHT11(DHT11_pin)
        self.BH1750_sensor = adafruit_bh1750.BH1750(board.I2C())


    def read_sensors(self):
        
        # humidity, temperature = Adafruit_DHT.read(self.DHT11_sensor, self.DHT11_pin)
        DHT_reading = self.DHT11_sensor.read()
        intensity = self.BH1750_sensor.lux
        data_string = 'T{0:0.1f}H{1:0.0f}I{2:0.1f}'.format(DHT_reading['temp_c'], DHT_reading['humidity'], intensity)
        
        return bytes(data_string, 'utf8')
    
    # This is an alternate version of Adafruit_DHT.read_retry. The only difference is that
    # it will return when it has any value for H and T. They don't need to be from the same
    # call to read
    def DHT_read_retry(self, retries=15, delay_seconds=2):

        humidity, temperature = None, None
        for i in range(retries):
            H, T = Adafruit_DHT.read(self.DHT11_sensor, self.DHT11_pin)
            if H is not None:
                humidity = H
            if T is not None:
                temperature = T
            if humidity is not None and temperature is not None:
                return humidity, temperature
            time.sleep(delay_seconds)
        return None, None




class ThreadingTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    pass



class Handler(socketserver.BaseRequestHandler):
    
    def handle(self):
        
        """
        Request should be of the form "S[0-9]/[DTHLFC]/[0-9]+"
            Number following S speficies station no.
            Letter indicates request type as follows:
                D -> provide sensor data
                T -> temperature command
                H -> humiditiy command
                L -> lighting command
                F -> fan command
                C -> control command
            Final number is value associated with request type
        """

        regex = r"S([0-9])/([DTHLFC])/([0-9]+)"

        while True:

            incoming = self.request.recv(1024)
            
            if not incoming:
                break

            match = re.match(regex, incoming.decode('utf8'))

            # Should probably do some error handling here incase request is in wrong format...

            station_no = int(match[1])
            command = match[2]
            val = int(match[3])
            
            if command == 'D':  # Data read
                data = stations[station_no].read_sensors()
                self.request.sendall(data)
            else:
                self.request.sendall(f"Received {command}-type request with val {val}".encode('utf8'))
            


if __name__ == "__main__":

    NSTATIONS = 1
    STATION_DHT_PINS = [23]

    stations = list()

    for i in range(NSTATIONS):
        stations.append(Station(STATION_DHT_PINS[i]))


    with ThreadingTCPServer((HOST, PORT), Handler) as server:
        server.serve_forever()