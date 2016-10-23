# speaker-agent

This is the central hub, which coordinates all actions around the connected active speaker.

## How it works

On my Raspberry Pi 3, I am using some active speakers. To save power and some noise when they are not used, they can be switched off. This is done using a relay card connected to the GPIO connectors.
In my case, the Speakers are controlled using GPIO 2 (wiringPI). They are on, if the Output is set to LOW and turn off, if the output is set to HIGH!

The central hub connects to dbus (for Bluetooth), mpd (for radio) and has an API (over unix socket) which allows for a variety of use cases.

There are two main scripts in this repository: 

1. The first one is `simple-agent.py` which handles all the bluetooth related stuff.
2. THen there is `speaker-agent.py` which does all the magic.

## Further reading

For a client to connect to this hib, check out [Speaker Control](https://github.com/wendelb/speaker-control)

