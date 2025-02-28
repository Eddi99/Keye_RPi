import smbus2
import time
import RPi.GPIO as GPIO
from lcd import Lcd

# I2C Adresse des LCD
I2C_ADDR = 0x27
LCD_COLUMNS = 20
LCD_ROWS = 4

# GPIO Pins für Buttons
BUTTON_PINS = [4, 10, 9, 16]

# Initialisiere das Display
lcd = Lcd(I2C_ADDR, LCD_COLUMNS, LCD_ROWS)
lcd.clear()
lcd.write_line("LCD & Buttons Test", 0)
lcd.write_line("Warte auf Eingabe...", 1)

# GPIO Setup
GPIO.setmode(GPIO.BCM)
GPIO.setup(BUTTON_PINS, GPIO.IN, pull_up_down=GPIO.PUD_UP)

def button_callback(channel):
    button_index = BUTTON_PINS.index(channel) + 1
    lcd.clear()
    lcd.write_line(f"Taste {button_index} gedrueckt!", 1)
    time.sleep(0.5)
    lcd.clear()
    lcd.write_line("LCD & Buttons Test", 0)
    lcd.write_line("Warte auf Eingabe...", 1)

# Event-Listener für Tasten
for pin in BUTTON_PINS:
    GPIO.add_event_detect(pin, GPIO.FALLING, callback=button_callback, bouncetime=300)

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("Beende das Programm...")
    lcd.clear()
    GPIO.cleanup()
