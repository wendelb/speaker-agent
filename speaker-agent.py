#!/usr/bin/python3

"""
Main file to be called by systemd (or your init-system in case you don’t have systemd)
"""

import dbus
import dbus.service
import dbus.mainloop.glib
import logging
import logging.handlers
import os
import sys
import signal
from gi.repository import GObject
from MPDListener import MPDListener
from SocketListener import SocketListener
from SpeakerActor import Speakers

#LOG_LEVEL = logging.INFO
LOG_LEVEL = logging.DEBUG
LOG_FILE = "/dev/stdout"
LOG_FORMAT = "%(asctime)s %(name)s %(levelname)s %(message)s"
BLUEZ_DEV = "org.bluez.MediaControl1"

def setupLogger(logger):
    """Setup the supplied logger. All other used loggers should be children of this one. To become a child you need to have this loggers name as basename"""
    logger.setLevel(LOG_LEVEL)
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(LOG_FORMAT)
    handler.setFormatter(formatter)
    logger.addHandler(handler)


# Initialize Logger
logger = logging.getLogger("SpeakerAgent")
setupLogger(logger)

def device_property_changed_cb(property_name, value, path, interface, device_path):
    """This function is the callback that gets executed, when there is a bluetooth event"""
    global bus, devices
    if property_name != BLUEZ_DEV:
        return

    device = dbus.Interface(bus.get_object("org.bluez", device_path), "org.freedesktop.DBus.Properties")
    properties = device.GetAll(BLUEZ_DEV)

    #logger.info("Getting dbus interface for device: %s interface: %s property_name: %s" % (device_path, interface, property_name))
    bt_addr = ":".join(device_path.split('/')[-1].split('_')[1:])

    if properties["Connected"]:
        logger.info("Device: %s has connected" % bt_addr)
        Speakers.addDevice(bt_addr)
    else:
        logger.info("Device: %s has disconnected" % bt_addr)
        Speakers.removeDevice(bt_addr)



def shutdown(signum, frame):
    logger.error("Shutdown received")
    mainloop.quit()


if __name__ == "__main__":
    # shut down on a TERM signal
    # apparently this is not working as expected!
    signal.signal(signal.SIGTERM, shutdown)

    # start logging
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

    # Start the worker for mpd
    mpd = MPDListener()
    mpd.run()

    # Start the worker for our listening socket
    socket = SocketListener()
    socket.run()

    # Run the bus specific events
    try:
        mainloop = GObject.MainLoop()
        mainloop.run()
    except KeyboardInterrupt:
        logger.error("Keyboard Interrupt")
        pass
    except:
        logger.error("Unable to run the GObject main loop")
        sys.exit(1)

    logger.info("Shutting down")
    sys.exit(0)

