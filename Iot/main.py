import tkinter as tk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import random
import time
import server
import telegram_bot

class IoTDeviceApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Управление температурой IoT")

        self.auto_mode = tk.BooleanVar(value=True)  # Автоматический режим
        self.ac_on = False  # Состояние кондиционера
        self.temperatures = []  # Список температур
        self.times = []  # Список времени
        self.start_time = time.time()  # Время старта
        self.manual_ac_button = None  # Кнопка включения кондиционера в ручном режиме

        # Частота обновления графика
        self.update_interval = tk.IntVar(value=1)  # Частота обновления графика, по умолчанию 1 секунда

        # График
        self.fig, self.ax = plt.subplots()
        self.line, = self.ax.plot([], [], 'r-', label="Температура")
        self.ac_limit_line, = self.ax.plot([], [], 'b--', label="Порог AC")
        self.ax.set_ylim(15, 35)
        self.ax.set_xlim(0, 60)
        self.ax.set_xlabel("Время (с)")
        self.ax.set_ylabel("Температура (°C)")
        self.ax.legend()

        self.canvas = FigureCanvasTkAgg(self.fig, master=self.root)
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # Панель управления
        control_frame = tk.Frame(self.root)
        control_frame.pack(side=tk.BOTTOM, fill=tk.X)

        tk.Radiobutton(control_frame, text="Авто", variable=self.auto_mode, value=True,
                       command=self.toggle_mode).pack(side=tk.LEFT)
        tk.Radiobutton(control_frame, text="Ручной", variable=self.auto_mode, value=False,
                       command=self.toggle_mode).pack(side=tk.LEFT)

        self.ac_limit = tk.DoubleVar(value=26.0)  # Порог для кондиционера
        self.ac_limit_scale = tk.Scale(control_frame, from_=15, to=35, orient=tk.HORIZONTAL,
                                       variable=self.ac_limit, label="Порог AC")
        self.ac_limit_scale.pack(side=tk.LEFT)

        self.time_slider = tk.Scale(control_frame, from_=1, to=30, orient=tk.HORIZONTAL,
                                    variable=self.update_interval, label="Частота обновления (с)")
        self.time_slider.pack(side=tk.LEFT)

        # Кнопка для включения/выключения кондиционера в ручном режиме
        self.manual_ac_button = tk.Button(control_frame, text="Включить/Выключить кондиционер",
                                          command=self.toggle_ac, state=tk.DISABLED)
        self.manual_ac_button.pack(side=tk.LEFT)

        self.message_label = None  # Хранение метки сообщения
        self.update_plot()

    def toggle_mode(self):
        if self.auto_mode.get():
            self.manual_ac_button.config(state=tk.DISABLED)  # Отключение кнопки в авто режиме
        else:
            self.manual_ac_button.config(state=tk.NORMAL)  # Включение кнопки в ручном режиме
        self.update_message_label()

    def toggle_ac(self):
        self.ac_on = not self.ac_on  # Переключаем состояние кондиционера
        self.update_message_label()

    def update_plot(self):
        current_time = time.time() - self.start_time

        # Генерация температуры с плавными изменениями
        if len(self.temperatures) == 0:
            new_temp = random.uniform(20, 30)
        elif self.ac_on:
            new_temp = self.temperatures[-1] + random.uniform(-0.5, 0.5)
        else:
            new_temp = self.temperatures[-1] + random.uniform(-0.2, 1.0)
            new_temp = max(15, min(35, new_temp))  # Ограничение температуры

        # Проверка на включение кондиционера
        if new_temp >= self.ac_limit.get():
            if self.auto_mode.get():
                self.ac_on = True  # Автоматическое включение кондиционера
            self.update_message_label()
        else:
            if self.auto_mode.get():
                self.ac_on = False  # Автоматическое выключение кондиционера
            self.update_message_label()

        # Обновление температуры
        if self.ac_on:
            new_temp -= 0.5  # Симуляция работы кондиционера (понижение температуры)

        self.temperatures.append(new_temp)
        self.times.append(current_time)

        # Обновление данных графика
        self.line.set_data(self.times, self.temperatures)
        self.ac_limit_line.set_data(self.times, [self.ac_limit.get()] * len(self.times))

        self.ax.set_xlim(0, max(60, current_time + 10))

        self.canvas.draw()
        self.root.after(self.update_interval.get() * 1000, self.update_plot)  # Регулировка частоты обновления графика

    def update_message_label(self):
        if self.message_label is not None:
            self.message_label.destroy()  # Удаление предыдущего сообщения

        if self.ac_on:
            self.message_label = tk.Label(self.root, text="Кондиционер ВКЛ", fg="green")
        else:
            self.message_label = tk.Label(self.root, text="Кондиционер ВЫКЛ", fg="black")  # Черный цвет в обоих режимах

        self.message_label.pack(side=tk.TOP)


if __name__ == "__main__":
    root = tk.Tk()
    app = IoTDeviceApp(root)

    # Запускаем MQTT клиент
    import threading
    mqtt_thread = threading.Thread(target=server.start_mqtt, args=(app,))
    mqtt_thread.daemon = True
    mqtt_thread.start()

    bot_thread = threading.Thread(target=telegram_bot.main)
    bot_thread.daemon = True  # Устанавливаем поток как демон, чтобы он завершился при закрытии основного окна
    bot_thread.start()

    root.mainloop()