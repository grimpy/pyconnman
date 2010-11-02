#!/usr/bin/env python
import dbus
bus = dbus.SystemBus()

class DbusInt(object):
    def __init__(self, path, name=None):
        if not name:
            name = self.__class__.__name__
        self.dbus = dbus.Interface(bus.get_object("org.moblin.connman", path),
                        "org.moblin.connman.%s" % name)
    
    properties = property(lambda s: s.dbus.GetProperties())
    
    def __str__(self):
        name = self.properties.get("Name", "")
        if name:
            return name
        return "<%s object at %s>" % (self.__class__.__name__, hex(id(self)))

    def __repr__(self):
        return "<%s %s object at %s>" % (self.__class__.__name__, self, hex(id(self)))

class Service(DbusInt):
    
    def set_password(self, password):
        self.dbus.SetProperty("Passphrase", password)
    
    def connect(self, timeout=60000):
        self.dbus.Connect(timeout=timeout)
    
    def disconnect(self):
        self.dbus.Disconnect()
    
    def _set_autoconnect(self, value):
        self.dbus.SetProperty("AutoConnect", value)
    
    autoconnect = property(fget=lambda s: s.properties['AutoConnect'], 
                        fset=_set_autoconnect)

class Technology(DbusInt):
    def __init__(self, path, manager):
        self.manager = manager
        super(Technology, self).__init__(path) 
    
    def _set_enabled(self, value):
        t_type = self.properties['Type']
        if value:
            self.manager.dbus.EnableTechnology(t_type)
        else:
            self.manager.dbus.DisableTechnology(t_type)
        
    devices = property(fget=lambda s: [ Device(path) for path in s.properties['Devices'] ] )
    enabled = property(fget=lambda s: s.properties['State'] == 'enabled', 
                    fset=_set_enabled)

class Device(DbusInt):
    
    def _set_powered(self, value):
        self.dbus.SetProperty("Powered", value)
    
    powered = property(fget=lambda s: s.properties['Powered'], fset=_set_powered)
        

class Manager(DbusInt):
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
