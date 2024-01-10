import network
from machine import Pin, I2C, PWM, RTC,SPI,unique_id, Timer
from i2c_lcd import I2cLcd
from utime import sleep
from mfrc522 import MFRC522
from umqtt.simple import MQTTClient
import utime
import time
import ubinascii
import urequests
import math
import machine
wifi_ssid = "Hi"
wifi_password = "khang22102020"
def connect_wifi(wifi_ssid, wifi_password):
    wifi = network.WLAN(network.STA_IF)
    if not wifi.isconnected():
        print(f"Connecting to wifi {wifi_ssid}...")
        wifi.active(True)
        wifi.connect(wifi_ssid, wifi_password)
        while not wifi.isconnected():
           pass
    print(f'Wifi {wifi_ssid} connected!')
    print("Network config", wifi.ifconfig())
# connect_wifi(wifi_ssid, wifi_password)
Slot = 4
flag1 = 1
flag2 = 1

HN1 = Pin(33,  Pin.IN)
HN2 = Pin(35,  Pin.IN)
'''---------------------------------------SƠ ĐỒ KẾT NỐI VỚI ESP32-----------------------------------------
        I2C:  SCL-> 22
              SDA -> 21
              
        CỔNG VÀO: SERVO 0 -> 32 ---HỒNG NGOẠI 1->33
        CỔNG RA: SERVO 1 -> 25 ---HỒNG NGOẠI 2 -> 35
        LỬA -> 13
        DHT22 -> 15
        -----------------------------------
        RFID: SDA -> 19
              SCK -> 18
              MOSI -> 23
              MISO -> 5
              RST -> 4'''
Fire = Pin(13,  Pin.IN)
light = Pin(26,  Pin.IN)
led = Pin(14,  Pin.OUT)
servo_in=PWM(Pin(32),50)
servo_in.duty(80)
servo_out=PWM(Pin(25),50)
servo_out.duty(80)
  
i2c = I2C(scl=Pin(22), sda=Pin(21), freq=400000)
# connect scl to GPIO 22, sda to GPIO 21
lcd = I2cLcd(i2c, 0x27, 2, 16)

# Default MQTT server to connect to
SERVER = "ff310008.us-east-1.emqx.cloud"
MQTT_port = 15593
CLIENT_ID = "Phi"
TOPIC1 = b"UID1"
TOPIC2 = b"UID2"
TOPIC3 = b"UID3"
TOPIC4 = b"UID4"
TOPIC5 = b"DkIn"
TOPIC6 = b"DkOut"
TOPIC7 = b"TtIn"
TOPIC8 = b"TtOut"
TOPIC9 = b"CanhBao"
TOPIC10 = b"Coi" 
# Kết nối RFID
# Khởi tạo SPI cho MFRC522
sck = Pin(18, Pin.OUT)
mosi = Pin(23, Pin.OUT)
miso = Pin(5, Pin.IN)
gpioRst = 4
gpioCs= 19
spi = SPI(2, baudrate=1000000, polarity=0, phase=0, sck=sck, mosi=mosi, miso=miso)
rfid = MFRC522(spi, gpioRst, gpioCs)
spi.init()
rfid.init()
# Kết nối RTC (Real-Time Clock)
rtc = RTC()
# Dữ liệu lưu trữ thẻ và thời gian vào ra
card_data = {}
last_entry_time = None
#TtIn = 0
#TtOut = 0
card1='179168103146238'
card2='1311361013379'   #đã thu thập từ trước
card3='21124117216741'
card4='1951098916780'
lcd.move_to(0,0)
lcd.putstr('      ESP32     ') 
lcd.move_to(0,1) 
lcd.putstr(' PARKING SYSTEM ')
#time.sleep(3)

#Đọc thẻ từ
def read_card():
    (status, tag_type) = rfid.request(rfid.REQIDL)
    if status == rfid.OK:
        print("Thẻ đã được đặt lên!")
        (status1, raw_uid) = rfid.anticoll()
        if status1 == rfid.OK:
            uid = "".join([str(i) for i in raw_uid])
            return uid
    return False
#Ghi thời gian xe vào
def record_entry(card_id):
    global last_entry_time
    last_entry_time = utime.time()
    card_data[card_id] = {"entry_time": last_entry_time}
    real_time_in = get_time()
    print(real_time_in)
    print(f"Thẻ {card_id} vào bãi đỗ ")
    return real_time_in

def time_CarIn(mqttClient, card_id, real_time_in):
    if card_id == card1:
        DateTimeIn1 = f'Vào bãi lúc {real_time_in}'
        mqttClient.publish(TOPIC1, str(DateTimeIn1).encode())
    elif card_id == card2:
        DateTimeIn2 = f'Vào bãi Lúc {real_time_in}'
        mqttClient.publish(TOPIC2, str(DateTimeIn2).encode())
    elif card_id == card3:
        DateTimeIn3 = f'Vào bãi lúc {real_time_in}'
        mqttClient.publish(TOPIC3, str(DateTimeIn3).encode())
    elif card_id == card4:
        DateTimeIn4 = f'Vào bãi lúc {real_time_in}'
        mqttClient.publish(TOPIC4, str(DateTimeIn4).encode())
