from __future__ import annotations
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path


from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


from domain import DEFAULT_FILE_PATH, COLUMNS, EJERCICIOS, format_number
from data_layer import (
    ensure_plan,
    load_plan,
    load_plan_with_migration,
    get_objective,
    get_last_updates,
    weekly_summary_df,
)
from charts import build_performance_figure




class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Seguimiento Calistenia – Tkinter")
        self.geometry("900x720")
        self.minsize(900, 680)


        # Estado
        self.file_path: Path = DEFAULT_FILE_PATH
        ensure_plan(self.file_path)
        self._chart_canvas: FigureCanvasTkAgg | None = None


        # UI
        self._build_menu()
        self._build_form()
        self._build_table()
        self._build_chart()
        self._build_statusbar()
        self._refresh_table()


    # ---------- Menú superior ----------
    def _build_menu(self):
        menubar = tk.Menu(self)
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Cambiar archivo Excel…", command=self._choose_file)
        file_menu.add_separator()
        file_menu.add_command(label="Resetear progreso...", command=self._on_reset_progress)
        file_menu.add_separator()
        file_menu.add_command(label="Salir", command=self.destroy)
        menubar.add_cascade(label="Archivo", menu=file_menu)
        self.config(menu=menubar)


    def _choose_file(self):
        path = filedialog.asksaveasfilename(
            title="Seleccionar/crear archivo Excel",
            defaultextension=".xlsx",
            filetypes=[("Excel", "*.xlsx"), ("Todos", "*.*")],
            initialfile=str(self.file_path.name),
        )
        if not path:
            return
        new_path = Path(path)
        self.file_path = new_path
        ensure_plan(self.file_path)
        _, migrated = load_plan_with_migration(self.file_path)
        if migrated:
            self._set_status("Migración aplicada: columnas faltantes fueron añadidas")
        else:
            self._set_status(f"Usando el archivo: {self.file_path}")
        messagebox.showinfo("Archivo", f"Usando archivo: {self.file_path}")
        self._refresh_table()
        
    def _on_reset_progress(self):
        if not self.file_path:
            messagebox.showwarning("Reset", "No hay archivo seleccionado.")
            return

        ok = messagebox.askyesno(
            "Resetear progreso",
            "Esto borrará las repeticiones, comentarios y fechas cargadas.\n"
            "Se creará un backup automático del archivo actual.\n\n"
            "¿Deseás continuar?"
        )
        if not ok:
            return

        try:
            from data_layer import reset_progress
            reset_progress(self.file_path, create_backup=True)
            self._set_status("Progreso reseteado. Se creó un backup automático.")
            messagebox.showinfo("Reset", "Progreso reseteado correctamente.")
            self._refresh_table()
            self._update_objective_label()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo resetear el progreso.\n{e}")
    # Formulario PRINCIPAL
    def _build_form(self):
        frm = ttk.LabelFrame(self, text="Cargar los registros")
        frm.pack(fill=tk.X, padx=12, pady=8)
        
        # Semanal
        ttk.Label(frm, text="Semana:").grid(row=0, column=0,padx=6, pady=6,sticky=tk.W)
        self.cbo_week = ttk.Combobox(frm, values=[1, 2, 3, 4], width=5, state="readonly")
        self.cbo_week.grid(row=0, column=1, padx=6, pady=6, sticky=tk.W)
        self.cbo_week.bind("<<ComboboxSelected>>", self._update_objective_label)
        
        # Ejercicio
        ttk.Label(frm, text="Ejercicio:").grid(row=0, column=2, padx=6, pady=6, sticky=tk.W)
        self.cbo_ex = ttk.Combobox(frm, values=EJERCICIOS, width=38, state="readonly")
        self.cbo_ex.grid(row=0, column=3, padx=6, pady=6, sticky=tk.W)
        self.cbo_ex.bind("<<ComboboxSelected>>", self._update_objective_label)
        
        # Objetivo (solo lectura)
        self.lbl_obj = ttk.Label(frm, text="Objetivo: -")
        self.lbl_obj.grid(row=0, column=4, padx=6, pady=6, sticky=tk.W)
        
        # Reps/Seg Realizadas
        ttk.Label(frm, text="Reps/Seg realizadas:").grid(row=1, column=0, padx=6, pady=6, sticky=tk.W)
        self.ent_done = ttk.Entry(frm, width=12)
        self.ent_done.grid(row=1, column=1, padx=6, pady=6, sticky=tk.W)

        # Comentarios
        ttk.Label(frm, text="Comentarios:").grid(row=1, column=2, padx=6, pady=6, sticky=tk.W)
        self.ent_comments = ttk.Entry(frm, width=50)
        self.ent_comments.grid(row=1, column=3, columnspan=2, padx=6, pady=6, sticky=tk.W)

        # Botones
        btn_save = ttk.Button(frm, text="Guardar", command=self._on_save)
        btn_save.grid(row=2, column=0, padx=6, pady=8, sticky=tk.W)
        
        btn_reset = ttk.Button(frm, text="Resetear progreso", command=self._on_reset_progress)
        btn_reset.grid(row=2, column=3, padx=6, pady=8, sticky=tk.W)

        btn_summary = ttk.Button(frm, text="Resumen semanal", command=self._on_summary)
        btn_summary.grid(row=2, column=1, padx=6, pady=8, sticky=tk.W)

        btn_reload = ttk.Button(frm, text="Recargar tabla", command=self._refresh_table)
        btn_reload.grid(row=2, column=2, padx=6, pady=8, sticky=tk.W)
        
        for i in range(5):
            frm.grid_columnconfigure(i, weight=1)
            
    def _update_objective_label(self, *_):
        week = self.cbo_week.get()
        ex = self.cbo_ex.get()
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
            messagebox.showerror("Error", "No se pudo actualizar el registro")
            return
        done = self.ent_done.get().strip()
        comments = self.ent_comments.get().strip()
        from data_layer import update_entry
        ok = update_entry(self.file_path, int(self.cbo_week.get()), self.cbo_ex.get(), done, comments)
        if not ok:
            messagebox.showerror("Errr", "No se pudo actualizar el registro.")
            return
        messagebox.showinfo("Guardado", "Registro guardado correctamente")
        self._refresh_table()
        self._update_objective_label()
        
    # Ultimas cargas
    
    def _build_table(self):
        tbl_frame = ttk.LabelFrame(self, text="Últimas cargas")
        tbl_frame.pack(fill=tk.BOTH, expand=True, padx=12, pady=8)
        
        cols = ("Semana", "Ejercicio", "Objetivo", "Reps/Seg Realizadas", "Comentarios", "Última actualización")
        self.tree = ttk.Treeview(tbl_frame, columns=cols, show="headings")
        
        numeric_cols = {"Semana", "Objetivo", "Reps/Seg Realizadas"}
        for c in cols:
            anchor = tk.CENTER if c in numeric_cols else tk.W
            self.tree.heading(c, text=c)
            self.tree.column(c, anchor=anchor, width=120 if c != "Ejercicio" else 260)
            
        self.tree.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        
        scrollbar = ttk.Scrollbar(tbl_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill= tk.Y)

