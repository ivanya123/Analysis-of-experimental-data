import tkinter as tk
import tkinter.filedialog as fd
from tkinter import messagebox
from tkinter import ttk
import os
from data_class_communication.class_for_communication import Temperature, Strength, Couple, Plot
from analytical_functions.analysis_functions import extract_param_path, list_all_path_strength_temperature
import shelve
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import (
    FigureCanvasTkAgg, NavigationToolbar2Tk)
from tkinter_models.function import enter, leave, open_folder_in_explorer, create_widgets_experiments
from typing import Any


def extract_main_path() -> str:
    """
    :return: str - путь к основной папке, где будут находится наши файлы и база данных. Если такого файла не найдено,
    то функция предложит создать папку или выбрать к ней путь.
    """
    try:
        with open("Config.txt", "r") as f:
            main_path = f.readlines()
            return main_path[0].split(':', 1)[1].strip()
    except FileNotFoundError:
        main_path = fd.askdirectory(title="Выберите основную папку для хранения", initialdir=os.getcwd())
        if main_path:
            with open("Config.txt", "w") as f:
                f.write(f"Main path: {main_path}\n")
            return main_path
        else:
            return extract_main_path()


def on_mouse_wheel(event, canvas):
    if event.delta:
        canvas.yview_scroll(-1 * int(event.delta / 120), "units")
    else:
        if event.num == 4:
            canvas.yview_scroll(-1, "units")
        elif event.num == 5:
            canvas.yview_scroll(1, "units")


def extract_search_path() -> str:
    """
    :return: str - путь к папке с данными, путь к вспомогательной папке где лежат исходники экспериментов.
    Если такой папки нет, предложит выбрать папку с файлами.
    """
    try:
        with open("Config.txt", "r") as f:
            search_path = f.readlines()
            return search_path[1].split(':', 1)[1].strip()
    except IndexError:
        search_path = fd.askdirectory(title="Выберите папку с данными", initialdir=os.getcwd())
        if search_path:
            with open("Config.txt", "a") as f:
                f.write(f"Search path: {search_path}\n")
            return search_path
        else:
            return extract_search_path()


