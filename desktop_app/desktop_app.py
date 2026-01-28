import sys
import requests
import json
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QLineEdit, QFileDialog, QTableWidget,
    QTableWidgetItem, QTabWidget, QTextEdit, QMessageBox, QGridLayout
)
from PyQt5.QtCore import Qt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure


# ============================================
# CONFIGURATION
# ============================================
BACKEND_URL = "http://127.0.0.1:8000"


# ============================================
# LOGIN WINDOW
# ============================================
class LoginWindow(QWidget):
    """Simple login window for user authentication"""
    
    def __init__(self, main_app):
        super().__init__()
        self.main_app = main_app
        self.setup_window()
    
    def setup_window(self):
        """Setup the login window layout and widgets"""
        self.setWindowTitle('ChemViz - Login')
        self.setFixedSize(400, 300)
        
        # Create main layout
        layout = QVBoxLayout()
        
        # Title
        title = QLabel("ChemViz Login")
        title.setStyleSheet("font-size: 24px; font-weight: bold;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Username input
        layout.addWidget(QLabel("Username:"))
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Enter username")
        layout.addWidget(self.username_input)
        
        # Password input
        layout.addWidget(QLabel("Password:"))
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Enter password")
        self.password_input.setEchoMode(QLineEdit.Password)
        layout.addWidget(self.password_input)
        
        # Login button
        login_button = QPushButton("Login")
        login_button.clicked.connect(self.do_login)
        layout.addWidget(login_button)
        
        # Status message
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: red;")
        self.status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_label)
        
        self.setLayout(layout)
        
        # Press Enter to login
        self.password_input.returnPressed.connect(self.do_login)
    
    def do_login(self):
        """Handle login button click"""
        username = self.username_input.text()
        password = self.password_input.text()
        
        # Check if fields are empty
        if not username or not password:
            self.status_label.setText("Please enter username and password")
            return
        
        # Try to login via API
        try:
            response = requests.post(
                f"{BACKEND_URL}/api/login/",
                json={"username": username, "password": password}
            )
            
            if response.status_code == 200:
                # Login successful
                data = response.json()
                self.main_app.token = data['token']
                self.main_app.username = username
                self.main_app.open_dashboard()
                self.close()
            else:
                # Login failed
                self.status_label.setText("Invalid username or password")
        
        except Exception as e:
            self.status_label.setText("Cannot connect to server")
            print(f"Login error: {e}")


