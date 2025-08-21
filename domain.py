from __future__ import annotations
from pathlib import Path
from typing import List, Dict

DEFAULT_FILE_PATH = Path(r"C:\\ProjectsZeqe\\PythonCodigo\\plan_calistenia_progreso.xlsx")

EJERCICIOS: List[str] = [
    "Dominadas asistidas / negativas",
    "Fondos asistidos",
    "Lagartijas",
    "Remo invertido",
    "Sentadillas",
    "Plancha frontal (seg)",
    "Colgarse de la barra (seg)",
]

# Objetivos semanales
REPS_PLAN: Dict[int, List[int]] = {
1: [5, 6, 8, 6, 12, 20, 15],
2: [6, 7, 9, 7, 14, 25, 20],
3: [6, 8, 10, 8, 15, 30, 25],
4: [8, 9, 12, 9, 16, 30, 30],
}

# Esquema de las columnas de mi archivo excel

COLUMNS: List[str] = [
"Semana",
"Ejercicio",
"Objetivo",
"Reps/Seg Realizadas",
"Comentarios",
"Ultima actualización",
]

def format_number(val: object) -> str:
    '''
    función para formatear números y que se vean bien, según el dato que sea, INT o FLOAT
    '''
    try:
        num = float(str(val).replace(",", "."))
        return str(int(num)) if num.is_integer() else str(round(num, 2))
    except (ValueError, TypeError):
        return str(val) if val is not None else ""