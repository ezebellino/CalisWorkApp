import pandas as pd

data = []
weeks = [1, 2, 3, 4]
exercises = [
    "Dominadas asistidas / negativas",
    "Fondos asistidos",
    "Lagartijas",
    "Remo invertido",
    "Sentadillas",
    "Plancha frontal (seg)",
    "Colgarse de la barra (seg)"
]

reps_plan = {
    1: [5, 6, 8, 6, 12, 20, 15],
    2: [6, 7, 9, 7, 14, 25, 20],
    3: [6, 8, 10, 8, 15, 30, 25],
    4: [8, 9, 12, 9, 16, 30, 30]
}

for week in weeks:
    for ex, target in zip(exercises, reps_plan[week]):
        data.append({
            "Semana": week,
            "Ejercicio": ex,
            "Objetivo": target,
            "Reps/Seg Realizadas": "",
            "Comentarios": ""
        })

df = pd.DataFrame(data)

file_path = r"C:\ProjectsZeqe\PythonCodigo\plan_calistenia_progreso.xlsx"
df.to_excel(file_path, index=False)

print(f"Archivo guardado en: {file_path}")
