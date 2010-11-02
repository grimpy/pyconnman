#!/usr/bin/env python
import dbus
bus = dbus.SystemBus()

class Service(object):
    def __init__(self, path):
        self.service = dbus.Interface(bus.get_object("org.moblin.connman", path),
                        "org.moblin.connman.Service")
    
    def _get_properties(self):
        return self.service.GetProperties()
    
    properties = property(_get_properties)

class ConnMan(object):
    def __init__(self):
        self.manager = manager = dbus.Interface(bus.get_object("org.moblin.connman", "/"),
                    "org.moblin.connman.Manager")
    
    def list_devices(self):
        pass
    
    def _get_properties(self):
        return self.manager.GetProperties()
    
    def _get_services(self):
        services = list()
        for service in self.properties['Services']:
            services.append(Service(service))
        return services

    properties = property(fget=_get_properties) 
    services = property(fget=_get_services)

if __name__ == '__main__':
    con = ConnMan()
    print con.services[0].properties
