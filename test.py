from PyQt5.QtWidgets import QPushButton, QVBoxLayout, QWidget
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt

class PlotToggleWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.plot_window = None
        self.button = QPushButton("Show Graph")
        self.button.clicked.connect(self.toggle_plot)

        layout = QVBoxLayout()
        layout.addWidget(self.button)
        self.setLayout(layout)

    def toggle_plot(self):
        if self.plot_window is None:
            self.plot_window = self.create_plot_window()
            self.plot_window.show()
            self.button.setText("Hide Graph")
        else:
            self.plot_window.close()
            self.plot_window = None
            self.button.setText("Show Graph")

    def create_plot_window(self):
        fig, ax = plt.subplots()
        # Replace this with your actual plotting logic
        ax.plot([0, 1, 2], [0, 1, 0], label="Sample")
        ax.legend()

        canvas = FigureCanvas(fig)
        plot_widget = QWidget()
        layout = QVBoxLayout()
        layout.addWidget(canvas)
        plot_widget.setLayout(layout)
        plot_widget.setWindowTitle("Matplotlib Graph")
        plot_widget.resize(600, 400)
        return plot_widget