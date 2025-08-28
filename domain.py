from pathlib import Path

DEFAULT_FILE_PATH = Path(r"C:\ProjectsZeqe\PythonCodigo\plan_calistenia_progreso.xlsx")

COLUMNS = [
    "Semana",
    "Ejercicio",
    "Objetivo",
    "Reps/Seg Realizadas",
    "Comentarios",
    "Ultima actualización",
]

def format_number(val: object) -> str:
    s = "" if val is None else str(val).strip()
    if s == "" or s.lower() == "nan":
        return ""
    try:
        num = float(s.replace(",", "."))
        if num != num:  # NaN
            return ""
        return str(int(num)) if float(num).is_integer() else str(round(num, 2))
    except (ValueError, TypeError):
        return s