# ============================================
# MAIN DASHBOARD WINDOW
# ============================================
class DashboardWindow(QMainWindow):
    """Main dashboard window with tabs"""
    
    def __init__(self, main_app):
        super().__init__()
        self.main_app = main_app
        self.results = None  # Store analysis results
        self.history_data = []  # Store history data
        self.selected_file = None  # Store selected file path
        self.setup_window()
    
    def setup_window(self):
        """Setup the main dashboard window"""
        self.setWindowTitle('ChemViz - Dashboard')
        self.setGeometry(100, 100, 1200, 700)
        
        # Create main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout()
        
        # Add header section
        header = self.create_header()
        main_layout.addWidget(header)
        
        # Add tabs
        self.tabs = QTabWidget()
        self.tabs.addTab(self.create_overview_tab(), "Overview")
        self.tabs.addTab(self.create_analytics_tab(), "Analytics")
        self.tabs.addTab(self.create_history_tab(), "History")
        main_layout.addWidget(self.tabs)
        
        main_widget.setLayout(main_layout)
    
    def create_header(self):
        """Create the top header with file upload and buttons"""
        header_widget = QWidget()
        header_layout = QHBoxLayout()
        
        # Title
        title = QLabel("ChemViz Dashboard")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # File label
        self.file_label = QLabel("No file selected")
        header_layout.addWidget(self.file_label)
        
        # Choose file button
        choose_btn = QPushButton("Choose CSV File")
        choose_btn.clicked.connect(self.choose_file)
        header_layout.addWidget(choose_btn)
        
        # Upload button
        self.upload_btn = QPushButton("Upload & Analyze")
        self.upload_btn.clicked.connect(self.upload_file)
        header_layout.addWidget(self.upload_btn)
        
        # Download report button
        report_btn = QPushButton("Download Report")
        report_btn.clicked.connect(self.download_report)
        header_layout.addWidget(report_btn)
        
        # Logout button
        logout_btn = QPushButton("Logout")
        logout_btn.clicked.connect(self.logout)
        header_layout.addWidget(logout_btn)
        
        header_widget.setLayout(header_layout)
        return header_widget
    
    # ========================================
    # OVERVIEW TAB
    # ========================================
    def create_overview_tab(self):
        """Create the overview tab with stats and charts"""
        tab = QWidget()
        layout = QVBoxLayout()
        
        # Stats section
        stats_layout = QGridLayout()
        
        # Create stat labels
        self.stat_equipment = QLabel("Total Equipment: 0")
        self.stat_equipment.setStyleSheet("font-size: 14px; font-weight: bold; padding: 10px; background-color: lightblue;")
        stats_layout.addWidget(self.stat_equipment, 0, 0)
        
        self.stat_flowrate = QLabel("Avg Flowrate: 0.00")
        self.stat_flowrate.setStyleSheet("font-size: 14px; font-weight: bold; padding: 10px; background-color: lightgreen;")
        stats_layout.addWidget(self.stat_flowrate, 0, 1)
        
        self.stat_temp = QLabel("Avg Temperature: 0.00")
        self.stat_temp.setStyleSheet("font-size: 14px; font-weight: bold; padding: 10px; background-color: lightyellow;")
        stats_layout.addWidget(self.stat_temp, 0, 2)
        
        self.stat_pressure = QLabel("Avg Pressure: 0.00")
        self.stat_pressure.setStyleSheet("font-size: 14px; font-weight: bold; padding: 10px; background-color: lightcoral;")
        stats_layout.addWidget(self.stat_pressure, 0, 3)
        
        layout.addLayout(stats_layout)
        
        # Charts section
        charts_layout = QHBoxLayout()
        
        # Bar chart
        self.bar_chart = SimpleChart("Equipment Distribution")
        charts_layout.addWidget(self.bar_chart)
        
        # Pie chart
        self.pie_chart = SimpleChart("Type Distribution")
        charts_layout.addWidget(self.pie_chart)
        
        layout.addLayout(charts_layout)
        
        tab.setLayout(layout)
        return tab
    
    # ========================================
    # ANALYTICS TAB
    # ========================================
    def create_analytics_tab(self):
        """Create the analytics tab with trend chart and JSON"""
        tab = QWidget()
        layout = QVBoxLayout()
        
        # Line chart for temperature trend
        self.line_chart = SimpleChart("Temperature Trend")
        layout.addWidget(self.line_chart)
        
        # JSON output area
        layout.addWidget(QLabel("Raw Data (JSON):"))
        self.json_output = QTextEdit()
        self.json_output.setReadOnly(True)
        self.json_output.setPlainText("Upload a file to see data...")
        layout.addWidget(self.json_output)
        
        tab.setLayout(layout)
        return tab
    
    # ========================================
    # HISTORY TAB
    # ========================================
    def create_history_tab(self):
        """Create the history tab with upload history table"""
        tab = QWidget()
        layout = QVBoxLayout()
        
        # Refresh button
        refresh_btn = QPushButton("Refresh History")
        refresh_btn.clicked.connect(self.load_history)
        layout.addWidget(refresh_btn)
        
        # History table
        self.history_table = QTableWidget()
        self.history_table.setColumnCount(6)
        self.history_table.setHorizontalHeaderLabels([
            "Time", "Equipment", "Flowrate", "Pressure", "Temperature", "Status"
        ])
        layout.addWidget(self.history_table)
        
        tab.setLayout(layout)
        return tab
    
    # ========================================
    # FILE OPERATIONS
    # ========================================
    def choose_file(self):
        """Open file dialog to choose CSV file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Choose CSV File", "", "CSV Files (*.csv)"
        )
        
        if file_path:
            self.selected_file = file_path
            # Show just the filename
            import os
            filename = os.path.basename(file_path)
            self.file_label.setText(f"Selected: {filename}")
    
    def upload_file(self):
        """Upload the selected file to backend"""
        if not self.selected_file:
            QMessageBox.warning(self, "No File", "Please choose a CSV file first!")
            return
        
        # Disable button while uploading
        self.upload_btn.setEnabled(False)
        self.upload_btn.setText("Uploading...")
        
        try:
            # Open and send file
            with open(self.selected_file, 'rb') as f:
                files = {'file': f}
                headers = {'Authorization': f'Token {self.main_app.token}'}
                
                response = requests.post(
                    f"{BACKEND_URL}/api/upload/",
                    files=files,
                    headers=headers
                )
                
                if response.status_code == 200:
                    # Success!
                    self.results = response.json()['summary']
                    self.update_all_data()
                    QMessageBox.information(self, "Success", "File uploaded successfully!")
                else:
                    QMessageBox.warning(self, "Error", "Upload failed!")
        
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error: {str(e)}")
        
        finally:
            # Re-enable button
            self.upload_btn.setEnabled(True)
            self.upload_btn.setText("Upload & Analyze")
    
    # ========================================
    # UPDATE UI WITH DATA
    # ========================================
    def update_all_data(self):
        """Update all tabs with new data"""
        if not self.results:
            return
        
        # Update overview stats
        self.stat_equipment.setText(f"Total Equipment: {self.results.get('total_equipment', 0)}")
        self.stat_flowrate.setText(f"Avg Flowrate: {self.results.get('avg_flowrate', 0):.2f} L/min")
        self.stat_temp.setText(f"Avg Temperature: {self.results.get('avg_temperature', 0):.2f} °C")
        self.stat_pressure.setText(f"Avg Pressure: {self.results.get('avg_pressure', 0):.2f} PSI")
        
        # Update charts
        dist = self.results.get('type_distribution', {})
        if dist:
            labels = list(dist.keys())
            values = list(dist.values())
            
            # Update bar chart
            self.bar_chart.plot_bar(labels, values)
            
            # Update pie chart
            self.pie_chart.plot_pie(labels, values)
        
        # Update JSON output
        json_text = json.dumps(self.results, indent=2)
        self.json_output.setPlainText(json_text)
        
        # Load history
        self.load_history()
    
    def load_history(self):
        """Load upload history from backend"""
        try:
            headers = {'Authorization': f'Token {self.main_app.token}'}
            response = requests.get(f"{BACKEND_URL}/api/history/", headers=headers)
            
            if response.status_code == 200:
                self.history_data = response.json()
                self.update_history_table()
                self.update_line_chart()
        
        except Exception as e:
            print(f"Error loading history: {e}")
    
    def update_history_table(self):
        """Update the history table with data"""
        self.history_table.setRowCount(len(self.history_data))
        
        for i, item in enumerate(self.history_data):
            self.history_table.setItem(i, 0, QTableWidgetItem(item['time']))
            self.history_table.setItem(i, 1, QTableWidgetItem(str(item['total_equipment'])))
            self.history_table.setItem(i, 2, QTableWidgetItem(f"{item['avg_flowrate']:.2f}"))
            self.history_table.setItem(i, 3, QTableWidgetItem(f"{item['avg_pressure']:.2f}"))
            self.history_table.setItem(i, 4, QTableWidgetItem(f"{item['avg_temperature']:.2f}"))
            self.history_table.setItem(i, 5, QTableWidgetItem("Complete"))
    
    def update_line_chart(self):
        """Update the temperature trend line chart"""
        if not self.history_data:
            return
        
        labels = [f"Upload {i+1}" for i in range(len(self.history_data))]
        temps = [item['avg_temperature'] for item in self.history_data]
        self.line_chart.plot_line(labels, temps)
    
    # ========================================
    # OTHER FUNCTIONS
    # ========================================
    def download_report(self):
        """Download PDF report"""
        if not self.results:
            QMessageBox.warning(self, "No Data", "Please upload a file first!")
            return
        
        try:
            headers = {'Authorization': f'Token {self.main_app.token}'}
            data = {
                'results': self.results,
                'history': self.history_data,
                'username': self.main_app.username
            }
            
            response = requests.post(
                f"{BACKEND_URL}/api/generate-pdf-report/",
                json=data,
                headers=headers
            )
            
            if response.status_code == 200:
                # Ask user where to save
                file_path, _ = QFileDialog.getSaveFileName(
                    self, "Save Report", "ChemViz_Report.pdf", "PDF Files (*.pdf)"
                )
                
                if file_path:
                    # Save the PDF
                    with open(file_path, 'wb') as f:
                        f.write(response.content)
                    QMessageBox.information(self, "Success", "Report saved!")
            else:
                QMessageBox.warning(self, "Error", "Failed to generate report")
        
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error: {str(e)}")
    
    def logout(self):
        """Logout and return to login screen"""
        self.close()
        self.main_app.show_login_window()


# ============================================
# SIMPLE CHART WIDGET
# ============================================
class SimpleChart(QWidget):
    """A simple widget to display matplotlib charts"""
    
    def __init__(self, title):
        super().__init__()
        self.title = title
        
        # Create layout
        layout = QVBoxLayout()
        
        # Add title
        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        layout.addWidget(title_label)
        
        # Create matplotlib figure
        self.figure = Figure(figsize=(5, 4))
        self.canvas = FigureCanvas(self.figure)
        layout.addWidget(self.canvas)
        
        self.setLayout(layout)
    
    def plot_bar(self, labels, values):
        """Plot a bar chart"""
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        ax.bar(labels, values, color='skyblue')
        ax.set_ylabel('Count')
        ax.set_title(self.title)
        self.canvas.draw()
    
    def plot_pie(self, labels, values):
        """Plot a pie chart"""
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        ax.pie(values, labels=labels, autopct='%1.1f%%')
        ax.set_title(self.title)
        self.canvas.draw()
    
    def plot_line(self, labels, values):
        """Plot a line chart"""
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        ax.plot(labels, values, marker='o', color='orange')
        ax.set_ylabel('Temperature (°C)')
        ax.set_title(self.title)
        ax.grid(True)
        self.canvas.draw()


# ============================================
# MAIN APPLICATION CLASS
# ============================================
class ChemVizApp:
    """Main application controller"""
    
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.token = None
        self.username = None
        self.login_window = None
        self.dashboard_window = None
    
    def show_login_window(self):
        """Show the login window"""
        self.login_window = LoginWindow(self)
        self.login_window.show()
    
    def open_dashboard(self):
        """Open the main dashboard"""
        self.dashboard_window = DashboardWindow(self)
        self.dashboard_window.show()
        self.dashboard_window.load_history()
    
    def run(self):
        """Start the application"""
        self.show_login_window()
        sys.exit(self.app.exec_())


# ============================================
# START THE APPLICATION
# ============================================
if __name__ == '__main__':
    app = ChemVizApp()
    app.run()