#Tính thời gian xe đậu
def record_exit(card_id):
    exit_time = utime.time()
    entry_time = card_data[card_id]["entry_time"]
    parking_duration = math.ceil(float(exit_time - entry_time)/60)
    parking_duration_h = parking_duration // 60
    parking_duration_p = parking_duration 
    so_ngay = math.ceil(parking_duration / 1440)
    time_parking_duration = f'{parking_duration_h} giờ {parking_duration_p}'
    real_time = get_time()
    print(real_time)
    print(f"Thẻ {card_id} đỗ xe hết {time_parking_duration} phút")
    return real_time, time_parking_duration, parking_duration_h, so_ngay
def tinh_tien(mqttClient, card_id, real_time, time_parking_duration, parking_duration_h, so_ngay):
    gia_ngay = so_ngay * 10
    if parking_duration_h <= 24:
        lcd.move_to(0,1)
        lcd.putstr("   PRICE: 10$    ")
    else:
        lcd.move_to(0,1)
        lcd.putstr("   PRICE: 20$   ")
    if card_id == card1:
        if parking_duration_h <= 24:
            time_parked = f'Rời bãi đỗ lúc {real_time} -- \nHết {time_parking_duration} phút -- Giá tiền: 10$'
        else:
            so_ngay = math.ceil(parking_duration / 1440)
            time_parked = f'Rời bãi đỗ lúc {real_time} -- \nHết {time_parking_duration} phút -- Giá tiền: {gia_ngay}'
        mqttClient.publish(TOPIC1, str(time_parked).encode())
    elif card_id == card2:
        if parking_duration_h <= 24:
            time_parked = f'Rời bãi đỗ lúc {real_time} -- \nHết {time_parking_duration} phút -- Giá tiền: 10$'
        else:
            time_parked = f'Rời bãi đỗ lúc {real_time} -- \nHết {time_parking_duration} phút -- Giá tiền: {gia_ngay}'
        mqttClient.publish(TOPIC2, str(time_parked).encode())
    elif card_id ==  card3:
        if parking_duration_h <= 24:
            time_parked = f'Rời bãi đỗ lúc {real_time} -- \nHết {time_parking_duration} phút -- Giá tiền: 10$'
        else:
            time_parked = f'Rời bãi đỗ lúc {real_time} -- \nHết {time_parking_duration} phút -- Giá tiền: {gia_ngay}'
        mqttClient.publish(TOPIC3, str(time_parked).encode())
    elif card_id == card4:
        if parking_duration_h <= 24:
            time_parked = f'Rời bãi đỗ lúc {real_time} -- \nHết {time_parking_duration} phút -- Giá tiền: 10$'
        else:
            time_parked = f'Rời bãi dỗ lúc {real_time} -- \nHết {time_parking_duration} phút -- Giá tiền: {gia_ngay}'
        mqttClient.publish(TOPIC4, str(time_parked).encode())
    del card_data[card_id]
    # Xóa dữ liệu thẻ ra
# Ghi thông tin vào bộ nhớ hoặc hệ thống lưu trữ
def get_time():
    response = urequests.get("http://worldtimeapi.org/api/timezone/Asia/Ho_Chi_Minh")
    data = response.json()
    response.close()
    time_string = data["datetime"]
    # Lấy phần của chuỗi thời gian không bao gồm  giây và múi giờ
    formatted_time = time_string.replace("T", " ")
    date_time= formatted_time[11:16] +' '+ formatted_time[8:10]+ formatted_time[4:7]+'-'+ formatted_time[ :4]
    sleep(0.2)
    return date_time
def handle_control(Topic, msg, mqttClient):
    new_status = msg.decode()
    print((Topic, msg))
    if Topic == TOPIC5 and new_status == "true": 
        set_servo_in(30, mqttClient)
    elif Topic == TOPIC5 and new_status == 'false':
        set_servo_in(80, mqttClient)      
    elif Topic == TOPIC6 and new_status == 'true':
        set_servo_out(30, mqttClient)        
    elif Topic == TOPIC6 and new_status == 'false':
        set_servo_out(80, mqttClient)
def menu():
    real_time = get_time()
    lcd.move_to(0,0)
    lcd.putstr(real_time)
    lcd.move_to(0,1) 
    lcd.putstr("  Slot left: {}  ".format(Slot))
    sleep(0.5)
def set_servo_in(duty, mqttClient):
    servo_in.duty(duty)
    if duty == 80:
        TtIn = 'false'
    else:
        TtIn = 'true' 
    mqttClient.publish(TOPIC7, str(TtIn).encode())
