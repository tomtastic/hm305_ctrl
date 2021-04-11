import logging
from queue import Empty


class HM305pSerialQueueHandler:  # todo priority queue? monitoring commands for i3bar are much less important
    time_to_die = False

    def __init__(self, queue, hm):
        self.queue = queue
        self.hm = hm

    def run(self):
        while not self.time_to_die:
            try:
                item = self.queue.get(timeout=1)
                if item.stale:
                    logging.debug(f"stale item! {item}")
                else:
                    logging.debug(f"processing {item}")
                    item.invoke(self.hm)
                self.queue.task_done()
            except Empty:
                continue


class HM305pFastQueueHandler:
    time_to_die = False

    def __init__(self, queue, hm):
        self.queue = queue
        self.hm = hm

    def run(self):
        while not self.time_to_die:
            try:
                item = self.queue.get(timeout=1)
                if item.stale:
                    logging.debug(f"stale item! {item}")
                elif item.uses_serial_port:
                    logging.error(f"Bad programmer! You cannot put {item} in the fast queue!")
                    item.result = "QUEUE ERROR"
                else:
                    logging.debug(f"processing {item}")
                    item.invoke(self.hm)
                self.queue.task_done()
            except Empty:
                continue
