#!/usr/bin/env python
import dbus
import functools
bus = dbus.SystemBus()

class DbusInt(object):
    def __init__(self, path, name=None):
        if not name:
            name = self.__class__.__name__
        self.dbus = dbus.Interface(bus.get_object("org.moblin.connman", path),
                        "org.moblin.connman.%s" % name)
        if hasattr(self, '_exposed_properties'):
            for prop in self._exposed_properties:
                def mysetter(name, s, value):
                    s.dbus.SetProperty(name, value)
                def mygetter(name, s):
                    return s.properties[name]
                myprop = property(fget=functools.partial(mygetter, prop), fset=functools.partial(mysetter, prop))
                setattr(self.__class__, prop.lower(), myprop)
    
    properties = property(lambda s: s.dbus.GetProperties())
    
    def __str__(self):
        name = self.properties.get("Name", "")
        if name:
            return name
        return "<%s object at %s>" % (self.__class__.__name__, hex(id(self)))

    def __repr__(self):
        return "<%s %s object at %s>" % (self.__class__.__name__, self, hex(id(self)))

class Service(DbusInt):
    _exposed_properties = ('Passphrase', 'AutoConnect')
    
    def connect(self, timeout=60000):
        self.dbus.Connect(timeout=timeout)
    
    def disconnect(self):
        self.dbus.Disconnect()

class Technology(DbusInt):
    def __init__(self, path, manager):
        self.manager = manager
        super(Technology, self).__init__(path) 
        self.type = self.properties['Type']
    
    def _set_enabled(self, value):
        if value:
            self.manager.dbus.EnableTechnology(self.type)
        else:
            self.manager.dbus.DisableTechnology(self.type)
    
    def scan(self):
        self.manager.dbus.RequestScan(self.type)
    
    devices = property(fget=lambda s: [ Device(path) for path in s.properties['Devices'] ] )
    enabled = property(fget=lambda s: s.properties['State'] == 'enabled', 
                    fset=_set_enabled)

class Device(DbusInt):
    _exposed_properties = ("Powered", )

class Manager(DbusInt):
    _exposed_properties = ('State',)
    def __init__(self):
        super(Manager, self).__init__("/")
    
    def list_devices(self):
        pass
        
    def _get_services(self):
        services = list()
        for service in self.properties['Services']:
            services.append(Service(service))
        return services
    
    def _get_technologies(self):
        technologies = list()
        for technology in self.properties['Technologies']:
            technologies.append(Technology(technology, self))
        return technologies
    

    services = property(fget=_get_services)
    technologies = property(fget=_get_technologies)

if __name__ == '__main__':
    con = Manager()
