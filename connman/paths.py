import sys, os
def getFullPath(value):
    basepath = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(basepath, value)
APP = sys.argv[0]
def getPrefix():
    return os.path.dirname(os.path.dirname(APP))

def isInstalled():
    return os.path.basename(os.path.dirname(APP)) == "bin"

PREFIX=getPrefix()
PIXMAPS=None
if isInstalled():
    XML = os.path.join(PREFIX, 'share', 'connman', 'ui', 'connman.xml')
    PIXMAPS = os.path.join(PREFIX, 'share', 'pixmaps', 'connman')
else:
    XML = getFullPath("ui/connman.xml")
    PIXMAPS = getFullPath("../icons/")
