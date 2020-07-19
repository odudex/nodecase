#! /usr/bin/python
# -*- coding: utf-8 -*-

import RPi.GPIO as gpio
from gpiozero import CPUTemperature
import time
import os
import argparse
import logging
import daemon
from daemon import pidfile

# Used GPIOs
GPIOpower = 26      # GPIO connected to power monitor
GPIOfan = 16        # GPIO connected fan MOSFET switch

# General definitions
debug = False
sample_period = 30 #period(seconds) in which status is verified

# Power monitor definitions
power_monitor = True
no_power_timeout = 120 #Time(seconds) monitor waits before shutdown

# Temperature control definitions
control_temperature = True
trigger_temp = 65       #if off, fan will not start before it reaches this temperature
off_temp = 45          #if on, fan will not stop before it reaches this temperature
fan_full_power = 100    #fan power if temperature is over 'trigger_temp'
fan_cruise_power = 50  #fan power if temperature is between 'trigger_temp' and 'off_temp'
#Setup
cooling = True
gpio.setmode(gpio.BCM)
gpio.setup(GPIOpower, gpio.IN, pull_up_down=gpio.PUD_DOWN)
gpio.setup(GPIOfan, gpio.OUT)
fanPWM = gpio.PWM(GPIOfan,100) #100Hz

def mainloop(logf):
    global cooling
    logger = logging.getLogger('hw_daemon')
    logger.setLevel(logging.INFO)
    fh = logging.FileHandler(logf)
    fh.setLevel(logging.INFO)
    formatstr = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    formatter = logging.Formatter(formatstr)
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    power_counter = no_power_timeout/sample_period
    fanPWM.start(100) #starts at 100% duty cycle(power)
    while True:
        time.sleep(sample_period)
        message = ""
        if power_monitor:
            if gpio.input(GPIOpower):
                message += "Power ok\n"
                power_counter = no_power_timeout/sample_period
            else:
                power_counter -= 1
                if not power_counter:
                    message += "Shutting down\n"
                    os.system("cd /home/admin && XXshutdown.sh")
                else:
                    message += 'Power lost! Shutting down in '
                    message += str(power_counter*sample_period)
                    message += ' seconds\n'

        if control_temperature: #todo - test new control without pwm
            cpu = CPUTemperature()
            temperature = int(cpu.temperature)
            message += str(temperature)
            message += "C"
            if cooling:
                if temperature > trigger_temp:
                    fanPWM.ChangeDutyCycle(fan_full_power)
                elif temperature > off_temp:
                    fanPWM.ChangeDutyCycle(fan_cruise_power)
                else:
                    fanPWM.stop()
                    cooling = False
                message += " Cooling"
            else:
                if temperature > trigger_temp:
                    fanPWM.start(fan_full_power)
                    cooling = True
                message += " Fan off"
        if debug:
            logger.info(message)
            

def start_daemon(pidf, logf):
    ### This launches the daemon in its context

    ### XXX pidfile is a context
    with daemon.DaemonContext(
        working_directory='/var/lib/hw_daemon',
        umask=0o002,
            pidfile=pidfile.TimeoutPIDLockFile(pidf)) as context:
        mainloop(logf)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Power and fan monitor daemon")
    parser.add_argument('-p', '--pid-file', default='/var/run/hw_daemon.pid')
    parser.add_argument('-l', '--log-file', default='/var/log/hw_daemon.log')
    args = parser.parse_args()
    start_daemon(pidf=args.pid_file, logf=args.log_file)
