import binascii
import logging
import struct
from typing import Optional

logger = logging.getLogger(__name__)


class Modbus:
    WriteSingleRegister = 0x06
    ReadMultichannelRegisterInput = 0x03

    def __init__(self, fd):
        """
        :param fd: the file descriptor with read/write methods to use
        """
        self.s = fd

    def _send(self, data) -> int:
        d = data + struct.pack('<H', self.calculate_crc(data))
        logger.debug(f"TX[{len(binascii.hexlify(d)) / 2:02.0f}]: {binascii.hexlify(d)}")
        ret = self.s.write(d)
        # logging.debug(f"TX: done")
        # self.s.flush() doesn't seem to help
        return ret

    def _recv(self, length=1) -> Optional[bytes]:
        data = b''
        while True:
            b = self.s.read(length)
            if len(b) == 0:
                break
            data += b
        if len(data) > 2:
            pkt_without_crc = self._proc_pkt_crc(data)
            return pkt_without_crc
        return None

    def send_packet(self, device_address=1, address=5, value=None):
        if value is None:
            value = 1  # todo this can be used to increase the length of a read!
            # set value to "2" to read 2 consecutive registers!
            function_code = Modbus.ReadMultichannelRegisterInput
        else:
            function_code = Modbus.WriteSingleRegister
        pack = struct.pack('>BBHH', device_address, function_code, address, value)
        self._send(pack)

    class RxPacket:
        def __init__(self, pkt):
            self.sof = pkt[0]
            self.address = pkt[1]
            if self.address == 0x3:
                length = pkt[2]
                assert len(pkt[3:]) == length
                if length == 2:
                    self.data, = struct.unpack('>H', pkt[3:])
                else:
                    self.data = pkt  # todo why
            elif self.address == 0x6:
                assert len(pkt[2:]) == 4
                addr, val = struct.unpack('>HH', pkt[2:])
                self.data = (addr, val)
            elif self.address == 0x83:
                if pkt[2] == 0x08:
                    logger.error(f"CRC TX Error {pkt}")
                    self.data = (0, 0)
                else:
                    logger.error(f"RX fail! {pkt}")
                    self.data = 0
            else:
                logger.error(f"RxPacket couldn't handle {self.address: x}")
                self.data = 0

    def receive_packet(self):
        p = self._recv()
        if p:
            pkt = Modbus.RxPacket(p)
            return pkt.data
        else:
            logger.error(f"read timed out!")
            return 0

    def _proc_pkt_crc(self, data: bytes) -> bytes:
        crc = self.calculate_crc(data[:-2])
        packet_crc, = struct.unpack('<H', data[-2:])
        if crc != packet_crc:
            raise CRCError("RX")
        logger.debug(f"RX[{len(binascii.hexlify(data)) / 2:02.0f}]: {binascii.hexlify(data)}")
        return data[:-2]

    def set_by_addr(self, address: int, value) -> bool:
        self.send_packet(address=address, value=value)
        ret = self.receive_packet()
        return (address, value) == ret

    def get_by_addr(self, address: int) -> int:
        self.send_packet(address=address, value=None)
        ret = self.receive_packet()
        return ret

    @staticmethod
    def calculate_crc(data: bytes) -> int:
        """Calculate the CRC16 of a datagram"""
        crc = 0xFFFF
        for i in data:
            crc ^= i
            for _ in range(8):
                if crc & 1:
                    crc >>= 1
                    crc ^= 0xa001
                else:
                    crc >>= 1
        return crc


class CRCError(Exception):
    pass
