import logging
import os
from threading import Lock

class SpeakerActor(object):
    """
    Schaltet den Lautsprecher an, wenn ein Gerät diesen verwenden möchte, und schaltet diesen wieder aus, wenn keiner mehr zugreifen möchte
    Diese Klasse ist als Singleton zu betrachten!
    """
    def __init__(self):
        self.devices = set()
        self.lock = Lock()
        self.speakerStatus = False
        self.logger = logging.getLogger('SpeakerAgent.SpeakerActor')

    def addDevice(self, name):
        self.lock.acquire()
        try:
            self.devices.add(name)
            self.logger.info('Adding device %s' % name)
            self._handle_speaker()
        finally:
            self.lock.release()

    def removeDevice(self, name):
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
                # Speaker sind an, können aber ausgeschalten werden
                self.logger.info('Turning off speakers')
                os.system('gpio write 2 1')
                self.speakerStatus = False
        else:
            if (self.speakerStatus == False):
                self.logger.info('Turning on speakers')
                self.logger.info('Aktuell verbundene Geräte: %s' % self.devices)
                os.system('gpio write 2 0')
                self.speakerStatus = True
            else:
                # Es kam ein Gerät dazu
                self.logger.info('Aktuell verbundene Geräte: %s' % self.devices)


Speakers = SpeakerActor()
