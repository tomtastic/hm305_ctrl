import logging
from enum import IntEnum
import serial
from modbus import Modbus

logger = logging.getLogger(__name__)


class HM305:
    class CMD(IntEnum):
        Output = 0x0001  # (R/W)
        Protect_state_address = 0x0002  # (R)
        Model_address = 0x0003  # (R)
        Class_detail = 0x0004  # (R)
        Decimals = 0x0005  # (R)
        Voltage = 0x0010  # (R)
        Current = 0x0011  # (R)
        Power = 0x0012  # (R) 4 byte response
        Power_cal = 0x0014  # (R/W?) 4 byte response, "calculated power"
        Protect_Voltage = 0x0020  # (R)
        Protect_Current = 0x0021  # (R)
        Protect_Power = 0x0022  # (R) 4 byte response
        Set_Voltage = 0x0030
        Set_Current = 0x0031
        Set_Time_span = 0x0032
        Power_state = 0x8801  # "device power on status address, 2 bytes"
        Default_show = 0x8802  # "default value display addr"
        SCP = 0x8803  # short-circuit protection
        Buzzer = 0x8804
        Device = 0x9999
        SD_Time = 0xCCCC
        Voltage_Max = 0xC110

    def __init__(self, fd=None):
        if fd is None:
            logger.debug("HM305 opened without a serial obj! using defaults.")
            fd = serial.Serial('/dev/ttyUSB0', baudrate=9600, timeout=0.1)
        self.modbus = Modbus(fd)
        self.v_setpoint_sw = 0
        self.i_setpoint_sw = 0

    def _set_val(self, addr: int, val) -> bool:
        self.modbus.send_packet(address=addr, value=val)
        ret = self.modbus.receive_packet()
        return (addr, val) == ret

    def _get_val(self, addr: int) -> int:
        self.modbus.send_packet(address=addr, value=None)
        ret = self.modbus.receive_packet()
        return ret

    def _tx_rx_word(self, addr: int, val=None) -> int:
        if val is None:  # a getter
            return (self._get_val(addr) << 16) + self._get_val(addr + 1)
        else:
            a = self._set_val(addr, val >> 16)
            if a:
                return self._set_val(addr + 1, val & 0xffff)
            return False

    def initialize(self):
        self.v_setpoint_sw = self._get_val(HM305.CMD.Set_Voltage) / 100
        self._get_val(HM305.CMD.Set_Current) / 1000

    ###########################################################

    @property
    def v(self):
        return self._get_val(HM305.CMD.Voltage) / 100

    @v.setter
    def v(self, val):
        self.v_setpoint_sw = val
        self._set_val(HM305.CMD.Set_Voltage, val=rint(val * 100))

    @property
    def vset(self):
        return self.v_setpoint_sw

    @vset.setter
    def vset(self, x):
        # self.v_setpoint_sw = self.x(HM305.CMD.Set_Voltage) / 100
        self.v_setpoint_sw = x

    def v_inc(self, inc):
        self.v_setpoint_sw += inc

    def v_apply(self):
        self._set_val(HM305.CMD.Set_Voltage, val=rint(self.v_setpoint_sw * 100))

    ###########################################################
    @property
    def i(self):
        out = self._get_val(HM305.CMD.Current)
        if out is None:
            out = 0
        return out / 1000

    @i.setter
    def i(self, c):
        self._set_val(HM305.CMD.Set_Current, val=rint(c * 1000))

    @property
    def iset(self):
        return self.i_setpoint_sw

    def i_inc(self, inc):
        self.i_setpoint_sw += inc

    ###########################################################
    @property
    def w(self):
        return self._tx_rx_word(HM305.CMD.Power) / 1000

    @property
    def vmax(self):
        return self._tx_rx_word(HM305.CMD.Voltage_Max)

    @property
    def output(self):
        return self._get_val(HM305.CMD.Output)

    def off(self):
        self._set_val(HM305.CMD.Output, 0)

    def on(self):
        self._set_val(HM305.CMD.Output, 1)

    @property
    def beep(self):
        return self._get_val(HM305.CMD.Buzzer)

    @beep.setter
    def beep(self, v):
        self._set_val(HM305.CMD.Buzzer, v)

    @property
    def model(self):
        return self._get_val(HM305.CMD.Model_address)

    @property
    def protect_state(self):
        return self._get_val(HM305.CMD.Protect_state_address)

    @property
    def decimals(self):
        return self._get_val(HM305.CMD.Decimals)

    @property
    def classdetail(self):
        return self._get_val(HM305.CMD.Class_detail)

    @property
    def device(self):
        return self._get_val(HM305.CMD.Device)


def rint(x):
    return int(round(x))
