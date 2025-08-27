from __future__ import annotations
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox


import ttkbootstrap as tb
from ttkbootstrap.constants import *
from ttkbootstrap.widgets import DateEntry
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


from domain import DEFAULT_FILE_PATH, EJERCICIOS, format_number
from data_layer import (
    ensure_plan,
    load_plan,
    load_plan_with_migration,
    get_objective,
    get_last_updates,
    weekly_summary_df,
    reset_progress,
    load_exercises,
    save_exercises,
    load_exercises_with_categories
)
from charts import build_performance_figure




class App(tb.Window):
    def __init__(self, theme: str = "flatly"):
        super().__init__(title="Seguimiento Calistenia", themename=theme)
        self.geometry("980x760")
        self.minsize(960, 720)


        # Estado
        self.file_path: Path = DEFAULT_FILE_PATH
        ensure_plan(self.file_path)
        self._chart_canvas: FigureCanvasTkAgg | None = None


        # Paleta (personalizable)
        self.primary = "#2563EB" # azul
        self.bg_card = self.style.colors.light # usa color del tema
        self.bg_page = self.style.colors.dark


        self._build_header()
        self._build_body()
        self._refresh_table()


    # ---------------- Header ----------------
    def _build_header(self):
        header = tb.Frame(self, padding=16)
        header.pack(fill=X)
        title = tb.Label(header, text="Seguimiento de Calistenia", font=("Segoe UI", 20, "bold"))
        title.pack(side=LEFT)
        tb.Button(header, text="Cambiar Excel…", bootstyle=SECONDARY, command=self._choose_file).pack(side=RIGHT, padx=6)
        tb.Button(header, text="Gestionar ejercicios…", bootstyle=INFO, command=self._manage_exercises).pack(side=RIGHT, padx=6)
        tb.Button(header, text="Resetear progreso", bootstyle=DANGER, command=self._on_reset_progress).pack(side=RIGHT, padx=6)


    # ---------------- Body (two rows) ----------------
    def _build_body(self):
        body = tb.Frame(self, padding=(16, 8, 16, 16))
        body.pack(fill=BOTH, expand=True)


        # Row 1: Form card
        card_form = tb.Labelframe(body, text="Cargar registro", padding=12, bootstyle=INFO)
        card_form.pack(fill=X)


        # Semana
        tb.Label(card_form, text="Semana:").grid(row=0, column=0, padx=6, pady=6, sticky=W)
        self.cbo_week = tb.Combobox(card_form, values=[1, 2, 3, 4], width=6, state="readonly")
        self.cbo_week.grid(row=0, column=1, padx=6, pady=6, sticky=W)
        self.cbo_week.bind("<<ComboboxSelected>>", self._update_objective_label)


        # Ejercicio (lista dinámica y editable, sin comentarios)
        tb.Label(card_form, text="Ejercicio:").grid(row=0, column=2, padx=6, pady=6, sticky=W)

        ex_list, self.ex_cat_map = load_exercises_with_categories()
        self.cbo_ex = tb.Combobox(card_form, values=ex_list, width=42, state="normal")
        self.cbo_ex.grid(row=0, column=3, padx=6, pady=6, sticky=W)
        self.cbo_ex.bind("<<ComboboxSelected>>", self._update_objective_label)

        # (opcional) setear uno por defecto
        if ex_list:
            self.cbo_ex.set(ex_list[0])

        # Etiqueta de categoría visible debajo del objetivo (o donde te guste)
        self.lbl_cat = tb.Label(card_form, text="Categoría: -")
        self.lbl_cat.grid(row=0, column=5, padx=6, pady=6, sticky=W)


        # Objetivo (solo lectura)
        self.lbl_obj = tb.Label(card_form, text="Objetivo: -", font=("Segoe UI", 10, "bold"))
        self.lbl_obj.grid(row=0, column=4, padx=6, pady=6, sticky=W)


        # Reps/Seg Realizadas
        tb.Label(card_form, text="Reps/Seg realizadas:").grid(row=1, column=0, padx=6, pady=6, sticky=W)
        self.ent_done = tb.Entry(card_form, width=12)
        self.ent_done.grid(row=1, column=1, padx=6, pady=6, sticky=W)


        # Comentarios
        tb.Label(card_form, text="Comentarios:").grid(row=1, column=2, padx=6, pady=6, sticky=W)
        self.ent_comments = tb.Entry(card_form, width=52)
        self.ent_comments.grid(row=1, column=3, columnspan=2, padx=6, pady=6, sticky=W)


        # Botones
        tb.Button(card_form, text="Guardar", bootstyle=SUCCESS, command=self._on_save).grid(row=2, column=0, padx=6, pady=8, sticky=W)
        tb.Button(card_form, text="Resumen semanal", bootstyle=PRIMARY, command=self._on_summary).grid(row=2, column=1, padx=6, pady=8, sticky=W)
        tb.Button(card_form, text="Recargar tabla", bootstyle=SECONDARY, command=self._refresh_table).grid(row=2, column=2, padx=6, pady=8, sticky=W)

        for i in range(5):
            card_form.grid_columnconfigure(i, weight=1)


        # Row 2: Table + Chart split
        split = tb.Panedwindow(body, orient=HORIZONTAL, bootstyle=LIGHT)
        split.pack(fill=BOTH, expand=True, pady=10)


        # Table card
        table_card = tb.Labelframe(split, text="Últimas cargas", padding=8)
        split.add(table_card, weight=3)


        cols = ("Semana", "Ejercicio", "Categoría", "Objetivo", "Reps/Seg Realizadas", "Comentarios", "Ultima actualización")
        self.tree = tb.Treeview(table_card, columns=cols, show="headings", height=16)
        numeric_cols = {"Semana", "Objetivo", "Reps/Seg Realizadas"}
        for c in cols:
            anchor = CENTER if c in numeric_cols else W
            self.tree.heading(c, text=c)
            # ancho un poco mayor para Ejercicio/Comentarios
            default_width = 120
            if c == "Ejercicio": default_width = 220
            if c == "Comentarios": default_width = 220
            if c == "Categoría": default_width = 140
            self.tree.column(c, anchor=anchor, width=default_width)
        self.tree.pack(fill=BOTH, expand=True)


        # Chart card
        chart_card = tb.Labelframe(split, text="Gráfica de desempeño", padding=8)
        split.add(chart_card, weight=2)


        # Controles del chart
        ctrl = tb.Frame(chart_card)
        ctrl.pack(fill=X)
        tb.Label(ctrl, text="Periodo:").pack(side=LEFT, padx=6)
        self.cbo_period = tb.Combobox(ctrl, values=["Diario", "Semanal", "Mensual"], width=10, state="readonly")
        self.cbo_period.current(1)
        self.cbo_period.pack(side=LEFT)


        tb.Label(ctrl, text="Ejercicio:").pack(side=LEFT, padx=(12, 6))
        ex_list_for_chart, _ = load_exercises_with_categories()
        self.cbo_ex_chart = tb.Combobox(ctrl, values=["Todos"] + ex_list_for_chart, width=32, state="readonly")
        self.cbo_ex_chart.current(0)
        self.cbo_ex_chart.pack(side=LEFT)


        tb.Button(ctrl, text="Actualizar gráfica", bootstyle=PRIMARY, command=self._plot_chart).pack(side=LEFT, padx=8)


        # wrapper para chart
        self.chart_wrap = tb.Frame(chart_card)
        self.chart_wrap.pack(fill=BOTH, expand=True, pady=6)


        # Status bar
        self.status_var = tk.StringVar(value="Listo.")
        tb.Separator(self).pack(fill=X)
        status = tb.Label(self, textvariable=self.status_var, anchor=W, padding=8)
        status.pack(fill=X)
        
        # ---------------- Handlers ----------------
    def _choose_file(self):
        path = filedialog.asksaveasfilename(
            title="Seleccionar/crear archivo Excel",
            defaultextension=".xlsx",
            filetypes=[("Excel", "*.xlsx"), ("Todos", "*.*")],
            initialfile=str(self.file_path.name),
        )
        if not path:
            return
        self.file_path = Path(path)
        ensure_plan(self.file_path)
        _, migrated = load_plan_with_migration(self.file_path)
        self._set_status("Migración aplicada: columnas faltantes fueron añadidas" if migrated else f"Usando: {self.file_path}")
        messagebox.showinfo("Archivo", f"Usando archivo: {self.file_path}")
        self._refresh_table()
        
    def _update_objective_label(self, *_):
        week = self.cbo_week.get()
        ex = self.cbo_ex.get()
        try:
            # si el usuario tipea un ejercicio nuevo que no está en el mapa,
            # mostramos "General" por defecto
            cat = self.ex_cat_map.get(ex, "General")
            self.lbl_cat.config(text=f"Categoría: {cat}")
        except Exception:
            self.lbl_cat.config(text="Categoría: -")

        if not (week and ex):
            self.lbl_obj.config(text="Objetivo: -")
            return
        try:
            df = load_plan(self.file_path)
            obj = get_objective(df, int(week), ex)
            self.lbl_obj.config(text=f"Objetivo: {obj if obj is not None else '-'}")
        except Exception:
            self.lbl_obj.config(text="Objetivo: -")


    def _on_save(self):
        if not self.cbo_week.get():
            messagebox.showwarning("Validación", "Seleccioná la semana (1-4).")
            return
        if not self.cbo_ex.get():
            messagebox.showwarning("Validación", "Seleccioná un ejercicio.")
            return
        done = self.ent_done.get().strip()
        comments = self.ent_comments.get().strip()
        from data_layer import update_entry
        ok = update_entry(self.file_path, int(self.cbo_week.get()), self.cbo_ex.get(), done, comments)
        if not ok:
            messagebox.showerror("Error", "No se pudo actualizar el registro.")
            return
        messagebox.showinfo("Guardado", "Registro guardado correctamente.")
        self._refresh_table()
        self._update_objective_label()
        
    def _on_summary(self):
        if not self.cbo_week.get():
            messagebox.showwarning("Validación", "Seleccioná la semana para el resumen.")
            return
        week = int(self.cbo_week.get())
        df = weekly_summary_df(self.file_path, week)
        if df.empty:
            messagebox.showinfo("Resumen", "No hay datos para esa semana.")
            return


        top = tb.Toplevel(self, title=f"Resumen Semana {week}")
        top.geometry("820x400")


        cols = list(df.columns)
        tree = tb.Treeview(top, columns=cols, show="headings")
        numeric_cols = {"Objetivo", "Reps/Seg Realizadas", "% Objetivo"}
        for c in cols:
            anchor = CENTER if c in numeric_cols else W
            tree.heading(c, text=c)
            tree.column(c, width=120 if c not in ("Ejercicio", "Comentarios") else 260, anchor=anchor)
        tree.pack(fill=BOTH, expand=True, side=LEFT, padx=8, pady=8)


        sb = tb.Scrollbar(top, orient=VERTICAL, command=tree.yview)
        tree.configure(yscroll=sb.set)
        sb.pack(side=RIGHT, fill=Y)


        for _, r in df.iterrows():
            values = [
            r.get("Ejercicio", ""),
            format_number(r.get("Objetivo", "")),
            format_number(r.get("Reps/Seg Realizadas", "")),
            format_number(r.get("% Objetivo", "")),
            r.get("Comentarios", ""),
            r.get("Ultima actualización", ""),
            ]
            tree.insert("", tk.END, values=values)
                
    def _on_reset_progress(self):
        if not self.file_path:
            messagebox.showwarning("Reset", "No hay archivo seleccionado.")
            return
        ok = messagebox.askyesno(
            "Resetear progreso",
            "Se borrarán repeticiones, comentarios y fechas (se creará backup).\n\n¿Deseás continuar?",
        )
        if not ok:
            return
        try:
            reset_progress(self.file_path, create_backup=True)
            self._set_status("Progreso reseteado. Backup creado.")
            messagebox.showinfo("Reset", "Progreso reseteado correctamente.")
            self._refresh_table()
            self._update_objective_label()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo resetear el progreso.\n{e}")
            
    def _plot_chart(self):
        try:
            df, _ = load_plan_with_migration(self.file_path)
            fig = build_performance_figure(df, self.cbo_period.get() or "Semanal", self.cbo_ex_chart.get())


            if self._chart_canvas is not None:
                self._chart_canvas.get_tk_widget().destroy()
                self._chart_canvas = None


            self._chart_canvas = FigureCanvasTkAgg(fig, master=self.chart_wrap)
            self._chart_canvas.draw()
            self._chart_canvas.get_tk_widget().pack(fill=BOTH, expand=True)
            self._set_status("Gráfica actualizada.")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo generar la gráfica.\n{e}")


    def _refresh_table(self):
        # Limpiar filas actuales
        if hasattr(self, "tree"):
            for item in self.tree.get_children():
                self.tree.delete(item)

        # Cargar/migrar plan
        df, migrated = load_plan_with_migration(self.file_path)
        self._set_status("Migración aplicada: columnas faltantes añadidas." if migrated else "Listo.")

        try:
            # Traer últimas cargas ya ordenadas
            df = get_last_updates(self.file_path, limit=20)
            if df.empty:
                return

            # Normalizar reps para evitar errores raros
            if "Reps/Seg Realizadas" in df.columns:
                df["Reps/Seg Realizadas"] = df["Reps/Seg Realizadas"].astype(str).str.strip()

            # Insertar filas
            for _, r in df.iterrows():
                semana = format_number(r.get("Semana", ""))
                ejercicio = r.get("Ejercicio", "")
                categoria = self.ex_cat_map.get(ejercicio, "General")  # <- NUEVO
                objetivo = format_number(r.get("Objetivo", ""))
                reps = format_number(r.get("Reps/Seg Realizadas", ""))
                comentarios = r.get("Comentarios", "")
                ultima = r.get("Ultima actualización", "")
                self.tree.insert("", tk.END, values=[semana, ejercicio, categoria, objetivo, reps, comentarios, ultima])

        except Exception as e:
            messagebox.showerror("Error", f"No se pudo cargar la tabla.\n{e}")
    
    
    def _set_status(self, text: str):
        self.status_var.set(text)
        



    def _manage_exercises(self):
        top = tb.Toplevel(self)
        top.title("Gestionar ejercicios")
        top.geometry("520x420")

        frame = tb.Frame(top, padding=10)
        frame.pack(fill=BOTH, expand=True)

        tb.Label(frame, text="Ejercicios (uno por línea):").pack(anchor=W)

        # ⚠️ Tkinter Text (no ttkbootstrap)
        txt = tk.Text(frame, height=16)
        txt.pack(fill=BOTH, expand=True, pady=6)

        # cargar actuales
        current = load_exercises()
        txt.insert("1.0", "\n".join(current))

        btns = tb.Frame(frame)
        btns.pack(fill=X)

        def _save_and_close():
            lines = txt.get("1.0", "end").splitlines()
            save_exercises(lines)
            # refrescar combos y mapa de categorías
            exs, self.ex_cat_map = load_exercises_with_categories()
            self.cbo_ex.configure(values=exs)
            self.cbo_ex_chart.configure(values=["Todos"] + exs)
            # si el ejercicio actual ya no existe, vaciamos selección
            if self.cbo_ex.get() not in exs:
                self.cbo_ex.set(exs[0] if exs else "")
            # refrescá la etiqueta de categoría
            self._update_objective_label()
            top.destroy()

        tb.Button(btns, text="Guardar", bootstyle=SUCCESS, command=_save_and_close).pack(side=RIGHT, padx=6)
        tb.Button(btns, text="Cancelar", bootstyle=SECONDARY, command=top.destroy).pack(side=RIGHT)
