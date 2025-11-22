import pyqtgraph as pg
import pandas as pd
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QListWidget, QSlider
from PyQt6.QtCore import Qt

# --------------------------
# EJE X CON FECHAS LEIBLES
# --------------------------
class TimeAxis(pg.AxisItem):
    def tickStrings(self, values, scale, spacing):
        out = []
        for v in values:
            try:
                t = pd.to_datetime(v)
                out.append(t.strftime("%Y-%m-%d\n%H:%M:%S"))
            except:
                out.append(str(v))
        return out


class PlotWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        # Fondo limpio
        pg.setConfigOption("background", "w")
        pg.setConfigOption("foreground", "k")

        layout = QVBoxLayout(self)

        # -------------------------------
        # Lista de columnas
        # -------------------------------
        self.columns_list = QListWidget()
        self.columns_list.setSelectionMode(self.columns_list.SelectionMode.MultiSelection)
        self.columns_list.itemSelectionChanged.connect(self.update_plot)
        layout.addWidget(self.columns_list)

        # -------------------------------
        # Gráfico principal
        # -------------------------------
        self.plot = pg.PlotWidget(
            axisItems={"bottom": TimeAxis(orientation="bottom")},
            background="w",
        )

        # Malla más suave
        self.plot.showGrid(x=True, y=True, alpha=0.2)

        self.plot.addLegend()
        layout.addWidget(self.plot, stretch=1)

        # Bloquear zoom vertical
        view = self.plot.getPlotItem().getViewBox()
        view.setMouseEnabled(x=True, y=False)

        # Limitar movimiento
        view.setLimits(xMin=0, xMax=1e15)

        # -------------------------------
        # Slider de tiempo inferior
        # -------------------------------
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.valueChanged.connect(self.update_plot)
        layout.addWidget(self.slider)

        # Dataframe cargado
        self.df = None
        self.window_size = None

    # -------------------------------
    # Cargar DataFrame
    # -------------------------------
    def set_dataframe(self, df):
        self.df = df.copy()
        self.columns_list.clear()

        # Ventana del 10% del dataset
        self.window_size = max(200, len(df) // 10)

        self.slider.setMinimum(0)
        self.slider.setMaximum(max(0, len(df) - self.window_size))

        for col in df.columns[1:]:
            self.columns_list.addItem(col)

        # Limitar pan en eje X (no salir del dataset)
        vb = self.plot.getPlotItem().getViewBox()
        vb.setLimits(
            xMin=df.iloc[0, 0].value if hasattr(df.iloc[0, 0], "value") else df.index[0],
            xMax=df.iloc[-1, 0].value if hasattr(df.iloc[-1, 0], "value") else df.index[-1],
        )

        self.update_plot()

    # -------------------------------
    # Actualizar gráfico
    # -------------------------------
    def update_plot(self):
        if self.df is None:
            return

        self.plot.clear()
        self.plot.addLegend()

        # Ventana temporal según slider
        start = self.slider.value()
        end = start + self.window_size
        end = min(end, len(self.df))

        df_vis = self.df.iloc[start:end]

        x = df_vis[self.df.columns[0]]

        selected_cols = [i.text() for i in self.columns_list.selectedItems()]
        if not selected_cols:
            return

        ymin_total = float("inf")
        ymax_total = float("-inf")

        # -------------------------------
        # Dibujar curvas de colores
        # -------------------------------
        for idx, col in enumerate(selected_cols):
            y = df_vis[col].values

            pen = pg.mkPen(color=pg.intColor(idx, len(selected_cols)), width=2)

            self.plot.plot(
                x,
                y,
                pen=pen,
                name=col
            )

            ymin_total = min(ymin_total, y.min())
            ymax_total = max(ymax_total, y.max())

        # -------------------------------
        # Escala Y dinámica SOLO para ventana visible
        # -------------------------------
        max_abs = max(abs(ymin_total), abs(ymax_total))
        self.plot.setYRange(-max_abs, max_abs)

        # Asegurar que la vista no sale del rango
        vb = self.plot.getPlotItem().getViewBox()
        vb.setLimits(
            xMin=self.df.iloc[0, 0].value if hasattr(self.df.iloc[0, 0], "value") else self.df.index[0],
            xMax=self.df.iloc[-1, 0].value if hasattr(self.df.iloc[-1, 0], "value") else self.df.index[-1],
        )
