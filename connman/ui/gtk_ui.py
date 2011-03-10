import gtk
import gobject
import logging
import pynotify

from connman import dbuswrapper
from connman.ui import icons, pref
from connman import paths


class GtkUi(object):
    def __init__(self):
        self.default_service = None
        pynotify.init("Connman")
        self.notify = pynotify.Notification("Connman")
        self.mainloop = gobject.MainLoop()
        self.connman = dbuswrapper.Manager()
        self.status_icon = gtk.StatusIcon()
        self.spinner_connect = icons.Spinner(self.status_icon, icons.SPINNER_CONNECTING)
        self.spinner_scanning = icons.Spinner(self.status_icon, icons.SPINNER_SCANNING)
        self.check_status_icon()
        self.builder = gtk.Builder()
        self.builder.add_from_file(paths.XML)
        self.pref = pref.Preferences(self)
        self.password_messagebox = self.builder.get_object("msgPassword")
        self.attach_signals()

    def service_changed(self, service, propertyname, propertyvalue):
        if propertyname == "Strength":
            icon = icons.get_icon_by_strenght(propertyvalue)
            self.status_icon.set_from_file(icon)
        elif propertyname == "State":
            self.notify.update("Connman", "Sevice %s is now %s" % (service.name, propertyvalue))
            self.notify.show()
            if service.state in ("failure", "online", "ready"):
                self.spinner_connect.reset()

    def service_password_entered(self, dialog, response, service):
        if response == gtk.RESPONSE_OK:
            service.passphrase = self.builder.get_object("txtPass").props.text
            self.connect_service(service, True)
        dialog.hide()


    def check_status_icon(self, service=None):
        icon = icons.TYPE_UNKOWN
        tooltip = "Not connected"
        if not service:
            service = self.connman.get_default_service()
        if not service:
            icon = icons.TYPE_NONE
            type_ = None
        else:
            type_ = service.type
        if type_ in ("wifi", "3G", "bluetooth"):
            #register signal checker
            strenght = service.properties['Strength']
            icon = icons.get_icon_by_strenght(strenght)
        elif type_ == "ethernet":
            icon = icons.TYPE_WIRED
        if icon != icons.TYPE_NONE:
            self.spinner_connect.reset()
        if service:
            ipinfo = service.properties['IPv4']
            tooltip = "Connected to %s\nAddress %s/%s\nGateway %s" % (service, ipinfo.get('Address'), ipinfo.get('Netmask'), ipinfo.get('Gateway'))
        self.status_icon.set_tooltip(tooltip)
        self.status_icon.set_from_file(icon)

    def service_connect(self, group_item, service):
        group_item.set_active(True)
        self.connect_service(service)


    def service_connected(self):
        logging.info("Service connected")
        self.spinner_connect.reset()

    def service_connect_failed(self, error):
        if error._dbus_error_name != "org.moblin.connman.Error.InProgress":
            logging.warn("Failed to connect %s", error)
            self.notify.update("Connman", "Failed to connect")
            self.notify.show()
            self.spinner_connect.reset()
            self.check_status_icon()

    def connect_service(self, service, newpass=False):
        state = service.state
        if state not in ("online", "ready"):
            self.spinner_connect.start()
            if service.properties.get('PassphraseRequired', False) or (state == "failure" and not newpass) and service.type == "wifi":
                self.password_messagebox.props.text = "Provide password for wireless network %s" % service.name
                self.builder.get_object("txtPass").props.text = service.passphrase
                self.password_messagebox.connect("response", self.service_password_entered, service)
                self.password_messagebox.show()
                return
            logging.info("Connecting to service %s", service.name)
            service.connect(reply_handler=self.service_connected, error_handler=self.service_connect_failed)

    def build_right_menu(self, icon, button, timeout):
        menu = self.builder.get_object('tray_menu')
        for child in menu.get_children()[::-1]:
            menu.remove(child)
        services = self.connman.get_services_by_type()

        for servicetype, services in services.iteritems():
            servicetype = servicetype.capitalize()
            lbl = gtk.MenuItem(servicetype)
            lbl.show()
            menu.append(lbl)
            sep = gtk.SeparatorMenuItem()
            sep.show()
            menu.append(sep)
            lastitem = None
            for service in services:
                item = gtk.RadioMenuItem(lastitem, "%s %s" % (service.name, service.type))
                if service.state in ("online", "ready"):
                    item.set_active(True)
                item.connect("toggled", self.service_connect, service)
                item.show()
                menu.append(item)
            sep = gtk.SeparatorMenuItem()
            sep.show()
            menu.append(sep)
        self.append_technology_menu(menu)
        self.append_default_menu(menu)
        menu.show()
        menu.popup(None, None, None, button, timeout)

    def scan(self, menuitem):
        for dev in self.connman.get_devices():
            dev.register_propertychange_callback(self.device_changed)
        self.connman.scan()

    def toggle_technology(self, menuitem, technology):
        technology.enabled = not technology.enabled

    def append_technology_menu(self, menu):
        mainitem = gtk.ImageMenuItem(gtk.STOCK_NETWORK)
        mainitem.set_label("Technologies")
        mainitem.show()
        technologymenu = gtk.Menu()
        technologymenu.show()
        for technology in self.connman.technologies:
            techitem = gtk.CheckMenuItem(str(technology))
            techitem.set_active(technology.enabled)
            techitem.connect("toggled", self.toggle_technology, technology)
            techitem.show()
            technologymenu.append(techitem)

        mainitem.set_submenu(technologymenu)
        menu.append(mainitem)

    def append_default_menu(self, menu):
        #Refresh IP
        scan = gtk.ImageMenuItem(gtk.STOCK_EXECUTE)
        scan.set_label("Renew IP Address")
        scan.connect("activate", self.connman.refresh_ipaddress)
        scan.show()
        menu.append(scan)
        #Scan
        scan = gtk.ImageMenuItem(gtk.STOCK_REFRESH)
        scan.set_label("Scan")
        scan.connect("activate", self.scan)
        scan.show()
        menu.append(scan)
        #Configure
        pref = gtk.ImageMenuItem(gtk.STOCK_PREFERENCES)
        pref.set_label("Configure")
        pref.connect("activate", self.pref.show)
        pref.show()
        menu.append(pref)
        #Quit
        quit_item = gtk.ImageMenuItem(gtk.STOCK_QUIT)
        quit_item.connect("activate", self.quit)
        quit_item.show()
        menu.append(quit_item)

    def quit(self, *args, **kwargs):
        self.mainloop.quit()

    def start(self):
        self.mainloop.run()

    def manager_changed(self, manager, propertyname, propertyvalue):
        if propertyname == "DefaultTechnology":
            self.check_status_icon()
        self.verify_default_service()

    def verify_default_service(self):
        default_service = self.connman.get_default_service()
        if self.default_service != default_service:
            if default_service:
                default_service.register_propertychange_callback(self.service_changed)
            if self.default_service:
                self.default_service.unregister_propertychange_callback(self.service_changed)
            self.default_service = default_service

    def device_changed(self, device, propertyname, propertyvalue):
        if propertyname == "Scanning":
            if propertyvalue:
                self.spinner_scanning.start()
            else:
                self.spinner_scanning.stop()
                device.unregister_propertychange_callback(self.device_changed)
                self.check_status_icon()

    def attach_signals(self):
        self.status_icon.connect("popup-menu", self.build_right_menu)
        self.connman.register_propertychange_callback(self.manager_changed)
        self.verify_default_service()
