from __future__ import annotations
from pathlib import Path
from datetime import datetime
from typing import Tuple


import pandas as pd


from domain import DEFAULT_FILE_PATH, EJERCICIOS, REPS_PLAN, COLUMNS


# --- Gestión de ejercicios dinámicos ---
EXERCISES_FILE = Path(__file__).resolve().parent / "exercises.txt"
DEFAULT_EXERCISES = [
    "Dominadas asistidas / negativas",
    "Fondos asistidos",
    "Lagartijas",
    "Remo invertido",
    "Sentadillas",
    "Plancha frontal (seg)",
    "Colgarse de la barra (seg)",
    # Podés sumar muchas más por defecto si querés
    
]

# Objetivos sugeridos (principiante). Números son reps; strings con "s" indican segundos.
SUGGESTED_OBJECTIVES: dict[str, str | float | int] = {
    # Tirón
    "Dominadas asistidas / negativas": 5,
    "Dominadas estrictas": 3,
    "Dominadas supinas (chin-ups)": 4,
    "Dominadas agarre neutro": 4,
    "Remo invertido": 8,
    "Remo invertido con pies elevados": 6,

    # Empuje
    "Flexiones (lagartijas)": 10,
    "Flexiones inclinadas": 12,
    "Flexiones declinadas": 8,
    "Flexiones diamante": 6,
    "Lagartijas": 10,
    "Lagartijas arqueras": 6,
    "Fondos asistidos": 6,
    "Fondos en paralelas": 5,
    "Pike push-ups": 6,

    # Piernas
    "Sentadillas": 15,
    "Sentadillas búlgaras": 8,
    "Zancadas": 10,
    "Pistol squat asistida": 4,

    # Core / isométricos
    "Plancha frontal (seg)": "30s",
    "Plancha lateral (seg)": "25s",
    "Abdominales con rueda": 6,
    "Elevaciones de rodillas en barra": 6,
    "Elevaciones de piernas en barra": 4,
    "Hollow hold (seg)": "25s",
    "Dead bug": 10,

    # Espalda baja / estabilidad
    "Superman": 10,
    "Superman hold": "20s",
    "Perro de caza (Bird-dog)": 10,
    "Puente de glúteos": 12,

    # Agarre / colgar
    "Colgarse de la barra (seg)": "20s",
    "Colgar activo escapular (seg)": "15s",

    # Variantes técnicas (valores suaves)
    "Tuck planche hold (asistido)": "10s",
    "Front lever tuck hold": "8s",
    "Back lever tuck hold": "8s",
}

def _coerce_objective_value(obj: str | float | int) -> str:
    """Devuelve un string para guardar en Excel: números como '12' y tiempos como '30s'."""
    if isinstance(obj, (int, float)):
        # Entero si es casi entero, de lo contrario dejamos con un decimal
        if isinstance(obj, float) and abs(obj - round(obj)) < 1e-6:
            return str(int(round(obj)))
        return str(obj)
    return str(obj).strip()

def suggest_objective_for(exercise: str) -> str | None:
    """Busca un objetivo sugerido por nombre exacto o por heurística de palabras clave."""
    # 1) match exacto
    if exercise in SUGGESTED_OBJECTIVES:
        return _coerce_objective_value(SUGGESTED_OBJECTIVES[exercise])

    # 2) heurísticas simples
    name = exercise.lower()
    if "plancha" in name or "hold" in name or "colgar" in name:
        return "20s"
    if "elevaciones" in name or "rodillas" in name or "piernas" in name:
        return "6"
    if "flexiones" in name or "lagartijas" in name or "fondos" in name or "remo" in name:
        return "8"
    if "sentadilla" in name or "zancada" in name or "pistol" in name:
        return "10"
    # default
    return None


def ensure_exercises_store() -> None:
    EXERCISES_FILE.parent.mkdir(parents=True, exist_ok=True)
    if not EXERCISES_FILE.exists():
        EXERCISES_FILE.write_text("\n".join(DEFAULT_EXERCISES), encoding="utf-8")

def load_exercises() -> list[str]:
    # Delego al parser nuevo (excluye líneas con '#')
    exs, _ = load_exercises_with_categories()
    return exs

def load_exercises_with_categories() -> tuple[list[str], dict[str, str]]:
    """
    Lee exercises.txt y devuelve:
      - lista de ejercicios (sin líneas de comentario)
      - mapa ejercicio -> categoría (tomada de la última línea que empieza con '#')
    """
    ensure_exercises_store()
    lines = EXERCISES_FILE.read_text(encoding="utf-8").splitlines()

    current_cat = None
    exercises: list[str] = []
    cat_map: dict[str, str] = {}

    for raw in lines:
        ln = raw.strip()
        if not ln:
            continue
        if ln.startswith("#"):
            # sección/categoría
            current_cat = ln.lstrip("#").strip() or None
            continue
        # es ejercicio
        exercises.append(ln)
        cat_map[ln] = current_cat or "General"

    return exercises, cat_map


def save_exercises(ex_list: list[str]) -> None:
    ensure_exercises_store()
    # quitar duplicados y vacíos manteniendo orden
    seen = set()
    cleaned = []
    for x in ex_list:
        x = x.strip()
        if x and x not in seen:
            seen.add(x)
            cleaned.append(x)
    EXERCISES_FILE.write_text("\n".join(cleaned), encoding="utf-8")


# ---------- Creación / Migración ----------


