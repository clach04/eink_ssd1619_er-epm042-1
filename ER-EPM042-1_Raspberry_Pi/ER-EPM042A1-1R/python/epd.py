#!/usr/bin/env python
# -*- coding: ascii -*-
# vim:tabstop=4:shiftwidth=4:softtabstop=4:smarttab:expandtab
# Python "driver" for ER-EPM042-1R (hard coded for red, black, and white)
# Copyright (C) 2023  Chris Clark (clach04)

"""Simple Python port of C demo for:

Web: http://www.buydisplay.com
EastRising Technology Co.,LTD
Examples for ER-EPD042A1-1R 
Display is Hardward SPI 4-Wire SPI Interface 
Tested and works with: 
Works with Raspberry pi


So far only implements:

  * reset
  * init
  * clear
  * sleep mode

Need root access, if this is a venv, need to call python venv wrapper

    sudo `which python` epd.py

Note on Raspberry Pi Zero takes about 30 secs to init, clear, and sleep.
"""

import os
import sys
import time

import spidev  # https://github.com/doceme/py-spidev
import RPi.GPIO as gpio  # https://pypi.org/project/RPi.GPIO/  FIXME replace! Check out https://github.com/c0t088/libregpio

try:
    from PIL import Image
except ImportError:
    try:
        import Image    # http://www.pythonware.com/products/pil/
    except ImportError:
        Image = None


RST_PIN = 17
DC_PIN = 25
CS_PIN = 8
BUSY_PIN = 24

DEEP_SLEEP_MODE = 0x10
DISPLAY_UPDATE_CONTROL_2 = 0x22
MASTER_ACTIVATION = 0x20

WRITE_RAM = 0x24
WRITE_RAM_RED = 0x26

EPD_WIDTH = 400
EPD_HEIGHT = 300

SET_RAM_X_ADDRESS_START_END_POSITION = 0x44
SET_RAM_Y_ADDRESS_START_END_POSITION = 0x45
SET_RAM_X_ADDRESS_COUNTER = 0x4E
SET_RAM_Y_ADDRESS_COUNTER = 0x4F

DRIVER_OUTPUT_CONTROL = 0x01
DATA_ENTRY_MODE_SETTING = 0x11  # Page 38, Section: 8.3 Data Entry Mode Setting (11h)
BORDER_WAVEFORM_CONTROL = 0x3C
DISPLAY_UPDATE_CONTROL_1 = 0x21


def delay_ms(delaytime):
    time.sleep(delaytime / 1000.0)


