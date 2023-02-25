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

    sudo `which pythoni` epd.py

Note on Raspberry Pi Zero takes about 30 secs to init, clear, and sleep.
"""

import os
import sys
import time

import spidev  # https://github.com/doceme/py-spidev
import RPi.GPIO as gpio  # https://pypi.org/project/RPi.GPIO/  FIXME replace! Check out https://github.com/c0t088/libregpio


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
DATA_ENTRY_MODE_SETTING = 0x11
BORDER_WAVEFORM_CONTROL = 0x3C
DISPLAY_UPDATE_CONTROL_1 = 0x21



def digital_write(pin, value):
    # needs GPIO - want something portable
    gpio.output(pin, value)

def digital_read(pin):
    return gpio.input(pin)

def spi_writebyte(data):
    spi.writebytes([data])

def epd_send_command(command):
    digital_write(DC_PIN, 0)
    digital_write(CS_PIN, 0)
    spi_writebyte(command)
    digital_write(CS_PIN, 1)

def epd_send_data(data):
    digital_write(DC_PIN, 1)
    digital_write(CS_PIN, 0)
    spi_writebyte(data)
    digital_write(CS_PIN, 1)

def delay_ms(delaytime):
    time.sleep(delaytime / 1000.0)

def epd_wait_until_idle():
    while(digital_read(BUSY_PIN) == 1):      #  0/LOW: idle, 1/HIGH: busy
        delay_ms(100)

def epd_turn_on_display():
    epd_send_command(DISPLAY_UPDATE_CONTROL_2)
    epd_send_data(0xC7)
    epd_send_command(MASTER_ACTIVATION)
    epd_wait_until_idle()
    
def epd_set_windows(x_start, y_start, x_end, y_end):
    epd_send_command(SET_RAM_X_ADDRESS_START_END_POSITION)
    epd_send_data((x_start >> 3) & 0xFF)
    epd_send_data((x_end >> 3) & 0xFF)

    epd_send_command(SET_RAM_Y_ADDRESS_START_END_POSITION)
    epd_send_data(y_start & 0xFF)
    epd_send_data((y_start >> 8) & 0xFF)
    epd_send_data(y_end & 0xFF)
    epd_send_data((y_end >> 8) & 0xFF)

def epd_set_cursor(x_start, y_start):
    epd_send_command(SET_RAM_X_ADDRESS_COUNTER)
    epd_send_data((x_start >> 3) & 0xFF)

    epd_send_command(SET_RAM_Y_ADDRESS_COUNTER)
    epd_send_data(y_start & 0xFF)
    epd_send_data((y_start >> 8) & 0xFF)

def epd_clear():
    #width = (EPD_WIDTH % 8 == 0)? (EPD_WIDTH / 8 ): (EPD_WIDTH / 8 + 1);
    width = (EPD_WIDTH / 8 ) if (EPD_WIDTH % 8 == 0) else (EPD_WIDTH / 8 + 1)
    width = int(width)
    height = EPD_HEIGHT;
    epd_set_windows(0, 0, EPD_WIDTH, EPD_HEIGHT)
    # for loop black
    for j in range(height):
        epd_set_cursor(0, j)
        epd_send_command(WRITE_RAM)
        for i in range(width):
            epd_send_data(0XFF)

    # for loop red
    for j in range(height):
        epd_set_cursor(0, j)
        epd_send_command(WRITE_RAM_RED)
        for i in range(width):
            epd_send_data(0XFF)
    epd_turn_on_display()

def epd_sleep():
    epd_send_command(DEEP_SLEEP_MODE)
    epd_send_data(0x01)

def epd_reset():
    digital_write(RST_PIN, 1)
    delay_ms(200)
    digital_write(RST_PIN, 0)
    delay_ms(200)
    digital_write(RST_PIN, 1)
    delay_ms(200)

def epd_init():
    epd_reset()

    epd_send_command(0x74)
    epd_send_data(0x54)
    epd_send_command(0x7E)
    epd_send_data(0x3B)
    epd_send_command(0x2B)   #  Reduce glitch under ACVCOM  
    epd_send_data(0x04)           
    epd_send_data(0x63)
        
    epd_send_command(0x0C)   #  Soft start setting
    epd_send_data(0x8E)           
    epd_send_data(0x8C)
    epd_send_data(0x85)
    epd_send_data(0x3F)    


    epd_send_command(DRIVER_OUTPUT_CONTROL)   #  Driver Output control  Set MUX as 300
    epd_send_data(0x2B)           
    epd_send_data(0x01)
    epd_send_data(0x00)  
    epd_send_command(DATA_ENTRY_MODE_SETTING)   #  Data Entry mode setting
    epd_send_data(0x03)         
    epd_send_command(SET_RAM_X_ADDRESS_START_END_POSITION)  # Set RAM X - address Start / End position
    epd_send_data(0x00)  #  RAM x address start at 0
    epd_send_data(0x31)  # RAM x address end at 31h(49+1)*8->400
    epd_send_command(SET_RAM_Y_ADDRESS_START_END_POSITION)  # Set Ram Y- address Start / End position
    epd_send_data(0x2B)  #  RAM y address start at  12Bh  
    epd_send_data(0x01)
    epd_send_data(0x00)  #  RAM y address end at 00h
    epd_send_data(0x00)      
        
    epd_send_command(BORDER_WAVEFORM_CONTROL)  #  Border Waveform Control
    epd_send_data(0x01)  #  HIZ

    epd_send_command(DISPLAY_UPDATE_CONTROL_1)
    epd_send_data(0x80) # Inverse RED RAM content

            
    epd_send_command(0x18) # Temperature Sensor Control
    epd_send_data(0x80)   # Internal temperature sensor
    epd_send_command(DISPLAY_UPDATE_CONTROL_2) # Display UpdateControl 2
    epd_send_data(0xB1)  # Load Temperature and waveform setting.
    epd_send_command(MASTER_ACTIVATION)  # Master Activation
    epd_wait_until_idle()

def epd_connect(bus=0, device=0)
    # bus, device = 0, 0  # /dev/spidev<bus>.<device>
    spi = spidev.SpiDev()
    spi.open(bus, device)

    # init GPIO
    gpio.setmode(gpio.BCM)
    gpio.setwarnings(False)
    gpio.setup(RST_PIN, gpio.OUT)
    gpio.setup(DC_PIN, gpio.OUT)
    gpio.setup(CS_PIN, gpio.OUT)
    gpio.setup(BUSY_PIN, gpio.IN)

    spi.max_speed_hz = 32000000  # is this 32Mhz? units are not documented in wiringpim struct implies this is hz
    spi.mode = 0b00


def main(argv=None):
    if argv is None:
        argv = sys.argv

    #import pdb ; pdb.set_trace()

    epd_connect()

    epd_init()
    epd_clear()
    epd_sleep()

    # need to reset GPIO?
    spi.close()

    return 0


if __name__ == "__main__":
    sys.exit(main())
