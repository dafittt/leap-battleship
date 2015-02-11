/*
 Copyright (C) 2011 J. Coliz <maniacbug@ymail.com>

 This program is free software; you can redistribute it and/or
 modify it under the terms of the GNU General Public License
 version 2 as published by the Free Software Foundation.
 */

/**
 * Example RF Radio Ping Pair
 *
 * This is an example of how to use the RF24 class.  Write this sketch to two different nodes,
 * connect the role_pin to ground on one.  The ping node sends the current time to the pong node,
 * which responds by sending the value back.  The ping node can then see how long the whole cycle
 * took.
 */

#include <SPI.h>
#include "nRF24L01.h"
#include "RF24.h"
#include "printf.h"

RF24 radio(9,10);
const int role_pin = 7;
const int debug = 6;
const uint64_t pipes[2] = { 0xF0F0F0F0E1LL, 0xF0F0F0F0D2LL };
typedef enum { role_ping_out = 1, role_pong_back } role_e;

// The debug-friendly names of those roles
const char* role_friendly_name[] = { "invalid", "Ping out", "Pong back"};

// The role of the current running sketch
role_e role;
void setup(void)
{
  pinMode(debug, OUTPUT);
  pinMode(6, OUTPUT);
  digitalWrite(debug, LOW);
  pinMode(role_pin, INPUT);
  digitalWrite(role_pin,HIGH);
  delay(20); // Just to get a solid reading on the role pin

  // read the address pin, establish our role
  if ( ! digitalRead(role_pin) )
    role = role_ping_out;
  else
    role = role_pong_back;
  Serial.begin(57600);
  printf_begin();

  radio.begin();

  radio.setRetries(15,15);

  radio.setPayloadSize(sizeof(char));

  if ( role == role_ping_out )
  {
    radio.openWritingPipe(pipes[0]);
    radio.openReadingPipe(1,pipes[1]);
  }
  else
  {
    radio.openWritingPipe(pipes[1]);
    radio.openReadingPipe(1,pipes[0]);
  }
  radio.startListening();
  radio.printDetails();
}

void loop(void)
{
  if (role == role_ping_out && Serial.available())
  {
    // First, stop listening so we can talk.
    radio.stopListening();
    
    // Take the time, and send it.  This will block until complete
    char time = (char)Serial.read();
    if(time == 'b'){
      time = (int)10;
      radio.write( &time, sizeof(char) );
      radio.startListening();
      delay(250);
      radio.stopListening();
      time = (int)0;
      radio.write( &time, sizeof(char) );
    }else{
    if(time == '0')
      time = (int)time - 48;
    else
      time = (int)time - 47;
    bool ok = radio.write( &time, sizeof(char) );
    }
    radio.startListening();
  }
  if ( role == role_pong_back )
  {
    // if there is data ready
    if ( radio.available() )
    {
      // Dump the payloads until we've gotten everything
      char got_time;
      bool done = false;
      while (!done)
      {
        // Fetch the payload, and see if this was the last one.
        done = radio.read( &got_time, sizeof(unsigned long) );
	delay(20);
      }
      analogWrite(6, got_time*25);
    }
  }
}
// vim:cin:ai:sts=2 sw=2 ft=cpp
