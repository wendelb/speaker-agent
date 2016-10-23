import logging
import os
from threading import Lock

class SpeakerActor(object):
    """
    Handles the speaker-lock and turns them on if a device/program wants to use
    them. Speakers are turned off again, if there is no-one left to use them.

    This is a Singleton class. Do not instantiate this yourself!
    """

    def __init__(self):
        self.devices = set()
        self.lock = Lock()
        self.speakerStatus = False
        self.logger = logging.getLogger('SpeakerAgent.SpeakerActor')

    def addDevice(self, name):
        """Call this to set a lock for (name) and turn the speakers on if necessary"""
        self.lock.acquire()
        try:
            self.devices.add(name)
            self.logger.info('Adding device %s' % name)
            self._handle_speaker()
        finally:
            self.lock.release()

    def removeDevice(self, name):
        """Call this to release the previously set lock for (name) and turn the speakers off if necessary"""
        self.lock.acquire()
        try:
            self.logger.info('Removing device %s' %name)
            if (name in self.devices):
                self.devices.remove(name)
            self._handle_speaker()
        finally:
            self.lock.release()

    def _handle_speaker(self):
        if (self.devices == set()):
            if (self.speakerStatus == True):
                # Speakers are on, but no-one is using them -> turning off
                self.logger.info('Turning off speakers')
                os.system('gpio write 2 1')
                self.speakerStatus = False
        else:
            if (self.speakerStatus == False):
                self.logger.info('Turning on speakers')
                self.logger.info('Currently connected devices: %s' % self.devices)
                os.system('gpio write 2 0')
                self.speakerStatus = True
            else:
                # Es kam ein Gerät dazu
                self.logger.info('Currently connected devices: %s' % self.devices)


# Instantiating the class
Speakers = SpeakerActor()