def ensure_plan(path: Path) -> None:
    if not path.exists():
        data = []
        # ejercicios desde el store dinámico
        exercises = load_exercises()
        for week in (1, 2, 3, 4):
            for ex in exercises:
                # si tenés REPS_PLAN y coincide el índice, se puede mapear;
                # como ahora es abierto, dejamos Objetivo vacío:
                data.append({
                    "Semana": week,
                    "Ejercicio": ex,
                    "Objetivo": "",
                    "Reps/Seg Realizadas": "",
                    "Comentarios": "",
                    "Ultima actualización": "",
                })
        df = pd.DataFrame(data, columns=COLUMNS)
        df.to_excel(path, index=False)




def _ensure_columns(df: pd.DataFrame) -> Tuple[pd.DataFrame, bool]:
    """Garantiza columnas esperadas; si agrega, devuelve modified=True."""
    modified = False
    for col in COLUMNS:
        if col not in df.columns:
            df[col] = ""
            modified = True
    # Reordenar si es posible
    try:
        df = df[COLUMNS]
    except Exception:
        pass
    return df, modified



def _migrate_file(path: Path) -> pd.DataFrame:
    df = pd.read_excel(path)
    df, modified = _ensure_columns(df)
    if modified:
        df.to_excel(path, index=False)
    return df


def load_plan_with_migration(path: Path) -> tuple[pd.DataFrame, bool]:
    df = pd.read_excel(path)
    df, modified = _ensure_columns(df)
    if modified:
        df.to_excel(path, index=False)
    return df, modified


def load_plan(path: Path) -> pd.DataFrame:
    return _migrate_file(path)




def save_plan(path: Path, df: pd.DataFrame) -> None:
    df.to_excel(path, index=False)




# ---------- Consultas / Actualizaciones ----------


def get_objective(df: pd.DataFrame, week: int, exercise: str) -> int | None:
    row = df.loc[(df["Semana"] == week) & (df["Ejercicio"] == exercise), "Objetivo"]
    return int(row.values[0]) if not row.empty else None




def update_entry(path: Path, week: int, exercise: str, done: str, comments: str) -> bool:
    df = load_plan(path)
    df, _ = _ensure_columns(df)

    idx = df.index[(df["Semana"] == week) & (df["Ejercicio"] == exercise)]
    now_ts = pd.Timestamp.now()

    # Normalizar "done": intentar número, si no, string
    try:
        done_val = float(str(done).replace(",", ".").strip())
    except Exception:
        done_val = str(done).strip()

    if len(idx) == 0:
        new_row = {
            "Semana": int(week),
            "Ejercicio": exercise,
            "Objetivo": "",  # se setea abajo si hay sugerido
            "Reps/Seg Realizadas": done_val,
            "Comentarios": comments,
            "Ultima actualización": now_ts,
        }
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        idx = df.index[(df["Semana"] == week) & (df["Ejercicio"] == exercise)]
    else:
        df.loc[idx, "Reps/Seg Realizadas"] = done_val
        df.loc[idx, "Comentarios"] = comments
        df.loc[idx, "Ultima actualización"] = now_ts

    # 👉 Autocompletar objetivo si está vacío
    try:
        cur_obj = str(df.loc[idx, "Objetivo"].values[0]).strip()
    except Exception:
        cur_obj = ""
    if not cur_obj or cur_obj.lower() == "nan":
        sug = suggest_objective_for(exercise)
        if sug is not None:
            df.loc[idx, "Objetivo"] = sug

    if "Ultima actualización" in df.columns:
        df["Ultima actualización"] = pd.to_datetime(df["Ultima actualización"], errors="coerce")

    save_plan(path, df)
    return True


def get_last_updates(path: Path, limit: int = 10) -> pd.DataFrame:
    df = load_plan(path)
    # Asegurar columnas y normalizar tipo
    df, _ = _ensure_columns(df)

    # Filtro de filas con algo cargado en "Reps/Seg Realizadas"
    # (convierte a str, recorta espacios, descarta vacíos y "nan")
    reps = (
        df["Reps/Seg Realizadas"]
        .astype(str)
        .str.strip()
    )
    mask_nonempty = reps.ne("") & reps.str.lower().ne("nan")

    filled = df[mask_nonempty].copy()
    if filled.empty:
        return filled

    # Ordenar por fecha si existe y es parseable
    if "Ultima actualización" in filled.columns:
        filled["_ts"] = pd.to_datetime(filled["Ultima actualización"], errors="coerce")
        filled = filled.sort_values("_ts", ascending=False)

    # Devolver solo las columnas esperadas (si existen)
    cols = [c for c in COLUMNS if c in filled.columns]
    return filled[cols].head(limit)





def weekly_summary_df(path: Path, week: int) -> pd.DataFrame:
    df = load_plan(path)
    df, _ = _ensure_columns(df)
    sub = df[df["Semana"] == week].copy()
    return sub[["Ejercicio", "Objetivo", "Reps/Seg Realizadas", "% Objetivo", "Comentarios", "Ultima actualización"]]



def reset_progress(path: Path, create_backup: bool = True) -> None:
    """
    Limpia las columnas de progreso y deja el plan en estado inicial.
    Conserva semanas/ejercicios/objetivos. Opcionalmente crea un backup.
    """
    df, _ = load_plan_with_migration(path)

    # Backup opcional
    if create_backup:
        ts = datetime.now().strftime("%D%m%y")
        backup_path = path.with_name(f"{path.stem}.backup_{ts}{path.suffix}")
        df.to_excel(backup_path, index=False)

    # Limpiar progreso
    for col in ["Reps/Seg Realizadas", "Comentarios", "Ultima actualización"]:
        if col in df.columns:
            df[col] = ""

    save_plan(path, df)