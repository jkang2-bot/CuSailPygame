import nav_algo.nmea as nmea
import nav_algo.coordinates as coord
import nav_algo.SailSensors as SailSensors
from math import pi
import serial
import struct
import time


class sensorData:
    def __init__(self, coordinate_system=None):
        self.coordinate_system = coordinate_system

        # IMU
        self.pitch = 0
        self.roll = 0
        self.yaw = 0  # we read as wrt N, convert to wrt x-axis (E) (make sure 90 degrees is north)

        # anemometer
        self.wind_direction = 0  # wrt x-axis and noise removed
        self.wind_speed = 0  #don't need this, might add as an extra if there is time left
        self.anemomSMA = []  #helps remove noise from the anemometer reading

        # GPS
        self.fix = False
        self.latitude = 0.0
        self.longitude = 0.0
        self.velocity = None
        self.position = None
        self.prev_time = None

        #Sensor objects
        self.IMU = SailSensors.SailIMU()
        self.anemometer = SailSensors.SailAnemometer(0)
        # do not open gps port yet (don't give a port in the initialization)
        self.gps_serial_port = serial.Serial(port=None,
                                             baudrate=9600,
                                             timeout=1)
        self.gps_serial_port.port = '/dev/ttyAMA3'  #ttyAMA3 needs to bes

        #sensorData
        self.boat_direction = 0  # angle of the sail wrt north.
        self.sailAngleBoat = 0  #angle of the sail wrt to the boat.
        self.rawWind = 0

    def readIMU(self):
        rawData = self.IMU.i2c_read_imu()
        eulerAngles = [0, 0, 0]
        #iterates through the list of raw data and converts int into a list of three floats
        for n in range(3):
            byteFloatList = rawData[4 * n:4 + 4 * n]
            eulerAngles[n] = struct.unpack(">f", bytes(byteFloatList))[0]
            eulerAngles[n] *= (180 / pi)

        self.pitch = eulerAngles[0]
        self.roll = eulerAngles[2]
        self.yaw = 360 + 90 - eulerAngles[1]
        if self.yaw < 0:
            self.yaw += 360
        elif self.yaw > 360:
            self.yaw -= 360
        self.boat_direction = self.yaw

        return

    def readWindDirection(self):
        rawData = self.anemometer.readAnemometerVoltage()
        """print(rawData)"""
        rawWind = rawData
        rawAngle = (360 - rawData * 360 / 1700) + 180

        windWrtN = (rawAngle + self.sailAngleBoat)
        windWrtN = (windWrtN + self.boat_direction + 270) % 360
        self.wind_direction = self._addAverage(windWrtN)
        return


    def readGPS(self):
        # use the NMEA parser
        # TODO you may want to just leave this open
        self.gps_serial_port.open()
        self.gps_serial_port.reset_input_buffer()
        for _ in range(5):
            try:
                line = self.gps_serial_port.readline().decode('utf-8')
                #print(line)
            except:
                line = ''
            nmea_data = nmea.NMEA(line)
            if nmea_data.status:
                self.fix = True
                self.latitude = nmea_data.latitude
                self.longitude = nmea_data.longitude
                print("got lat {}, long {}".format(self.latitude,
                                                   self.longitude))
                new_position = coord.Vector(self.coordinate_system,
                                            self.latitude, self.longitude)
                cur_time = time.time()

                if self.prev_time is None:
                    self.position = new_position
                    self.prev_time = cur_time
                else:
                    self.velocity = new_position.vectorSubtract(self.position)
                    self.velocity.scale(1.0 / (cur_time - self.prev_time))
                    self.position = new_position
                    self.prev_time = cur_time
                    
        self.gps_serial_port.close()




    def _addAverage(self, newValue):
        """Helper function that manages the SMA of the anemometer, this keeps the list at size =11 and returns the
        average of the list of ints. This function assumes that anemometer readings are taken semi-frequently
        parameter: newValue - int denoting number to be added to the """
        self.anemomSMA.append(newValue / 2)
        if (len(self.anemomSMA) > 1):
            for i in range(len(self.anemomSMA) - 1):
                self.anemomSMA[i] = self.anemomSMA[i] / 2
        if (len(self.anemomSMA) > 10):
            self.anemomSMA.pop(0)
        sum = 0
        for n in self.anemomSMA:
            sum = sum + n
        return sum

    def readAll(self):
        self.readIMU()
        self.readWindDirection()
        self.readGPS()