# -- GRAFICO
    def _build_chart(self):
        frm = ttk.LabelFrame(self, text="Gráfica de desempeño")
        frm.pack(fill=tk.BOTH, expand=False, padx=12, pady=4)


        ttk.Label(frm, text="Periodo:").grid(row=0, column=0, padx=6, pady=6, sticky=tk.W)
        self.cbo_period = ttk.Combobox(frm, values=["Diario", "Semanal", "Mensual"], width=10, state="readonly")
        self.cbo_period.current(1)
        self.cbo_period.grid(row=0, column=1, padx=6, pady=6, sticky=tk.W)


        ttk.Label(frm, text="Ejercicio:").grid(row=0, column=2, padx=6, pady=6, sticky=tk.W)
        self.cbo_ex_chart = ttk.Combobox(frm, values=["Todos"] + EJERCICIOS, width=38, state="readonly")
        self.cbo_ex_chart.current(0)
        self.cbo_ex_chart.grid(row=0, column=3, padx=6, pady=6, sticky=tk.W)


        btn_plot = ttk.Button(frm, text="Actualizar gráfica", command=self._plot_chart)
        btn_plot.grid(row=0, column=4, padx=6, pady=6, sticky=tk.W)


        self.chart_frame = ttk.Frame(frm)
        self.chart_frame.grid(row=1, column=0, columnspan=5, sticky="nsew", padx=6, pady=6)
        for i in range(5):
            frm.grid_columnconfigure(i, weight=1)
            
    def _plot_chart(self):
        try:
            df, _ = load_plan_with_migration(self.file_path)
            fig = build_performance_figure(df, self.cbo_period.get() or "Semanal", self.cbo_ex_chart.get())


            if self._chart_canvas is not None:
                self._chart_canvas.get_tk_widget().destroy()
                self._chart_canvas = None


            self._chart_canvas = FigureCanvasTkAgg(fig, master=self.chart_frame)
            self._chart_canvas.draw()
            self._chart_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
            self._set_status("Gráfica actualizada.")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo generar la gráfica.\n{e}")
            
