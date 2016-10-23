#!/usr/bin/python3

import os
import sys
import signal
import logging
import logging.handlers
import dbus
import dbus.service
import dbus.mainloop.glib
import threading
import socket
from gi.repository import GObject
import mpd
from time import sleep

LOG_LEVEL = logging.INFO
#LOG_LEVEL = logging.DEBUG
LOG_FILE = "/dev/stdout"
LOG_FORMAT = "%(asctime)s %(levelname)s %(message)s"
BLUEZ_DEV = "org.bluez.MediaControl1"

# List of all connected devices
devices = set()
speaker_status = False

# The way to stop mpd
mpc = False
aborted = False

def device_property_changed_cb(property_name, value, path, interface, device_path):
    global bus, devices
    if property_name != BLUEZ_DEV:
        return

    device = dbus.Interface(bus.get_object("org.bluez", device_path), "org.freedesktop.DBus.Properties")
    properties = device.GetAll(BLUEZ_DEV)

    #logger.info("Getting dbus interface for device: %s interface: %s property_name: %s" % (device_path, interface, property_name))
    bt_addr = ":".join(device_path.split('/')[-1].split('_')[1:])

    if properties["Connected"]:
        logger.info("Device: %s has connected" % bt_addr)
        devices.add(bt_addr)
    else:
        logger.info("Device: %s has disconnected" % bt_addr)
        if (bt_addr in devices):
            devices.remove(bt_addr)

    handle_speaker()

def handle_speaker():
    global speaker_status

    if (devices == set()):
        if (speaker_status == True):
            # Speaker sind an, können aber ausgeschalten werden
            logger.info('Turning off speakers')
            os.system('gpio write 2 1')
            speaker_status = False
    else:
        if (speaker_status == False):
            logger.info('Turning on speakers')
            logger.info('Aktuell verbundene Geräte: %s' % devices)
            os.system('gpio write 2 0')
            speaker_status = True
        else:
            # Es kam ein Gerät dazu
            logger.info('Aktuell verbundene Geräte: %s' % devices)

def handle_mpd():
    global devices

    client = mpd.MPDClient()
    client.timeout = 2
    mpc = client
    while(True):
        try:
            client.connect("localhost", 6600)
            break
        except:
            pass
        sleep(5)

    logger.info("MPD Version: %s" % client.mpd_version)

    mpd_status = client.status().get('state')

    while (not aborted):
        # Variable setzen, falls es in der Schleife zu Exceptions kommt
        new_status = 'Stop'
        try:
            client.idle('player')
            new_status = client.status().get('state')
        except (mpd.ConnectionError, ConnectionRefusedError) as e:
            # Verbindung verloren
            logger.warn('Verbindung zu MPD verloren')

            # -> keine Speaker mehr
            if ('mpd' in devices):
                devices.remove('mpd')

            handle_speaker()

            # Wenn beendet werden soll, dann halt beenden
            if (aborted):
                return

            # -> neu verbinden
            while(True):
                sleep(5)
                try:
                    client.connect("localhost", 6600)
                    break
                except:
                    pass


        if ((new_status == 'play') and (mpd_status == 'stop')):
            logger.info('Neuer MPD Status: play')
            devices.add('mpd')
            handle_speaker()
        elif ((new_status == 'stop') and (mpd_status == 'play')):
            logger.info('Neuer MPD Status: stop')
            if ('mpd' in devices):
                devices.remove('mpd')

            handle_speaker()

        mpd_status = new_status


def shutdown(signum, frame):
    aborted = True
    mainloop.quit()
    mpc.close()

if __name__ == "__main__":
    # shut down on a TERM signal
    signal.signal(signal.SIGTERM, shutdown)

    # start logging
    logger = logging.getLogger("bt_auto_loader")
    logger.setLevel(LOG_LEVEL)
    logger.addHandler(logging.StreamHandler(sys.stdout))
    logger.info("Starting to monitor Bluetooth connections")

    # Get the system bus
    try:
        dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
        bus = dbus.SystemBus()
    except Exception as ex:
        logger.error("Unable to get the system dbus: '{0}'. Exiting. Is dbus running?".format(ex.message))
        sys.exit(1)

    # listen for signals on the Bluez bus
    bus.add_signal_receiver(device_property_changed_cb, bus_name="org.bluez", signal_name="PropertiesChanged", path_keyword="device_path", interface_keyword="interface")

    th = threading.Thread(target=handle_mpd)
    th.start()

    try:
        mainloop = GObject.MainLoop()
        mainloop.run()
    except KeyboardInterrupt:
        pass
    except:
        logger.error("Unable to run the GObject main loop")
        sys.exit(1)

    logger.info("Shutting down")
    sys.exit(0)

