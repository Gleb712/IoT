import paho.mqtt.client as mqtt
import time
import json
from main import IoTDeviceApp  # noqa # Импортируем класс для управления кондиционером

# Настройки брокера и топиков
BROKER = "test.mosquitto.org"
PORT = 1883
TOPIC_SENSOR = "Iot/sensor"
TOPIC_MODE = "Iot/mode"
TOPIC_ACTUATOR = "Iot/actuator"

# Объект приложения для доступа к состояниям и данным
app = None


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
        app.auto_mode.set(new_mode)  # Обновляем режим в приложении
        app.toggle_mode()  # Вызываем метод для изменения состояния кнопок и сообщений
        print(f"Режим работы изменен: {'Авто' if new_mode else 'Ручной'}")

    elif msg.topic == TOPIC_ACTUATOR:
        # Включение/выключение кондиционера в ручном режиме
        app.ac_on = not app.ac_on
        app.update_message_label()  # Обновляем метку о состоянии кондиционера
        print(f"Состояние кондиционера: {'ВКЛ' if app.ac_on else 'ВЫКЛ'}")


# Функция публикации данных датчиков на сервер
def publish_sensor_data(client):
    global app
    if app:
        # Берем последние данные температуры и времени
        current_time = time.time() - app.start_time
        if app.temperatures:
            temperature = app.temperatures[-1]
        else:
            temperature = 20  # Если данных нет, используем дефолтное значение

        # Создаем JSON-объект с данными
        sensor_data = {
            "temperature": temperature,
            "time": round(current_time, 2)  # Время с начала работы
        }

        # Публикуем данные
        client.publish(TOPIC_SENSOR, json.dumps(sensor_data))
        print(f"Данные опубликованы: {sensor_data}")


# Инициализация MQTT-клиента
def start_mqtt(app_instance):
    global app
    app = app_instance  # Сохраняем ссылку на объект приложения
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message

    client.connect(BROKER, PORT, keepalive=60)

    # Начинаем публикацию данных датчиков раз в период
    client.loop_start()
    while True:
        publish_sensor_data(client)
        time.sleep(app.update_interval.get())  # Интервал обновления данных
