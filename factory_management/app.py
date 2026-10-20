"""Application entry point."""
import tkinter as tk
from .ui.main_window import FactoryManagementSystem

def main() -> None:
    root = tk.Tk()
    FactoryManagementSystem(root)
    root.mainloop()

if __name__ == "__main__":
    main()
