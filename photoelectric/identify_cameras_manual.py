from PIL import Image
import numpy as np
import serial
from serial.tools import list_ports
import time
import subprocess as proc
import os
import re
from matplotlib import pyplot as plt
from matplotlib import image as mpimg


# Pyplot used for debugging, checking camera images
# from matplotlib import pyplot as plt

# ENTER STATION NUMBERS FOR THIS COMPUTER HERE
station_numbers = ['1', '2', '3', '4']

commandPrefix = 'U'

# Directory used for writing files (permission issues with C:\farlabs)
temp_path = 'C:/Users/S-Nectar/Desktop/'


class Camera:

    def __init__(self, cam_name):
        self.cam_name = cam_name

    def take_photo(self, path=temp_path, fname='test.jpg'):
        exec = f'C:/farlabs/ffmpeg.exe -f dshow -i "video={self.cam_name}" -frames:v 1 {path+fname}'
        proc.call(exec, stderr=proc.PIPE)
        image = mpimg.imread(path+fname)
        os.remove(path+fname)
        return image
    

class PEstation:

    def __init__(self, com, camera=None):
        self.com = com
        self.camera = camera
        self.serial = serial.Serial(self.com, 38400, timeout=5)

    def set_camera(self, camera):
        self.camera = camera

    def turn_on(self, colour='B9'):
        cmd = commandPrefix + colour
        self.serial.write(cmd.encode())
 
    def turn_off(self):
        cmd = commandPrefix + 'O9'
        self.serial.write(cmd.encode())


def list_of_PEstation_coms():
    port_list = list_ports.comports()
    for port in list(port_list):
        if "USB Serial Port" not in port.description:
            port_list.remove(port)
    return port_list



def list_of_camera_names():
    
    exec = "c:/farlabs/ffmpeg -list_devices true -f dshow -i dummy"
    process = proc.Popen(exec, stderr=proc.PIPE)
    dev_txt = process.stderr.read()
    dev_txt = dev_txt.decode('utf-8')
    
    regex = r'Alternative name "(.*?)"'
    results = re.findall(regex, dev_txt, re.DOTALL)

    return results


def save_camera_station_map(station_list, path=temp_path, fname='camera_station_map.txt'):
    with open(path+fname, 'w') as f:
        for station_number, station in zip(station_numbers, station_list):
            if station.camera is not None:
                f.write(station_number + ',' + station.com + ',' + station.camera.cam_name + '\n')


def is_different_pic(new, dark, tol = 10):
    """Determines if new and dark are 'different'
        May need to play arround with this if cameras are not being assigned correctly.
        Should return True if a light for given lab is on, false otherwise
    """
    
    # This seems to work... dissregard pixels where value is < twice dark
    # then integrate. Set highter tolerance if false positives start appearing
    threshold = dark.max() * 2
    brightness = np.sum(new > threshold * new)
    print(f"\tCamera test result: {brightness}")
    
    # Alternative method - not as effective
    # square_diff = (new - dark)**2
    
    # Show plot of new photo for debugging
    # plt.imshow(pic1)
    # plt.show()

    return True if brightness > tol else False


if __name__ == "__main__":

    # Get lists of cameras and station hardware
    camera_list = [Camera(cam) for cam in list_of_camera_names()]
    station_list = [PEstation(com.name) for com in list_of_PEstation_coms()]

    # Prints lists
    print("\nAvailable cameras:")
    for cam in camera_list:
        print(cam.cam_name)

    print("\nAvailable PE stations:")
    for station in station_list:
        print(station.com) 

    # List that keeps track of which cameras have been assigned
    assigned = []



    for station in station_list:
        station.turn_off()

    time.sleep(1)

    colour_list = ['B9', 'R9', 'G9', 'Y9']


    try:

        print('')
        for station, colour in zip(station_list, colour_list):
            station.turn_on(colour)
            print(f'{station.com} is set to {colour}')

        print('\nwaiting to ensure camera is on...')
        time.sleep(5)

        for i, camera in enumerate(camera_list):
            fname = f'cam{i}.png'
            image = camera.take_photo(fname=fname)
            plt.title(fname)
            
            plt.imshow(image)
            plt.show()
            
            while True:
                station_index = -1
                entry = input("Enter appropriate COM (eg COM3): ")
                for j, station in enumerate(station_list):
                    if station.com == entry:
                        station_index = j
                if station_index > -1:
                    break
                else:
                    coms = [station.com for station in station_list]
                    print("Please enter one of the following:")
                    for com in coms: 
                        print(com)
                
            station_list[station_index].set_camera(camera)

    finally:

        for station in station_list:
            station.turn_off()

    save_camera_station_map(station_list)

    


    # for station in station_list:
        
    #     # Turn on the station LED
    #     print(f"\nTurining on station at {station.com}")
    #     station.turn_on()

    #     # Delay to ensure LED is turned on
    #     time.sleep(0.1)

    #     # Loop through cameras to find the one that seens the light!
    #     print(f"Identifying camera...")
    #     for pic, camera in zip(pics, camera_list):
            
    #         new_pic = camera.take_photo()
    #         if is_different_pic(new_pic, pic):

    #             # Raise error if camera is assigned to more than one lab.
    #             # If this error occurs, may need to fiddle with is_different_pic function
    #             assert camera not in assigned

    #             print(f"Camera {camera_list.index(camera)+1} assigned to {station.com}")
    #             station.set_camera(camera)
    #             assigned.append(camera)
                
    #             break

    #     if station.camera is None:
    #         print(f"No camera assigned to {station.com}")

    #     # Switch of the ligh!
    #     station.turn_off()

    # # Write camera/station mappings to file
    # # This will be used by photo.py to identify correct camera for each station
    # save_camera_station_map(station_list)