/***************************************************
//Web: http://www.buydisplay.com
EastRising Technology Co.,LTD
****************************************************/
#include "ER-EPD042A1-1.h"
#include "Debug.h"


/******************************************************************************
function :	Software reset
parameter:
******************************************************************************/
static void EPD_Reset(void)
{
    DEV_Digital_Write(EPD_RST_PIN, 1);
    DEV_Delay_ms(200);
    DEV_Digital_Write(EPD_RST_PIN, 0);
    DEV_Delay_ms(200);
    DEV_Digital_Write(EPD_RST_PIN, 1);
    DEV_Delay_ms(200);
}


/******************************************************************************
function :	send command
parameter:
     Reg : Command register
******************************************************************************/
static void EPD_SendCommand(UBYTE Reg)
{
    DEV_Digital_Write(EPD_DC_PIN, 0);
    DEV_Digital_Write(EPD_CS_PIN, 0);
    DEV_SPI_WriteByte(Reg);
    DEV_Digital_Write(EPD_CS_PIN, 1);
}

/******************************************************************************
function :	send data
parameter:
    Data : Write data
******************************************************************************/
static void EPD_SendData(UBYTE Data)
{
    DEV_Digital_Write(EPD_DC_PIN, 1);
    DEV_Digital_Write(EPD_CS_PIN, 0);
    DEV_SPI_WriteByte(Data);
    DEV_Digital_Write(EPD_CS_PIN, 1);
}

/******************************************************************************
function :	Wait until the busy_pin goes LOW
parameter:
******************************************************************************/
void EPD_WaitUntilIdle(void)
{
    Debug("e-Paper busy\r\n");
    while(DEV_Digital_Read(EPD_BUSY_PIN) == 1) {      //LOW: idle, HIGH: busy
        DEV_Delay_ms(100);
    }
    Debug("e-Paper busy release\r\n");
}

/******************************************************************************
function :	Setting the display window
parameter:
******************************************************************************/
static void EPD_SetWindows(UWORD Xstart, UWORD Ystart, UWORD Xend, UWORD Yend)
{
    EPD_SendCommand(SET_RAM_X_ADDRESS_START_END_POSITION);
    EPD_SendData((Xstart >> 3) & 0xFF);
    EPD_SendData((Xend >> 3) & 0xFF);

    EPD_SendCommand(SET_RAM_Y_ADDRESS_START_END_POSITION);
    EPD_SendData(Ystart & 0xFF);
    EPD_SendData((Ystart >> 8) & 0xFF);
    EPD_SendData(Yend & 0xFF);
    EPD_SendData((Yend >> 8) & 0xFF);
}

/******************************************************************************
function :	Set Cursor
parameter:
******************************************************************************/
static void EPD_SetCursor(UWORD Xstart, UWORD Ystart)
{
    EPD_SendCommand(SET_RAM_X_ADDRESS_COUNTER);
    EPD_SendData((Xstart >> 3) & 0xFF);

    EPD_SendCommand(SET_RAM_Y_ADDRESS_COUNTER);
    EPD_SendData(Ystart & 0xFF);
    EPD_SendData((Ystart >> 8) & 0xFF);

}

/******************************************************************************
function :	Turn On Display
parameter:
******************************************************************************/
static void EPD_TurnOnDisplay(void)
{
    EPD_SendCommand(DISPLAY_UPDATE_CONTROL_2);
    EPD_SendData(0xC7);
    EPD_SendCommand(MASTER_ACTIVATION);


    EPD_WaitUntilIdle();
}




