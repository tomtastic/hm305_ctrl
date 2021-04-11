import logging
import binascii
import socketserver
import time
import signal
import scpi

logging.basicConfig(format='%(asctime)s %(message)s', level=logging.INFO)

global hm
global server

def get_volt():
    return hm.v

cmds = {
    'VOLTage': scpi.FloatCmd(doc='voltage')
}

scpi_cmds = scpi.Commands(cmds)

