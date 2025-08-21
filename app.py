from tkinter import messagebox

try:
    import openpyxl
except Exception:
    print("[ERROR] falta 'openpyxl'. Instalá con: pip install openpyxl")
    raise

from ui_modern import App

def main() -> int:
    app = App(theme="superhero")
    print("Usando theme:", app.style.theme_use())
    app.mainloop()
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
    