/******************************************************************************
function :	Initialize the e-Paper register
parameter:
******************************************************************************/
UBYTE EPD_Init(void)
{
    EPD_Reset();
   

    EPD_SendCommand(0x74);
    EPD_SendData(0x54);
    EPD_SendCommand(0x7E);
    EPD_SendData(0x3B);
    EPD_SendCommand(0x2B);  // Reduce glitch under ACVCOM	
    EPD_SendData(0x04);           
    EPD_SendData(0x63);
        
    EPD_SendCommand(0x0C);  // Soft start setting
    EPD_SendData(0x8E);           
    EPD_SendData(0x8C);
    EPD_SendData(0x85);
    EPD_SendData(0x3F);    


    EPD_SendCommand(DRIVER_OUTPUT_CONTROL);  // Driver Output control  Set MUX as 300
    EPD_SendData(0x2B);           
    EPD_SendData(0x01);
    EPD_SendData(0x00);  
    EPD_SendCommand(DATA_ENTRY_MODE_SETTING);  // Data Entry mode setting
    EPD_SendData(0x03);         
    EPD_SendCommand(SET_RAM_X_ADDRESS_START_END_POSITION); //Set RAM X - address Start / End position
    EPD_SendData(0x00); // RAM x address start at 0
    EPD_SendData(0x31); //RAM x address end at 31h(49+1)*8->400
    EPD_SendCommand(SET_RAM_Y_ADDRESS_START_END_POSITION); //Set Ram Y- address Start / End position
    EPD_SendData(0x2B); // RAM y address start at  12Bh  
    EPD_SendData(0x01);
    EPD_SendData(0x00); // RAM y address end at 00h;
    EPD_SendData(0x00);      
        
    EPD_SendCommand(BORDER_WAVEFORM_CONTROL); // Border Waveform Control
    EPD_SendData(0x01); // HIZ

    EPD_SendCommand(DISPLAY_UPDATE_CONTROL_1);
    EPD_SendData(0x80);//Inverse RED RAM content

        	
    EPD_SendCommand(0x18);//Temperature Sensor Control
    EPD_SendData(0x80);  //Internal temperature sensor
    EPD_SendCommand(DISPLAY_UPDATE_CONTROL_2);//Display UpdateControl 2
    EPD_SendData(0xB1);	//Load Temperature and waveform setting.
    EPD_SendCommand(MASTER_ACTIVATION); //Master Activation
    EPD_WaitUntilIdle();
	       		    
    return 0;
}

/******************************************************************************
function :	Clear screen
parameter:
******************************************************************************/
void EPD_Clear(void)
{
    UWORD Width, Height,j,i;
    Width = (EPD_WIDTH % 8 == 0)? (EPD_WIDTH / 8 ): (EPD_WIDTH / 8 + 1);
    Height = EPD_HEIGHT;
    EPD_SetWindows(0, 0, EPD_WIDTH, EPD_HEIGHT);
  
  for (j = 0; j < Height; j++) {
        EPD_SetCursor(0, j);
        EPD_SendCommand(WRITE_RAM);
        for (i = 0; i < Width; i++) {
            EPD_SendData(0XFF);
        }
    }

  for (j = 0; j < Height; j++) {
        EPD_SetCursor(0, j);
        EPD_SendCommand(WRITE_RAM_RED);
        for (i = 0; i < Width; i++) {
            EPD_SendData(0XFF);
        }
    }

    EPD_TurnOnDisplay();
}

/******************************************************************************
function :	Sends the image buffer in RAM to e-Paper and displays
parameter:
******************************************************************************/
void EPD_Display(const UBYTE *blackimage, const UBYTE *redimage)
{
    UWORD Width, Height,j,i;
    Width = (EPD_WIDTH % 8 == 0)? (EPD_WIDTH / 8 ): (EPD_WIDTH / 8 + 1);
    Height = EPD_HEIGHT;

    UDOUBLE Addr = 0;
    // UDOUBLE Offset = ImageName;
    EPD_SetWindows(0, 0, EPD_WIDTH, EPD_HEIGHT);
    for (j = 0; j < Height; j++) {
        EPD_SetCursor(0, j);
        EPD_SendCommand(WRITE_RAM);
        for (i = 0; i < Width; i++) {
            Addr = i + j * Width;
            EPD_SendData(blackimage[Addr]);
        }
    }

    for (j = 0; j < Height; j++) {
        EPD_SetCursor(0, j);
        EPD_SendCommand(WRITE_RAM_RED);
        for (i = 0; i < Width; i++) {
            Addr = i + j * Width;
            EPD_SendData(redimage[Addr]);
        }
    }

    EPD_TurnOnDisplay();
}

/******************************************************************************
function :	Enter sleep mode
parameter:
******************************************************************************/
void EPD_Sleep(void)
{
    EPD_SendCommand(DEEP_SLEEP_MODE);
    EPD_SendData(0x01);
   
}