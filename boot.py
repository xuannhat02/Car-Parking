import network
ssid = "Hi"
password = "khang22102020"
def connect_wifi(ssid, password):
    sta_if = network.WLAN(network.STA_IF)

    if not sta_if.isconnected():
        print('Connecting to WiFi...')
        sta_if.active(True)
        sta_if.connect(ssid, password)

        while not sta_if.isconnected():
            pass

    print('WiFi connected!')
    print('IP address:', sta_if.ifconfig()[0])

# Thay thế 'Your_SSID' và 'Your_Password' bằng thông tin WiFi của bạn
connect_wifi(ssid, password)
