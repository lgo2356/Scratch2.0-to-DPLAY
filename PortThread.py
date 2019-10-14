import threading
import ExecuteDPLAY


class S2aThreading(threading.Thread):
    def __init__(self, com_port):
        threading.Thread.__init__(self)
        self.com_port = com_port

    def run(self):
        ExecuteDPLAY.execute_s2a_fm()
