import telebot
import server


def main():
    bot = telebot.TeleBot('8083786842:AAFzYRSDhvkv5UeWOEix7ukMrUpZFWNbC5Y')

    @bot.message_handler(content_types=['text'])
    def get_text_messages(message):
        if message.text == "/help" or message.text == "/start":
            bot.send_message(message.from_user.id,
                             "Команды:\n"
                             "/data - отображение данных о температуре\n"
                             "/manual - установить ручной режим работы\n"
                             "/auto - установить автоматический режим работы\n"
                             "/actuator - включение/выключение кондиционера (только в ручном режиме работы)")

        elif message.text == "/data":
            data = server.sensor_data
            data_str = "Данные:\n"
            if data:
                for k, v in data.items():
                    data_str += k + ": " + str(v)[:5] + "\n"
                bot.send_message(message.from_user.id, data_str)
            else:
                bot.send_message(message.from_user.id, "Данные ещё не сгенерировались, подождите")

        elif message.text == "/manual":
            server.app.auto_mode.set(0)
            server.app.toggle_mode()
            bot.send_message(message.from_user.id, "Включен ручной режим работы")

        elif message.text == "/auto":
            server.app.auto_mode.set(1)
            server.app.toggle_mode()
            bot.send_message(message.from_user.id,"Включен автоматический режим работы")

        elif message.text == "/actuator":
            if server.app.auto_mode.get() == 0:
                server.app.ac_on = not server.app.ac_on
                server.app.update_message_label()
                if server.app.ac_on:
                    bot.send_message(message.from_user.id, "Кондиционер включен")
                else:
                    bot.send_message(message.from_user.id, "Кондиционер выключен")
            else:
                bot.send_message(message.from_user.id,'Невозможно переключить режим работы кондиционера, установлен автоматический режим работы')

        else:
            bot.send_message(message.from_user.id, "Команда не распознана. Напишите /help.")

    bot.polling(non_stop=True, interval=0)
