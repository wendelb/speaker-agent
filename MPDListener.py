import logging
import threading
import socket
from mpd import MPDClient
from SpeakerActor import Speakers

class MPDListener(object):
    """
    This class connects to the local mpd via unix socket and ensures
    that the speakers are turned on, while mad is playing
    """

    def __init__(self):
        self.logger = logging.getLogger('SpeakerAgent.MPDListener')


    def run(self):
        """Start the handler in background"""
        th = threading.Thread(target=self._thread,args=())
        th.start()

    def _thread(self):
        client = MPDClient()
        client.timeout = 2
        while(True):
            try:
                client.connect("/run/mpd/socket", 0)
                break
            except:
                pass
            sleep(5)

        self.logger.info("MPD Version: %s" % client.mpd_version)

        mpd_status = client.status().get('state')

        while (True):
            # Variable setzen, falls es in der Schleife zu Exceptions kommt
            new_status = 'Stop'
            try:
                client.idle('player')
                new_status = client.status().get('state')
            except (mpd.ConnectionError, ConnectionRefusedError) as e:
                # Verbindung verloren
                self.logger.warn('Verbindung zu MPD verloren')

                # -> keine Speaker mehr
                Speakers.removeDevice('mpd')

                # -> neu verbinden
                while(True):
                    sleep(5)
                    try:
                        client.connect("/run/mpd/socket", 0)
                        break
                    except:
                        pass


            if ((new_status == 'play') and (mpd_status == 'stop')):
                self.logger.info('Neuer MPD Status: play')
                Speakers.addDevice('mpd')
            elif ((new_status == 'stop') and (mpd_status == 'play')):
                self.logger.info('Neuer MPD Status: stop')
                Speakers.removeDevice('mpd')

            mpd_status = new_status
