import network, socket
import time


SOCK_TIMEOUT = 20           # wait for socket requests, in seconds
class WIFI:

    stat_code = {
        'find':'fnd',       # searching for AP
        'trying':'ip?',     # connected, waiting for IP address
        'connected':'con'}  # connected

    def __init__(self, hostname=''):
        self.scan_rate = 15                         # seconds between scans
        self._last_scan = 0
        self._check_state = 'find'
        self.hostname = hostname
        self._is_connected = False
        self.ap = network.WLAN(network.AP_IF)
        self.ap.active(False)                       # Disable the access point interface
        self.wlan = network.WLAN(network.STA_IF)    # create station interface
        self.wlan.config(dhcp_hostname=self.hostname)
        self.wlan.active(True)                      # activate the interface
        self.mac = self.wlan.config('mac')          # get the interface's MAC address
        self.ip = '0.0.0.0'
        #print(self.wlan.ifconfig())                 # get the interface's IP/netmask/gw/DNS addresses

    @property
    def is_connected(self):
        if self._is_connected:
            if not self.wlan.isconnected():
                # we were connected but now we are not
                self._is_connected = False
                self.ip = '0.0.0.0'
        else:
            if self.wlan.isconnected():
                # we were not connected but now we are
                self._is_connected = True
                self.ip = self.wlan.ifconfig()[0]            
        return self._is_connected

    def connect(self, ssid, pwd, block=False):
        if not self.wlan.isconnected():
            #print('Connecting to network', ssid)
            self.wlan.connect(ssid, pwd)
            if block:
                while not self.wlan.isconnected():
                    time.sleep(0.2)
                self._is_connected = True
                self.ip = self.wlan.ifconfig()[0]
        else:
            self.ip = self.wlan.ifconfig()[0]
            self._is_connected = True

    def disconnect(self):
        self._is_connected = False
        self.ip = '0.0.0.0'
        if self.wlan.isconnected():
            self.wlan.disconnect()

    def scan(self, printable=False):
        aps = self.wlan.scan()

        # Example results:
        # [(b'MySpectrumWiFi18-2G', b'\x84\xa0n\xc9(\x0e', 1, -91, 3, 0),
        # (b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00', b'\xdc\x7f\xa4\xca\t\x04', 11, -90, 3, 1)]

        if not printable:
            return aps
        for ap in aps:
            name = "".join([chr(_) if _ >= 32 else "" for _ in ap[0]])
            signal = ap[3]
            print('{}, {}'.format(name, signal))

    def find(self, ap):
        try:
            aps = self.wlan.scan()
        except OSError:     # sometimes a scan will return "OSError: scan failed"
            return False
        ap = ap.encode()
        
        # Each line will look like: (b'Starbucks WiFi', b'\xe0\xcb\xbc\x92\x1f\xe6', 11, -41, 0, 0)
        for _ap in aps:
            if ap == _ap[0]:
                return True
        return False

    def check(self, ssid, pwd):
        # State machine for connecting and reconnecting to an access point.
        # Call this periodically and it returns the state short code
        for _i in [1]:
            if self._check_state == 'find':
                # scan only every so often
                if self._last_scan + self.scan_rate > time.time():
                    break
                # Scan and return if AP not found
                self._last_scan = time.time()
                if self.find(ssid) == False:
                    break
                # Try to connect to AP
                self._check_state = 'trying'
                self.connect(ssid, pwd)
                break
            elif self._check_state == 'trying':
                if self.is_connected:
                    self._check_state = 'connected'
            elif self._check_state == 'connected':
                if not self.is_connected:
                    self._check_state = 'find'
        return self.stat_code[self._check_state]
        
    def http_get(self, url, full=False):
        # Use this for posting only; throws away received data. Returns
        # True if successful. Gets only first 50 bytes unless full=True
        # Return codes:
        #   ntc = not connected
        #   ok = request success. Got 'OK' and '200'.
        #   err = socket error
        #   nok = got data but never got '200 OK' from server
        if not self._is_connected:
            return 'ntc'

        if url.count('/') < 3:
            url = url.strip() + '/'
        _, _, host, path = url.split('/', 3)

        status = ''
        
        for i in [1]:   # Loop only once. Use loop for convenience using "break".
            try:
                addr = socket.getaddrinfo(host, 80)[0][-1]
                s = socket.socket()
            except OSError:
                print('ERR: Could not open socket')
                status = 'er1'
                break
            try:
                s.settimeout(SOCK_TIMEOUT)
                s.connect(addr)
                s.send(bytes('GET /%s HTTP/1.0\r\nHost: %s\r\n\r\n' % (path, host), 'utf8'))
            except OSError:
                print('ERR: connect() or send() resulted in error')
                status = 'er2'
                break

            # Don't care about data back. Just get enough to check 
            # headers for success.
            try:
                data = s.recv(100)
                print(data)     #DEBUG
            except OSError:
                print('ERR: recv() resulted in error')
                status = 'er3'
                break
            if (b'200' in data) and (b'OK' in data):
                status = 'ook'
            else:
                print('WARN: Did not get 200 OK')
                status = 'nok'

        # Make sure socket is always closed. Don't run out of resources.
        try:
            s.close()
        except NameError:
            pass
        return status
