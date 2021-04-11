#!/usr/bin/env python3


import hm305
import sys
import serial
import logging
import socketserver
import signal
from queue import Queue
import threading

from hm305.queue_handler import HM305pSerialQueueHandler, HM305pFastQueueHandler
from hm305.server import HM305pServer

logging.basicConfig(format='%(asctime)s %(message)s', level=logging.INFO)

global server


def exit_gracefully(a=None, b=None):
    global server
    HM305pSerialQueueHandler.time_to_die = True
    HM305pFastQueueHandler.time_to_die = True
    server.shutdown()
    server.socket.close()




# psu0 on : snmpset -v 1 -c private pdu 1.3.6.1.4.1.318.1.1.4.4.2.1.3.8 i 1
# psu1 on : snmpset -v 1 -c private pdu 1.3.6.1.4.1.318.1.1.4.4.2.1.3.7 i 1



def main():
    import argparse
    global server
    parser = argparse.ArgumentParser()
    signal.signal(signal.SIGINT, exit_gracefully)
    signal.signal(signal.SIGTERM, exit_gracefully)
    serial_parser = parser.add_mutually_exclusive_group(required=True)
    serial_parser.add_argument('--port', type=str, help='serial port')
    parser.add_argument('--debug', action='store_true', help='enable verbose logging')
    args = parser.parse_args()

    if len(sys.argv) == 1:
        # display help message when no args are passed.
        parser.print_help()
        sys.exit(1)

    HM305pServer.serial_q = Queue()
    HM305pServer.fast_q = Queue()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    with serial.Serial(args.port, baudrate=9600, timeout=0.1) as ser:
        # ser.set_low_latency_mode(True) # doesn't work on ch341
        hm = hm305.HM305(ser)
        serial_consumer = HM305pSerialQueueHandler(HM305pServer.serial_q, hm)
        serial_consumer_thread = threading.Thread(target=serial_consumer.run)
        serial_consumer_thread.start()
        fast_consumer = HM305pFastQueueHandler(HM305pServer.fast_q, hm)
        fast_consumer_thread = threading.Thread(target=fast_consumer.run)
        fast_consumer_thread.start()
        try:
            server = socketserver.TCPServer(("127.0.0.1", 9091), HM305pServer)
            server.serve_forever()
        except OSError:
            exit_gracefully()


if __name__ == "__main__":
    main()
