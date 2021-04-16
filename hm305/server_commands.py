from functools import partial
import hm305
import scpi


class Command:
    def __init__(self):
        self.stale = False
        self.complete = False
        self.result = None

    wait_for_result = False
    uses_serial_port = True

    def invoke(self, hm: hm305.HM305):
        """
        Used by the command runner to actually perform the command
        Sets result (if applicable) and complete before returning.
        The external command runner checks the stale flag first, not this function
        """
        self.result = 'Not implemented'
        self.complete = True

    def result_as_string(self):
        return f"{self.result}"


class CommandWithArg(Command):
    def __init__(self, arg):
        super().__init__()
        self.arg = arg


class CommandWithFloatArg(CommandWithArg):
    def __init__(self, arg):
        super().__init__(arg)
        try:
            self.arg = float(arg)
        except ValueError:
            self.stale = True
            self.result = 'error: bad float'

    def result_as_string(self):
        return f"{self.result:2.3f}"


class QueryCommand(Command):
    wait_for_result = True


class OutputQuery(QueryCommand):
    def invoke(self, hm):
        self.result = hm.output
        self.complete = True

    def result_as_string(self):
        return scpi.encode_on_off(self.result)


class SetOutputCommand(CommandWithArg):
    def __init__(self, arg):
        super().__init__(arg)
        self.arg = scpi.decode_on_off(arg)  # ON/OFF->true/false

    uses_serial_port = True
    wait_for_result = False

    def invoke(self, hm):
        if self.arg:
            hm.on()
        else:
            hm.off()
        self.result = self.arg
        self.complete = True

    def result_as_string(self):
        return str(self.arg)


class MeasureVoltageQuery(QueryCommand):
    uses_serial_port = True

    def invoke(self, hm):
        self.result = hm.v
        self.complete = True


class SetVoltageCommand(CommandWithFloatArg):
    """
    NOTE: This class is manually split into a SetVoltageSetpoint and a VoltageApply
    Need to find a cleaner way to do this
    """
    uses_serial_port = True

    def invoke(self, hm):
        if not self.complete:
            hm.v = self.arg
        self.complete = True


class SetVoltageSetpointCommand(CommandWithFloatArg):
    uses_serial_port = False
    wait_for_result = True

    def invoke(self, hm):
        hm.vset = self.arg
        self.result = self.arg
        self.complete = True


class VoltageApplyCommand(Command):
    uses_serial_port = True
    wait_for_result = False
    in_queue = False

    def __init__(self):
        super().__init__()
        if VoltageApplyCommand.in_queue:  # TODO
            self.stale = True
            self.complete = True
        else:
            VoltageApplyCommand.in_queue = True

    def invoke(self, hm):
        VoltageApplyCommand.in_queue = False
        hm.v_apply()
        self.complete = True


class VoltageSetpointQuery(QueryCommand):
    uses_serial_port = False
    wait_for_result = True

    def invoke(self, hm):
        self.result = float(hm.vset)
        self.complete = True


class MeasureCurrentQuery(QueryCommand):
    uses_serial_port = True

    def invoke(self, hm):
        self.result = float(hm.i)
        self.complete = True


class SetCurrentCommand(CommandWithFloatArg):
    uses_serial_port = True
    wait_for_result = False

    def invoke(self, hm):
        hm.i = self.arg
        self.complete = True


class CurrentSetpointQuery(QueryCommand):
    uses_serial_port = False
    wait_for_result = True

    def invoke(self, hm):
        self.result = float(hm.iset)
        self.complete = True


# TODO
SetCurrentSetpointCommand = SetCurrentCommand


class CommandFactory:
    Commands = scpi.Commands({
        "VOLTage": partial(dict, get=MeasureVoltageQuery, set=SetVoltageCommand),
        "VOLTage:SETPoint": partial(dict, get=VoltageSetpointQuery, set=SetVoltageSetpointCommand),
        "VOLTage:APPLY": partial(dict, get=None, set=VoltageApplyCommand),
        "CURRent": partial(dict, get=MeasureCurrentQuery, set=SetCurrentCommand),
        "CURRent:SETPoint": partial(dict, get=CurrentSetpointQuery, set=SetCurrentSetpointCommand),
        "OUTput": partial(dict, get=OutputQuery, set=SetOutputCommand),
    })

    @staticmethod
    def parse(cmd_str: str) -> Command:
        cmd_str = cmd_str.strip()  # remove whitespace
        is_query = cmd_str.endswith('?')
        cmd_str = cmd_str.strip('? ')
        num_spaces = cmd_str.count(' ')
        to_return = None
        if num_spaces == 1:  # has arg
            (cmd_str_base, arg_str) = cmd_str.split(' ')
            scpi_cmd = CommandFactory.Commands[cmd_str_base]()
            if scpi_cmd is not None:
                if is_query and scpi_cmd['get'] is not None:
                    to_return = scpi_cmd['get'](arg_str)  # does this case exist?
                elif not is_query and scpi_cmd['set'] is not None:
                    to_return = scpi_cmd['set'](arg_str)
            else:
                to_return = None
        elif num_spaces == 0:  # no arg
            scpi_cmd = CommandFactory.Commands[cmd_str]()
            if scpi_cmd is not None:
                if is_query and scpi_cmd['get'] is not None:
                    to_return = scpi_cmd['get']()
                elif not is_query and scpi_cmd['set'] is not None:
                    to_return = scpi_cmd['set']()  # does this case exist?
            else:
                to_return = None
        else:  # a problem
            to_return = None
        return to_return
