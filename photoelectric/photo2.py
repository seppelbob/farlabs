from subprocess import call
import datetime, time, serial, sys, os, string
import BaseHTTPServer
import SocketServer
import threading

HOST_NAME = os.getenv('COMPUTERNAME') + '.ltu.edu.au'
PORT_NUMBER = 1131 

#allowed_clients = {'115.146.85.225':1, '115.146.94.221':1}

#pat edit: copied allowed_clients from turntable code 9ydt
#allowed_clients = {'115.146.85.225':1, '115.146.94.221':1, '43.240.99.49':1}

#bec edit 19/4/2021 <------ ?
allowed_clients = {'115.146.85.225':1, '115.146.94.221':1, '203.101.228.254':1}



commandPrefix = 'U'

colors = { 	
	'uv':'U',
	'ir':'I',
	'red':'R',
	'green':'G',
	'blue':'B',
	'amber':'A'
}

valToVolts = 5.0 / 1024.0

def checkClient(handler, ipString):
	if ipString in allowed_clients: return 1	
	if ipString.split('.')[0:3] == ['131','172','133']: return 1		
	handler.send_error(401)
	return 0	

class Station:
	collectId = 0
	com = -1
	serial = None
	number = -1
	currentLED = ""
	recording = False
	recordingThread = None
	volts = []
	times = []
	
	def collectFor(self, seconds):
		self.collectId = self.collectId + 1
		self.recording = True	
		sleepTime = .05
		self.volts = []
		self.times = []
		startTime = time.time()
		while (time.time() - startTime) < seconds:
			if not self.recording: break
			readBack = self.send('?9').rstrip()
			try:
				self.volts.append(str(float(readBack) * valToVolts))
				self.times.append(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f"))				
			except:
				f = open('error_log' + str(self.number) + '.txt', 'a')
				f.write(readBack + '\n')
				f.close()				
			time.sleep(sleepTime)
		self.recording = False	
	
	def readl(self):
		return self.serial.readline().rstrip()

	def send(self, string):
		self.serial.write(commandPrefix + string)
		return self.readl()	

	def turnOffAll(self):
		return self.send('O9')	
		
	def discharge(self):
		r = self.send('D9')
		time.sleep(.1)
		return r
		
	def selectLED(self, color, intensity, collectForSeconds):			
		if color not in colors: return '[]'
		self.currentLED = color + "-" + intensity
		cmd = colors[color] + str(int(intensity) + 1)
		self.discharge()	
		self.send(cmd)
		self.recordingThread = threading.Thread(target=self.collectFor, args=(collectForSeconds,))
		self.recordingThread.start()	
		return 'OK'
		
	def dataToString(self):
		if len(self.times) == 0: return '[]'	
		result = '['
		for t in zip(self.times, self.volts):
			result = result + '{"time":"' + t[0] + '", "id": ' + str(self.collectId) + ', "value":' + t[1] + '},'	
		return result[:-1] + ']'
		

	
class ThreadedHTTPServer(SocketServer.ThreadingMixIn, BaseHTTPServer.HTTPServer):
    pass
		
class Web(BaseHTTPServer.BaseHTTPRequestHandler):

	def do_HEAD(self, code, type):
		self.send_response(code)
		self.send_header("Content-type", type)
		self.send_header("Access-Control-Allow-Origin", "*")
		self.end_headers()		
	
	def do_POST(self):		                
		
		print('running...')

		if not checkClient(self, self.client_address[0]):
			return
		
		self.do_HEAD(200, "text/plain")
		request = (self.path.split('/'))[-1]

		print "Incoming request: " + self.path
		
		# Every command is prefixed with 'station-#_'
		parts = request.split('_')
		station = stations[parts[0]]
		command = parts[1]			
		
		if command.startswith('led'):
			if station.recording: return
			parts = command.split('-')			
			color = parts[1]
			intens = parts[2]
			seconds = int(parts[3])
			if int(intens) > 9: intens = '9'			
			self.wfile.write(station.selectLED(color, intens, seconds))
		elif command == 'stop':                        
			station.recording = False
			self.wfile.write("OK")
		elif command == 'discharge':
			if station.recording: return
			self.wfile.write(station.discharge())
		elif command == 'turnOffAll':
			if station.recording: return
			self.wfile.write(station.turnOffAll())
		elif command == 'update':
			if not station.recording:
				result = '{"done":true, "led":"' + station.currentLED + '", "data":' + station.dataToString() + '}'
			else:
				result = '{"done":false, "led":"' + station.currentLED + '", "data":' + station.dataToString() + '}'
			self.wfile.write(result)
		else:			
			self.wfile.write("Unknown command: " + command)
			
		
		
if __name__ == '__main__':

    stations = {}


    path = "C:/Users/S-Nectar/Desktop/"
    com_map_fname = "camera_station_map.txt"

    with open(path+com_map_fname, 'r') as f:
        for line in f:
            station, com, _ = line.rstrip('\n').split(',')
            s = Station()
            s.com = com
            s.number = station
            s.serial = serial.Serial(s.com, 38400, timeout=5)
            print('Photo: ' + station + ' - ' + str(s.serial))
            stations['Photoelectric' + station] = s




    # Start the server in the main thread	
    httpd = ThreadedHTTPServer((HOST_NAME, PORT_NUMBER), Web)
    print time.asctime(), "Server Starts - %s:%s" % (HOST_NAME, PORT_NUMBER)

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
        
    httpd.server_close()			

    for num, station in stations.iteritems():			
        station.serial.close()	
        
    print time.asctime(), "Server Stops - %s:%s" % (HOST_NAME, PORT_NUMBER)



        

