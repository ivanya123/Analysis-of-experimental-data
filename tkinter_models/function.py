import os
import subprocess
import tkinter as tk


def open_folder_in_explorer(path: str) -> None:
    if os.path.isdir(path):
        os.startfile(path)
    else:
        print("Path is not a directory")


def enter(event: str, label: tk.Label) -> None:
    label.config(bg="lightblue")


def leave(event, label: tk.Label) -> None:
    label.config(bg="white")


if __name__ == "__main__":
    open_folder_in_explorer(r"C:\Users\aples\PycharmProjects\Analysis-of-experimental-data\files")
