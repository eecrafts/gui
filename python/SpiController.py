
import USB910H as spi

class SpiController(object):
    def __init__(self):
        spi.initialSPI()

    def send_command(self, cmd):
        spi.SPIexecute(cmd)

    def __del__(self):
        spi.closeAdapter()
