/*
 * poweroff.c
 *
 * turn the power of the pi-top hub off
 *
 * IMPORTANT WARNING: to not execute except at the end of the shutdown process
 * otherwise your sd card might get corrupted
 * 
 * Copyright 2016  rricharz
 * 
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2 of the License, or
 * (at your option) any later version.
 * 
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 * 
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software
 * Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
 * MA 02110-1301, USA.
 * 
 * 
 */


#include <stdio.h>
#include <unistd.h>
#include <string.h>
#include <wiringPiSPI.h>

#define MAXCOUNT 10     // maximum number of spi transfer attemps

#define LIDBITMASK      0x04
#define SCREENOFFMASK   0x02
#define PARITYMASK      0x80
#define BRIGHTNESSMASK  0x78
#define SHUTDOWNMASK    0X01

int lidbit;
int screenoffbit;
int parity;
int brightness;
int shutdown;

//////////////////////////////
int parity7(unsigned char data)
//////////////////////////////
{
    int i;
    int p = 0;
    for (i = 0; i < 7; i++) {
        if (data & 1) p = !p;
        data = data >> 1;
    }
    return p;
}

///////////////////////////////
int analyze(unsigned char data)
///////////////////////////////
{
    lidbit          = (data & LIDBITMASK) != 0;
    screenoffbit    = (data & SCREENOFFMASK) != 0;
    parity          = (data & PARITYMASK) != 0;
    brightness      = (data & BRIGHTNESSMASK) >> 3;
    shutdown        = (data & SHUTDOWNMASK) != 0;
    
    // printf("lid = %d, screen = %d, parity = %d, shutdown = %d, brightness = %d\n", lidbit, screenoffbit, parity, shutdown, brightness);
    
    return (parity7(data) == parity);
}

///////////////
int calculate()
///////////////
{
    int data = brightness << 3;
    if (parity7(brightness))
        data += PARITYMASK;
    if (shutdown)
        data += SHUTDOWNMASK;
    if (screenoffbit)
        data += SCREENOFFMASK;
    if (parity7(data & 3))
        data += LIDBITMASK;     // parity of the two state bits
    return data;        
}

///////////////////////////////
int main(int argc, char **argv)
///////////////////////////////
{
    unsigned char data, new_data;
    int count, ok;
    
    printf("Pi-top poweroff version 1.1 rr\n");
    sleep(5);   // let other processes finish
    
    int spi = wiringPiSPISetup(1, 9600);
    if (spi < 0) {
      printf("Cannot initialize spi driver\n");
      return 1;
    }
     
    // printf("spi handle = %d\n", spi);
    
    // send 0xFF and receive current status of pi-top-hub
    count = 0;
    data = 0xff;
    printf("Sending: 0x%X\n", data);
    do {
        data = 0xff;
        ok = wiringPiSPIDataRW(1, &data, 1);
        if (ok) {
            ok &= analyze(data);
        }
    }
    while ((!ok) && (count++ < MAXCOUNT));
    
    if (ok) {
        printf("Receiving: 0x%X\n", data);
        printf("Current brightness = %d\n", brightness);
        
        // check whether current brightness s within acceptable range
        if (brightness > 10)
            brightness = 10;
        if (brightness < 3)
            brightness = 3;
        
        // calculate data to send
        shutdown = 1;
        screenoffbit = 0;       
        new_data = calculate();
        
        // send new data twice
        data = new_data;
        printf("Sending: 0x%X\n", data);
        wiringPiSPIDataRW(1, &data, 1);
        data = new_data;
        wiringPiSPIDataRW(1, &data, 1);
    }
    else
      printf("reading current brightness not successful\n");
    return 0;
}
