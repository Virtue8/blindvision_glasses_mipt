import machine
import utime

print("=" * 50)
print("ПАРКТРОНИК")
print("=" * 50)

TRIG_PIN = 1
ECHO_PIN = 0
RED_PIN = 4
GREEN_PIN = 2
BUZZER_PIN = 3

trigger = machine.Pin(TRIG_PIN, machine.Pin.OUT)
echo = machine.Pin(ECHO_PIN, machine.Pin.IN)
red = machine.Pin(RED_PIN, machine.Pin.OUT)
green = machine.Pin(GREEN_PIN, machine.Pin.OUT)
buzzer = machine.PWM(machine.Pin(BUZZER_PIN))
buzzer.freq(1000)

FAR = 130
MID = 100
NEAR = 50

last_beep_time = 0
is_beeping = False
measurement_count = 0

def get_beep_settings(distance):
    if distance > FAR:
        return 0, 0, "🟢", "Дальнее", 0, 1
    elif distance > MID:
        return 800, 500, "🟡", "Среднее", 1, 1
    elif distance > NEAR:
        return 300, 800, "🟠", "Близко", 1, 0
    else:
        return 0, 1200, "🔴", "Критично", 1, 0

def update_indicators(interval, freq, red_val, green_val, distance):
    global last_beep_time, is_beeping
    
    current_time = utime.ticks_ms()
    red.value(red_val)
    green.value(green_val)
    
    if interval == 0 and freq == 0:
        buzzer.duty_u16(0)
        is_beeping = False
    elif interval == 0:
        buzzer.freq(freq)
        buzzer.duty_u16(15000)
        is_beeping = True
    else:
        if is_beeping:
            if utime.ticks_diff(current_time, last_beep_time) > 100:
                buzzer.duty_u16(0)
                is_beeping = False
                last_beep_time = current_time
        else:
            if utime.ticks_diff(current_time, last_beep_time) > interval:
                buzzer.freq(freq)
                buzzer.duty_u16(12000)
                is_beeping = True
                last_beep_time = current_time

print("Запуск системы...")
for i in range(2):
    red.value(1)
    utime.sleep_ms(100)
    red.value(0)
    green.value(1)
    utime.sleep_ms(100)
    green.value(0)

print("\nДистанции:")
print(f"🟢 >{FAR} см - Дальнее (без звука)")
print(f"🟡 {MID}-{FAR} см - Среднее")
print(f"🟠 {NEAR}-{MID} см - Близко")
print(f"🔴 <{NEAR} см - Критично")
print("=" * 50)
print("Начинаю измерения...")

try:
    while True:
        measurement_count += 1
        
        trigger.value(0)
        utime.sleep_us(2)
        trigger.value(1)
        utime.sleep_us(10)
        trigger.value(0)
        
        timeout = utime.ticks_us()
        while echo.value() == 0:
            if utime.ticks_diff(utime.ticks_us(), timeout) > 50000:
                break
        
        start = utime.ticks_us()
        while echo.value() == 1:
            if utime.ticks_diff(utime.ticks_us(), start) > 50000:
                break
        
        end = utime.ticks_us()
        
        if start < end:
            dist = (end - start) * 0.0343 / 2
            
            if 5 < dist < 400:
                interval, freq, icon, name, red_val, green_val = get_beep_settings(dist)
                update_indicators(interval, freq, red_val, green_val, dist)
                
                if measurement_count % 10 == 0:
                    bar_len = 20
                    filled = int((1 - min(dist, 150) / 150) * bar_len)
                    bar = "█" * filled + "░" * (bar_len - filled)
                    beep_icon = "🔊" if is_beeping else "🔇"
                    print(f"{icon} {dist:5.0f} см | {name:8} | [{bar}] {beep_icon}", end="\r")
        else:
            buzzer.duty_u16(0)
            red.value(0)
            green.value(0)
            
            if measurement_count % 100 == 0:
                print("Поиск датчика...", end="\r")
        
        utime.sleep_ms(50)

except KeyboardInterrupt:
    print("\n\nОстановка...")

finally:
    buzzer.duty_u16(0)
    red.value(0)
    green.value(0)
    print("\nСистема выключена")