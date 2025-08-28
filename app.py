from tkinter import messagebox

try:
    import openpyxl
except Exception:
    print("[ERROR] falta 'openpyxl'. Instalá con: pip install openpyxl")
    raise

from ui_modern import App
'''
Temas claros (light)

flatly

cosmo

litera

lumen

minty

pulse

sandstone

united

yeti

Temas oscuros (dark)

cyborg

darkly

solar

superhero

Neutros / especiales

journal

morph

'''
def main() -> int:
    app = App(theme="solar")
    app.mainloop()
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
    