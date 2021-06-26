import ctypes
from enum import Enum

DLE = 0x10
ETX = 0x03


class ReportPacketStructure(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ('code', ctypes.c_uint8),
        ("e1", ctypes.c_float*3),
        ("e2", ctypes.c_float*3),
        ("e3", ctypes.c_float*3),
        ("e4", ctypes.c_float*3),
        ("e5", ctypes.c_float*3),
        ("checksum", ctypes.c_uint8)
    ]


class IMUPacket(ctypes.Union):
    _fields_ = [
        ("packet", ReportPacketStructure),
        ("buffer", ctypes.c_uint8*ctypes.sizeof(ReportPacketStructure))
    ]


class ParserStates(Enum):
    WAIT_DLE1 = 1
    WAIT_DATA = 2
    WAIT_DLE2 = 3


class IMUParserState:
    def __init__(self):
        self.state = ParserStates.WAIT_DLE1
        self.packet = ReportPacketStructure()
        self.code = 0
        self.len = 0
        self.buffer = []
        self.data = []
        self.packet = IMUPacket()
        self.data_ready = False

    def parse_byte(self, new_byte):
        self.data_ready = False
        if self.state == ParserStates.WAIT_DLE1:
            if new_byte == DLE:
                self.len = 0
                self.buffer = []
                self.state = ParserStates.WAIT_DATA
        elif self.state == ParserStates.WAIT_DATA:
            if new_byte == DLE:
                self.state = ParserStates.WAIT_DLE2
            else:
                self.buffer.append(new_byte)
                self.len += 1
        elif self.state == ParserStates.WAIT_DLE2:
            if new_byte == DLE:
                self.buffer.append(new_byte)
                self.len += 1
                self.state = ParserStates.WAIT_DATA
            elif new_byte == ETX:
                self.state = ParserStates.WAIT_DLE1
                self.data_ready = True
                self.data = self.buffer[0:self.len]
                serial_data = bytes(self.data)
                self.packet = ReportPacketStructure.from_buffer_copy(serial_data)
            else:
                self.len = 0
                self.state = ParserStates.WAIT_DLE1
                self.buffer = []
