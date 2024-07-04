import tkinter as tk
import tkinter.filedialog as fd
from tkinter import messagebox
import os
from data_class_communication.class_for_communication import Temperature, Strength, Couple
from analytical_functions.analysis_functions import extract_param_path


def extract_main_path():
    try:
        with open("Config.txt", "r") as f:
            main_path = f.read()
            return main_path.split(':', 1)[1].strip()
    except FileNotFoundError as e:
        main_path = fd.askdirectory(title="Выберите основную папку",initialdir=os.getcwd())
        if main_path:
            with open("Config.txt", "w") as f:
                f.write(f"Main path: {main_path}")
            return main_path
        else:
            return extract_main_path()



class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Analysis of Experimental data")
        self.geometry("800x600")
        self.main_path = extract_main_path()



    # def create_widgets(self):


if __name__ == "__main__":
    app = App()
    app.mainloop()
