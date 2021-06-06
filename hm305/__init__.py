import logging
from enum import IntEnum
import serial

from modbus import Modbus
from hm305.floatsetting import FloatSetting

logger = logging.getLogger(__name__)


class HM305:
    class CMD(IntEnum):
        Output = 0x0001  # (R/W)
        ProtectionStatus = (
            0x0002  # (R), bit field of "isOVP, isOCP, isOPP, isOTP, isSCP"
        )
        ModelNum = 0x0003  # (R)
        Class_detail = 0x0004  # (R) # returns "KP". Perhaps is ClassTemplate in DevicesClassInfo.xml?
        Decimals = 0x0005  # (R) # returns 0x233 == scale factors for V/A/P
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
        Power_state = (
            0x8801  # "device power on status address, 2 bytes / Device boot state"
        )
        Default_show = 0x8802  # "default value display addr"
        SCP = 0x8803  # short-circuit protection
        Buzzer = 0x8804
        Device = 0x9999
        SD_Time = 0xCCCC
        Voltage_Min = 0xC110  # seems to return 0d10, so is 0.1?
        Voltage_Max = 0xC11E  # returns 3200 = 32.0 V
        Current_Min = 0xC120  # returns 21 on my HM310P = 0.021A?
        Current_Max = 0xC12E  # returns 10100 on my HM310p = 10.1A

    def __init__(self, fd=None):
        if fd is None:
            logger.debug("HM305 opened without a serial obj! using defaults.")
            fd = serial.Serial("/dev/ttyUSB0", baudrate=9600, timeout=0.1)
        self.modbus = Modbus(fd)
        # self.v_setpoint_sw = 0
        self.i_setpoint_sw = 0
        self.voltage = FloatSetting(
            self.modbus,
            value_addr=HM305.CMD.Voltage,
            setpoint_addr=HM305.CMD.Set_Voltage,
            value_scalar=100.0,
            min_addr=HM305.CMD.Voltage_Min,
            max_addr=HM305.CMD.Voltage_Max,
        )
        self.current = FloatSetting(
            self.modbus,
            value_addr=HM305.CMD.Current,
            setpoint_addr=HM305.CMD.Set_Current,
            value_scalar=1000.0,
            min_addr=HM305.CMD.Current_Min,
            max_addr=HM305.CMD.Current_Max,
        )

    def _set_val(self, addr: int, val) -> bool:
        return self.modbus.set_by_addr(addr, val)

    def _get_val(self, addr: int) -> int:
        return self.modbus.get_by_addr(addr)

    def _tx_rx_word(self, addr: int, val=None) -> int:
        if val is None:  # a getter
            return (self._get_val(addr) << 16) + self._get_val(addr + 1)
        else:
            a = self._set_val(addr, val >> 16)
            if a:
                return self._set_val(addr + 1, val & 0xFFFF)
            return False

    def initialize(self):
        # self.v_setpoint_sw = self._get_val(HM305.CMD.Set_Voltage) / 100
        self.voltage.initialize()
        self.current.initialize()

    ###########################################################
    # @property
    # def i(self):
    #     out = self._get_val(HM305.CMD.Current)
    #     if out is None:
    #         out = 0
    #     return out / 1000
    #
    # @i.setter
    # def i(self, c):
    #     self._set_val(HM305.CMD.Set_Current, val=rint(c * 1000))
    #
    # @property
    # def iset(self):
    #     return self.i_setpoint_sw
    #
    # def i_inc(self, inc):
    #     self.i_setpoint_sw += inc

    ###########################################################
    @property
    def w(self):
        return self._tx_rx_word(HM305.CMD.Power) / 1000

    @property
    def cmax(self):
        return self._tx_rx_word(HM305.CMD.Current_Max)

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
        return self._get_val(HM305.CMD.ModelNum)

    @property
    def protect_state(self):
        return self._get_val(HM305.CMD.ProtectionStatus)

    @property
    def decimals(self):
        return self._get_val(HM305.CMD.Decimals)

    @property
    def classdetail(self):
        return self._get_val(HM305.CMD.Class_detail)

    @property
    def device(self):
        return self._get_val(HM305.CMD.Device)


def rint(x: float) -> int:
    return int(round(x))
