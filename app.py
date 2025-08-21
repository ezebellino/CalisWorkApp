from tkinter import messagebox

try:
    import openpyxl
except Exception:
    print("[ERROR] falta 'openpyxl'. Instalá con: pip install openpyxl")
    raise

from ui import App

def main() -> int:
    app = App()
    app.mainloop()
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
    