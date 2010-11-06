import gtk
import gobject
from connman import dbuswrapper
from connman.ui import icons, pref
import logging
import pynotify

class GtkUi(object):
        def __init__(self):
            self.default_service = None
            pynotify.init("Connman")
            self.notify = pynotify.Notification("Connman")
            self.mainloop = gobject.MainLoop()
            self.connman = dbuswrapper.Manager()
            self.status_icon = gtk.StatusIcon()
            self.spinner_connect = icons.Spinner(self.status_icon, icons.SPINNER_CONNECTING)
            self.spnner_scanning = icons.Spinner(self.status_icon, icons.SPINNER_SCANNING)
            self.check_status_icon()
            self.builder = gtk.Builder()
            self.builder.add_from_file("connman/ui/connman.xml")
            self.pref = pref.Preferences(self)
            self.password_messagebox = self.builder.get_object("msgPassword")
            self.attach_signals()

        def service_update(self, service, propertyname, propertyvalue):
            logging.info("Service property update of %s with value %s", propertyname, propertyvalue)
            if propertyname == "Strength":
                icon = icons.get_icon_by_strenght(propertyvalue)
                self.status_icon.set_from_file(icon)
            elif propertyname == "State":
                self.notify.update("Connman", "Sevice %s is now %s" % (service.name, propertyvalue))
                self.notify.show()

        def service_password_entered(self, dialog, response, service):
            if response == gtk.RESPONSE_OK:
                service.passphrase = self.builder.get_object("txtPass").props.text
                self.connect_service(service)
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
                self.spinner_connect.stop()
            if service:
                ipinfo = service.properties['IPv4']
                tooltip = "Connected to %s\nAddress %s/%s\nGateway %s" % (service, ipinfo['Address'], ipinfo['Netmask'], ipinfo['Gateway'])
            self.status_icon.set_tooltip(tooltip)
            self.status_icon.set_from_file(icon)

        def service_connect(self, group_item, service):
            group_item.set_active(True)
            self.connect_service(service)

        def connect_service(self, service):
            state = service.state
            if state not in ("online", "ready"):
                self.spinner_connect.start()
                try:
                    if service.properties['PassphraseRequired'] or state == "failure" and service.type == "wifi":
                        self.password_messagebox.props.text = "Provide password for wireless network %s" % service.name
                        self.builder.get_object("txtPass").props.text = ""
                        self.password_messagebox.connect("response", self.service_password_entered, service)
                        self.password_messagebox.show()
                        return
                    service.connect(1)
                except:
                    raise
                    pass

        def build_right_menu(self, icon, button ,timeout):
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
                    lastitme = item
                    menu.append(item)
                sep = gtk.SeparatorMenuItem()
                sep.show()
                menu.append(sep)
            self.append_technology_menu(menu)
            self.append_default_menu(menu)
            menu.show()
            menu.popup(None, None, None, button, timeout)

        def scan(self, menuitem):
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
            scan = gtk.ImageMenuItem(gtk.STOCK_REFRESH)
            scan.set_label("Scan")
            scan.connect("activate", self.scan)
            scan.show()
            menu.append(scan)
            pref = gtk.ImageMenuItem(gtk.STOCK_PREFERENCES)
            pref.set_label("Configure")
            pref.connect("activate", self.pref.show)
            pref.show()
            menu.append(pref)
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
                    default_service.register_propertychange_callback(self.service_update)
                self.default_service = default_service

        def device_changed(self, device, propertyname, propertyvalue):
            if propertyname == "Scanning":
                if propertyvalue:
                    self.spnner_scanning.start()
                else:
                    self.spnner_scanning.stop()
                    self.check_status_icon()

        def attach_signals(self):
            self.status_icon.connect("popup-menu", self.build_right_menu)
            self.connman.register_propertychange_callback(self.manager_changed)
            self.verify_default_service()
            for dev in self.connman.get_devices():
                dev.register_propertychange_callback(self.device_changed)
