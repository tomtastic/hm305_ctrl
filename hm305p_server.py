#!/usr/bin/env python3
import hm305
import sys
import serial
import logging
import socketserver
from queue import Queue
import threading

from hm305.queue_handler import HM305pSerialQueueHandler, HM305pFastQueueHandler
from hm305.server import HM305pServer

logging.basicConfig(format='%(asctime)s %(name) %(message)s', level=logging.DEBUG)

global server


def exit_gracefully(a=None, b=None):
    global server
    HM305pSerialQueueHandler.time_to_die = True
    HM305pFastQueueHandler.time_to_die = True
    server.shutdown()
    server.socket.close()
    exit(0)


# psu0 on : snmpset -v 1 -c private pdu 1.3.6.1.4.1.318.1.1.4.4.2.1.3.8 i 1
# psu1 on : snmpset -v 1 -c private pdu 1.3.6.1.4.1.318.1.1.4.4.2.1.3.7 i 1


def main():
    import argparse
    global server
    print(sys.argv)
    parser = argparse.ArgumentParser()
    parser.add_argument('--serial-port', type=str, help='serial port', required=True)
    parser.add_argument('--port', type=int, help='network port', required=True)
    parser.add_argument('--addr', type=str, help='ip to bind to', required=False, default='0.0.0.0')
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
    with serial.Serial(args.serial_port, baudrate=9600, timeout=0.1) as ser:
        # ser.set_low_latency_mode(True) # doesn't work on ch341
        hm = hm305.HM305(ser)
        serial_consumer = HM305pSerialQueueHandler(HM305pServer.serial_q, hm)
        serial_consumer_thread = threading.Thread(target=serial_consumer.run)
        serial_consumer_thread.daemon = True
        serial_consumer_thread.start()
        fast_consumer = HM305pFastQueueHandler(HM305pServer.fast_q, hm)
        fast_consumer_thread = threading.Thread(target=fast_consumer.run)
        fast_consumer_thread.daemon = True
        fast_consumer_thread.start()
        while True:
            try:
                server = socketserver.TCPServer((args.addr, args.port), HM305pServer)
                server.serve_forever()
            except OSError as e:
                logging.error(e)
            except (KeyboardInterrupt):
                exit_gracefully()
            


if __name__ == "__main__":
    main()
