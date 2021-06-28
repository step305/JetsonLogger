import imu_parser
import serial
import multiprocessing as mp
import numpy as np
import time
from config import *


class IMUMessage:
    def __init__(self, dthe=None):
        self.ts = time.time()
        if dthe is None:
            self.dthe = np.zeros(3, dtype=np.float32)
        else:
            self.dthe = dthe


def imu_reader(queue_imu: mp.Queue,
               stop: mp.Event):
    imu_device = serial.Serial(port=IMU_SERIAL_DEVICE, baudrate=115200,
                               bytesize=serial.EIGHTBITS, stopbits=serial.STOPBITS_ONE, xonxoff=False,
                               rtscts=False, dsrdtr=False)
    parser_machine = imu_parser.IMUParserState()
    time.sleep(1)
    imu_device.flushInput()
    dtheta = np.zeros(3, dtype=np.float32)

    fps_counter = 0
    fps_timer_start = time.time()
    print('IMUReader: Started!')

    while True:
        if stop.is_set():
            break

        data_len = imu_device.in_waiting
        if data_len > 0:
            buffer = imu_device.read(size=data_len)
            #print(buffer)
            for next_byte in buffer:
                parser_machine.parse_byte(next_byte)
                if parser_machine.data_ready:
                    packet = parser_machine.packet
                    dtheta[0] = packet.e3[0]
                    dtheta[1] = packet.e3[1]
                    dtheta[2] = packet.e3[2]
                    if not queue_imu.full():
                        queue_imu.put(IMUMessage(dtheta))
                    else:
                        print('IMUReader: Warning! Queue is full!')
                    if fps_counter >= FPS_MAX_COUNTER:
                        fps_timer_stop = time.time()
                        print('IMUReader at {:.1f}fps'.format(fps_counter / (fps_timer_stop - fps_timer_start)))
                        fps_timer_start = time.time()
                        fps_counter = 0
                    else:
                        fps_counter += 1
    imu_device.close()
    print('IMUReader: Finished!')
