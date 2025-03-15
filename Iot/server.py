import paho.mqtt.client as mqtt
import time
import json
from main import IoTDeviceApp  # noqa # Импортируем класс для управления кондиционером

# Настройки брокера и топиков
BROKER = "dev.rightech.io"
PORT = 1883
CLIENT_ID = "mqtt-glebmaskalev712-temp"
TOPIC_SENSOR = f"devices/{CLIENT_ID}/state"
TOPIC_MODE = "devices/mqtt-glebmaskalev712-temp/commands/mode"
TOPIC_ACTUATOR = "devices/mqtt-glebmaskalev712-temp/commands/actuator"
sensor_data = None

# Объект приложения для доступа к состояниям и данным
app : IoTDeviceApp = None


# Функция, вызываемая при подключении клиента к брокеру
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Подключено к MQTT-брокеру!")
        # Подписываемся на топики управления режимом и состоянием кондиционера
        client.subscribe(TOPIC_MODE)
        client.subscribe(TOPIC_ACTUATOR)
    else:
        print(f"Не удалось подключиться, код ошибки: {rc}")


# Функция, вызываемая при получении сообщения
def on_message(client, userdata, msg):
    global app
    payload = msg.payload.decode()

    if msg.topic == TOPIC_MODE:
        # Переключение режима работы (автоматический/ручной)
        new_mode = payload.lower() == "auto"
        app.auto_mode = new_mode  # Обновляем режим в приложении
        print(payload)
        app.toggle_mode()  # Вызываем метод для изменения состояния кнопок и сообщений
        print(f"Режим работы изменен: {'Авто' if new_mode else 'Ручной'}")

    elif msg.topic == TOPIC_ACTUATOR:
        # Включение/выключение кондиционера в ручном режиме
        if not app.auto_mode:
            app.ac_on = not app.ac_on
            app.update_message_label()  # Обновляем метку о состоянии кондиционера
            print(f"Состояние кондиционера: {'ВКЛ' if app.ac_on else 'ВЫКЛ'}")
        else:
            print("Невозможно изменить режим работы кондиционера в автоматическом режиме")


# Функция публикации данных датчиков на сервер
def publish_sensor_data(client):
    global app
    global sensor_data
    if app:
        # Берем последние данные температуры
        if app.temperatures:
            temperature = app.temperatures[-1]
        else:
            temperature = None  # Если данных нет, используем дефолтное значение
            print("Нет данных о температуре") # Выводим сообщение об ошибке

        # Публикуем данные
        client.publish(TOPIC_SENSOR, temperature)
        print(f"Данные опубликованы: {temperature}")


# Инициализация MQTT-клиента
def start_mqtt(app_instance):
    global app
    app = app_instance  # Сохраняем ссылку на объект приложения
    client = mqtt.Client(client_id=CLIENT_ID, protocol=mqtt.MQTTv311)
    client.on_connect = on_connect
    client.on_message = on_message

    client.connect(BROKER, PORT, keepalive=60)

    # Начинаем публикацию данных датчиков раз в период
    client.loop_start()
    while True:
        publish_sensor_data(client)
        time.sleep(app.update_interval.get())  # Интервал обновления данных