def set_servo_out(duty, mqttClient):
    servo_out.duty(duty)
    if duty == 80:
        TtOut = 'false'
    else:
        TtOut = 'true' 
    mqttClient.publish(TOPIC8, str(TtOut).encode())
def car_in(mqttClient):
    global Slot
    lcd.move_to(0,0)
    lcd.putstr('    CHECK IN    ')
    lcd.move_to(0,1)
    lcd.putstr('  ENTER CARD IN')
    sleep(3)
    card_id = read_card()
    sleep(0.1)
    if card_id == card1 or card_id == card2 or card_id == card3 or card_id == card4:
        if card_id not in card_data:
            real_time_in = record_entry(card_id)
            time_CarIn(mqttClient, card_id, real_time_in)
            set_servo_in(30, mqttClient)
            lcd.move_to(0,0)
            lcd.putstr('     CAR IN    ')
            lcd.move_to(0,1)
            lcd.putstr('               ')            
            Slot = Slot-1
            sleep(4)
            set_servo_in(80, mqttClient)
        else:
            lcd.move_to(0,0)
            lcd.putstr('     DONE     ')
            lcd.move_to(0,1)
            lcd.putstr('   CAN OUT     ')
            sleep(3)
    elif card_id != card1 or card_id != card2 or card_id != card3 or card_id != card4:
        lcd.move_to(0,0)
        lcd.putstr(' WRONG CARD IN  ')
        lcd.move_to(0,1)
        lcd.putstr('   ENTER CARD   ')
        mqttClient.publish(TOPIC10, str(1))
        sleep(3)
        # Stop đọc thẻ
        rfid.stop_crypto1()
        
def check_fire(Pin, mqttClient):
    set_servo_out(30, mqttClient)
    set_servo_in(30, mqttClient)
    fire = 1
    lcd.move_to(0,0) 
    lcd.putstr('----WARNING---- ')
    lcd.move_to(0,1) 
    lcd.putstr('THERE IS A FIRE ')
    mqttClient.publish(TOPIC9, str(fire).encode())
    mqttClient.publish(TOPIC10, str(fire).encode())
    sleep(1)
    while Fire.value() == 1:
        pass
    fire = 0
    #set_servo_out(80, mqttClient)
    #set_servo_in(80, mqttClient)
    mqttClient.publish(TOPIC9, str(fire).encode())
    mqttClient.publish(TOPIC10, str(fire).encode())
def car_out(mqttClient):
    global Slot
    lcd.move_to(0,0)
    lcd.putstr('    CHECK OUT   ')
    lcd.move_to(0,1)
    lcd.putstr(' ENTER CARD OUT ')
    sleep(3)
    card_id = read_card()
    sleep(0.1)
    if card_id == card1 or card_id == card2 or card_id == card3 or card_id == card4:
        if card_id in card_data:
            real_time, time_parking_duration, parking_duration_h, so_ngay = record_exit(card_id)
            tinh_tien(mqttClient, card_id, real_time, time_parking_duration, parking_duration_h, so_ngay)
            set_servo_out(30, mqttClient)
            lcd.move_to(0,0)
            lcd.putstr("    CAR OUT     ")
            lcd.move_to(0,1)
            lcd.putstr("                ")
            Slot = Slot+1
            sleep(4)
            set_servo_out(80, mqttClient)
        else:
            lcd.move_to(0,0)
            lcd.putstr('                ')
            lcd.move_to(0,1)
            lcd.putstr('  CAN NOT OUT   ')
            sleep(3)        
            
    elif card_id != card1 or card_id != card2 or card_id != card3 or card_id != card4:
        lcd.move_to(0,0)
        lcd.putstr(' WRONG CARD OUT  ')
        lcd.move_to(0,1)
        lcd.putstr('   ENTER CARD   ')
        mqttClient.publish(TOPIC10, str(1))
        rfid.stop_crypto1()

def full_slot(mqttClient):
    lcd.move_to(0,0) 
    lcd.putstr('    SORRY :(    ')
    lcd.move_to(0,1) 
    lcd.putstr('  PARKING FULL  ')
    coi=1
    mqttClient.publish(TOPIC10, str(coi).encode())
    sleep(3)
    
def reset():
    print("Resetting...")
    time.sleep(5)
    machine.reset()
# Hàm kết nối MQTT
def connect_mqtt():
    client = MQTTClient(CLIENT_ID, SERVER, MQTT_port, user="ESP32_Phi", password="1111", keepalive=60)
    try:
        client.connect()
        print(f"Connected to MQTT  Broker : {SERVER}")
        return client
    except Exception as e:
        print("Error connecting to MQTT Broker:", e)
        reset()
def tt_servo(timer, mqttClient):
    if servo_in.duty()== 30 or servo_out.duty()== 30:
        set_servo_in(80, mqttClient) 
        set_servo_out(80, mqttClient)
        