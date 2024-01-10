#khai báo các thư viện
from machine import Pin, ADC
import time
import ubinascii
import machine
from umqtt.simple import MQTTClient
import random
import dht
import ujson
import utime 

# Thiết lập MQTT và TOPIC
SERVER = "ff310008.us-east-1.emqx.cloud"
MQTT_port = 15593 
CLIENT_ID = ubinascii.hexlify(machine.unique_id())
TOPIC_Blank  = b"Vitri"
TOPIC1         = b"NhietDo"
TOPIC2         = b"DoAm"
TOPIC3         = b"KhiGas"
TOPIC4         = b"Coi"
TOPIC5          = b"CanhBao"
# Thiết lập Sensor
MQ_PIN =32
analog_min = 0
analog_max = 4950
adc = ADC(Pin(MQ_PIN))
adc.atten(ADC.ATTN_11DB)
dht_pin = machine.Pin(25)
dht_sensor = dht.DHT11(dht_pin)
IR_SENSOR_PINS = [16, 17, 18, 19]
BUZZER_PIN = 26
buzzer = Pin(BUZZER_PIN, Pin.OUT)

# các hàm
def reset():
    print("Resetting...")
    time.sleep(5)
    machine.reset()

def beep1(BUZZER_PIN, duration,frequency =5500, volume_percent =100):
    coi = machine.PWM(machine.Pin(BUZZER_PIN), freq=frequency)
    volume = int((volume_percent / 100) * 1023)
    # Mô phỏng tiếng còi giống tiếng báo cháy
    for _ in range(int(duration / 0.1)):  # Chia thời gian thành các khoảng 0.1 giây
        coi.duty(volume)  # Âm lượng tăng lên
        time.sleep(0.05)
        coi.duty(0)  # Tắt còi
        time.sleep(0.05)


def beep():
    buzzer.on()
    utime.sleep(0.3)
    buzzer.off()

def read_ir_sensor(pin):
    ir_sensor = machine.Pin(pin, machine.Pin.IN)
    value = ir_sensor.value()
    if value == 1:
        value = "Trống"
    else:
        value = "Có xe"
    return value

def read_sensor():
    dht_sensor.measure()
    t = dht_sensor.temperature()
    Nhietdo = str(t) + "°C"
    d = dht_sensor.humidity()
    Doam = str(d)+"%"
    gas = adc.read()
    g = ((gas - analog_min) / (analog_max - analog_min)) * 100
    G = round(g, 2)
    Gas = str(G) + '%'
    return Nhietdo, Doam, Gas, t, G

def sub_coi(topic, msg):
    coi_status = str(msg.decode()) 
    print((topic, msg))
    if topic == TOPIC4 and coi_status == "1": 
        print('Sai The')
        beep1(BUZZER_PIN, duration= 0.1, volume_percent=75)

    if topic ==TOPIC5 and coi_status== "1":
        print("Canh bao chay")
        beep1(BUZZER_PIN, duration= 1.5, volume_percent=75)  

def Canh_Bao(t, G, mqttClient):
    if t > 60:
        print ("Nhiệt Độ cao")
        mqttClient.publish(TOPIC4, str("1"))
    elif int(G) > 20:
        print("Nồng độ khí gây cháy cao")
        mqttClient.publish(TOPIC4, str("1"))
    else:
        print("Xin chào Quý khách")
    time.sleep(0.1)

def publish_ir_value(mqttClient, sensor_number, value):
    topic = TOPIC_Blank + "/" + str(sensor_number)
    mqttClient.publish(topic, str(value).encode())

def main():
    mqttClient = MQTTClient(CLIENT_ID, SERVER, MQTT_port, user="ESP32_Nhat", password="1111", keepalive=10)
    mqttClient.connect()
    mqttClient.set_callback(sub_coi)
    mqttClient.subscribe(TOPIC4)
    mqttClient.subscribe(TOPIC5)
    print(f"Connected to MQTT  Broker :: {SERVER}")
    beep()
    while True:            
        mqttClient.check_msg()
        global last_ping
        Nhietdo, Doam, Gas, t, G = read_sensor()
        print(G)
        Canh_Bao(t, G, mqttClient)
        print("Nhietdo:", Nhietdo)
        print("Doam:", Doam)
        print("KhiGas", Gas)
        mqttClient.publish(TOPIC3, str(Gas).encode())
        mqttClient.publish(TOPIC1, str(Nhietdo).encode())
        mqttClient.publish(TOPIC2, str(Doam).encode())
        for sensor_number, pin in enumerate(IR_SENSOR_PINS, start=1):
                value = read_ir_sensor(pin)
                print(f"Vitri {sensor_number}: {value}")
                publish_ir_value(mqttClient, sensor_number, value)
                time.sleep(0.1)
        time.sleep(0.2
                   )
    mqttClient.disconnect()
    
if __name__ == "__main__":
    try:
        main()
    except OSError as e:
        print("Error: " + str(e))
        reset()