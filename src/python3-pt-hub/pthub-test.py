import pthub
from time import sleep

pthub.initialise()

while True:
	pthub.increment_brightness()
	pthub.communicate()
	sleep(0.25)