def update_plot_db(path: str, **dict_params: dict[str, Any]):
    """
    Функция для обновления атрибутов эксземпляров классов в базу данных.
    :param path: - путь к базе данных.
    :param dict_params: dict - словарь с атрибутами эксземпляров классов и их значений.
    :return: None
    """
    db = shelve.open(path)
    for key in db.keys():
        couple = db[key]
        for name, items in dict_params.items():
            couple.plot.name = items
        db[key] = couple
    db.close()


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.combobox_material = None
        self.combobox_coating = None
        self.combobox_stage = None
        self.title("Analysis of Experimental data")
        self.geometry("1400x700")
        self.main_path = extract_main_path()
        self.search_path = extract_search_path()
        self.list_couple: list[Couple] = None
        self.canvas_plot = None
        self.create_widgets(material=None, coating=None, stage=None)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(2, weight=1)

        # self.label_main_path = tk.Label(self, text=self.main_path)
        # self.label_main_path.pack()

    def update_data_base(self) -> None:
        """
        Функция для обновления отображения базы данных в приложении.
        :return: None
        """
        self.list_couple = self.extract_data_base()
        material = None
        coating = None
        stage = None
        if self.combobox_material:
            material = self.combobox_material.get()
            coating = self.combobox_coating.get()
            stage = self.combobox_stage.get()
        for widget in self.winfo_children():
            widget.destroy()
        self.create_widgets(material, coating, stage)
        self.canvas.update_idletasks()
        self.canvas.config(scrollregion=self.canvas.bbox("all"))

    def extract_data_base(self):
        """
        Функция для извлечения данных из базы данных.
        :return: list[Couple] - список экземпляров класса Couple.
        """
        db = shelve.open(f"{self.main_path}/data_base/shelve_db")
        self.list_couple: list[Couple] = [db[key] for key in db.keys()]
        db.close()
        return self.list_couple

    def plot_show(self, couple: Couple) -> None:
        """
        Функция для отображения графиков.
        :param couple: принимает экземпляр класса Couple.
        :return: None
        """
        fig, ax1, ax2 = couple.plot.show_plots()
        if self.canvas_plot:
            self.canvas_plot.get_tk_widget().destroy()
        self.canvas_plot = FigureCanvasTkAgg(fig, master=self)
        self.canvas_plot.get_tk_widget().grid(row=0, column=2, padx=8, pady=8)
        self.canvas_plot.draw()
        plt.close()

    def clear_plot(self):
        if self.canvas_plot:
            self.canvas_plot.get_tk_widget().destroy()

    def create_widgets(self, material, coating, stage):
        self.scrollbar = tk.Scrollbar(orient=tk.VERTICAL)
        self.canvas = tk.Canvas(self, yscrollcommand=self.scrollbar.set)

        self.scrollbar.config(command=self.canvas.yview)
        self.canvas.grid(column=0, row=0, ipadx=8, ipady=8, sticky='nswe')
        self.scrollbar.grid(row=0, column=1, sticky='ns')

        self.viewing_frame = tk.Frame(self.canvas, width=600)
        self.viewing_frame.pack(padx=8, pady=8)
        self.canvas.create_window((0, 0), anchor='nw', window=self.viewing_frame)

        self.label_main_path = tk.Label(self.viewing_frame, text=self.main_path)
        self.label_main_path.grid(row=0, column=0, padx=8, pady=8, sticky='w')

        if self.list_couple:
            if self.combobox_material:
                create_widgets_experiments(self, self.viewing_frame, self.list_couple, material, coating, stage)
            else:
                create_widgets_experiments(self, self.viewing_frame, self.list_couple)

        self.canvas.update_idletasks()
        self.canvas["scrollregion"] = self.canvas.bbox("all")
        self.viewing_frame.bind('<MouseWheel>', lambda event: on_mouse_wheel(event, self.canvas))
        self.bind('<MouseWheel>', lambda event: on_mouse_wheel(event, self.canvas))

        self.frame_filter_update = tk.LabelFrame(self, text="Experiment filter", padx=8, pady=8)
        self.frame_filter_update.grid(padx=5, pady=5, sticky='we')
        self.button_update = tk.Button(self.frame_filter_update, text="Update", command=self.update_data_base, width=15)
        self.button_update.grid(row=0, column=0, padx=5, pady=5)
        if self.list_couple:
            self.combobox_material = ttk.Combobox(self.frame_filter_update,
                                                  values=list(
                                                      set([couple.strength.material for couple in self.list_couple])),
                                                  state='normal')
            self.combobox_material.grid(row=0, column=1, padx=8, pady=8)
            self.combobox_coating = ttk.Combobox(self.frame_filter_update,
                                                 values=list(
                                                     set([couple.strength.coating for couple in self.list_couple])),
                                                 state='normal')
            self.combobox_coating.grid(row=0, column=2, padx=8, pady=8)
            self.combobox_stage = ttk.Combobox(self.frame_filter_update,
                                               values=list(
                                                   set([couple.strength.stage for couple in self.list_couple])),
                                               state='normal')
            self.combobox_stage.grid(row=0, column=3, padx=8, pady=8)

        # self.search_widget = ttk.Combobox(self.frame_add_password,
        #                                   values=list(set([passw.company for passw in self.list_password.list_pass])),
        #                                   state='normal')

        self.create_data_frame = tk.LabelFrame(self, text="Create data")
        self.create_data_frame.grid(row=1, column=2, padx=8, pady=8)
        self.label_add = tk.Label(self.create_data_frame, text="Add data")
        self.label_add.grid(row=0, column=0, padx=8, pady=8)
        self.button_add = tk.Button(self.create_data_frame, text="Add", command=self.add_data, width=15)
        self.button_add.grid(row=0, column=1, padx=8, pady=8)
        self.button_full_data = tk.Button(self.create_data_frame, text="Create Full data", command=self.full_data,
                                          width=15)
        self.button_full_data.grid(row=0, column=2, padx=8, pady=8)

    def full_data(self):
        """
        Функция для для добавления данных в базу данных.
        list_all_path_strength_temperature - находит все папки где есть папки Сила и Температура
        :return: None
        """
        directory = fd.askdirectory(title="Выберите папку с данными", initialdir=self.search_path)
        list_tuple_strength_temperature = list_all_path_strength_temperature(directory)
        for strength, temperature in list_tuple_strength_temperature:
            material, coating, tool, stage = extract_param_path(strength)
            app_confirm = AddData(material, coating, tool, stage, strength)
            app_confirm.mainloop()
            material = app_confirm.material
            coating = app_confirm.coating
            tool = app_confirm.tool
            stage = app_confirm.stage
            speed = app_confirm.speed
            feed = app_confirm.feed
            app_confirm.destroy()
            try:
                strength = Strength(path_strength=strength,
                                    material=material,
                                    coating=coating,
                                    tool=tool,
                                    stage=stage,
                                    spindle_speed=speed,
                                    feed=feed)
                temperature = Temperature(path_temperature=temperature,
                                          material=material,
                                          coating=coating,
                                          tool=tool,
                                          stage=stage,
                                          spindle_speed=speed,
                                          feed=feed,
                                          couple_strength=strength)
                couple = Couple(strength=strength,
                                temperature=temperature)
                couple.save_file(self.main_path)
            except IndexError:
                continue

    def add_data(self):
        """
        Функция для добавления данных в базу данных. но только одиного экземпляра.
        :return:
        """
        dir_strength = fd.askdirectory(title="Выберите папку с силами", initialdir=self.search_path)
        dir_temperature = fd.askdirectory(title="Выберите папку с температурой", initialdir=dir_strength)
        material, coating, tool, stage = extract_param_path(dir_strength.replace('\\', '/'))
        app_confirm = AddData(material, coating, tool, stage, dir_strength)
        app_confirm.mainloop()
        material = app_confirm.material
        coating = app_confirm.coating
        tool = app_confirm.tool
        stage = app_confirm.stage
        speed = app_confirm.speed
        feed = app_confirm.feed
        app_confirm.destroy()
        strength = Strength(path_strength=dir_strength,
                            material=material,
                            coating=coating,
                            tool=tool,
                            stage=stage,
                            spindle_speed=speed,
                            feed=feed)
        temperature = Temperature(path_temperature=dir_temperature,
                                  material=material,
                                  coating=coating,
                                  tool=tool,
                                  stage=stage,
                                  spindle_speed=speed,
                                  feed=feed,
                                  couple_strength=strength)

        couple = Couple(strength=strength,
                        temperature=temperature)

        couple.save_file(self.main_path)

    def destroy(self):
        self.clear_plot()
        super().destroy()


