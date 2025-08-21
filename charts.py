# charts.py
from __future__ import annotations
from typing import Optional
import pandas as pd
from matplotlib.figure import Figure


def build_performance_figure(
    df: pd.DataFrame,
    period_sel: str,
    ex_sel: Optional[str] = None,
) -> Figure:
    """
    Recibe un DataFrame con columnas: 'Ultima actualización', 'Objetivo',
    'Reps/Seg Realizadas', 'Ejercicio'. Devuelve una Figure de matplotlib.
    """
    if df.empty:
        raise ValueError("No hay datos para graficar.")

    # Preparación de timestamp y % objetivo
    df = df.copy()
    df["_ts"] = pd.to_datetime(df["Ultima actualización"], errors="coerce")

    def pct(row) -> Optional[float]:
        try:
            actual_raw = str(row["Reps/Seg Realizadas"]).replace(",", ".").strip()
            actual = float(actual_raw)
            objetivo = float(row["Objetivo"])
            return (actual / objetivo) * 100 if objetivo > 0 else None
        except Exception:
            return None

    df["pct_obj"] = df.apply(pct, axis=1)
    df = df.dropna(subset=["pct_obj", "_ts"])  # mantengo válidos
    if df.empty:
        raise ValueError("Cargá algunos registros primero.")

    # Filtro por ejercicio
    if ex_sel and ex_sel != "Todos":
        df = df[df["Ejercicio"] == ex_sel]
        if df.empty:
            raise ValueError("No hay datos para ese ejercicio.")

    # Agregación por periodo (usar 'ME' para mensual para evitar FutureWarning)
    if period_sel == "Diario":
        freq = "D"
    elif period_sel == "Mensual":
        freq = "ME"
    else:
        freq = "W"

    grp = (
        df.set_index("_ts")
          .groupby(pd.Grouper(freq=freq))["pct_obj"]
          .mean()
          .dropna()
    )
    if grp.empty:
        raise ValueError("No hay datos agregados para ese periodo.")

    # Construcción de la figura
    fig = Figure(figsize=(7.5, 3.0), dpi=100)
    ax = fig.add_subplot(111)
    ax.plot(grp.index, grp.values, marker="o")
    ax.set_ylabel("% del objetivo (promedio)")
    ax.set_xlabel("Tiempo")
    title_ex = ex_sel if ex_sel and ex_sel != "Todos" else "Todos los ejercicios"
    ax.set_title(f"Desempeño {period_sel.lower()} – {title_ex}")
    ax.grid(True, linestyle=":", linewidth=0.5)
    ax.set_ylim(0, max(100, min(140, (grp.max() // 10 + 2) * 10)))
    return fig
