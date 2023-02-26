# eink_ssd1619_er-epm042-1

Sample code and docs for eink/epaper ER-EPM042-1R EastRising SSD1619 used on ER-EPM042A1-1R white, black, and Red 4.2" inch e-Ink Display Module 400x300

Hardware available from https://www.buydisplay.com/red-4-2-inch-e-ink-display-module-400x300-for-arduino-raspberry-pi

Contains pure Python (3 and 2.7) library and sample/demo to load/display any image.
Also contains original sample C code for Raspberry Pi using either bcm2835 or wiringpi over SPI (Raspberry Pi Library and Example for 4-wire SPI from https://www.buydisplay.com/red-4-2-inch-e-ink-display-module-400x300-for-arduino-raspberry-pi).

Differences in this repo to original tutorial zip:

  * Rename `ER-EPD(M)042A1-1_Raspberry_Pi_Tutorial` directory to `ER-EPM042-1_Raspberry_Pi`
  * Rename `Library-Example_ER-EPD(M)042A1-1B` directory to `ER-EPM042A1-1B`
  * Rename `Library-Example_ER-EPD(M)042A1-1R` directory to `ER-EPM042A1-1R`

Contains samples for Black and White board ER-EPM042A1-1B and Red, Black and White board ER-EPM042A1-1R. BW code can be ran against Red board.
Samples for:

  * bcm https://www.airspayce.com/mikem/bcm2835/
  * wiringpi https://github.com/WiringPi/WiringPi

Directories:

  * [ER-EPM042-1_Raspberry_Pi/ER-EPM042A1-1B](ER-EPM042-1_Raspberry_Pi/ER-EPM042A1-1B) Black and White only
  * [ER-EPM042-1_Raspberry_Pi/ER-EPM042A1-1R](ER-EPM042-1_Raspberry_Pi/ER-EPM042A1-1R) Red, Black and White

## Raspberry pi SPI notes

https://pimylifeup.com/raspberry-pi-spi/


Enable via:

    sudo raspi-config  # enable SPI

Sanity checks:

    ls /dev/*spi*

    pi@pizero:~ $ cat /boot/config.txt|grep -i spi
    #dtparam=spi=on

    pi@pizero:~/ $ cat /boot/config.txt|grep -i spi
    dtparam=spi=on

    pi@pizero:~ $ lsmod | grep spi
    pi@pizero:~ $

    pi@pizero:~/ $ lsmod | grep spi
    spidev                 20480  0
    spi_bcm2835            20480  0

## Building and running

Assuming build dependency installed, issue `make` in sample directory. Both samples create an `epd` binary.

The sample has very little error checking and will crash if:

  * not ran in the current directory (i.e. calling with absolute path leads to crashes when attempting to load images/bitmaps)
  * when not ran as root for bcm demo (wiringpi can run as regular user)

I.e.

    cd ER-EPM042-1_Raspberry_Pi/ER-EPM042A1-1R/bcm2835 ; make ; sudo ./epd
    cd ../../..
    cd ER-EPM042-1_Raspberry_Pi/ER-EPM042A1-1R/wiringpi ; make ; ./epd
    cd ../../..
    cd ER-EPM042-1_Raspberry_Pi/ER-EPM042A1-1R/python ; time sudo `which python3` epd.py   # clear screen, (load images) then enter sleep mode
    cd ER-EPM042-1_Raspberry_Pi/ER-EPM042A1-1R/python ; time sudo `which python3` display_image.py FILENAME  # load image and display it, any format supported by Python Pillow/PIL

