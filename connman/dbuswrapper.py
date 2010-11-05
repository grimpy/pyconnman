#!/usr/bin/env python
import dbus
import functools
from dbus.mainloop.glib import DBusGMainLoop
DBusGMainLoop(set_as_default=True)

class DbusInt(object):
    bus = dbus.SystemBus()

    def __init__(self, path, name=None):
        if not name:
            name = self.__class__.__name__
        self.dbus = dbus.Interface(self.bus.get_object("org.moblin.connman", path),
                        "org.moblin.connman.%s" % name)
        if hasattr(self, '_exposed_properties'):
            for prop in self._exposed_properties:
                def mysetter(name, s, value):
                    s.dbus.SetProperty(name, value)
                def mygetter(name, s):
                    return s.properties.get(name)
                myprop = property(fget=functools.partial(mygetter, prop), fset=functools.partial(mysetter, prop))
                setattr(self.__class__, prop.lower(), myprop)

    def register_propertychange_callback(self, callback):
        self.dbus.connect_to_signal("PropertyChanged", callback)

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.dbus.object_path == other.dbus.object_path and \
                self.dbus.dbus_interface == other.dbus.dbus_interface
        return False

    properties = property(lambda s: s.dbus.GetProperties())

    def __str__(self):
        name = self.properties.get("Name", "")
        type_ = self.properties.get("Type", "")
        if name:
            return "%s %s" % (name, type_)
        return "<%s object at %s>" % (self.__class__.__name__, hex(id(self)))

    def __repr__(self):
        return "<%s %s object at %s>" % (self.__class__.__name__, self, hex(id(self)))

class Service(DbusInt):
    _exposed_properties = ('Passphrase', 'AutoConnect', 'Type', 'Name')
    ip4config = "IPv4.Configuration"
    dnsconfig = "Nameservers.Configuration"

    def connect(self, timeout=60000):
        self.dbus.Connect(timeout=timeout)

    def disconnect(self):
        self.dbus.Disconnect()

    def set_ipaddress(self, address, netmask, gateway, nameservers):
        ip = {'Method': 'manual', 'Address': address, 'Netmask': netmask}
        if gateway:
            ip['Gateway'] = gateway
        self.dbus.SetProperty(self.ip4config, ip)
        if nameservers:
            self.dbus.SetProperty(self.dnsconfig, nameservers)

    def enable_dhcp(self):
        self.dbus.SetProperty(self.ip4config, {"Method": "dhcp"})

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

    def get_devices(self):
        devices = list()
        for tech in self.technologies:
            for dev in tech.devices:
                devices.append(dev)
        return devices

    def scan(self, type_=""):
        self.dbus.RequestScan(type_)

    def _get_services(self):
        services = list()
        for service in self.properties['Services']:
            services.append(Service(service))
        return services

    def get_default_service(self):
        defaulttechtype = self.properties['DefaultTechnology']
        services = self.get_services_by_type().get(str(defaulttechtype))
        if not services:
            return
        for service in services:
            if service.properties['State'] == "online":
                return service

    def get_services_by_type(self):
        services = dict()
        for service in self.services:
            type_ = str(service.type)
            servicepertype = services.get(type_, list())
            servicepertype.append(service)
            services[type_] = servicepertype
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
