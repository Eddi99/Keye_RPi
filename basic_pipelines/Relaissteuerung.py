import hid
from time import sleep
import sys
import termios
import tty

USB_CFG_VENDOR_ID = 0x16c0  # Should suit, if not check ID with a tool like USBDeview
USB_CFG_DEVICE_ID = 0x05DF  # Should suit, if not check ID with a tool like USBDeview

device = None

def get_Hid_USBRelay():
    global device
    try:
        device = hid.Device(USB_CFG_VENDOR_ID, USB_CFG_DEVICE_ID)
        print("Device connected successfully")
    except Exception as e:
        print(f"Failed to open device: {e}")
        device = None

def close_device():
    global device
    if device:
        device.close()
        device = None
        print("Device closed")

def write_row_data(buffer):
    global device
    if device:
        try:
            device.write(bytes(buffer))
            return True
        except Exception as e:
            print(f"Failed to write data: {e}")
            return False
    else:
        print("Device not connected")
        return False

def on_all():
    if write_row_data([0, 0xFE, 0, 0, 0, 0, 0, 0, 1]):
        return True
    else:
        print("Cannot turn ON all relays")
        return False

def off_all():
    if write_row_data([0, 0xFC, 0, 0, 0, 0, 0, 0, 1]):
        return True
    else:
        print("Cannot turn OFF all relays")
        return False

def get_key():
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    tty.setcbreak(fd)
    try:
        return sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

get_Hid_USBRelay()

print('e für einschalten, a für ausschalten, Leertaste, um zu beenden')
while True:
    try:
        key = get_key()
        if key == 'a':
            print('Relais aus!')
            print("TURN OFF ALL: {}".format(off_all()))
            sleep(0.1)

        elif key == 'e':
            print('Relais ein!')
            print("TURN ON ALL: {}".format(on_all()))
            sleep(0.1)

        elif key == ' ':
            print('Beenden!')
            print("TURN OFF ALL: {}".format(off_all()))
            close_device()
            break
    except KeyboardInterrupt:
        print("Beenden durch STRG+C")
        close_device()
        break
