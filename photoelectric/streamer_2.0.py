import subprocess as proc
import time, datetime, sys
import multiprocessing

child = None
starts = 0
reconnect = True

vid_server = "http://203.101.226.33"

class Camera(multiprocessing.Process):
    def __init__(self, id, exe):
        super(Camera, self).__init__()
        self.id = id
        self.exe = exe
        self.starts = 0
        self.buf = ""

    def restart(self):
        print("Restarting ffmpeg")
        self.starts += 1
        self.child = proc.Popen(self.exe, stderr=proc.PIPE)
        print("Started child {}".format(self.starts))

    def monitor(self, line, phnum=99):
        if line.find("bitrate=") > -1:
            try:
                bitrate = int(float(line.split("bitrate=")[1].split("kbits/s")[0]))
            except ValueError:
                bitrate = 1
            print("Photo " + str(phnum) + " | " + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + " | Current Bitrate: " + str(bitrate))
            if bitrate == 0:
                self.child.kill()
        else:
            print(line)

    def run(self):
        while True:
            print ('Running exe: ' + self.exe)
            self.restart()

            while self.child.returncode is None:
                self.child.poll()
                log = self.child.stderr.read(100)
                self.buf += log            
                lines = self.buf.split("frame=")
                if len(lines) > 1:
                    self.monitor(lines[-2], self.id)
                    buf = lines[-1]

            print("ffmpeg process stopped...waiting 10 seconds")
            time.sleep(10)




if __name__ == '__main__':

    # DW edit 13/02/2024
    # Read camera names from file
    path = 'C:/Users/S-Nectar/Desktop/'
    fname = 'camera_station_map.txt'
    with open(path+fname, 'r') as f:
	    cam_map = [line.rstrip('\n') for line in f.readlines()]
	
    cam_dic = {}
    for cam in cam_map:
         num, _, name = cam.split(',')
         cam_dic.update({num : name})

    cameras = {}
    for key in cam_dic:
        radio = ":803{0}/photoelectric{1}".format(key, key)
        exe = './ffmpeg -f dshow -i video="' +cam_dic[key] +'" -f mpegts -codec:v mpeg1video -b 0 ' + vid_server + radio
        cam = Camera(key, exe)
        cam.start()
        cameras.update({key : cam})
        time.sleep(1)
    # exe = './ffmpeg -f dshow -i video="' +cam_dic['5'] +'" -f mpegts -codec:v mpeg1video -b 0 ' + vid_server + '/photoelectric' + '5'
    # cam = Camera(5, exe)
    cam.start()
    

