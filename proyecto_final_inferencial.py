import tkinter as tk  # Importa tkinter para construir la interfaz gráfica.
from tkinter import ttk, messagebox  # Importa widgets modernos y ventanas de alerta.
from datetime import date, datetime  # Importa herramientas para manejar fechas.
import numpy as np  
import pandas as pd 
import yfinance as yf  
from scipy.optimize import minimize  
from matplotlib.figure import Figure  # Importa Figure para crear gráficas de Matplotlib.
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg  # Permite insertar Matplotlib dentro de Tkinter.


class MarkowitzGUI:  # Define la clase principal de la aplicación.
    def __init__(self, root: tk.Tk):  # Inicializa la aplicación con una ventana raíz.
        self.root = root  # Guarda la ventana principal en un atributo de la clase.
        self.root.title("Modelo de Markowitz con perfiles de riesgo")  # Define el título de la ventana.
        self.root.geometry("1380x820")  # Define el tamaño inicial de la ventana.

        self.R: np.ndarray | None = None  # Guardará la matriz de rendimientos como arreglo NumPy.
        self.retornos_df: pd.DataFrame | None = None  # Guardará los rendimientos como DataFrame con fechas.
        self.nombres_activos: list[str] = []  # Guardará los nombres de los activos descargados.
        self.fechas_rendimientos: pd.Index | None = None  # Guardará las fechas de los rendimientos.
        self.precios_descargados: pd.DataFrame | None = None  # Guardará los precios descargados y limpiados.

        self._crear_interfaz()  # Construye todos los elementos visuales de la interfaz.
        self.actualizar_estado_mu()  # Activa o desactiva el cuadro de retornos personalizados.

    # ------------------------------------------------------------------  # Separador visual de sección.
    # Interfaz gráfica  
    # ------------------------------------------------------------------  # Separador visual de sección.
    def _crear_interfaz(self) -> None:  # Crea la interfaz usando grid para que sea adaptable.
        self.root.minsize(1220, 760)  # Define el tamaño mínimo para evitar que se empalmen controles.
        self.root.columnconfigure(0, weight=0, minsize=410)  # Configura la primera columna para entradas.
        self.root.columnconfigure(1, weight=2, minsize=460)  # Configura la segunda columna para tablas y texto.
        self.root.columnconfigure(2, weight=1, minsize=390)  # Configura la tercera columna para gráfica y resultados.
        self.root.rowconfigure(0, weight=1)  # Permite que la primera fila crezca con la ventana.
        self.root.rowconfigure(1, weight=1)  # Permite que la segunda fila crezca con la ventana.

        pad = 8  # Define un margen general entre paneles.

        pnl_input = ttk.LabelFrame(self.root, text="Datos, perfil y optimización")  # Crea panel de entradas.
        pnl_input.grid(row=0, column=0, sticky="nsew", padx=(pad, pad // 2), pady=(pad, pad // 2))  # Ubica el panel.
        pnl_input.columnconfigure(0, weight=0)  # Deja fija la columna de etiquetas.
        pnl_input.columnconfigure(1, weight=1)  # Permite que la columna de campos crezca.

        ttk.Label(pnl_input, text="Tickers:").grid(row=0, column=0, sticky="w", padx=12, pady=(12, 4))  # Etiqueta de tickers.
        self.tickers_var = tk.StringVar(value="AAPL MSFT GOOGL AMZN")  # Valor inicial de tickers.
        ttk.Entry(pnl_input, textvariable=self.tickers_var).grid(row=0, column=1, sticky="ew", padx=(4, 12), pady=(12, 4))  # Campo de tickers.

        ttk.Label(pnl_input, text="Separados por comas o espacios. Ej.: AAPL MSFT TSLA", wraplength=320).grid(row=1, column=0, columnspan=2, sticky="ew", padx=12, pady=(0, 10))  # Ayuda para capturar tickers.

        ttk.Label(pnl_input, text="Fecha inicial:").grid(row=2, column=0, sticky="w", padx=12, pady=4)  # Etiqueta de fecha inicial.
        self.fecha_inicio_var = tk.StringVar(value="2020-01-01")  # Fecha inicial predeterminada.
        ttk.Entry(pnl_input, textvariable=self.fecha_inicio_var).grid(row=2, column=1, sticky="ew", padx=(4, 12), pady=4)  # Campo de fecha inicial.

        ttk.Label(pnl_input, text="Fecha final:").grid(row=3, column=0, sticky="w", padx=12, pady=4)  # Etiqueta de fecha final.
        self.fecha_fin_var = tk.StringVar(value=date.today().isoformat())  # Fecha final predeterminada igual a hoy.
        ttk.Entry(pnl_input, textvariable=self.fecha_fin_var).grid(row=3, column=1, sticky="ew", padx=(4, 12), pady=4)  # Campo de fecha final.

        ttk.Label(pnl_input, text="Periodicidad:").grid(row=4, column=0, sticky="w", padx=12, pady=4)  # Etiqueta de periodicidad.
        self.intervalo_var = tk.StringVar(value="1d - Diario")  # Periodicidad inicial.
        self.dd_intervalo = ttk.Combobox(pnl_input, textvariable=self.intervalo_var, values=["1d - Diario", "1wk - Semanal", "1mo - Mensual", "3mo - Trimestral"], state="readonly")  # Selector de periodicidad.
        self.dd_intervalo.grid(row=4, column=1, sticky="ew", padx=(4, 12), pady=4)  # Ubica el selector.

        ttk.Label(pnl_input, text="Perfil de inversionista:").grid(row=5, column=0, sticky="w", padx=12, pady=4)  # Etiqueta de perfil.
        self.perfil_riesgo_var = tk.StringVar(value="Moderado")  # Perfil inicial del usuario.
        self.dd_perfil_riesgo = ttk.Combobox(pnl_input, textvariable=self.perfil_riesgo_var, values=["Conservador", "Moderado", "Agresivo"], state="readonly")  # Selector de perfil.
        self.dd_perfil_riesgo.grid(row=5, column=1, sticky="ew", padx=(4, 12), pady=4)  # Ubica el selector de perfil.
        self.dd_perfil_riesgo.bind("<<ComboboxSelected>>", lambda _event: self.actualizar_objetivo_por_perfil())  # Actualiza objetivo y tasa cuando cambia el perfil.

        ttk.Label(pnl_input, text="Objetivo según perfil:").grid(row=6, column=0, sticky="w", padx=12, pady=4)  # Etiqueta de objetivo automático.
        self.objetivo_var = tk.StringVar(value="Minimizar riesgo con retorno mínimo")  # Objetivo inicial asociado al perfil moderado.
        self.dd_objetivo = ttk.Combobox(pnl_input, textvariable=self.objetivo_var, values=["Minimizar riesgo", "Minimizar riesgo con retorno mínimo", "Maximizar Sharpe Ratio"], state="disabled")  # Muestra objetivo sin permitir cambios manuales.
        self.dd_objetivo.grid(row=6, column=1, sticky="ew", padx=(4, 12), pady=4)  # Ubica el campo de objetivo automático.

        ttk.Label(pnl_input, text="Rendimiento mínimo manual:").grid(row=7, column=0, sticky="w", padx=12, pady=4)  # Etiqueta de rendimiento mínimo.
        self.r_min_var = tk.DoubleVar(value=0.01)  # Valor inicial de rendimiento mínimo por periodo.
        ttk.Entry(pnl_input, textvariable=self.r_min_var).grid(row=7, column=1, sticky="ew", padx=(4, 12), pady=4)  # Campo de rendimiento mínimo.

        ttk.Label(pnl_input, text="Usar r_min manual:").grid(row=8, column=0, sticky="w", padx=12, pady=4)  # Etiqueta del checkbutton.
        self.usar_rmin_manual_var = tk.BooleanVar(value=False)  # Define si se usa r_min manual o automático.
        ttk.Checkbutton(pnl_input, variable=self.usar_rmin_manual_var, text="Sí, usar el valor capturado").grid(row=8, column=1, sticky="w", padx=(4, 12), pady=4)  # Checkbutton para r_min manual.

        ttk.Label(pnl_input, text="Tasa libre de riesgo anual:").grid(row=9, column=0, sticky="w", padx=12, pady=4)  # Etiqueta de tasa libre de riesgo.
        self.rf_var = tk.DoubleVar(value=0.10)  # Tasa libre de riesgo anual predeterminada.
        self.entry_rf = ttk.Entry(pnl_input, textvariable=self.rf_var)  # Crea campo manual de tasa libre de riesgo.
        self.entry_rf.grid(row=9, column=1, sticky="ew", padx=(4, 12), pady=4)  # Ubica el campo de tasa libre de riesgo.

        ttk.Label(pnl_input, text="Fuente de tasa libre:").grid(row=10, column=0, sticky="w", padx=12, pady=4)  # Etiqueta de fuente de tasa libre.
        self.fuente_rf_var = tk.StringVar(value="Manual")  # Fuente inicial de tasa libre de riesgo.
        self.dd_fuente_rf = ttk.Combobox(pnl_input, textvariable=self.fuente_rf_var, values=["Manual", "yfinance - T-Bill 13 semanas (^IRX)"], state="disabled")  # Selector de fuente bloqueado salvo perfil agresivo.
        self.dd_fuente_rf.grid(row=10, column=1, sticky="ew", padx=(4, 12), pady=4)  # Ubica selector de fuente de tasa libre.

        ttk.Label(pnl_input, text="Capital total:").grid(row=11, column=0, sticky="w", padx=12, pady=4)  # Etiqueta de capital.
        self.capital_var = tk.DoubleVar(value=10000.0)  # Capital inicial predeterminado.
        ttk.Entry(pnl_input, textvariable=self.capital_var).grid(row=11, column=1, sticky="ew", padx=(4, 12), pady=4)  # Campo de capital.

        ttk.Label(pnl_input, text="Retorno esperado:").grid(row=12, column=0, sticky="w", padx=12, pady=4)  # Etiqueta de tipo de retorno esperado.
        self.tipo_mu_var = tk.StringVar(value="Promedio histórico")  # Define método inicial para mu.
        self.dd_tipo_mu = ttk.Combobox(pnl_input, textvariable=self.tipo_mu_var, values=["Promedio histórico", "Vector personalizado"], state="readonly")  # Selector de método de mu.
        self.dd_tipo_mu.grid(row=12, column=1, sticky="ew", padx=(4, 12), pady=4)  # Ubica selector de mu.
        self.dd_tipo_mu.bind("<<ComboboxSelected>>", lambda _event: self.actualizar_estado_mu())  # Actualiza estado del cuadro personalizado.

        btn_frame = ttk.Frame(pnl_input)  # Crea un marco para botones.
        btn_frame.grid(row=13, column=0, columnspan=2, sticky="ew", padx=12, pady=(12, 8))  # Ubica el marco de botones.
        btn_frame.columnconfigure(0, weight=1)  # Permite crecer al botón izquierdo.
        btn_frame.columnconfigure(1, weight=1)  # Permite crecer al botón derecho.

        ttk.Button(btn_frame, text="Descargar precios", command=self.descargar_datos_yfinance).grid(row=0, column=0, sticky="ew", padx=(0, 6))  # Botón para descargar datos.
        ttk.Button(btn_frame, text="Calcular portafolio", command=self.calcular_markowitz).grid(row=0, column=1, sticky="ew", padx=(6, 0))  # Botón para optimizar.

        pnl_mu = ttk.LabelFrame(self.root, text="Vector de retornos esperados personalizado")  # Crea panel para vector mu.
        pnl_mu.grid(row=1, column=0, sticky="nsew", padx=(pad, pad // 2), pady=(pad // 2, pad))  # Ubica panel de mu.
        pnl_mu.columnconfigure(0, weight=1)  # Permite que el contenido crezca horizontalmente.
        pnl_mu.rowconfigure(1, weight=1)  # Permite que el área de texto crezca verticalmente.

        ttk.Label(pnl_mu, text="Vector personalizado separado por comas o espacios:").grid(row=0, column=0, sticky="w", padx=12, pady=(12, 4))  # Etiqueta del vector mu.
        self.txt_mu_custom = tk.Text(pnl_mu, height=6, width=40, wrap="word")  # Crea cuadro de texto para mu personalizado.
        self.txt_mu_custom.grid(row=1, column=0, sticky="nsew", padx=12, pady=4)  # Ubica cuadro de texto.
        self._set_text(self.txt_mu_custom, " ")  # Coloca un espacio inicial para evitar texto vacío visual.

        self.lbl_mu_info = ttk.Label(pnl_mu, text="Descarga precios para generar el promedio histórico o capturar un vector propio.", wraplength=350)  # Etiqueta informativa.
        self.lbl_mu_info.grid(row=2, column=0, sticky="ew", padx=12, pady=(8, 12))  # Ubica etiqueta informativa.

        pnl_tabla = ttk.LabelFrame(self.root, text="Rendimientos calculados")  # Crea panel de tabla de rendimientos.
        pnl_tabla.grid(row=0, column=1, sticky="nsew", padx=pad // 2, pady=(pad, pad // 2))  # Ubica tabla de rendimientos.
        pnl_tabla.columnconfigure(0, weight=1)  # Permite crecer a la tabla.
        pnl_tabla.rowconfigure(0, weight=1)  # Permite crecer a la tabla.

        self.tbl = ttk.Treeview(pnl_tabla, show="headings")  # Crea tabla para rendimientos.
        self.tbl.grid(row=0, column=0, sticky="nsew", padx=(12, 0), pady=(12, 0))  # Ubica la tabla.
        self.tbl_scroll_y = ttk.Scrollbar(pnl_tabla, orient="vertical", command=self.tbl.yview)  # Crea scrollbar vertical.
        self.tbl_scroll_y.grid(row=0, column=1, sticky="ns", pady=(12, 0), padx=(0, 12))  # Ubica scrollbar vertical.
        self.tbl_scroll_x = ttk.Scrollbar(pnl_tabla, orient="horizontal", command=self.tbl.xview)  # Crea scrollbar horizontal.
        self.tbl_scroll_x.grid(row=1, column=0, sticky="ew", padx=(12, 0), pady=(0, 12))  # Ubica scrollbar horizontal.
        self.tbl.configure(yscrollcommand=self.tbl_scroll_y.set, xscrollcommand=self.tbl_scroll_x.set)  # Conecta scrollbars con la tabla.

        pnl_grafica = ttk.LabelFrame(self.root, text="Gráficas y matrices")  # Crea panel para gráfica y matrices.
        pnl_grafica.grid(row=0, column=2, sticky="nsew", padx=(pad // 2, pad), pady=(pad, pad // 2))  # Ubica panel de gráfica.
        pnl_grafica.columnconfigure(0, weight=1)  # Permite que el contenido crezca horizontalmente.
        pnl_grafica.rowconfigure(0, weight=1)  # Permite que el contenido crezca verticalmente.

        self.nb_graficas = ttk.Notebook(pnl_grafica)  # Crea pestañas para separar frontera, covarianza y correlación.
        self.nb_graficas.grid(row=0, column=0, sticky="nsew", padx=12, pady=12)  # Ubica el notebook dentro del panel.

        tab_frontera = ttk.Frame(self.nb_graficas)  # Pestaña de frontera eficiente.
        tab_cov = ttk.Frame(self.nb_graficas)  # Pestaña de matriz de covarianza.
        tab_corr = ttk.Frame(self.nb_graficas)  # Pestaña de matriz de correlación.
        for tab in (tab_frontera, tab_cov, tab_corr):  # Configura expansión de las tres pestañas.
            tab.columnconfigure(0, weight=1)  # Permite crecer horizontalmente.
            tab.rowconfigure(0, weight=1)  # Permite crecer verticalmente.

        self.nb_graficas.add(tab_frontera, text="Frontera eficiente")  # Agrega pestaña de frontera.
        self.nb_graficas.add(tab_cov, text="Covarianza")  # Agrega pestaña de covarianza.
        self.nb_graficas.add(tab_corr, text="Correlación")  # Agrega pestaña de correlación.

        self.fig = Figure(figsize=(4.5, 3.5), dpi=90)  # Crea figura de Matplotlib para la frontera eficiente.
        self.ax = self.fig.add_subplot(111)  # Agrega eje principal a la figura.
        self._configurar_ejes()  # Configura título, ejes y cuadrícula.
        self.canvas = FigureCanvasTkAgg(self.fig, master=tab_frontera)  # Crea lienzo de Matplotlib dentro de la pestaña de frontera.
        self.canvas.get_tk_widget().grid(row=0, column=0, sticky="nsew", padx=12, pady=12)  # Ubica el lienzo.
        self.canvas.draw()  # Dibuja la gráfica inicial.

        tab_cov.rowconfigure(1, weight=0)  # Reserva una fila inferior para la interpretación de covarianza.
        self.fig_cov = Figure(figsize=(4.5, 3.5), dpi=90)  # Crea figura para la matriz de covarianza.
        self.canvas_cov = FigureCanvasTkAgg(self.fig_cov, master=tab_cov)  # Crea lienzo para covarianza.
        self.canvas_cov.get_tk_widget().grid(row=0, column=0, sticky="nsew", padx=12, pady=(12, 6))  # Ubica lienzo de covarianza.
        self.lbl_cov_interp = ttk.Label(tab_cov, text="La matriz de covarianza aparecerá aquí después de calcular el portafolio.", wraplength=360, justify="left")  # Crea interpretación de covarianza.
        self.lbl_cov_interp.grid(row=1, column=0, sticky="ew", padx=12, pady=(0, 12))  # Ubica interpretación de covarianza.
        self._dibujar_placeholder_matriz(self.fig_cov, self.canvas_cov, "Matriz de covarianza")  # Dibuja vista inicial de covarianza.

        tab_corr.rowconfigure(1, weight=0)  # Reserva una fila inferior para la interpretación de correlación.
        self.fig_corr = Figure(figsize=(4.5, 3.5), dpi=90)  # Crea figura para la matriz de correlación.
        self.canvas_corr = FigureCanvasTkAgg(self.fig_corr, master=tab_corr)  # Crea lienzo para correlación.
        self.canvas_corr.get_tk_widget().grid(row=0, column=0, sticky="nsew", padx=12, pady=(12, 6))  # Ubica lienzo de correlación.
        self.lbl_corr_interp = ttk.Label(tab_corr, text="La matriz de correlación aparecerá aquí después de calcular el portafolio.", wraplength=360, justify="left")  # Crea interpretación de correlación.
        self.lbl_corr_interp.grid(row=1, column=0, sticky="ew", padx=12, pady=(0, 12))  # Ubica interpretación de correlación.
        self._dibujar_placeholder_matriz(self.fig_corr, self.canvas_corr, "Matriz de correlación")  # Dibuja vista inicial de correlación.

        pnl_resultados = ttk.LabelFrame(self.root, text="Resultados, métricas y diagnóstico")  # Crea panel de texto de resultados.
        pnl_resultados.grid(row=1, column=1, sticky="nsew", padx=pad // 2, pady=(pad // 2, pad))  # Ubica panel de resultados.
        pnl_resultados.columnconfigure(0, weight=1)  # Permite crecer al texto.
        pnl_resultados.rowconfigure(0, weight=1)  # Permite crecer al texto.

        self.txt_resultados = tk.Text(pnl_resultados, height=18, width=58, state="disabled", wrap="none")  # Crea cuadro de texto de resultados.
        self.txt_resultados.grid(row=0, column=0, sticky="nsew", padx=(12, 0), pady=(12, 0))  # Ubica cuadro de resultados.
        self.txt_resultados_scroll_y = ttk.Scrollbar(pnl_resultados, orient="vertical", command=self.txt_resultados.yview)  # Scroll vertical de resultados.
        self.txt_resultados_scroll_y.grid(row=0, column=1, sticky="ns", pady=(12, 0), padx=(0, 12))  # Ubica scroll vertical.
        self.txt_resultados_scroll_x = ttk.Scrollbar(pnl_resultados, orient="horizontal", command=self.txt_resultados.xview)  # Scroll horizontal de resultados.
        self.txt_resultados_scroll_x.grid(row=1, column=0, sticky="ew", padx=(12, 0), pady=(0, 12))  # Ubica scroll horizontal.
        self.txt_resultados.configure(yscrollcommand=self.txt_resultados_scroll_y.set, xscrollcommand=self.txt_resultados_scroll_x.set)  # Conecta scrollbars.
        self._set_text(self.txt_resultados, "Escribe los tickers, el rango de fechas y la periodicidad; después descarga precios.")  # Mensaje inicial.

        pnl_asignacion = ttk.LabelFrame(self.root, text="Pesos, montos y riesgo por activo")  # Crea panel de tabla final.
        pnl_asignacion.grid(row=1, column=2, sticky="nsew", padx=(pad // 2, pad), pady=(pad // 2, pad))  # Ubica panel final.
        pnl_asignacion.columnconfigure(0, weight=1)  # Permite crecer a la tabla final.
        pnl_asignacion.rowconfigure(0, weight=1)  # Permite crecer a la tabla final.

        self.tbl_resultados = ttk.Treeview(pnl_asignacion, show="headings")  # Crea tabla de pesos y métricas por activo.
        self.tbl_resultados.grid(row=0, column=0, sticky="nsew", padx=(12, 0), pady=(12, 0))  # Ubica tabla final.
        self.tbl_res_scroll_y = ttk.Scrollbar(pnl_asignacion, orient="vertical", command=self.tbl_resultados.yview)  # Scroll vertical tabla final.
        self.tbl_res_scroll_y.grid(row=0, column=1, sticky="ns", pady=(12, 0), padx=(0, 12))  # Ubica scroll vertical final.
        self.tbl_res_scroll_x = ttk.Scrollbar(pnl_asignacion, orient="horizontal", command=self.tbl_resultados.xview)  # Scroll horizontal tabla final.
        self.tbl_res_scroll_x.grid(row=1, column=0, sticky="ew", padx=(12, 0), pady=(0, 12))  # Ubica scroll horizontal final.
        self.tbl_resultados.configure(yscrollcommand=self.tbl_res_scroll_y.set, xscrollcommand=self.tbl_res_scroll_x.set)  # Conecta scrollbars de tabla final.

    def _configurar_ejes(self) -> None:  # Configura la gráfica de la frontera eficiente.
        self.ax.clear()  # Limpia el eje para evitar empalmar gráficas anteriores.
        self.ax.set_title("Frontera eficiente")  # Define el título de la gráfica.
        self.ax.set_xlabel(r"Riesgo anualizado $\sigma_p$")  # Define etiqueta del eje horizontal.
        self.ax.set_ylabel(r"Rendimiento anualizado $\mu_p$")  # Define etiqueta del eje vertical.
        self.ax.grid(True)  # Activa cuadrícula para facilitar lectura.

    def _set_text(self, widget: tk.Text, value: str | list[str]) -> None:  # Escribe texto en un widget Text aunque esté deshabilitado.
        previous_state = widget.cget("state")  # Guarda el estado actual del widget.
        widget.configure(state="normal")  # Habilita temporalmente la edición.
        widget.delete("1.0", "end")  # Borra todo el contenido previo.
        widget.insert("1.0", "\n".join(value) if isinstance(value, list) else value)  # Inserta texto o lista de líneas.
        widget.configure(state=previous_state)  # Restaura el estado anterior del widget.

    def _llenar_treeview(self, tree: ttk.Treeview, dataframe: pd.DataFrame) -> None:  # Llena una tabla Treeview desde un DataFrame.
        tree.delete(*tree.get_children())  # Borra todas las filas existentes.
        tree["columns"] = list(dataframe.columns)  # Define las columnas de la tabla.
        for col in dataframe.columns:  # Recorre cada columna del DataFrame.
            tree.heading(col, text=str(col))  # Asigna el nombre visible de la columna.
            tree.column(col, width=125, anchor="center")  # Define ancho y alineación de columna.
        for _, row in dataframe.iterrows():  # Recorre cada fila del DataFrame.
            values = []  # Crea lista donde se guardarán valores formateados.
            for value in row:  # Recorre cada valor de la fila.
                if isinstance(value, (float, np.floating)):  # Detecta valores numéricos decimales.
                    values.append(f"{value:.6f}")  # Formatea flotantes con seis decimales.
                elif isinstance(value, pd.Timestamp):  # Detecta fechas de pandas.
                    values.append(value.strftime("%Y-%m-%d"))  # Formatea fechas como año-mes-día.
                else:  # Maneja cualquier otro tipo de dato.
                    values.append(str(value))  # Convierte el valor a texto.
            tree.insert("", "end", values=values)  # Inserta la fila en la tabla.

    def _dibujar_placeholder_matriz(self, fig: Figure, canvas: FigureCanvasTkAgg, titulo: str) -> None:  # Dibuja una vista inicial para matrices aún no calculadas.
        fig.clear()  # Limpia la figura previa.
        ax = fig.add_subplot(111)  # Crea un eje simple.
        ax.set_title(titulo)  # Coloca el título de la matriz.
        ax.axis("off")  # Oculta ejes porque todavía no hay datos.
        ax.text(0.5, 0.5, "Se mostrará aquí después de calcular el portafolio.", ha="center", va="center", wrap=True)  # Mensaje inicial.
        fig.tight_layout()  # Ajusta márgenes.
        canvas.draw()  # Redibuja el lienzo.

    def _graficar_matriz(self, fig: Figure, canvas: FigureCanvasTkAgg, matriz: pd.DataFrame, titulo: str, cmap: str = "coolwarm", vmin: float | None = None, vmax: float | None = None) -> None:  # Grafica una matriz como mapa de calor.
        fig.clear()  # Limpia figura previa.
        ax = fig.add_subplot(111)  # Crea eje de la matriz.
        valores = matriz.to_numpy(dtype=float)  # Convierte la matriz a arreglo numérico.
        im = ax.imshow(valores, cmap=cmap, aspect="auto", vmin=vmin, vmax=vmax)  # Dibuja mapa de calor.
        ax.set_title(titulo)  # Define título.
        ax.set_xticks(np.arange(len(matriz.columns)))  # Define posiciones del eje X.
        ax.set_yticks(np.arange(len(matriz.index)))  # Define posiciones del eje Y.
        ax.set_xticklabels(matriz.columns, rotation=45, ha="right")  # Escribe nombres de activos en X.
        ax.set_yticklabels(matriz.index)  # Escribe nombres de activos en Y.
        for i in range(matriz.shape[0]):  # Recorre filas.
            for j in range(matriz.shape[1]):  # Recorre columnas.
                ax.text(j, i, f"{matriz.iloc[i, j]:.4f}", ha="center", va="center", fontsize=8)  # Escribe el valor dentro de cada celda.
        fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)  # Agrega barra de colores.
        fig.tight_layout()  # Ajusta márgenes.
        canvas.draw()  # Redibuja la imagen.

    def _interpretacion_covarianza(self, cov_df: pd.DataFrame) -> str:  # Genera interpretación automática de la matriz de covarianza.
        n = len(cov_df)  # Cuenta activos.
        if n < 2:  # Verifica mínimo de activos.
            return "No hay suficientes activos para interpretar la matriz de covarianza."  # Devuelve mensaje.
        mascara = ~np.eye(n, dtype=bool)  # Crea máscara para excluir la diagonal.
        pares = cov_df.where(mascara).stack()  # Obtiene solo covarianzas entre activos diferentes.
        if pares.empty:  # Verifica si hay pares válidos.
            return "No fue posible generar una interpretación de la covarianza."  # Devuelve mensaje.
        par_max = pares.idxmax()  # Localiza el par con mayor covarianza.
        val_max = float(pares.max())  # Obtiene mayor covarianza.
        par_min = pares.idxmin()  # Localiza el par con menor covarianza.
        val_min = float(pares.min())  # Obtiene menor covarianza.
        texto = [  # Construye explicación.
            "Interpretación de la matriz de covarianza:",
            "• Covarianza positiva: dos activos tienden a moverse en la misma dirección.",
            "• Covarianza negativa: dos activos tienden a moverse en direcciones opuestas.",
            "• Covarianza cercana a cero: la relación lineal entre ambos es débil.",
            f"• La mayor covarianza positiva es entre {par_max[0]} y {par_max[1]}: {val_max:.6f}.",
        ]
        if val_min < 0:  # Evalúa si existe covarianza negativa.
            texto.append(f"• La covarianza más negativa es entre {par_min[0]} y {par_min[1]}: {val_min:.6f}.")  # Agrega par negativo.
        else:  # Si no hay valores negativos.
            texto.append("• No se observan covarianzas negativas relevantes entre los activos.")  # Agrega interpretación.
        texto.append("• Esta matriz se usa directamente en Markowitz para calcular el riesgo total del portafolio mediante w^T Q w.")  # Relaciona con el modelo.
        return "\n".join(texto)  # Devuelve interpretación completa.

    def _interpretacion_correlacion(self, corr_df: pd.DataFrame) -> str:  # Genera interpretación automática de la matriz de correlación.
        n = len(corr_df)  # Cuenta activos.
        if n < 2:  # Verifica mínimo de activos.
            return "No hay suficientes activos para interpretar la matriz de correlación."  # Devuelve mensaje.
        mascara = ~np.eye(n, dtype=bool)  # Crea máscara para excluir la diagonal.
        pares = corr_df.where(mascara).stack()  # Obtiene correlaciones entre activos diferentes.
        if pares.empty:  # Verifica si hay pares válidos.
            return "No fue posible generar una interpretación de la correlación."  # Devuelve mensaje.
        par_max = pares.idxmax()  # Localiza correlación positiva más alta.
        val_max = float(pares.max())  # Obtiene valor máximo.
        par_min = pares.idxmin()  # Localiza correlación más baja.
        val_min = float(pares.min())  # Obtiene valor mínimo.
        par_abs = pares.abs().idxmax()  # Localiza relación más fuerte en valor absoluto.
        val_abs = float(pares.loc[par_abs])  # Obtiene signo y valor de esa relación.
        promedio_abs = float(pares.abs().mean())  # Calcula correlación media absoluta.
        texto = [  # Construye explicación.
            "Interpretación de la matriz de correlación:",
            "• La correlación toma valores entre -1 y 1.",
            "• Valores cercanos a 1 indican que dos activos se mueven de forma muy parecida.",
            "• Valores cercanos a -1 indican movimientos en sentidos opuestos.",
            "• Valores cercanos a 0 indican poca relación lineal.",
            f"• La correlación positiva más alta es entre {par_max[0]} y {par_max[1]}: {val_max:.4f}.",
            f"• La correlación más negativa es entre {par_min[0]} y {par_min[1]}: {val_min:.4f}.",
            f"• La relación lineal más fuerte en valor absoluto es entre {par_abs[0]} y {par_abs[1]}: {val_abs:.4f}.",
            f"• En promedio, la magnitud de las correlaciones es {promedio_abs:.4f}.",
        ]
        if promedio_abs > 0.70:  # Evalúa correlación alta general.
            texto.append("• En general, los activos están bastante relacionados; la diversificación puede ser limitada.")  # Mensaje de diversificación limitada.
        elif promedio_abs > 0.40:  # Evalúa correlación moderada.
            texto.append("• En general, existe una relación moderada entre los activos; hay diversificación, pero no total.")  # Mensaje intermedio.
        else:  # Caso de correlación baja.
            texto.append("• En general, la relación entre los activos es baja; esto favorece la diversificación.")  # Mensaje positivo.
        return "\n".join(texto)  # Devuelve interpretación completa.

    # ------------------------------------------------------------------  # Separador visual de sección.
    # Descarga y preparación de datos  # Nombre de la sección.
    # ------------------------------------------------------------------  # Separador visual de sección.
    def actualizar_estado_mu(self) -> None:  # Activa o bloquea el cuadro de mu personalizado.
        if self.tipo_mu_var.get() == "Promedio histórico":  # Revisa si el usuario eligió promedio histórico.
            self.txt_mu_custom.configure(state="disabled", background="#f0f0f0")  # Deshabilita el texto personalizado.
        else:  # Si el usuario eligió vector personalizado.
            self.txt_mu_custom.configure(state="normal", background="white")  # Habilita el texto personalizado.

    def _objetivo_por_perfil_interfaz(self) -> str:  # Determina el objetivo que debe mostrarse según el perfil.
        perfil = self.perfil_riesgo_var.get()  # Lee el perfil seleccionado por el usuario.
        if perfil == "Conservador":  # Revisa si el usuario eligió perfil conservador.
            return "Minimizar riesgo"  # Devuelve objetivo de mínima varianza.
        if perfil == "Moderado":  # Revisa si el usuario eligió perfil moderado.
            return "Minimizar riesgo con retorno mínimo"  # Devuelve objetivo de Markowitz con rendimiento mínimo.
        return "Maximizar Sharpe Ratio"  # Devuelve máximo Sharpe para perfil agresivo.

    def actualizar_objetivo_por_perfil(self) -> None:  # Sincroniza el objetivo y la fuente de tasa con el perfil.
        self.objetivo_var.set(self._objetivo_por_perfil_interfaz())  # Coloca en la interfaz el objetivo automático del perfil.
        self.actualizar_estado_rf()  # Actualiza si se permite o no la tasa automática con yfinance.

    def actualizar_estado_rf(self) -> None:  # Controla cuándo se puede usar la tasa libre de riesgo automática.
        perfil = self.perfil_riesgo_var.get()  # Lee el perfil seleccionado actualmente.
        if perfil == "Agresivo":  # Solo el perfil agresivo usa máximo Sharpe directamente.
            self.dd_fuente_rf.configure(state="readonly")  # Permite elegir la fuente automática o manual.
            self.fuente_rf_var.set("yfinance - T-Bill 13 semanas (^IRX)")  # Sugiere yfinance como fuente automática para Sharpe.
        else:  # Para perfiles conservador y moderado.
            self.fuente_rf_var.set("Manual")  # Fuerza fuente manual porque la tasa no define la optimización.
            self.dd_fuente_rf.configure(state="disabled")  # Bloquea la opción automática para esos perfiles.

    def _obtener_tickers(self) -> list[str]:  # Obtiene y limpia los tickers capturados.
        texto = self.tickers_var.get().strip().replace(",", " ")  # Convierte comas en espacios y limpia extremos.
        tickers = [t.upper() for t in texto.split() if t.strip()]  # Separa tickers y los convierte a mayúsculas.
        tickers_unicos = list(dict.fromkeys(tickers))  # Elimina duplicados manteniendo el orden original.
        if len(tickers_unicos) < 2:  # Verifica que existan al menos dos activos.
            raise ValueError("Debes capturar al menos 2 tickers para construir un portafolio.")  # Lanza error explicativo.
        return tickers_unicos  # Devuelve lista limpia de tickers.

    def _obtener_intervalo(self) -> str:  # Obtiene el código de intervalo usado por yfinance.
        return self.intervalo_var.get().split(" ")[0].strip()  # Extrae 1d, 1wk, 1mo o 3mo.

    def _factor_anualizacion(self) -> int:  # Devuelve el factor para anualizar según la periodicidad.
        factores = {"1d": 252, "1wk": 52, "1mo": 12, "3mo": 4}  # Define factores típicos de anualización.
        return factores.get(self._obtener_intervalo(), 252)  # Devuelve factor correspondiente o 252 por defecto.

    def _validar_fechas(self) -> tuple[str, str]:  # Valida que las fechas sean correctas.
        inicio_txt = self.fecha_inicio_var.get().strip()  # Lee fecha inicial como texto.
        fin_txt = self.fecha_fin_var.get().strip()  # Lee fecha final como texto.
        try:  # Intenta convertir ambos textos a fechas.
            inicio = datetime.strptime(inicio_txt, "%Y-%m-%d").date()  # Convierte fecha inicial.
            fin = datetime.strptime(fin_txt, "%Y-%m-%d").date()  # Convierte fecha final.
        except ValueError as exc:  # Captura error de formato.
            raise ValueError("Las fechas deben tener formato YYYY-MM-DD. Ejemplo: 2020-01-01") from exc  # Lanza mensaje claro.
        if fin <= inicio:  # Verifica que la fecha final sea posterior.
            raise ValueError("La fecha final debe ser posterior a la fecha inicial.")  # Lanza error de orden de fechas.
        return inicio.isoformat(), fin.isoformat()  # Devuelve fechas como texto ISO.

    @staticmethod  # Indica que este método no usa self.
    def _extraer_precios_cierre(datos: pd.DataFrame, tickers: list[str]) -> pd.DataFrame:  # Extrae precios Close ajustados.
        if datos.empty:  # Verifica si yfinance devolvió datos.
            raise ValueError("yfinance no devolvió datos para los parámetros seleccionados.")  # Lanza error si no hay datos.
        if isinstance(datos.columns, pd.MultiIndex):  # Revisa si las columnas vienen en varios niveles.
            if "Close" in datos.columns.get_level_values(0):  # Caso habitual: nivel 0 contiene OHLCV.
                precios = datos["Close"].copy()  # Extrae las columnas Close de cada ticker.
            elif "Close" in datos.columns.get_level_values(1):  # Caso alternativo: nivel 1 contiene OHLCV.
                precios = datos.xs("Close", axis=1, level=1).copy()  # Extrae Close por nivel.
            else:  # Si no existe Close en ningún nivel.
                raise ValueError("No se encontró la columna Close en los datos descargados.")  # Lanza error claro.
        else:  # Si las columnas no son MultiIndex.
            if "Close" not in datos.columns:  # Verifica columna Close.
                raise ValueError("No se encontró la columna Close en los datos descargados.")  # Lanza error claro.
            precios = datos[["Close"]].copy()  # Extrae columna Close.
            precios.columns = tickers[:1]  # Asigna nombre del ticker cuando solo hay un activo.
        precios = precios.apply(pd.to_numeric, errors="coerce")  # Convierte todo a numérico y vuelve NaN lo inválido.
        precios = precios.dropna(axis=1, how="all")  # Elimina activos sin ningún precio válido.
        precios = precios.dropna(axis=0, how="any")  # Elimina fechas con faltantes para mantener matriz completa.
        precios = precios.loc[:, ~precios.columns.duplicated()]  # Elimina columnas duplicadas.
        columnas = [t for t in tickers if t in precios.columns]  # Conserva tickers solicitados que sí llegaron.
        precios = precios[columnas] if columnas else precios  # Reordena columnas según solicitud si es posible.
        if precios.shape[1] < 2:  # Verifica que queden al menos dos activos.
            disponibles = ", ".join(map(str, precios.columns)) if precios.shape[1] else "ninguno"  # Lista activos disponibles.
            raise ValueError(f"Se necesitan al menos 2 activos con precios válidos. Activos disponibles: {disponibles}.")  # Lanza error.
        if precios.shape[0] < 3:  # Verifica que existan suficientes precios.
            raise ValueError("Se necesitan al menos 3 precios por activo para obtener suficientes rendimientos.")  # Lanza error.
        if (precios <= 0).any().any():  # Verifica que no existan precios cero o negativos.
            raise ValueError("Los precios contienen valores menores o iguales a cero; no se puede calcular rendimiento logarítmico.")  # Lanza error.
        return precios  # Devuelve precios limpios.

    def descargar_datos_yfinance(self) -> None:  # Descarga datos y calcula rendimientos logarítmicos.
        try:  # Captura errores para mostrarlos en ventana.
            tickers = self._obtener_tickers()  # Obtiene tickers limpios.
            fecha_inicio, fecha_fin = self._validar_fechas()  # Valida fechas de descarga.
            intervalo = self._obtener_intervalo()  # Obtiene intervalo de yfinance.
            datos = yf.download(tickers=tickers, start=fecha_inicio, end=fecha_fin, interval=intervalo, auto_adjust=True, progress=False, group_by="column", threads=True)  # Descarga precios ajustados.
            precios = self._extraer_precios_cierre(datos, tickers)  # Extrae precios Close limpios.
            retornos = np.log(precios / precios.shift(1)).dropna(how="any")  # Calcula rendimientos logarítmicos.
            if retornos.shape[0] < 2:  # Verifica que existan suficientes rendimientos.
                raise ValueError("Después de calcular rendimientos quedan menos de 2 periodos. Amplía el rango de fechas.")  # Lanza error.

            self.R = retornos.to_numpy(dtype=float)  # Guarda rendimientos como matriz NumPy.
            self.retornos_df = retornos.copy()  # Guarda rendimientos como DataFrame con fechas.
            self.nombres_activos = [str(c) for c in retornos.columns]  # Guarda nombres de activos.
            self.fechas_rendimientos = retornos.index  # Guarda fechas de rendimientos.
            self.precios_descargados = precios  # Guarda precios limpios.

            df_r = retornos.copy()  # Copia rendimientos para mostrar en tabla.
            df_r.insert(0, "Fecha", [idx.strftime("%Y-%m-%d") for idx in df_r.index])  # Agrega columna de fecha.
            self._llenar_treeview(self.tbl, df_r.reset_index(drop=True))  # Llena la tabla de rendimientos.

            mu_preview = np.mean(self.R, axis=0)  # Calcula promedio histórico por activo.
            self.r_min_var.set(float(np.min(mu_preview)))  # Sugiere r_min como el menor promedio histórico.
            self.txt_mu_custom.configure(state="normal")  # Habilita texto para insertar vista previa.
            self._set_text(self.txt_mu_custom, ", ".join(f"{x:.6f}" for x in mu_preview))  # Muestra mu histórico en el cuadro.
            self.actualizar_estado_mu()  # Vuelve a bloquear o activar el cuadro según opción elegida.

            k = self._factor_anualizacion()  # Obtiene factor de anualización.
            lineas = [  # Crea lista de líneas para resultados.
                "Datos descargados correctamente desde yfinance.",  # Mensaje de éxito.
                f"Tickers solicitados: {', '.join(tickers)}",  # Muestra tickers solicitados.
                f"Tickers usados: {', '.join(self.nombres_activos)}",  # Muestra tickers finalmente usados.
                f"Fecha inicial solicitada: {fecha_inicio}",  # Muestra fecha inicial.
                f"Fecha final solicitada: {fecha_fin}",  # Muestra fecha final.
                f"Periodicidad seleccionada: {self.intervalo_var.get()}",  # Muestra periodicidad.
                f"Factor de anualización usado: {k}",  # Muestra factor anual.
                f"Precios válidos por activo: {precios.shape[0]}",  # Muestra número de precios usados.
                f"Periodos de rendimiento usados: {self.R.shape[0]}",  # Muestra número de rendimientos usados.
                " ",  # Línea vacía.
                "Promedio histórico por activo, en escala de la periodicidad elegida:",  # Encabezado de promedio periódico.
            ]  # Termina lista inicial.
            for nombre, mu in zip(self.nombres_activos, mu_preview):  # Recorre activos y medias.
                lineas.append(f"{nombre}: {mu:.6f}")  # Agrega media periódica por activo.
            lineas.append(" ")  # Agrega línea vacía.
            lineas.append("Promedio histórico anualizado aproximado por activo:")  # Encabezado de medias anualizadas.
            for nombre, mu in zip(self.nombres_activos, mu_preview * k):  # Recorre activos y medias anualizadas.
                lineas.append(f"{nombre}: {mu:.6f}")  # Agrega media anualizada por activo.
            lineas.extend([" ", "Nota: con auto_adjust=True se usan precios ajustados por splits y dividendos cuando Yahoo los proporciona."])  # Agrega nota sobre precios ajustados.
            self._set_text(self.txt_resultados, lineas)  # Escribe resultados de descarga.

            self.lbl_mu_info.configure(text=f"Activos detectados: {len(self.nombres_activos)}\n\nSi eliges vector personalizado, captura exactamente {len(self.nombres_activos)} valores, uno por activo, en el mismo orden de la tabla.")  # Actualiza ayuda de mu.
            self._llenar_treeview(self.tbl_resultados, pd.DataFrame())  # Limpia tabla final.
            self._configurar_ejes()  # Reinicia gráfica.
            self.canvas.draw()  # Redibuja gráfica limpia.
            self._dibujar_placeholder_matriz(self.fig_cov, self.canvas_cov, "Matriz de covarianza")  # Reinicia imagen de covarianza.
            self._dibujar_placeholder_matriz(self.fig_corr, self.canvas_corr, "Matriz de correlación")  # Reinicia imagen de correlación.
            self.lbl_cov_interp.configure(text="La matriz de covarianza aparecerá aquí después de calcular el portafolio.")  # Reinicia interpretación de covarianza.
            self.lbl_corr_interp.configure(text="La matriz de correlación aparecerá aquí después de calcular el portafolio.")  # Reinicia interpretación de correlación.
        except Exception as exc:  # Captura cualquier error de descarga.
            messagebox.showerror("Error al descargar datos", str(exc))  # Muestra el error al usuario.

    # ------------------------------------------------------------------  # Separador visual de sección.
    # Retornos esperados y perfil del inversionista  # Nombre de sección.
    # ------------------------------------------------------------------  # Separador visual de sección.
    def obtener_vector_retornos_esperados(self, X: np.ndarray) -> np.ndarray:  # Obtiene vector mu según opción del usuario.
        n = X.shape[1]  # Obtiene número de activos.
        if self.tipo_mu_var.get() == "Promedio histórico":  # Si se eligió promedio histórico.
            return np.mean(X, axis=0)  # Devuelve media por columna.
        texto = self.txt_mu_custom.get("1.0", "end").strip()  # Lee texto del vector personalizado.
        if not texto:  # Verifica que no esté vacío.
            raise ValueError("Debes capturar un vector de retornos esperados. Ejemplo: 0.01, 0.015, 0.008")  # Lanza error.
        texto = texto.replace(",", " ")  # Convierte comas en espacios.
        try:  # Intenta convertir a números.
            mu = np.array([float(x) for x in texto.split()], dtype=float)  # Crea arreglo numérico.
        except ValueError as exc:  # Captura error de conversión.
            raise ValueError("No se pudo interpretar el vector personalizado. Usa números separados por comas o espacios.") from exc  # Lanza error claro.
        if mu.size != n:  # Verifica que haya un valor por activo.
            raise ValueError(f"El vector personalizado debe tener exactamente {n} valores, uno por activo.")  # Lanza error.
        if not np.all(np.isfinite(mu)):  # Verifica valores finitos.
            raise ValueError("El vector personalizado contiene valores no válidos.")  # Lanza error.
        return mu  # Devuelve vector personalizado.

    def obtener_parametros_perfil(self, mu: np.ndarray) -> dict:  # Calcula parámetros automáticos según perfil.
        perfil = self.perfil_riesgo_var.get()  # Lee perfil seleccionado.
        mu_min = float(np.min(mu))  # Calcula menor retorno esperado.
        mu_max = float(np.max(mu))  # Calcula mayor retorno esperado.
        rango = mu_max - mu_min  # Calcula rango de retornos esperados.
        if perfil == "Conservador":  # Caso de inversionista conservador.
            return {"r_min": mu_min + 0.25 * rango, "peso_max": 0.35, "objetivo": "Minimizar riesgo", "descripcion": "Prioriza menor riesgo y mayor diversificación."}  # Devuelve parámetros conservadores.
        if perfil == "Moderado":  # Caso de inversionista moderado.
            return {"r_min": mu_min + 0.50 * rango, "peso_max": 0.50, "objetivo": "Minimizar riesgo con retorno mínimo", "descripcion": "Busca equilibrio entre riesgo y rendimiento."}  # Devuelve parámetros moderados.
        if perfil == "Agresivo":  # Caso de inversionista agresivo.
            return {"r_min": mu_min + 0.75 * rango, "peso_max": 0.80, "objetivo": "Maximizar Sharpe Ratio", "descripcion": "Acepta mayor concentración y volatilidad buscando más rendimiento."}  # Devuelve parámetros agresivos.
        return {"r_min": mu_min + 0.50 * rango, "peso_max": 0.50, "objetivo": "Minimizar riesgo con retorno mínimo", "descripcion": "Perfil moderado por defecto."}  # Devuelve respaldo moderado.

    def obtener_rf_eua_yfinance(self) -> float:  # Descarga una tasa libre de riesgo aproximada de EUA con yfinance.
        ticker_rf = "^IRX"  # Define el ticker de Yahoo Finance para el T-Bill de 13 semanas.
        datos_rf = yf.download(ticker_rf, period="5d", interval="1d", auto_adjust=False, progress=False)  # Descarga los últimos días disponibles.
        if datos_rf.empty:  # Verifica si yfinance no devolvió datos.
            raise ValueError("No se pudo descargar ^IRX desde yfinance.")  # Lanza error si no hay datos.
        if "Close" not in datos_rf.columns:  # Verifica que exista la columna de cierre.
            raise ValueError("No se encontró la columna Close en ^IRX.")  # Lanza error si falta Close.
        cierre = datos_rf["Close"].dropna()  # Elimina valores faltantes de la columna Close.
        if isinstance(cierre, pd.DataFrame):  # Revisa si yfinance devolvió un DataFrame en vez de una Serie.
            cierre = cierre.iloc[:, 0]  # Toma la primera columna cuando hay estructura bidimensional.
        if cierre.empty:  # Verifica si no quedaron valores válidos.
            raise ValueError("La serie ^IRX no contiene cierres válidos.")  # Lanza error si no hay cierres útiles.
        ultimo_valor = float(cierre.iloc[-1])  # Toma el último valor disponible reportado por Yahoo Finance.
        rf_anual = ultimo_valor / 100.0  # Convierte porcentaje a decimal, por ejemplo 4.25 a 0.0425.
        if not np.isfinite(rf_anual) or rf_anual < 0:  # Valida que la tasa sea finita y no negativa.
            raise ValueError("La tasa obtenida desde ^IRX no es válida.")  # Lanza error si la tasa es inválida.
        return rf_anual  # Devuelve la tasa anual en decimal.

    def obtener_tasa_libre_riesgo_anual(self) -> tuple[float, str]:  # Decide qué tasa libre de riesgo anual usará el modelo.
        fuente = self.fuente_rf_var.get()  # Lee la fuente seleccionada en la interfaz.
        perfil = self.perfil_riesgo_var.get()  # Lee el perfil seleccionado en la interfaz.
        if fuente == "yfinance - T-Bill 13 semanas (^IRX)" and perfil == "Agresivo":  # Permite yfinance solo para perfil agresivo.
            try:  # Intenta descargar la tasa automáticamente.
                rf_anual = self.obtener_rf_eua_yfinance()  # Obtiene tasa anual desde ^IRX.
                self.rf_var.set(rf_anual)  # Actualiza el campo visible para que el usuario vea la tasa usada.
                return rf_anual, "yfinance ^IRX - T-Bill 13 semanas"  # Devuelve tasa y descripción de fuente.
            except Exception as exc:  # Captura errores de descarga o formato.
                messagebox.showwarning("Tasa libre de riesgo", f"No se pudo obtener ^IRX con yfinance. Se usará la tasa manual.\n\nDetalle: {exc}")  # Avisa que usará respaldo manual.
                return float(self.rf_var.get()), "Manual por respaldo"  # Devuelve valor manual si falla yfinance.
        if fuente == "yfinance - T-Bill 13 semanas (^IRX)" and perfil != "Agresivo":  # Detecta intento inconsistente.
            self.fuente_rf_var.set("Manual")  # Corrige la fuente para perfiles no arriesgados.
            return float(self.rf_var.get()), "Manual; yfinance solo permitido para perfil agresivo"  # Usa manual y explica fuente.
        return float(self.rf_var.get()), "Manual"  # Devuelve tasa manual por defecto.

    # ------------------------------------------------------------------  # Separador visual de sección.
    # Optimización  # Nombre de sección.
    # ------------------------------------------------------------------  # Separador visual de sección.
    def _asegurar_matriz_psd(self, Q: np.ndarray) -> tuple[np.ndarray, str]:  # Ajusta Q si no es semidefinida positiva.
        Q = (Q + Q.T) / 2.0  # Fuerza simetría numérica.
        valores_propios = np.linalg.eigvalsh(Q)  # Calcula valores propios simétricos.
        if np.all(valores_propios >= -1e-10):  # Verifica si Q ya es válida.
            return Q, ""  # Devuelve Q sin ajuste y sin mensaje.
        min_eig = float(np.min(valores_propios))  # Obtiene el valor propio más pequeño.
        Q_ajustada = Q + (abs(min_eig) + 1e-8) * np.eye(Q.shape[0])  # Suma diagonal para hacer Q PSD.
        return Q_ajustada, "La matriz de covarianza fue ajustada numéricamente para hacerla semidefinida positiva."  # Devuelve Q ajustada y mensaje.

    def _resolver_min_varianza(self, Q: np.ndarray, mu: np.ndarray, r_min: float | None, peso_max: float) -> tuple[np.ndarray, bool, str]:  # Resuelve mínima varianza.
        n = len(mu)  # Obtiene número de activos.
        x0 = np.full(n, 1.0 / n)  # Define punto inicial equiponderado.
        def objetivo(x: np.ndarray) -> float:  # Define función objetivo.
            return float(x.T @ Q @ x)  # Devuelve varianza del portafolio.
        restricciones = [{"type": "eq", "fun": lambda x: np.sum(x) - 1.0}]  # Restricción de suma de pesos igual a 1.
        if r_min is not None:  # Revisa si se requiere retorno mínimo.
            restricciones.append({"type": "ineq", "fun": lambda x, mu=mu, r_min=r_min: float(mu.T @ x - r_min)})  # Agrega restricción de rendimiento mínimo.
        resultado = minimize(objetivo, x0, method="SLSQP", bounds=[(0.0, peso_max)] * n, constraints=restricciones, options={"disp": False, "ftol": 1e-12, "maxiter": 1000})  # Ejecuta optimización.
        return resultado.x, bool(resultado.success), str(resultado.message)  # Devuelve pesos, éxito y mensaje.

    def _resolver_max_sharpe(self, Q: np.ndarray, mu: np.ndarray, rf_periodo: float, peso_max: float) -> tuple[np.ndarray, bool, str]:  # Resuelve máximo Sharpe.
        n = len(mu)  # Obtiene número de activos.
        x0 = np.full(n, 1.0 / n)  # Define punto inicial equiponderado.
        def objetivo(x: np.ndarray) -> float:  # Define objetivo a minimizar.
            ret = float(mu.T @ x)  # Calcula rendimiento esperado del portafolio.
            risk = float(np.sqrt(max(x.T @ Q @ x, 0.0)))  # Calcula riesgo del portafolio evitando raíz negativa.
            if risk <= 0:  # Evita división entre cero.
                return 1e6  # Penaliza soluciones con riesgo nulo o inválido.
            return -((ret - rf_periodo) / risk)  # Minimiza el negativo del Sharpe para maximizar Sharpe.
        restricciones = [{"type": "eq", "fun": lambda x: np.sum(x) - 1.0}]  # Restricción de suma de pesos igual a 1.
        resultado = minimize(objetivo, x0, method="SLSQP", bounds=[(0.0, peso_max)] * n, constraints=restricciones, options={"disp": False, "ftol": 1e-12, "maxiter": 1000})  # Ejecuta optimización.
        return resultado.x, bool(resultado.success), str(resultado.message)  # Devuelve pesos, éxito y mensaje.

    def _resolver_segun_objetivo(self, Q: np.ndarray, mu: np.ndarray, r_min: float, rf_periodo: float, peso_max: float, objetivo: str) -> tuple[np.ndarray, bool, str, str]:  # Selecciona optimizador.
        if objetivo == "Según perfil":  # Si el usuario dejó que el perfil decida.
            objetivo = self.obtener_parametros_perfil(mu)["objetivo"]  # Obtiene objetivo recomendado por perfil.
        if objetivo == "Minimizar riesgo":  # Si se eligió mínima varianza pura.
            x, ok, msg = self._resolver_min_varianza(Q, mu, r_min=None, peso_max=peso_max)  # Resuelve sin r_min.
            return x, ok, msg, objetivo  # Devuelve resultado y objetivo usado.
        if objetivo == "Minimizar riesgo con retorno mínimo":  # Si se eligió Markowitz clásico con retorno mínimo.
            x, ok, msg = self._resolver_min_varianza(Q, mu, r_min=r_min, peso_max=peso_max)  # Resuelve con r_min.
            return x, ok, msg, objetivo  # Devuelve resultado y objetivo usado.
        if objetivo == "Maximizar Sharpe Ratio":  # Si se eligió máximo Sharpe.
            x, ok, msg = self._resolver_max_sharpe(Q, mu, rf_periodo=rf_periodo, peso_max=peso_max)  # Resuelve máximo Sharpe.
            return x, ok, msg, objetivo  # Devuelve resultado y objetivo usado.
        raise ValueError("Objetivo de optimización no reconocido.")  # Lanza error si la opción es inválida.

    # ------------------------------------------------------------------  # Separador visual de sección.
    # Métricas financieras  # Nombre de sección.
    # ------------------------------------------------------------------  # Separador visual de sección.
    @staticmethod  # Indica que el método no usa self.
    def _metricas_portafolio(X: np.ndarray, Q: np.ndarray, mu: np.ndarray, w: np.ndarray, k: int, rf_anual: float) -> dict:  # Calcula métricas principales.
        ret_periodo = float(mu.T @ w)  # Calcula rendimiento esperado periódico.
        risk_periodo = float(np.sqrt(max(w.T @ Q @ w, 0.0)))  # Calcula riesgo periódico.
        ret_anual = ret_periodo * k  # Anualiza rendimiento esperado.
        risk_anual = risk_periodo * np.sqrt(k)  # Anualiza riesgo.
        sharpe = (ret_anual - rf_anual) / risk_anual if risk_anual > 0 else np.nan  # Calcula Sharpe anual.
        retornos_hist = X @ w  # Calcula rendimientos históricos del portafolio.
        return {"ret_periodo": ret_periodo, "risk_periodo": risk_periodo, "ret_anual": ret_anual, "risk_anual": risk_anual, "sharpe": sharpe, "retornos_hist": retornos_hist}  # Devuelve diccionario de métricas.

    @staticmethod  # Indica que el método no usa self.
    def _metricas_riesgo_historico(retornos_portafolio: np.ndarray, alpha: float = 0.95) -> tuple[float, float, float]:  # Calcula VaR, CVaR y drawdown.
        retornos_portafolio = np.asarray(retornos_portafolio, dtype=float)  # Asegura arreglo NumPy flotante.
        perdidas = -retornos_portafolio  # Convierte rendimientos negativos en pérdidas positivas.
        var = float(np.quantile(perdidas, alpha))  # Calcula VaR histórico al nivel alpha.
        cola = perdidas[perdidas >= var]  # Selecciona pérdidas en la cola extrema.
        cvar = float(np.mean(cola)) if cola.size else np.nan  # Calcula pérdida promedio en la cola.
        riqueza = np.cumprod(np.exp(retornos_portafolio))  # Convierte rendimientos logarítmicos en índice de riqueza.
        picos = np.maximum.accumulate(riqueza)  # Calcula máximos acumulados del índice.
        drawdowns = riqueza / picos - 1.0  # Calcula drawdown en cada periodo.
        max_drawdown = float(np.min(drawdowns))  # Obtiene peor drawdown histórico.
        return var, cvar, max_drawdown  # Devuelve las tres métricas.

    @staticmethod  # Indica que el método no usa self.
    def _contribucion_riesgo(Q: np.ndarray, w: np.ndarray) -> np.ndarray:  # Calcula contribución porcentual al riesgo.
        var_p = float(w.T @ Q @ w)  # Calcula varianza del portafolio.
        sigma_p = np.sqrt(max(var_p, 0.0))  # Calcula desviación estándar del portafolio.
        if sigma_p <= 0:  # Verifica riesgo positivo.
            return np.full_like(w, np.nan)  # Devuelve NaN si no se puede calcular.
        contrib_marginal = Q @ w / sigma_p  # Calcula contribución marginal al riesgo.
        contrib_total = w * contrib_marginal  # Calcula contribución total de cada activo.
        contrib_porcentual = contrib_total / sigma_p  # Convierte contribución total a proporción del riesgo total.
        return contrib_porcentual  # Devuelve contribuciones porcentuales.

    @staticmethod  # Indica que el método no usa self.
    def _concentracion(w: np.ndarray) -> tuple[float, float, float]:  # Calcula métricas de concentración.
        hhi = float(np.sum(w ** 2))  # Calcula índice Herfindahl-Hirschman.
        n_efectivo = float(1.0 / hhi) if hhi > 0 else np.nan  # Calcula número efectivo de activos.
        peso_maximo = float(np.max(w))  # Calcula peso máximo del portafolio.
        return hhi, n_efectivo, peso_maximo  # Devuelve concentración.

    def _diagnostico_automatico(self, nombres: list[str], w: np.ndarray, metricas_opt: dict, metricas_eq: dict, contrib_riesgo: np.ndarray, hhi: float, n_efectivo: float, peso_maximo: float, r_min: float) -> list[str]:  # Genera diagnóstico textual.
        lineas = []  # Crea lista de mensajes.
        idx_peso = int(np.argmax(w))  # Encuentra índice del activo con mayor peso.
        idx_riesgo = int(np.nanargmax(contrib_riesgo)) if np.any(np.isfinite(contrib_riesgo)) else idx_peso  # Encuentra activo con mayor contribución al riesgo.
        lineas.append("========= DIAGNÓSTICO AUTOMÁTICO =========")  # Agrega encabezado.
        lineas.append(f"El activo con mayor peso es {nombres[idx_peso]} con {w[idx_peso] * 100:.2f}%.")  # Describe activo dominante.
        lineas.append(f"El activo que más contribuye al riesgo es {nombres[idx_riesgo]} con {contrib_riesgo[idx_riesgo] * 100:.2f}% del riesgo total.")  # Describe riesgo dominante.
        if peso_maximo > 0.60:  # Evalúa concentración alta.
            lineas.append("Advertencia: el portafolio está altamente concentrado.")  # Mensaje de concentración alta.
        elif peso_maximo > 0.40:  # Evalúa concentración moderada.
            lineas.append("El portafolio tiene concentración moderada.")  # Mensaje de concentración moderada.
        else:  # Caso de concentración baja.
            lineas.append("El portafolio está relativamente diversificado por pesos.")  # Mensaje de diversificación.
        lineas.append(f"HHI = {hhi:.6f}; número efectivo de activos = {n_efectivo:.2f}.")  # Agrega medidas de concentración.
        if metricas_opt["sharpe"] > metricas_eq["sharpe"]:  # Compara Sharpe contra equiponderado.
            lineas.append("El portafolio optimizado tiene mejor Sharpe que el portafolio equiponderado.")  # Mensaje positivo.
        else:  # Si Sharpe no mejora.
            lineas.append("El portafolio optimizado no mejora el Sharpe del portafolio equiponderado; conviene revisar supuestos.")  # Mensaje crítico.
        if metricas_opt["ret_periodo"] >= r_min - 1e-8:  # Verifica si se alcanza r_min.
            lineas.append("El rendimiento mínimo usado por el modelo sí fue alcanzado.")  # Mensaje de factibilidad alcanzada.
        else:  # Si no se alcanza, puede ocurrir en objetivo máximo Sharpe sin restricción r_min.
            lineas.append("El rendimiento mínimo no fue vinculante o no fue usado por el objetivo seleccionado.")  # Mensaje explicativo.
        return lineas  # Devuelve lista de diagnósticos.

    # ------------------------------------------------------------------  # Separador visual de sección.
    # Cálculo principal  # Nombre de sección.
    # ------------------------------------------------------------------  # Separador visual de sección.
    def calcular_markowitz(self) -> None:  # Ejecuta cálculo completo de Markowitz y métricas adicionales.
        try:  # Captura errores para mostrarlos al usuario.
            if self.R is None:  # Verifica si ya se descargaron datos.
                messagebox.showwarning("Faltan datos", "Primero debes descargar precios desde yfinance.")  # Avisa que faltan datos.
                return  # Detiene ejecución.

            X = self.R  # Asigna matriz de rendimientos a variable corta.
            n = X.shape[1]  # Obtiene número de activos.
            if n < 2:  # Verifica mínimo de activos.
                messagebox.showerror("Error", "Se necesitan al menos 2 activos para construir un portafolio.")  # Muestra error.
                return  # Detiene ejecución.

            capital_total = float(self.capital_var.get())  # Lee capital total.
            if capital_total <= 0:  # Valida capital positivo.
                messagebox.showerror("Error", "El capital total debe ser mayor que cero.")  # Muestra error.
                return  # Detiene ejecución.

            k = self._factor_anualizacion()  # Obtiene factor de anualización.
            rf_anual, fuente_rf_usada = self.obtener_tasa_libre_riesgo_anual()  # Obtiene la tasa libre de riesgo manual o automática.
            rf_periodo = rf_anual / k  # Convierte tasa libre de riesgo anual a tasa periódica aproximada.
            mu = self.obtener_vector_retornos_esperados(X)  # Obtiene retornos esperados.
            parametros_perfil = self.obtener_parametros_perfil(mu)  # Obtiene r_min, peso máximo y objetivo por perfil.
            r_min = float(self.r_min_var.get()) if self.usar_rmin_manual_var.get() else parametros_perfil["r_min"]  # Decide si usar r_min manual o automático.
            peso_max = float(parametros_perfil["peso_max"])  # Obtiene peso máximo por activo según perfil.
            descripcion_perfil = str(parametros_perfil["descripcion"])  # Obtiene descripción textual del perfil.
            objetivo_solicitado = str(parametros_perfil["objetivo"])  # Usa siempre el objetivo automático definido por el perfil.
            self.objetivo_var.set(objetivo_solicitado)  # Actualiza la interfaz para mostrar el objetivo usado.
            self.r_min_var.set(r_min)  # Actualiza el campo r_min para mostrar el valor usado.

            if n * peso_max < 1.0:  # Verifica factibilidad de límites de peso.
                messagebox.showerror("Restricción no factible", f"El peso máximo por activo es demasiado bajo. n * peso_max = {n * peso_max:.2f}; debe ser al menos 1.")  # Muestra error.
                return  # Detiene ejecución.
            if r_min > np.max(mu) and objetivo_solicitado == "Minimizar riesgo con retorno mínimo":  # Revisa si r_min supera el máximo retorno disponible.
                messagebox.showerror("Rendimiento mínimo no factible", f"r_min = {r_min:.6f} supera el máximo retorno esperado individual = {np.max(mu):.6f}.")  # Muestra error.
                return  # Detiene ejecución.

            Q = np.cov(X, rowvar=False)  # Calcula matriz de covarianza muestral.
            Q, ajuste_texto = self._asegurar_matriz_psd(Q)  # Asegura que Q sea semidefinida positiva.
            cov_df = pd.DataFrame(Q, index=self.nombres_activos, columns=self.nombres_activos)  # Convierte Q en tabla para graficarla e interpretarla.
            if self.retornos_df is not None:  # Si existen rendimientos como DataFrame con nombres de activos.
                corr_df = self.retornos_df.corr()  # Calcula matriz de correlación de los rendimientos.
            else:  # Respaldo si solo existe la matriz NumPy.
                corr_df = pd.DataFrame(np.corrcoef(X, rowvar=False), index=self.nombres_activos, columns=self.nombres_activos)  # Calcula correlación desde NumPy.
            desviaciones = np.sqrt(np.diag(Q))  # Calcula desviación estándar periódica por activo.
            desviaciones_anuales = desviaciones * np.sqrt(k)  # Calcula desviación estándar anualizada por activo.
            mu_anual = mu * k  # Calcula retorno anualizado por activo.

            x_opt, ok, msg, objetivo_usado = self._resolver_segun_objetivo(Q, mu, r_min, rf_periodo, peso_max, objetivo_solicitado)  # Optimiza según objetivo.
            if not ok:  # Verifica si la optimización falló.
                messagebox.showerror("Error de optimización", f"No se encontró una solución factible.\n\nDetalle: {msg}")  # Muestra error.
                return  # Detiene ejecución.

            pesos_optimos = np.clip(x_opt, 0.0, peso_max)  # Recorta pequeños errores numéricos fuera de límites.
            pesos_optimos = pesos_optimos / np.sum(pesos_optimos)  # Renormaliza pesos para sumar exactamente 1.
            monto_optimo = capital_total * pesos_optimos  # Calcula monto invertido por activo.
            metricas_opt = self._metricas_portafolio(X, Q, mu, pesos_optimos, k, rf_anual)  # Calcula métricas del portafolio óptimo.
            var_95, cvar_95, max_dd = self._metricas_riesgo_historico(metricas_opt["retornos_hist"], alpha=0.95)  # Calcula riesgo histórico.
            contrib_riesgo = self._contribucion_riesgo(Q, pesos_optimos)  # Calcula contribución al riesgo.
            hhi, n_efectivo, peso_maximo_real = self._concentracion(pesos_optimos)  # Calcula concentración.

            w_eq = np.full(n, 1.0 / n)  # Construye pesos equiponderados.
            metricas_eq = self._metricas_portafolio(X, Q, mu, w_eq, k, rf_anual)  # Calcula métricas equiponderadas.
            var_eq, cvar_eq, dd_eq = self._metricas_riesgo_historico(metricas_eq["retornos_hist"], alpha=0.95)  # Calcula riesgo histórico equiponderado.

            x_mv, ok_mv, msg_mv = self._resolver_min_varianza(Q, mu, r_min=None, peso_max=peso_max)  # Calcula portafolio de mínima varianza para graficar.
            if not ok_mv:  # Verifica si falló mínima varianza.
                messagebox.showerror("Error", f"No se pudo calcular el portafolio de mínima varianza.\n\nDetalle: {msg_mv}")  # Muestra error.
                return  # Detiene ejecución.
            x_mv = np.clip(x_mv, 0.0, peso_max)  # Recorta errores numéricos.
            x_mv = x_mv / np.sum(x_mv)  # Renormaliza pesos.
            metricas_mv = self._metricas_portafolio(X, Q, mu, x_mv, k, rf_anual)  # Calcula métricas de mínima varianza.

            retornos_objetivo = np.linspace(metricas_mv["ret_periodo"], np.max(mu), 100)  # Define objetivos de retorno para frontera.
            riesgos_frontera = np.full_like(retornos_objetivo, np.nan, dtype=float)  # Crea arreglo de riesgos de frontera.
            retornos_frontera = np.full_like(retornos_objetivo, np.nan, dtype=float)  # Crea arreglo de retornos de frontera.
            for idx, r_obj in enumerate(retornos_objetivo):  # Recorre cada retorno objetivo.
                x_f, ok_f, _ = self._resolver_min_varianza(Q, mu, r_min=float(r_obj), peso_max=peso_max)  # Resuelve punto de frontera.
                if ok_f:  # Si la optimización fue exitosa.
                    x_f = np.clip(x_f, 0.0, peso_max)  # Recorta errores numéricos.
                    x_f = x_f / np.sum(x_f)  # Renormaliza pesos.
                    m_f = self._metricas_portafolio(X, Q, mu, x_f, k, rf_anual)  # Calcula métricas del punto.
                    riesgos_frontera[idx] = m_f["risk_anual"]  # Guarda riesgo anualizado.
                    retornos_frontera[idx] = m_f["ret_anual"]  # Guarda retorno anualizado.
            idx_validos = np.isfinite(riesgos_frontera) & np.isfinite(retornos_frontera)  # Identifica puntos válidos.

            diagnostico = self._diagnostico_automatico(self.nombres_activos, pesos_optimos, metricas_opt, metricas_eq, contrib_riesgo, hhi, n_efectivo, peso_maximo_real, r_min)  # Genera diagnóstico.
            periodo = self.intervalo_var.get()  # Lee periodicidad como texto visible.
            lineas = [  # Empieza líneas de resultados.
                "========= RESULTADOS =========",  # Encabezado principal.
                f"Perfil de inversionista: {self.perfil_riesgo_var.get()}",  # Muestra perfil.
                f"Descripción del perfil: {descripcion_perfil}",  # Muestra descripción del perfil.
                f"Objetivo solicitado: {objetivo_solicitado}",  # Muestra objetivo solicitado.
                f"Objetivo usado: {objetivo_usado}",  # Muestra objetivo realmente usado.
                f"Peso máximo permitido por activo según perfil: {peso_max:.2f}",  # Muestra límite de peso.
                f"Número de activos: {n}",  # Muestra número de activos.
                f"Número de periodos de rendimiento: {X.shape[0]}",  # Muestra número de periodos.
                f"Periodicidad de los rendimientos: {periodo}",  # Muestra periodicidad.
                f"Factor de anualización: {k}",  # Muestra factor anual.
                f"Rendimiento mínimo usado por el modelo: {r_min:.6f}",  # Muestra r_min usado.
                f"Capital total: {capital_total:.2f}",  # Muestra capital.
                f"Método para mu: {self.tipo_mu_var.get()}",  # Muestra método de mu.
                " ",  # Línea vacía.
                "========= PORTAFOLIO OPTIMIZADO =========",  # Encabezado de portafolio óptimo.
                f"Rendimiento esperado por periodo: {metricas_opt['ret_periodo']:.6f}",  # Muestra retorno periódico.
                f"Riesgo por periodo: {metricas_opt['risk_periodo']:.6f}",  # Muestra riesgo periódico.
                f"Rendimiento esperado anualizado: {metricas_opt['ret_anual']:.6f}",  # Muestra retorno anual.
                f"Riesgo anualizado: {metricas_opt['risk_anual']:.6f}",  # Muestra riesgo anual.
                f"Tasa libre de riesgo anual: {rf_anual:.6f}",  # Muestra tasa libre de riesgo.
                f"Fuente de tasa libre de riesgo: {fuente_rf_usada}",  # Muestra de dónde salió la tasa libre de riesgo.
                f"Sharpe Ratio: {metricas_opt['sharpe']:.6f}",  # Muestra Sharpe.
                f"VaR histórico 95% por periodo: {var_95:.6f}",  # Muestra VaR.
                f"CVaR histórico 95% por periodo: {cvar_95:.6f}",  # Muestra CVaR.
                f"Máximo drawdown histórico: {max_dd:.6f}",  # Muestra máximo drawdown.
                f"HHI: {hhi:.6f}",  # Muestra HHI.
                f"Número efectivo de activos: {n_efectivo:.2f}",  # Muestra número efectivo.
                " ",  # Línea vacía.
                "========= COMPARACIÓN CONTRA EQUIPONDERADO =========",  # Encabezado de comparación.
                f"Rendimiento equiponderado anualizado: {metricas_eq['ret_anual']:.6f}",  # Muestra retorno equiponderado.
                f"Riesgo equiponderado anualizado: {metricas_eq['risk_anual']:.6f}",  # Muestra riesgo equiponderado.
                f"Sharpe equiponderado: {metricas_eq['sharpe']:.6f}",  # Muestra Sharpe equiponderado.
                f"VaR equiponderado 95% por periodo: {var_eq:.6f}",  # Muestra VaR equiponderado.
                f"CVaR equiponderado 95% por periodo: {cvar_eq:.6f}",  # Muestra CVaR equiponderado.
                f"Drawdown equiponderado: {dd_eq:.6f}",  # Muestra drawdown equiponderado.
                " ",  # Línea vacía.
                "========= VECTOR DE RETORNOS ESPERADOS =========",  # Encabezado de mu.
            ]  # Termina lista inicial de resultados.
            for nombre, valor_mu, valor_mu_anual in zip(self.nombres_activos, mu, mu_anual):  # Recorre activos y retornos.
                lineas.append(f"{nombre}: mu_periodo={valor_mu:.6f}, mu_anual={valor_mu_anual:.6f}")  # Agrega retornos por activo.
            lineas.extend([" ", "========= DESVIACIÓN ESTÁNDAR POR ACTIVO ========="])  # Encabezado de desviaciones.
            for nombre, desv, desv_anual in zip(self.nombres_activos, desviaciones, desviaciones_anuales):  # Recorre activos y riesgos.
                lineas.append(f"{nombre}: sigma_periodo={desv:.6f}, sigma_anual={desv_anual:.6f}")  # Agrega riesgo individual.
            if ajuste_texto:  # Verifica si hubo ajuste en Q.
                lineas.extend([" ", ajuste_texto])  # Agrega nota de ajuste.
            lineas.extend([" "] + diagnostico)  # Agrega diagnóstico automático.
            lineas.extend([" ", "========= INTERPRETACIÓN DE LA MATRIZ DE COVARIANZA ========="])  # Encabezado de interpretación de covarianza.
            lineas.extend(self._interpretacion_covarianza(cov_df).split("\n"))  # Agrega interpretación de covarianza al texto de resultados.
            lineas.extend([" ", "========= INTERPRETACIÓN DE LA MATRIZ DE CORRELACIÓN ========="])  # Encabezado de interpretación de correlación.
            lineas.extend(self._interpretacion_correlacion(corr_df).split("\n"))  # Agrega interpretación de correlación al texto de resultados.
            self._set_text(self.txt_resultados, lineas)  # Escribe resultados en el cuadro de texto.

            df_resultados = pd.DataFrame({  # Crea DataFrame para tabla final.
                "Activo": self.nombres_activos,  # Columna con nombres de activos.
                "RetornoPeriodo": mu,  # Columna de retorno esperado periódico.
                "RetornoAnual": mu_anual,  # Columna de retorno esperado anual.
                "DesvPeriodo": desviaciones,  # Columna de riesgo periódico individual.
                "DesvAnual": desviaciones_anuales,  # Columna de riesgo anual individual.
                "Peso": pesos_optimos,  # Columna de pesos óptimos.
                "Porcentaje": 100.0 * pesos_optimos,  # Columna de pesos en porcentaje.
                "ContribRiesgo": contrib_riesgo,  # Columna de contribución al riesgo.
                "MontoOptimo": monto_optimo,  # Columna de monto invertido.
            })  # Termina DataFrame final.
            self._llenar_treeview(self.tbl_resultados, df_resultados)  # Llena tabla de resultados.

            self.ax.clear()  # Limpia gráfica anterior.
            self.ax.plot(riesgos_frontera[idx_validos], retornos_frontera[idx_validos], linewidth=2, label="Frontera eficiente")  # Grafica frontera eficiente.
            self.ax.plot(metricas_opt["risk_anual"], metricas_opt["ret_anual"], marker="o", markersize=8, linestyle="None", label="Portafolio optimizado")  # Grafica portafolio óptimo.
            self.ax.plot(metricas_mv["risk_anual"], metricas_mv["ret_anual"], marker="s", markersize=8, linestyle="None", label="Mínima varianza")  # Grafica mínima varianza.
            self.ax.plot(metricas_eq["risk_anual"], metricas_eq["ret_anual"], marker="^", markersize=8, linestyle="None", label="Equiponderado")  # Grafica equiponderado.
            self.ax.grid(True)  # Activa cuadrícula.
            self.ax.set_xlabel(r"Riesgo anualizado $\sigma_p$")  # Etiqueta eje X.
            self.ax.set_ylabel(r"Rendimiento anualizado $\mu_p$")  # Etiqueta eje Y.
            self.ax.set_title("Frontera eficiente y comparación")  # Título de gráfica.
            self.ax.legend(loc="best")  # Muestra leyenda.
            self.canvas.draw()  # Redibuja gráfica actualizada.
            self._graficar_matriz(self.fig_cov, self.canvas_cov, cov_df, "Matriz de covarianza", cmap="YlOrRd")  # Dibuja matriz de covarianza como imagen.
            self.lbl_cov_interp.configure(text=self._interpretacion_covarianza(cov_df))  # Muestra interpretación de covarianza.
            self._graficar_matriz(self.fig_corr, self.canvas_corr, corr_df, "Matriz de correlación", cmap="coolwarm", vmin=-1.0, vmax=1.0)  # Dibuja matriz de correlación como imagen.
            self.lbl_corr_interp.configure(text=self._interpretacion_correlacion(corr_df))  # Muestra interpretación de correlación.
        except Exception as exc:  # Captura cualquier error general.
            messagebox.showerror("Error", str(exc))  # Muestra error al usuario.


def main() -> None:  # Define función principal del programa.
    root = tk.Tk()  # Crea ventana raíz de Tkinter.
    MarkowitzGUI(root)  # Instancia la aplicación.
    root.mainloop()  # Inicia ciclo principal de eventos.


if __name__ == "__main__":  # Verifica si el archivo se ejecuta directamente.
    main()  # Ejecuta la función principal.
