import os
import gobject
import time
from connman import paths

basepath = paths.PIXMAPS
TYPE_NONE = os.path.join(basepath, "connman-type-none.png")
TYPE_WIRED = os.path.join(basepath, "connman-type-wired.png")
TYPE_WIRELESS = os.path.join(basepath, "connman-signal-05.png")
TYPE_WIRELESS_REL = os.path.join(basepath, "connman-signal-0%d.png")
TYPE_UNKOWN = os.path.join(basepath, "connman-notifier-unavailable.png")

SPINNER_CONNECTING = [ os.path.join(basepath, "connman-connecting-%02d.png" % x ) for x in xrange(1, 34) ]
SPINNER_SCANNING = [ os.path.join(basepath, "connman-detect-%02d.png" % x ) for x  in xrange(1, 17) ]

def get_icon_by_strenght(strenght):
    factor = round(strenght / 20.)
    return TYPE_WIRELESS_REL % factor

class Spinner(object):
    def __init__(self, status_icon, images):
        self.status_icon = status_icon
        self.images = images
        self.idx = 0
        self.running = False
        self.len = len(images)

    def start(self):
        if self.running == False:
            self.running = True
            gobject.timeout_add(200, self.run)

    def stop(self):
        self.running = False

    def run(self):
        if not self.running:
            return False
        if self.idx >= self.len:
            self.idx = 0
        self.status_icon.set_from_file(self.images[self.idx])
        self.idx+=1
        return True

