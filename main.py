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
def main():
    connect_wifi(wifi_ssid, wifi_password)
    mqttClient = connect_mqtt()
    Fire.irq(trigger = Pin.IRQ_RISING, handler = lambda Pin:check_fire(Pin, mqttClient ))
    mqttClient.set_callback(lambda Topic, msg: handle_control(Topic, msg, mqttClient))
    mqttClient.subscribe(TOPIC6)
    mqttClient.subscribe(TOPIC5)
    sleep(0.1)
    timer = Timer(1)
    timer.init(period=10000, mode=Timer.PERIODIC, callback=lambda timer: tt_servo(timer, mqttClient))
    mqttClient.publish(TOPIC7, str(0))
    mqttClient.publish(TOPIC8, str(0))
    mqttClient.publish(TOPIC9, str(0))
    #mqttClient.publish(TOPIC10, str(0))
    while True:
        global flag1, flag2
        mqttClient.check_msg()
        if light.value()==1:
            led.on()
        elif light.value()==0:
            led.off()
        if HN1.value() == 0 and flag1 == 1:
            if Slot>  0 and Slot < 5:
                car_in(mqttClient)
            else:
                full_slot(mqttClient)
        if HN1.value() == 0 and flag1 == 1 and HN2.value() == 0 and flag2 == 1:
            car_out(mqttClient)
        if HN2.value() == 0 and flag2 == 1:
            if Slot >=  0 and Slot < 4:
                car_out(mqttClient)    
        flag1 = HN1.value()
        flat2 = HN2.value()
        menu()
    print("Disconnecting...")
    mqttClient.disconnect()
if __name__ == "__main__":
    try:
        main()
    except OSError as e:
        print("Error: " + str(e))
        reset()
