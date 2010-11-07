import gtk

class ServiceEditor(object):
    def __init__(self, builder, service):
        self.sensitive_widgets = ("txtbox_address", "txtbox_gateway", "txtbox_netmask", "txtbox_dns1", "txtbox_dns2")
        self.service = service
        self.ipinfo = service.properties["IPv4"]
        self.ipinfo_config = service.properties["IPv4.Configuration"]
        self.dnsinfo = service.properties["Nameservers"]
        self.builder = builder
        self.window = builder.get_object("wnd_service_details")
        self.attach_signals()
        self.show()
    
    def show(self):
        usedhcp = self.ipinfo_config.get("Method", "dhcp") == "dhcp"
        self.builder.get_object("chkbox_dhcp").set_active(usedhcp)
        address = self.builder.get_object("txtbox_address")
        netmask = self.builder.get_object("txtbox_netmask")
        gateway = self.builder.get_object("txtbox_gateway")
        dns1 = self.builder.get_object("txtbox_dns1")
        dns2 = self.builder.get_object("txtbox_dns2")
        address.props.text = self.ipinfo.get("Address", "")
        netmask.props.text = self.ipinfo.get("Netmask", "")
        gateway.props.text = self.ipinfo.get("Gateway", "")
        nr_dns = len(self.dnsinfo)
        if nr_dns >= 1:
            dns1.props.text = self.dnsinfo[0]
        if nr_dns >= 2:
            dns2.props.text = self.dnsinfo[1]
        
        self.set_sensitive(not usedhcp)
        self.window.show()
    
    def set_sensitive(self, value):
        for widget in self.sensitive_widgets:
            self.builder.get_object(widget).set_sensitive(value)

    def apply(self, button):
        if self.builder.get_object("chkbox_dhcp").get_active():
            self.service.enable_dhcp()
        else:
            address = self.builder.get_object("txtbox_address").props.text
            netmask = self.builder.get_object("txtbox_netmask").props.text
            gateway = self.builder.get_object("txtbox_gateway").props.text
            dns = list()
            dns1 = self.builder.get_object("txtbox_dns1").props.text
            if dns1:
                dns.append(dns1)
            dns2 = self.builder.get_object("txtbox_dns2").props.text
            if dns2:
                dns.append(dns2)
            self.service.set_ipaddress(address, netmask, gateway, dns)
        self.close()
    
    def close(self, *args):
        self.window.hide()
    
    def toggled_dhcp(self, togglebutton):
        self.set_sensitive(not togglebutton.get_active())

    def attach_signals(self):
        self.builder.get_object("chkbox_dhcp").connect("toggled", self.toggled_dhcp)
        self.builder.get_object("btn_ok_edit_service").connect("clicked", self.apply)
        self.builder.get_object("btn_cancel_edit_service").connect("clicked", self.close)
        self.window.connect("delete-event", lambda a,b: a.hide() or True)