# -- Barra de estado

    def _build_statusbar(self):
        self.status_var = tk.StringVar(value="Listo.")
        bar = ttk.Label(self, textvariable=self.status_var, relief=tk.SUNKEN, anchor="w")
        bar.pack(side=tk.BOTTOM, fill=tk.X)


    def _set_status(self, text: str):
        self.status_var.set(text)
        
# -- Refresh de tabla

    def _refresh_table(self):
        # limpiar tabla
        if hasattr(self, "tree"):
            for item in self.tree.get_children():
                self.tree.delete(item)

        df, migrated = load_plan_with_migration(self.file_path)
        if migrated:
            self._set_status("Migración aplicada: columnas faltantes añadidas.")
        else:
            self._set_status("Listo.")

        try:
            df = get_last_updates(self.file_path, limit=20)
            if df.empty:
                return

            # Normalizar y prevenir “Series.strip”
            if "Reps/Seg Realizadas" in df.columns:
                df["Reps/Seg Realizadas"] = (
                    df["Reps/Seg Realizadas"].astype(str).str.strip()
                )

            for _, r in df.iterrows():
                semana = format_number(r.get("Semana", ""))
                objetivo = format_number(r.get("Objetivo", ""))
                reps = format_number(r.get("Reps/Seg Realizadas", ""))
                comentarios = r.get("Comentarios", "")
                ultima = r.get("Ultima actualización", "")
                ejercicio = r.get("Ejercicio", "")
                values = [semana, ejercicio, objetivo, reps, comentarios, ultima]
                self.tree.insert("", tk.END, values=values)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo cargar la tabla.\n{e}")

            
# --- Resumen de la semana

    def _on_summary(self):
        if not self.cbo_week.get():
            messagebox.showwarning("Validación", "Seleccioná la semana para el resumen.")
            return
        week = int(self.cbo_week.get())
        df = weekly_summary_df(self.file_path, week)
        if df.empty:
            messagebox.showinfo("Resumen", "No hay datos de esta semana.")
            return
        
        top = tk.Toplevel(self)
        top.title(f"Resumen Semana {week}")
        top.geometry("780x380")
        
        cols = list(df.columns)
        tree = ttk.Treeview(top, columns=cols, show="headings")
        numeric_cols = {"Objetivo", "Reps/Seg Realizadas", "% Objetivo"}
        for c in cols:
            anchor = tk.CENTER if c in numeric_cols else tk.W
            tree.heading(c, text=c)
            tree.column(c, width=120 if c not in ("Ejercicio", "Comentarios") else 260, anchor=anchor)
        tree.pack(fill=tk.BOTH, expand=True, side=tk.LEFT, padx=8, pady=8)
        
        sb = ttk.Scrollbar(top, orient="vertical", command=tree.yview)
        tree.configure(yscroll=sb.set)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        
        for _, r in df.iterrows():
            ejercicio = r.get("Ejercicio", "")
            objetivo = format_number(r.get("Objetivo", ""))
            reps = format_number(r.get("Reps/Seg Realizadas", ""))
            pct = format_number(r.get("% Objetivo", ""))
            comentarios = r.get("Comentarios", "")
            ultima = r.get("Última actualización", "")
            tree.insert("", tk.END, values=[ejercicio, objetivo, reps, pct, comentarios, ultima])