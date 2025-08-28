from __future__ import annotations
import pandas as pd
from matplotlib.figure import Figure

def _coerce_numeric_series(s: pd.Series) -> pd.Series:
    """
    Convierte una serie a float de forma tolerante:
    - strings con coma decimal
    - '30s' -> 30
    - 'nan' / '' -> NaN
    """
    if s is None:
        return pd.Series(dtype="float64")
    s = s.astype(str).str.strip().str.lower().str.replace(",", ".", regex=False)
    s = s.str.replace(r"s$", "", regex=True).str.strip()
    s = s.mask(s.isin(["", "nan", "none"]))
    return pd.to_numeric(s, errors="coerce")

def _choose_freq(period_sel: str) -> str:
    if period_sel == "Diario":
        return "D"
    if period_sel == "Mensual":
        return "ME"  # 'M' está deprecado -> usar MonthEnd
    return "W"  # Semanal (default)

def build_performance_figure(df: pd.DataFrame, period_sel: str, ex_sel: str | None) -> Figure:
    """
    Espera columnas:
      - 'Ultima actualización'
      - 'Reps/Seg Realizadas'
      - 'Objetivo'
      - 'Ejercicio'
    Devuelve una Figure lista para embebido.
    """
    if df is None or df.empty:
        raise ValueError("No hay datos para graficar.")

    # --- Copia y normalizaciones ---
    df = df.copy()
    # Fecha
    df["_ts"] = pd.to_datetime(df["Ultima actualización"], errors="coerce")
    df = df[pd.notna(df["_ts"])]
    if df.empty:
        raise ValueError("No hay fechas válidas para graficar. Cargá datos con fecha.")

    # Numéricos: reps y objetivo
    reps = _coerce_numeric_series(df.get("Reps/Seg Realizadas"))
    obj  = _coerce_numeric_series(df.get("Objetivo"))
    df["pct_obj"] = (reps / obj) * 100.0
    # Filtrar filas válidas
    df = df[pd.notna(df["pct_obj"]) & pd.notna(df["_ts"]) & (obj > 0)]
    if df.empty:
        raise ValueError("No hay valores numéricos suficientes (reps/objetivo) para graficar.")

    # Filtro por ejercicio (si corresponde)
    if ex_sel and ex_sel != "Todos":
        df = df[df["Ejercicio"] == ex_sel]
        if df.empty:
            raise ValueError("No hay datos para el ejercicio seleccionado.")

    # --- Agregación por periodo ---
    freq = _choose_freq(period_sel or "Semanal")
    grp = (
        df.set_index("_ts")
          .groupby(pd.Grouper(freq=freq))["pct_obj"]
          .mean()
          .dropna()
    )
    if grp.empty:
        raise ValueError("No hay datos agregados para ese período. Cargá más registros.")

    # --- Construcción de la figura ---
    fig = Figure(figsize=(7.8, 3.2), dpi=100)
    ax = fig.add_subplot(111)

    # Estética: línea + marcadores, banda 80-120%, línea 100%
    ax.plot(grp.index, grp.values, marker="o", linewidth=1.8)
    ax.axhline(100, linestyle="--", linewidth=1, alpha=0.9)
    ax.fill_between(grp.index, 80, 120, alpha=0.12)

    # Ejes y rótulos
    ax.set_ylabel("% del objetivo (promedio)")
    ax.set_xlabel("Tiempo")
    titulo_ej = ex_sel if ex_sel and ex_sel != "Todos" else "Todos los ejercicios"
    ax.set_title(f"Desempeño {period_sel.lower() if period_sel else 'semanal'} – {titulo_ej}")

    # Límites y grilla
    ymax = max(100, min(160, (float(grp.max()) // 10 + 3) * 10))
    ax.set_ylim(0, ymax)
    ax.grid(True, linestyle=":", linewidth=0.6, alpha=0.7)

    # Fechas legibles
    fig.autofmt_xdate(rotation=30)

    return fig
