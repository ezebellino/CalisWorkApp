# Seguimiento de Calistenia – GUI con Tkinter

Este es un proyecto personal creado para **registrar, visualizar y analizar entrenamientos de calistenia**. Incluye una interfaz gráfica sencilla hecha con **Tkinter**, almacenamiento en **Excel (pandas + openpyxl)** y gráficas con **matplotlib**.

## 🚀 Funcionalidades
- Registro de entrenamientos con fecha, ejercicio, repeticiones y tiempo.
- Visualización en tabla de los entrenamientos previos.
- Estado de migración de datos.
- Gráficas de desempeño con filtros (diario, semanal, mensual).
- Exportación automática a archivo Excel como base de datos local.

## 📂 Estructura del proyecto
```
seguimiento_calistenia/
│
├── app.py                 # Punto de entrada: instancia la App y corre mainloop
├── ui.py                  # Clase App con toda la interfaz Tkinter
├── data_layer.py          # Lógica de manejo de Excel (crear, leer, actualizar, migrar)
├── charts.py              # Funciones para generar y actualizar gráficas
├── domain.py              # Constantes, configuraciones y helpers puros
├── requirements.txt       # Librerías necesarias (pandas, openpyxl, matplotlib)
├── .gitignore             # Ignora venv, __pycache__, archivos temporales
├── LICENSE                # Licencia MIT
└── README.md              # Este archivo
```

## 📦 Requisitos
Instalar las dependencias:
```bash
pip install -r requirements.txt
```

## ▶️ Uso
Ejecutar el programa con:
```bash
python app.py
```

Se abrirá una interfaz gráfica donde podrás registrar tus entrenamientos y ver estadísticas.

## 📸 Capturas de pantalla
*(Agregar aquí screenshots de la app en funcionamiento)*

## 🛠️ Tecnologías utilizadas
- **Python 3.10+**
- **Tkinter** (interfaz gráfica)
- **Pandas + Openpyxl** (gestión de datos en Excel)
- **Matplotlib** (gráficas de desempeño)

## 📌 Notas
Este proyecto está pensado como un **ejemplo práctico para un perfil Trainee/Jr**, mostrando organización modular y uso de librerías populares en Python.

## 📜 Licencia
Este proyecto está bajo la licencia MIT – libre para usar y modificar.

