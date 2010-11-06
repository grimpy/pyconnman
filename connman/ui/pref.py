import gtk

class Preferences(object):
    def __init__(self, main):
        self.window = main.builder.get_object("wnd_pref")
        self.main = main
        self.connman = main.connman
        self.builder = main.builder
        self.servicelist = self.builder.get_object("servicelist")
        self.servicelist


    def show(self, menuitem):
        self.attach_signals()
        self.fill_service_list()
        self.window.show()

    def close(self, button):
        self.window.hide()

    def fill_service_list(self, *args, **kwargs):
        self.servicelist.clear()
        for service in self.connman.services:
            iter = self.servicelist.append()
            self.servicelist.set(iter, 0, str(service.name), 1, str(service.type), 2, service.state, 3, service)

    def refresh(self, *args, **kwargs):
        self.connman.scan()
        self.fill_service_list()

    def get_selected_service(self):
        treeview = self.builder.get_object("Servicetree")
        selector = treeview.get_selection()
        model, iter = selector.get_selected()
        if not iter:
            return
        return model.get_value(iter, 3)

    def connect(self, button):
        service = self.get_selected_service()
        if service and service.state != "online":
            self.main.connect_service(service)
            self.configure_buttons(True)

    def disconnect(self, button):
        service = self.get_selected_service()
        if service and service.state == "online":
            service.disconnect(False)
            self.configure_buttons()

    def configure_buttons(self, online):
        self.builder.get_object("btn_connect").set_sensitive(not online)
        self.builder.get_object("btn_disconnect").set_sensitive(online)

    def service_selected(self, treeview):
        service = self.get_selected_service()
        if service:
            online = service.state == "online"
            self.configure_buttons(online)

    def attach_signals(self):
        self.window.connect("delete-event", lambda a,b: a.hide() or True)
        self.builder.get_object("btnPrefClose").connect("clicked", self.close)
        self.builder.get_object("btn_connect").connect("clicked", self.connect)
        self.builder.get_object("btn_disconnect").connect("clicked", self.disconnect)
        self.builder.get_object("btn_add").connect("clicked", self.close)
        self.builder.get_object("btn_edit").connect("clicked", self.close)
        self.builder.get_object("btn_refresh").connect("clicked", self.refresh)
        self.builder.get_object("Servicetree").connect("cursor-changed", self.service_selected)
