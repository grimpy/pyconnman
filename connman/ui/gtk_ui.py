import gtk
import gobject
from connman import dbuswrapper
from connman.ui import icons
import logging

class GtkUi(object):
        def __init__(self):
            self.default_service = None
            self.mainloop = gobject.MainLoop()
            self.connman = dbuswrapper.Manager()
            self.status_icon = gtk.StatusIcon()
            self.spinner_connect = icons.Spinner(self.status_icon, icons.SPINNER_CONNECTING)
            self.spnner_scanning = icons.Spinner(self.status_icon, icons.SPINNER_SCANNING)
            self.check_status_icon()
            self.builder = gtk.Builder()
            self.builder.add_from_file("connman/ui/connman.xml")
            self.attach_signals()

        def service_update(self, propertyname, propertyvalue):
            logging.info("Service property update of %s with value %s", propertyname, propertyvalue)
            if propertyname == "Strength":
                icon = icons.get_icon_by_strenght(propertyvalue)
                self.status_icon.set_from_file(icon)

        def check_status_icon(self):
            icon = icons.TYPE_UNKOWN
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
            self.status_icon.set_from_file(icon)

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
                    item.show()
                    lastitme = item
                    menu.append(item)
                sep = gtk.SeparatorMenuItem()
                sep.show()
                menu.append(sep)
            menu.popup(None, None, None, button, timeout)


        def start(self):
            self.mainloop.run()


        def manager_changed(self, propertyname, propertyvalue):
            logging.info("Manager property update of %s with value %s", propertyname, propertyvalue)
            if propertyname == "DefaultTechnology":
                self.check_status_icon()
            self.verify_default_service()

        def verify_default_service(self):
            default_service = self.connman.get_default_service()
            if self.default_service != default_service:
                if default_service:
                    default_service.register_propertychange_callback(self.service_update)
                self.default_service = default_service

        def device_changed(self, propertyname, propertyvalue):
            logging.info("Device property update of %s with value %s", propertyname, propertyvalue)
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
