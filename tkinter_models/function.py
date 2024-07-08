import os
import subprocess
import tkinter as tk
from data_class_communication.class_for_communication import Temperature, Strength, Couple, Plot


def open_folder_in_explorer(path: str) -> None:
    if os.path.isdir(path):
        os.startfile(path)
    else:
        print("Path is not a directory")


def enter(event: str, label: tk.Label) -> None:
    label.config(bg="lightblue")


def leave(event, label: tk.Label) -> None:
    label.config(bg="white")


def create_widgets_experiments(root: tk.Tk,
                               frame: tk.Frame,
                               list_couple: list[Couple],
                               material: str = None,
                               coating: str = None,
                               stage: str = None):
    count = 1
    if material:
        list_couple = [couple for couple in list_couple if couple.strength.material == material]
    if coating:
        list_couple = [couple for couple in list_couple if couple.strength.coating == coating]
    if stage:
        list_couple = [couple for couple in list_couple if couple.strength.stage == stage]

    for couple in list_couple:
        label = tk.Label(frame, text=f'{couple}')
        label.grid(row=count, column=0, padx=10, pady=10)
        button = tk.Button(frame, text="Plot", command=lambda i=couple: root.plot_show(i),
                           width=10)
        button.grid(row=count, column=1, padx=10, pady=10)
        count += 1
        label.bind('<Enter>', lambda event, lab=label: enter(event, lab))
        label.bind('<Leave>', lambda event, lab=label: leave(event, lab))
        path_ = os.path.join(root.main_path, couple.strength.filename)
        label.bind("<Double-ButtonPress-1>", lambda event, path=path_: open_folder_in_explorer(path))


if __name__ == "__main__":
    open_folder_in_explorer(r"C:\Users\aples\PycharmProjects\Analysis-of-experimental-data\files")
