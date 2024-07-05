import os
import subprocess


def open_folder_in_explorer(path):
    if os.path.isdir(path):
        os.startfile(path)
    else:
        print("Path is not a directory")


def enter(event, label):
    label.config(bg="lightblue")

def leave(event, label):
    label.config(bg="white")






if __name__ == "__main__":
    open_folder_in_explorer(r"C:\Users\aples\PycharmProjects\Analysis-of-experimental-data\files")