class Epd:
    is_open = False

    def __init__(self, bus=0, device=0):
        self.is_open = True
        # bus, device = 0, 0  # /dev/spidev<bus>.<device>
        self.connect(bus=bus, device=device)
        self.init()

    def connect(self, bus=0, device=0):
        # bus, device = 0, 0  # /dev/spidev<bus>.<device>
        self.spi = spidev.SpiDev()
        self.spi.open(bus, device)

        # init GPIO
        gpio.setmode(gpio.BCM)
        gpio.setwarnings(False)
        gpio.setup(RST_PIN, gpio.OUT)
        gpio.setup(DC_PIN, gpio.OUT)
        gpio.setup(CS_PIN, gpio.OUT)
        gpio.setup(BUSY_PIN, gpio.IN)

        self.spi.max_speed_hz = 32000000  # is this 32Mhz? units are not documented in wiringpim struct implies this is hz
        self.spi.mode = 0b00

    def digital_write(self, pin, value):
        # needs GPIO - want something portable
        gpio.output(pin, value)

    def digital_read(self, pin):
        return gpio.input(pin)

    def spi_writebyte(self, data):
        self.spi.writebytes([data])

    def send_command(self, command):
        self.digital_write(DC_PIN, 0)
        self.digital_write(CS_PIN, 0)
        self.spi_writebyte(command)
        self.digital_write(CS_PIN, 1)

    def send_data(self, data):
        self.digital_write(DC_PIN, 1)
        self.digital_write(CS_PIN, 0)
        self.spi_writebyte(data)
        self.digital_write(CS_PIN, 1)

    def epd_wait_until_idle(self):
        while(self.digital_read(BUSY_PIN) == 1):      #  0/LOW: idle, 1/HIGH: busy
            delay_ms(100)

    def turn_on_display(self):
        self.send_command(DISPLAY_UPDATE_CONTROL_2)
        self.send_data(0xC7)
        self.send_command(MASTER_ACTIVATION)
        print('DEBUG self.epd_wait_until_idle')
        self.epd_wait_until_idle()
        
    def set_windows(self, x_start, y_start, x_end, y_end):
        self.send_command(SET_RAM_X_ADDRESS_START_END_POSITION)
        self.send_data((x_start >> 3) & 0xFF)
        self.send_data((x_end >> 3) & 0xFF)

        self.send_command(SET_RAM_Y_ADDRESS_START_END_POSITION)
        self.send_data(y_start & 0xFF)
        self.send_data((y_start >> 8) & 0xFF)
        self.send_data(y_end & 0xFF)
        self.send_data((y_end >> 8) & 0xFF)

    def epd_set_cursor(self, x_start, y_start):
        self.send_command(SET_RAM_X_ADDRESS_COUNTER)
        self.send_data((x_start >> 3) & 0xFF)

        self.send_command(SET_RAM_Y_ADDRESS_COUNTER)
        self.send_data(y_start & 0xFF)
        self.send_data((y_start >> 8) & 0xFF)

    def epd_clear(self):
        #width = (EPD_WIDTH % 8 == 0)? (EPD_WIDTH / 8 ): (EPD_WIDTH / 8 + 1);
        width = (EPD_WIDTH / 8 ) if (EPD_WIDTH % 8 == 0) else (EPD_WIDTH / 8 + 1)
        width = int(width)
        height = EPD_HEIGHT;
        self.set_windows(0, 0, EPD_WIDTH, EPD_HEIGHT)
        # for loop black
        for j in range(height):
            self.epd_set_cursor(0, j)
            self.send_command(WRITE_RAM)
            for i in range(width):
                self.send_data(0XFF)

        # for loop red
        for j in range(height):
            self.epd_set_cursor(0, j)
            self.send_command(WRITE_RAM_RED)
            for i in range(width):
                self.send_data(0XFF)
        self.turn_on_display()

    def epd_display(self, black_image_bytes, red_image_bytes):
        # one bit per pixel (not one byte), unclear on grayscale support
        width = (EPD_WIDTH / 8 ) if (EPD_WIDTH % 8 == 0) else (EPD_WIDTH / 8 + 1)
        width = int(width)
        height = EPD_HEIGHT;
        self.set_windows(0, 0, EPD_WIDTH, EPD_HEIGHT)
        # for loop black
        print('DEBUG write black')
        if not isinstance(black_image_bytes[0], int):
            def process_pixel(x):
                return ord(x)
        else:
            def process_pixel(x):
                return x  # NOOP
        addr = 0
        for j in range(height):
            self.epd_set_cursor(0, j)
            self.send_command(WRITE_RAM)
            for i in range(width):
                #addr = (i * width) + j
                addr = i + (j * width)
                #addr = i + j * width
                #addr = i + (height - j - 1) * width  # flip
                #print('%r' % addr)
                #print('\t%r' % black_image_bytes[addr])
                self.send_data(process_pixel(black_image_bytes[addr]))

        # for loop red
        print('DEBUG write red')
        if not isinstance(red_image_bytes[0], int):
            def process_pixel(x):
                return ord(x)
        else:
            def process_pixel(x):
                return x  # NOOP
        addr = 0
        for j in range(height):
            self.epd_set_cursor(0, j)
            self.send_command(WRITE_RAM_RED)
            for i in range(width):
                addr = i + (j * width)
                #addr = i + (height - j - 1) * width  # flip
                self.send_data(process_pixel(red_image_bytes[addr]))
        print('DEBUG done write red')
        self.turn_on_display()

    def sleep(self):
        self.send_command(DEEP_SLEEP_MODE)
        self.send_data(0x01)

    def reset(self):
        self.digital_write(RST_PIN, 1)
        delay_ms(200)
        self.digital_write(RST_PIN, 0)
        delay_ms(200)
        self.digital_write(RST_PIN, 1)
        delay_ms(200)

    def init(self):
        self.reset()

        self.send_command(0x74)
        self.send_data(0x54)
        self.send_command(0x7E)
        self.send_data(0x3B)
        self.send_command(0x2B)   #  Reduce glitch under ACVCOM  
        self.send_data(0x04)           
        self.send_data(0x63)
            
        self.send_command(0x0C)   #  Soft start setting
        self.send_data(0x8E)           
        self.send_data(0x8C)
        self.send_data(0x85)
        self.send_data(0x3F)    


        self.send_command(DRIVER_OUTPUT_CONTROL)   #  Driver Output control  Set MUX as 300
        self.send_data(0x2B)           
        self.send_data(0x01)
        self.send_data(0x00)  
        self.send_command(DATA_ENTRY_MODE_SETTING)   #  Data Entry mode setting
        self.send_data(0x03)  # 8.3 Data Entry Mode Setting (11h), top row, left to right, then 2nd row, ....
        self.send_command(SET_RAM_X_ADDRESS_START_END_POSITION)  # Set RAM X - address Start / End position
        self.send_data(0x00)  #  RAM x address start at 0
        self.send_data(0x31)  # RAM x address end at 31h(49+1)*8->400
        self.send_command(SET_RAM_Y_ADDRESS_START_END_POSITION)  # Set Ram Y- address Start / End position
        self.send_data(0x2B)  #  RAM y address start at  12Bh  
        self.send_data(0x01)
        self.send_data(0x00)  #  RAM y address end at 00h
        self.send_data(0x00)      
            
        self.send_command(BORDER_WAVEFORM_CONTROL)  #  Border Waveform Control
        self.send_data(0x01)  #  HIZ

        self.send_command(DISPLAY_UPDATE_CONTROL_1)
        self.send_data(0x80) # Inverse RED RAM content

                
        self.send_command(0x18) # Temperature Sensor Control
        self.send_data(0x80)   # Internal temperature sensor
        self.send_command(DISPLAY_UPDATE_CONTROL_2) # Display UpdateControl 2
        self.send_data(0xB1)  # Load Temperature and waveform setting.
        self.send_command(MASTER_ACTIVATION)  # Master Activation
        self.epd_wait_until_idle()

    def close(self):
        if self.is_open:
            # need to reset GPIO?
            self.spi.close()
            self.is_open = False

    def __del__(self):
        self.close()



