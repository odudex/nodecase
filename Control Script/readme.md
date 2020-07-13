Small python3 script to monitor Raspiblitz's power input and control a fan using RPi GPIO

If power is off during X secods, it shuts down RPi.
The temperature is PWM controlled acording to specified parameters.

Dependencies that are not in Raspiblitz: python-daemon.

sudo pip3 install python-daemon
