from __future__ import annotations
from pathlib import Path
from datetime import datetime
from typing import Tuple


import pandas as pd


from domain import DEFAULT_FILE_PATH, EJERCICIOS, REPS_PLAN, COLUMNS




# ---------- Creación / Migración ----------


def ensure_plan(path: Path) -> None:
    """Crea el Excel con el plan si no existe."""
    if not path.exists():
        data = []
        for week in (1, 2, 3, 4):
            for ex, target in zip(EJERCICIOS, REPS_PLAN[week]):
                data.append({
                    "Semana": week,
                    "Ejercicio": ex,
                    "Objetivo": target,
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
    idx = df.index[(df["Semana"] == week) & (df["Ejercicio"] == exercise)]
    if len(idx) == 0:
        return False
    df.loc[idx, "Reps/Seg Realizadas"] = done
    df.loc[idx, "Comentarios"] = comments
    df.loc[idx, "Ultima actualización"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
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
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = path.with_name(f"{path.stem}.backup_{ts}{path.suffix}")
        df.to_excel(backup_path, index=False)

    # Limpiar progreso
    for col in ["Reps/Seg Realizadas", "Comentarios", "Ultima actualización"]:
        if col in df.columns:
            df[col] = ""

    save_plan(path, df)