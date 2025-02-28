import smbus2
import time

class Lcd:
    def __init__(self, addr, cols, rows):
        self.addr = addr
        self.cols = cols
        self.rows = rows
        self.bus = smbus2.SMBus(1)
        self.init_lcd()

    def init_lcd(self):
        self.write_cmd(0x33)  # Initialize
        self.write_cmd(0x32)  # Set to 4-bit mode
        self.write_cmd(0x06)  # Cursor move direction
        self.write_cmd(0x0C)  # Turn cursor off
        self.write_cmd(0x28)  # 2 line display
        self.write_cmd(0x01)  # Clear display
        time.sleep(0.2)

    def write_cmd(self, cmd):
        self.bus.write_byte_data(self.addr, 0, cmd)
        time.sleep(0.01)

    def write_line(self, text, line):
        text = text.ljust(self.cols)
        self.write_cmd(0x80 + (0x40 * line))
        for char in text:
            self.bus.write_byte_data(self.addr, 0x40, ord(char))
    
    def clear(self):
        self.write_cmd(0x01)
        time.sleep(0.2)