class AddData(tk.Tk):
    """
    Окно для подтверждения данных при добавлени. т.к. функция extract_param_path может работать некореектно.
    """
    def __init__(self, material: str, coating: str, tool: str, stage: str, path_strength):
        super().__init__()
        self.title(path_strength)
        self.geometry("600x400")

        if 'ХН' in material:
            self.label_speed = tk.Label(self, text="Spindle Speed")
            self.label_speed.pack()
            self.entry_speed = tk.Entry(self)
            self.entry_speed.insert(0, "800")
            self.entry_speed.pack()

            self.label_feed = tk.Label(self, text="Feed")
            self.label_feed.pack()
            self.entry_feed = tk.Entry(self)
            self.entry_feed.insert(0, "53")
            self.entry_feed.pack()

        else:
            self.label_speed = tk.Label(self, text="Spindle Speed")
            self.label_speed.pack()
            self.entry_speed = tk.Entry(self)
            self.entry_speed.insert(0, "2000")
            self.entry_speed.pack()

            self.label_feed = tk.Label(self, text="Feed")
            self.label_feed.pack()
            self.entry_feed = tk.Entry(self)
            self.entry_feed.insert(0, "200")
            self.entry_feed.pack()

        self.label_material = tk.Label(self, text="Material")
        self.label_material.pack()
        self.entry_material = tk.Entry(self)
        self.entry_material.insert(0, material)
        self.entry_material.pack()

        self.label_coating = tk.Label(self, text="Coating")
        self.label_coating.pack()
        self.entry_coating = tk.Entry(self)
        self.entry_coating.insert(0, coating)
        self.entry_coating.pack()

        self.label_tool = tk.Label(self, text="Tool")
        self.label_tool.pack()
        self.entry_tool = tk.Entry(self)
        self.entry_tool.insert(0, tool)
        self.entry_tool.pack()

        self.label_stage = tk.Label(self, text="Stage")
        self.label_stage.pack()
        self.entry_stage = tk.Entry(self)
        self.entry_stage.insert(0, stage)
        self.entry_stage.pack()

        self.button_add = tk.Button(self, text="Confirm", command=self.confirm_data, width=15)
        self.button_add.pack(padx=10, pady=10)

    def confirm_data(self):
        self.material = self.entry_material.get()
        self.coating = self.entry_coating.get()
        self.tool = self.entry_tool.get()
        self.stage = self.entry_stage.get()
        self.speed = float(self.entry_speed.get())
        self.feed = float(self.entry_feed.get())
        self.quit()
