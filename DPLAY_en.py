import sys
import SearchPort
import PortThread
import ExecuteDPLAY_en


if __name__ == '__main__':
    com_port = SearchPort.search_dplay_port()
    # t = threading.Thread(target=ExecuteDPLAY.execute_s2a_fm)
    t = PortThread.S2aThreading(com_port)
    t.daemon = True
    t.start()
    ExecuteDPLAY_en.execute_scratch()
    sys.exit()
