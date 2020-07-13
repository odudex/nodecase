#! /usr/bin/python
# -*- coding: utf-8 -*-

import RPi.GPIO as gpio
from gpiozero import CPUTemperature
import time
import os
import daemon

#Used GPIOs
GPIOpower = 26      #GPIO connected to power monitor
GPIOfan = 16        #GPIO connected fan MOSFET switch

#General definitions
debug = True
sample_period = 1 #period(seconds) in which status is verified

#Power monitor definitions
power_monitor = True
no_power_timeout = 10 #Time(seconds) monitor waits before shutdown

#Temperature control definitions
control_temperature = True
trigger_temp = 65       #if off, fan will not start before it reaches this temperature
off_temp  = 45          #if on, fan will not stop before it reaches this temperature
fan_full_power = 100    #fan power if temperature is over 'trigger_temp'
fan_cruise_power = 100  #fan power if temperature is between 'trigger_temp' and 'off_temp'

#Setup
power_counter = no_power_timeout/sample_period
cooling = True
gpio.setmode(gpio.BCM)
gpio.setup(GPIOpower, gpio.IN, pull_up_down = gpio.PUD_DOWN)
gpio.setup(GPIOfan, gpio.OUT)
fanPWM = gpio.PWM(GPIOfan,1000) #1KHz
fanPWM.start(100) #starts at 100% duty cycle(power)

def mainloop():
    global cooling
    while True:
        time.sleep(sample_period)
        if power_monitor:
            if gpio.input(GPIOpower):
                print('Power ok')
                power_counter = no_power_timeout/sample_period
            else:
                power_counter -= 1
                if not power_counter:
                    print('Shutting down')
                    os.system("cd /home/admin && XXshutdown.sh")
                else:
                    message = 'Power lost! Shutting down in '
                    message +=str(power_counter*sample_rate)
                    message += 'seconds'
                    print(message)

        if control_temperature:
            cpu = CPUTemperature()
            temperature = int(cpu.temperature)
            print(temperature)
            if cooling:
                if temperature > trigger_temp:
                    fanPWM.ChangeDutyCycle(fan_full_power)
                elif temperature > off_temp:
                    fanPWM.ChangeDutyCycle(fan_cruise_power)
                else:
                    fanPWM.ChangeDutyCycle(0)
                    cooling = False
            elif temperature > trigger_temp:
                fanPWM.ChangeDutyCycle(fan_full_power)
                cooling = True
if debug:
    mainloop()
else:
    with daemon.DaemonContext():
        mainloop()
            
gpio.cleanup()
exit()
