"""CloudPad — lightweight notepad with Supabase cloud save.
Windows + Linux, pure Python standard library,
target: Intel Celeron + HDD, under 100 MB RAM."""
import tkinter as tk

from frontend.main_window import MainWindow


def main():
    root = tk.Tk()
    MainWindow(root)
    root.mainloop()


if __name__ == "__main__":
    main()