def main(argv=None):
    if argv is None:
        argv = sys.argv

    print('Python %s on %s' % (sys.version, sys.platform))
    #import pdb ; pdb.set_trace()

    Image = None  # DEBUG disable image support, demo will be to clear and sleep
    # TODO bit plane slice color into B and R
    if Image:
        image_path = os.path.dirname(__file__)
        image_path = os.path.join(image_path, '..', 'wiringpi', 'pic')


        black_image_path = os.path.join(image_path, '042-1rb1.bmp')
        red_image_path = os.path.join(image_path, '042-1rr1.bmp')

        black_image = Image.open(black_image_path)
        black_image = black_image.convert('1')  # 1bpp - ensure we have a black and white (TODO gray scale support in hardware?) ## TODO dithering options
        assert black_image.size == (400, 300)

        red_image = Image.open(red_image_path)
        red_image = red_image.convert('1')  # 1bpp - ensure we have a black and white (TODO gray scale support in hardware?) ## TODO dithering options
        assert red_image.size == (400, 300)

        """
        ### DEBUG - raw file
        f = open('debug_black.bin', 'rb')
        raw_bytes = f.read()  # expecting 120000
        f.close()
        assert len(raw_bytes) == 400 * 300
        black_image = Image.frombytes('L', (400, 300), raw_bytes)
        assert black_image.size == (400, 300)
        f = open('debug_red.bin', 'rb')
        raw_bytes = f.read()  # expecting 120000
        f.close()
        assert len(raw_bytes) == 400 * 300
        red_image = Image.frombytes('L', (400, 300), raw_bytes)
        assert red_image.size == (400, 300)
        """


    epd = Epd()

    try:
        epd.epd_clear()

        if Image:
            epd.epd_display(black_image.tobytes(), red_image.tobytes())
            print('image now displaying, sleeping for 30 secs')
            delay_ms(30 * 1000)
    finally:
        epd.sleep()
        epd.close()


    return 0


if __name__ == "__main__":
    sys.exit(main())
