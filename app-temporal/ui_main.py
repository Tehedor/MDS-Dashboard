# ui_main.py
import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel
)
from reader import auto_load_dataset
from plot_widget import PlotWidget

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("MVP – Visualizador CSV (PyQt + PyQtGraph)")
        self.resize(1600, 900)

        layout = QVBoxLayout(self)

        # Label superior
        self.label = QLabel("Cargando dataset…")
        layout.addWidget(self.label)

        # Widget del gráfico
        self.plot_widget = PlotWidget()
        layout.addWidget(self.plot_widget, stretch=1)

        # ------ cargar dataset automáticamente ------
        df, name = auto_load_dataset()
        if df is None:
            self.label.setText("❌ No se encontraron CSV en ./Datasets")
        else:
            self.label.setText(f"Dataset cargado: {name}")
            self.plot_widget.set_dataframe(df)
