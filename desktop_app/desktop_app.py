import sys
import requests
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton,
    QFileDialog, QTextEdit, QLabel, QTableWidget,
    QTableWidgetItem
)
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure


API_UPLOAD = "http://127.0.0.1:8000/api/upload/"
API_HISTORY = "http://127.0.0.1:8000/api/history/"


class ChemicalApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Chemical Equipment Visualizer - Desktop")
        self.setGeometry(200, 100, 800, 600)

        layout = QVBoxLayout()

        # Buttons
        self.uploadBtn = QPushButton("Upload CSV")
        self.uploadBtn.clicked.connect(self.upload_csv)

        self.historyBtn = QPushButton("Load History")
        self.historyBtn.clicked.connect(self.load_history)

        # Text Output
        self.resultBox = QTextEdit()
        self.resultBox.setReadOnly(True)

        # Table for History
        self.historyTable = QTableWidget()
        self.historyTable.setColumnCount(5)
        self.historyTable.setHorizontalHeaderLabels([
            "Time", "Total", "Avg Flow", "Avg Pressure", "Avg Temp"
        ])

        # Chart Area
        self.figure = Figure()
        self.canvas = FigureCanvas(self.figure)

        layout.addWidget(self.uploadBtn)
        layout.addWidget(QLabel("Upload Summary"))
        layout.addWidget(self.resultBox)
        layout.addWidget(self.canvas)
        layout.addWidget(self.historyBtn)
        layout.addWidget(self.historyTable)

        self.setLayout(layout)

    def upload_csv(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select CSV File", "", "CSV Files (*.csv)")
        if not file_path:
            return

        with open(file_path, 'rb') as f:
            response = requests.post(API_UPLOAD, files={"file": f})

        data = response.json()
        summary = data["summary"]

        # Show summary text
        self.resultBox.setText(str(summary))

        # Draw Chart
        type_dist = summary["type_distribution"]
        labels = list(type_dist.keys())
        values = list(type_dist.values())

        self.figure.clear()
        ax = self.figure.add_subplot(111)
        ax.bar(labels, values)
        ax.set_title("Equipment Type Distribution")
        self.canvas.draw()

    def load_history(self):
        response = requests.get(API_HISTORY)
        data = response.json()

        self.historyTable.setRowCount(len(data))

        for row in range(len(data)):
            self.historyTable.setItem(row, 0, QTableWidgetItem(data[row]["time"]))
            self.historyTable.setItem(row, 1, QTableWidgetItem(str(data[row]["total_equipment"])))
            self.historyTable.setItem(row, 2, QTableWidgetItem(str(data[row]["avg_flowrate"])))
            self.historyTable.setItem(row, 3, QTableWidgetItem(str(data[row]["avg_pressure"])))
            self.historyTable.setItem(row, 4, QTableWidgetItem(str(data[row]["avg_temperature"])))


# Run App
app = QApplication(sys.argv)
window = ChemicalApp()
window.show()
sys.exit(app.exec_())
