#!/usr/bin/env python3

import hm305
import struct
import sys
import serial
import logging
import binascii
import socketserver
import time
import signal

logging.basicConfig(format='%(asctime)s %(message)s', level=logging.INFO)

global hm
global server


class GracefulKiller:
    kill_now = False

    def __init__(self):
        signal.signal(signal.SIGINT, self.exit_gracefully)
        signal.signal(signal.SIGTERM, self.exit_gracefully)

    def exit_gracefully(self, signum, frame):
        self.kill_now = True
        server.shutdown()
        server.socket.close()


def set_v(v):
    hm.v = v  # todo why do I need this


def hm_do_init(x):
    logging.debug(hm.vset)  # latches hm.v_setpoint_sw


set_cmd_parser = {
    b'VOLT': lambda x: set_v(x),
    b'CURR': lambda x: hm.iset(x),
    b'INIT': lambda x: hm_do_init(x),
}

get_cmd_parser = {
    b'VOLT': lambda: str(hm.v),
    b'VOLT:SETP': lambda: str(hm.v_setpoint_sw),
    b'CURR': lambda: str(hm.i),
}


def get_arg_and_call(msg, func):
    (cmd, arg) = msg.split(b' ')
    marg = float(arg)
    func(marg)
    return 'DONE\n'


class HM305pServer(socketserver.StreamRequestHandler):
    def handle(self):
        # Receive and print the data received from client
        logging.debug(f"Recieved a request from {self.client_address[0]}")
        msg = self.rfile.readline().strip()
        logging.debug(f"Data Recieved from client is: {msg}")
        if b'?' in msg:
            msg = msg.strip(b'? ')  # remove spaces and '?'
            if msg in get_cmd_parser:
                resp = get_cmd_parser[msg]()
            else:
                resp = f"error bad query\n"
        else:
            msg_cmd = msg.strip(b' ')  # still need to remove whitespace from beginning and end
            if b' ' in msg_cmd:
                msg_cmd = msg.split(b' ')[0]
            if msg_cmd in set_cmd_parser:
                resp = get_arg_and_call(msg, set_cmd_parser[msg_cmd])
            else:
                resp = f"error bad cmd\n"

        logging.info(resp)
        self.wfile.write(resp.encode())


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()

    serial_parser = parser.add_mutually_exclusive_group(required=True)
    serial_parser.add_argument('--port', type=str, help='serial port')
    parser.add_argument('--debug', action='store_true', help='enable verbose logging')
    args = parser.parse_args()

    if len(sys.argv) == 1:
        # display help message when no args are passed.
        parser.print_help()
        sys.exit(1)

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    with serial.Serial(args.port, baudrate=9600, timeout=0.1) as ser:
        # ser.set_low_latency_mode(True) # doesn't work on ch341
        hm = hm305.HM305(ser)
        server = socketserver.TCPServer(("127.0.0.1", 9090), HM305pServer)
        server.serve_forever()
