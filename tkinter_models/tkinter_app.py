import tkinter as tk
import tkinter.filedialog as fd
from tkinter import messagebox
import os
from data_class_communication.class_for_communication import Temperature, Strength, Couple
from analytical_functions.analysis_functions import extract_param_path
import shelve


def extract_main_path():
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


def extract_search_path():
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


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Analysis of Experimental data")
        self.geometry("800x600")
        self.main_path = extract_main_path()
        self.search_path = extract_search_path()
        self.list_couple: list[Couple] = None
        self.create_widgets()

        # self.label_main_path = tk.Label(self, text=self.main_path)
        # self.label_main_path.pack()
    def update_data_base(self):
        self.list_couple = self.extract_data_base()
        self.viewing_frame.destroy()
        self.create_data_frame.destroy()
        self.create_widgets()

    def extract_data_base(self):
        db = shelve.open(f"{self.main_path}/data_base/shelve_db")
        self.list_couple = [db[key] for key in db.keys()]
        db.close()
        return self.list_couple

    def create_widgets(self):
        self.viewing_frame = tk.LabelFrame(self, text="Viewing data")
        self.viewing_frame.pack(fill="x", padx=8, pady=8)
        self.label_main_path = tk.Label(self.viewing_frame, text=self.main_path)
        self.label_main_path.pack()
        if self.list_couple:
            for couple in self.list_couple:
                label = tk.Label(self.viewing_frame, text=f"{couple}")
                label.pack()
        self.button_update = tk.Button(self.viewing_frame, text="Update", command=self.update_data_base, width=15)
        self.button_update.pack(padx=10, pady=10)

        self.create_data_frame = tk.LabelFrame(self, text="Create data")
        self.create_data_frame.pack(fill="x", padx=8, pady=8)
        self.label_add = tk.Label(self.create_data_frame, text="Add data")
        self.label_add.grid(row=0, column=0, padx=8, pady=8)
        self.button_add = tk.Button(self.create_data_frame, text="Add", command=self.add_data, width=15)
        self.button_add.grid(row=0, column=1, padx=8, pady=8)

    def add_data(self):
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


class AddData(tk.Tk):
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
        self.button_add.pack()

    def confirm_data(self):
        self.material = self.entry_material.get()
        self.coating = self.entry_coating.get()
        self.tool = self.entry_tool.get()
        self.stage = self.entry_stage.get()
        self.speed = float(self.entry_speed.get())
        self.feed = float(self.entry_feed.get())
        self.quit()


if __name__ == "__main__":
    app = App()
    app.mainloop()
