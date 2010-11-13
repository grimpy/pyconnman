#!/usr/bin/env python
import dbus
import functools
import logging
from dbus.mainloop.glib import DBusGMainLoop
DBusGMainLoop(set_as_default=True)

class DbusInt(object):
    bus = dbus.SystemBus()
    __instances = dict()
    _str_props = ("Name", "Type")

    @classmethod
    def load(cls, path=None, *args, **kwargs):
        key = cls.__name__, path
        if key not in cls.__instances:
            if path:
                inst = cls(path, *args, **kwargs)
            else:
                inst = cls(*args, **kwargs)
            cls.__instances[key] = inst
        return cls.__instances[key]

    def __init__(self, path):
        name = self.__class__.__name__
        self.__callback_registered = False
        self.__callbacks = list()
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

    def __callback_handler(self, propertyname, propertyvalue):
        logging.info("%s property update of %s with value %s", self.__class__.__name__, propertyname, propertyvalue)
        for callback in self.__callbacks:
            callback(self, propertyname, propertyvalue)

    def register_propertychange_callback(self, callback):
        if not self.__callback_registered:
            self.dbus.connect_to_signal("PropertyChanged", self.__callback_handler)
        self.__callback_registered = True
        self.__callbacks.append(callback)

    def unregister_propertychange_callback(self, callback):
        if callback in self.__callbacks:
            self.__callbacks.remove(callback)

    def __reload(self):
        path = self.dbus.object_path
        interface = self.dbus.dbus_interface
        del self.dbus
        self.dbus = dbus.Interface(self.bus.get_object("org.moblin.connman", path), interface)


    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.dbus.object_path == other.dbus.object_path and \
                self.dbus.dbus_interface == other.dbus.dbus_interface
        return False

    properties = property(lambda s: s.dbus.GetProperties())

    def __str__(self):
        nameparts = list()
        for namepart in self._str_props:
            part = self.properties.get(namepart)
            if part:
                nameparts.append(part)
        name = " ".join(nameparts)
        if name:
            return name
        return "<%s object at %s>" % (self.__class__.__name__, hex(id(self)))

    def __repr__(self):
        return "<%s %s object at %s>" % (self.__class__.__name__, self, hex(id(self)))

class Service(DbusInt):
    _exposed_properties = ('Passphrase', 'AutoConnect', 'Type', 'Name', 'State')
    ip4config = "IPv4.Configuration"
    dnsconfig = "Nameservers.Configuration"

    def connect(self, **kwargs):
        self.dbus.Connect(**kwargs)

    def disconnect(self):
        self.dbus.Disconnect()

    def remove(self):
        self.dbus.Remove()

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
    _str_props = ("Name", )

    def __init__(self, path, manager):
        self.manager = manager
        super(Technology, self).__init__(path)
        self.type = self.properties['Type']

    def __set_enabled(self, value):
        if value:
            self.manager.dbus.EnableTechnology(self.type)
        else:
            self.manager.dbus.DisableTechnology(self.type)

    def scan(self):
        self.manager.dbus.RequestScan(self.type)

    devices = property(fget=lambda s: [ Device.load(path) for path in s.properties['Devices'] ] )
    enabled = property(fget=lambda s: s.properties['State'] == 'enabled',
                    fset=__set_enabled)

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


    def get_default_service(self):
        defaulttechtype = self.properties['DefaultTechnology']
        services = self.get_services_by_type().get(str(defaulttechtype))
        if not services:
            return
        for service in services:
            if service.properties['State'] in ("online", "ready"):
                return service

    def get_services_by_type(self):
        services = dict()
        for service in self.services:
            type_ = str(service.type)
            servicepertype = services.get(type_, list())
            servicepertype.append(service)
            services[type_] = servicepertype
        return services

    services = property(fget=lambda s: [ Service.load(serv) for serv in s.properties['Services']])
    technologies = property(fget=lambda s: [ Technology.load(tech,s) for tech in s.properties['Technologies']])

if __name__ == '__main__':
    con = Manager.load()
