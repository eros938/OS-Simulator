import sys
import numpy as np
from PyQt5.QtWidgets import (QApplication, QMainWindow, QTabWidget, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QLineEdit, QPushButton, QTableWidget, QTableWidgetItem, 
                             QComboBox, QMessageBox, QGroupBox, QSpinBox,QTextEdit)
from PyQt5.QtCore import Qt
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

from PyQt5.QtGui import QColor
from PyQt5.QtCore import Qt

class ProcessScheduler:
    def __init__(self):
        self.processes = []
        
    def fcfs(self, processes):
        processes = sorted(processes, key=lambda x: x['arrival_time'])
        n = len(processes)
        waiting_time = [0] * n
        turnaround_time = [0] * n
        
        waiting_time[0] = 0
        for i in range(1, n):
            waiting_time[i] = processes[i-1]['burst_time'] + waiting_time[i-1]
            if waiting_time[i] < processes[i]['arrival_time']:
                waiting_time[i] = processes[i]['arrival_time']
        
        for i in range(n):
            turnaround_time[i] = processes[i]['burst_time'] + waiting_time[i]
        
        avg_waiting = sum(waiting_time) / n
        avg_turnaround = sum(turnaround_time) / n
        
        return {
            'processes': processes,
            'waiting_time': waiting_time,
            'turnaround_time': turnaround_time,
            'avg_waiting': avg_waiting,
            'avg_turnaround': avg_turnaround,
            'gantt_chart': self.generate_gantt(processes, waiting_time)
        }
    
    def sjf(self, processes):
        processes = sorted(processes, key=lambda x: x['burst_time'])
        return self.fcfs(processes)
    
    def round_robin(self, processes, quantum):
        n = len(processes)
        rem_bt = [p['burst_time'] for p in processes]
        wt = [0] * n
        tat = [0] * n
        time = 0
        gantt = []
        
        while True:
            done = True
            for i in range(n):
                if rem_bt[i] > 0:
                    done = False
                    if rem_bt[i] > quantum:
                        time += quantum
                        rem_bt[i] -= quantum
                        gantt.append((processes[i]['name'], time))
                    else:
                        time += rem_bt[i]
                        wt[i] = time - processes[i]['burst_time'] - processes[i]['arrival_time']
                        rem_bt[i] = 0
                        gantt.append((processes[i]['name'], time))
            if done:
                break
        
        for i in range(n):
            tat[i] = processes[i]['burst_time'] + wt[i]
        
        avg_waiting = sum(wt) / n
        avg_turnaround = sum(tat) / n
        
        return {
            'processes': processes,
            'waiting_time': wt,
            'turnaround_time': tat,
            'avg_waiting': avg_waiting,
            'avg_turnaround': avg_turnaround,
            'gantt_chart': gantt
        }
    
    def generate_gantt(self, processes, waiting_time):
        gantt = []
        for i, p in enumerate(processes):
            start = max(p['arrival_time'], waiting_time[i])
            end = start + p['burst_time']
            gantt.append((p['name'], start, end))
        return gantt

class DeadlockDetector:
    def __init__(self):
        pass
    
    def detect_deadlock(self, allocation, request, available):
        n = len(allocation)
        m = len(available)
        work = available.copy()
        finish = [False] * n
        
        # Safety algorithm
        safe_sequence = []
        count = 0
        while count < n:
            found = False
            for i in range(n):
                if not finish[i] and all(request[i][j] <= work[j] for j in range(m)):
                    for j in range(m):
                        work[j] += allocation[i][j]
                    finish[i] = True
                    safe_sequence.append(f"P{i}")
                    found = True
                    count += 1
            if not found:
                break
        
        if count < n:
            return {'deadlock': True, 'safe_sequence': []}
        else:
            return {'deadlock': False, 'safe_sequence': safe_sequence}

class SchedulingTab(QWidget):
    def __init__(self):
        super().__init__()
        self.scheduler = ProcessScheduler()
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Algorithm selection
        algo_group = QGroupBox("Scheduling Algorithm")
        algo_layout = QHBoxLayout()
        
        self.algo_combo = QComboBox()
        self.algo_combo.addItems(["FCFS", "SJF", "Round Robin"])
        self.algo_combo.currentTextChanged.connect(self.toggle_quantum)
        
        self.quantum_label = QLabel("Quantum:")
        self.quantum_input = QLineEdit("2")
        self.quantum_input.setFixedWidth(50)
        self.quantum_label.hide()
        self.quantum_input.hide()
        
        algo_layout.addWidget(QLabel("Algorithm:"))
        algo_layout.addWidget(self.algo_combo)
        algo_layout.addWidget(self.quantum_label)
        algo_layout.addWidget(self.quantum_input)
        algo_layout.addStretch()
        algo_group.setLayout(algo_layout)
        
        # Process table
        self.process_table = QTableWidget()
        self.process_table.setColumnCount(4)
        self.process_table.setHorizontalHeaderLabels(["Process", "Burst Time", "Arrival Time", "Action"])
        self.process_table.horizontalHeader().setStretchLastSection(True)
        
        # Buttons
        button_layout = QHBoxLayout()
        add_button = QPushButton("Add Process")
        add_button.clicked.connect(self.add_process_row)
        run_button = QPushButton("Run Scheduling")
        run_button.clicked.connect(self.run_scheduling)
        button_layout.addWidget(add_button)
        button_layout.addWidget(run_button)
        
        # Results
        self.results_label = QLabel("Results will appear here")
        self.results_label.setWordWrap(True)
        
        # Gantt chart
        self.figure = plt.figure()
        self.canvas = FigureCanvas(self.figure)
        
        layout.addWidget(algo_group)
        layout.addWidget(self.process_table)
        layout.addLayout(button_layout)
        layout.addWidget(self.results_label)
        layout.addWidget(self.canvas)
        
        self.setLayout(layout)
        
        # Add initial processes
        self.add_process_row()
        self.add_process_row()
    
    def toggle_quantum(self, text):
        if text == "Round Robin":
            self.quantum_label.show()
            self.quantum_input.show()
        else:
            self.quantum_label.hide()
            self.quantum_input.hide()
    
    def add_process_row(self):
        row = self.process_table.rowCount()
        self.process_table.insertRow(row)
        
        name_item = QTableWidgetItem(f"P{row+1}")
        burst_item = QTableWidgetItem("5")
        arrival_item = QTableWidgetItem("0")
        
        remove_button = QPushButton("Remove")
        remove_button.clicked.connect(lambda: self.remove_row(row))
        
        self.process_table.setItem(row, 0, name_item)
        self.process_table.setItem(row, 1, burst_item)
        self.process_table.setItem(row, 2, arrival_item)
        self.process_table.setCellWidget(row, 3, remove_button)
    
    def remove_row(self, row):
        self.process_table.removeRow(row)
    
    def run_scheduling(self):
        try:
            processes = []
            for row in range(self.process_table.rowCount()):
                name = self.process_table.item(row, 0).text()
                burst = int(self.process_table.item(row, 1).text())
                arrival = int(self.process_table.item(row, 2).text())
                processes.append({
                    'name': name,
                    'burst_time': burst,
                    'arrival_time': arrival
                })
            
            if not processes:
                QMessageBox.warning(self, "Error", "No processes to schedule!")
                return
            
            algorithm = self.algo_combo.currentText()
            if algorithm == "FCFS":
                result = self.scheduler.fcfs(processes)
            elif algorithm == "SJF":
                result = self.scheduler.sjf(processes)
            elif algorithm == "Round Robin":
                quantum = int(self.quantum_input.text())
                result = self.scheduler.round_robin(processes, quantum)
            
            self.display_results(result)
            self.plot_gantt_chart(result)
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred: {str(e)}")
    
    def display_results(self, result):
        text = f"""
        <h3>Scheduling Results</h3>
        <p><b>Algorithm:</b> {self.algo_combo.currentText()}</p>
        <p><b>Average Waiting Time:</b> {result['avg_waiting']:.2f}</p>
        <p><b>Average Turnaround Time:</b> {result['avg_turnaround']:.2f}</p>
        <table border="1">
            <tr>
                <th>Process</th>
                <th>Arrival Time</th>
                <th>Burst Time</th>
                <th>Waiting Time</th>
                <th>Turnaround Time</th>
            </tr>
        """
        
        for i, p in enumerate(result['processes']):
            text += f"""
            <tr>
                <td>{p['name']}</td>
                <td>{p['arrival_time']}</td>
                <td>{p['burst_time']}</td>
                <td>{result['waiting_time'][i]}</td>
                <td>{result['turnaround_time'][i]}</td>
            </tr>
            """
        
        text += "</table>"
        self.results_label.setText(text)
    
    def plot_gantt_chart(self, result):
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        
        if isinstance(result['gantt_chart'][0], tuple) and len(result['gantt_chart'][0]) == 3:
            # For FCFS/SJF
            for i, (name, start, end) in enumerate(result['gantt_chart']):
                ax.broken_barh([(start, end-start)], (i*10, 9), facecolors=('tab:blue'))
                ax.text(start + (end-start)/2, i*10 + 5, name, ha='center', va='center')
        else:
            # For Round Robin
            time = 0
            y_pos = 0
            for name, end in result['gantt_chart']:
                duration = end - time
                ax.broken_barh([(time, duration)], (y_pos*10, 9), facecolors=('tab:blue'))
                ax.text(time + duration/2, y_pos*10 + 5, name, ha='center', va='center')
                time = end
                y_pos = (y_pos + 1) % 3  # Cycle through 3 y positions for visibility
        
        ax.set_yticks([])
        ax.set_xlabel('Time')
        ax.set_title('Gantt Chart')
        self.canvas.draw()

class DeadlockTab(QWidget):
    def __init__(self):
        super().__init__()
        self.detector = DeadlockDetector()
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Setup controls
        setup_group = QGroupBox("Setup")
        setup_layout = QHBoxLayout()
        
        self.processes_input = QLineEdit("3")
        self.processes_input.setFixedWidth(50)
        self.resources_input = QLineEdit("2")
        self.resources_input.setFixedWidth(50)
        
        setup_button = QPushButton("Setup Tables")
        setup_button.clicked.connect(self.setup_tables)
        
        setup_layout.addWidget(QLabel("Processes:"))
        setup_layout.addWidget(self.processes_input)
        setup_layout.addWidget(QLabel("Resources:"))
        setup_layout.addWidget(self.resources_input)
        setup_layout.addWidget(setup_button)
        setup_layout.addStretch()
        setup_group.setLayout(setup_layout)
        
        # Tables
        tables_layout = QHBoxLayout()
        
        self.allocation_table = QTableWidget()
        self.allocation_table.setHorizontalHeaderLabels(["R0", "R1"])
        self.allocation_table.verticalHeader().setVisible(True)
        
        self.request_table = QTableWidget()
        self.request_table.setHorizontalHeaderLabels(["R0", "R1"])
        self.request_table.verticalHeader().setVisible(True)
        
        self.available_table = QTableWidget()
        self.available_table.setRowCount(1)
        self.available_table.setHorizontalHeaderLabels(["R0", "R1"])
        self.available_table.verticalHeader().setVisible(False)
        
        tables_layout.addWidget(self.create_table_group("Allocation", self.allocation_table))
        tables_layout.addWidget(self.create_table_group("Request", self.request_table))
        tables_layout.addWidget(self.create_table_group("Available", self.available_table))
        
        # Detect button
        detect_button = QPushButton("Detect Deadlock")
        detect_button.clicked.connect(self.detect_deadlock)
        
        # Results
        self.results_label = QLabel("Results will appear here")
        self.results_label.setWordWrap(True)
        
        layout.addWidget(setup_group)
        layout.addLayout(tables_layout)
        layout.addWidget(detect_button)
        layout.addWidget(self.results_label)
        
        self.setLayout(layout)
        
        # Initial setup
        self.setup_tables()
    
    def create_table_group(self, title, table):
        group = QGroupBox(title)
        layout = QVBoxLayout()
        layout.addWidget(table)
        group.setLayout(layout)
        return group
    
    def setup_tables(self):
        try:
            n = int(self.processes_input.text())
            m = int(self.resources_input.text())
            
            # Allocation table
            self.allocation_table.setRowCount(n)
            self.allocation_table.setColumnCount(m)
            self.allocation_table.setVerticalHeaderLabels([f"P{i}" for i in range(n)])
            
            # Request table
            self.request_table.setRowCount(n)
            self.request_table.setColumnCount(m)
            self.request_table.setVerticalHeaderLabels([f"P{i}" for i in range(n)])
            
            # Available table
            self.available_table.setColumnCount(m)
            for j in range(m):
                item = QTableWidgetItem("1")
                self.available_table.setItem(0, j, item)
            
            # Fill tables with default values
            for i in range(n):
                for j in range(m):
                    self.allocation_table.setItem(i, j, QTableWidgetItem("0"))
                    self.request_table.setItem(i, j, QTableWidgetItem("0"))
            
        except ValueError:
            QMessageBox.warning(self, "Error", "Please enter valid numbers for processes and resources")
    
    def detect_deadlock(self):
        try:
            n = self.allocation_table.rowCount()
            m = self.allocation_table.columnCount()
            
            allocation = []
            for i in range(n):
                row = []
                for j in range(m):
                    item = self.allocation_table.item(i, j)
                    row.append(int(item.text()) if item and item.text() else 0)
                allocation.append(row)
            
            request = []
            for i in range(n):
                row = []
                for j in range(m):
                    item = self.request_table.item(i, j)
                    row.append(int(item.text()) if item and item.text() else 0)
                request.append(row)
            
            available = []
            for j in range(m):
                item = self.available_table.item(0, j)
                available.append(int(item.text()) if item and item.text() else 0)
            
            result = self.detector.detect_deadlock(allocation, request, available)
            
            if result['deadlock']:
                self.results_label.setText("<h3>Deadlock Detected!</h3><p style='color: red;'>The system is in a deadlock state.</p>")
            else:
                self.results_label.setText(f"""
                    <h3>No Deadlock</h3>
                    <p style='color: green;'>The system is in a safe state.</p>
                    <p><b>Safe Sequence:</b> {' → '.join(result['safe_sequence'])}</p>
                """)
        
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred: {str(e)}")

from collections import deque
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, 
                            QLabel, QSpinBox, QLineEdit, QPushButton, 
                            QTableWidget, QTableWidgetItem, QTextEdit)

class Semaphore:
    def __init__(self, value=1):
        self.value = value          # Available permits
        self.queue = deque()        # Process wait queue (FIFO)
        self.holder = None          # Current process holding the semaphore
        
    def acquire(self, process_name):
        """Returns True if acquired successfully, False if blocked"""
        if self.value > 0:
            self.value -= 1
            self.holder = process_name
            return True
        else:
            if process_name not in self.queue:
                self.queue.append(process_name)
            return False
            
    def release(self):
        """Returns the next process to wake up or None"""
        self.value += 1
        self.holder = None
        if self.queue:
            return self.queue.popleft()
        return None

class ProcessSyncTab(QWidget):
    def __init__(self):
        super().__init__()
        self.semaphores = {}
        self.processes = []
        self.time = 0
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_simulation)
        self.MAX_HOLD_TIME = 3
        self.WORK_UNITS = 3
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Configuration Panel
        config_group = QGroupBox("Configuration")
        config_layout = QHBoxLayout()

        self.process_spin = QSpinBox()
        self.process_spin.setRange(2, 10)
        self.process_spin.setValue(3)

        self.resource_input = QLineEdit("Printer")
        self.semaphore_spin = QSpinBox()
        self.semaphore_spin.setRange(1, 3)
        self.semaphore_spin.setValue(1)

        config_layout.addWidget(QLabel("Processes:"))
        config_layout.addWidget(self.process_spin)
        config_layout.addWidget(QLabel("Shared Resource:"))
        config_layout.addWidget(self.resource_input)
        config_layout.addWidget(QLabel("Semaphores:"))
        config_layout.addWidget(self.semaphore_spin)
        config_layout.addStretch()

        config_group.setLayout(config_layout)

        # Control Buttons
        button_layout = QHBoxLayout()
        self.start_button = QPushButton("Start")
        self.start_button.clicked.connect(self.start_simulation)
        self.pause_button = QPushButton("Pause")
        self.pause_button.clicked.connect(self.pause_simulation)
        self.pause_button.setEnabled(False)
        self.reset_button = QPushButton("Reset")
        self.reset_button.clicked.connect(self.reset_simulation)

        button_layout.addWidget(self.start_button)
        button_layout.addWidget(self.pause_button)
        button_layout.addWidget(self.reset_button)

        # Process State Table
        self.state_table = QTableWidget()
        self.state_table.setColumnCount(5)
        self.state_table.setHorizontalHeaderLabels(
            ["Process", "State", "Action", "Blocked On", "Queue Pos"]
        )
        self.state_table.verticalHeader().setVisible(False)

        # Timeline Visualization
        self.timeline_label = QLabel("Timeline will appear here")
        self.timeline_label.setWordWrap(True)

        # Log Output
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setMaximumHeight(100)

        layout.addWidget(config_group)
        layout.addLayout(button_layout)
        layout.addWidget(self.state_table)
        layout.addWidget(self.timeline_label)
        layout.addWidget(self.log_output)
        self.setLayout(layout)

    def start_simulation(self):
        self.reset_simulation()
        num_processes = self.process_spin.value()
        resource = self.resource_input.text()
        num_semaphores = self.semaphore_spin.value()

        # Initialize semaphores
        self.semaphores = {resource: Semaphore(value=num_semaphores)}

        # Create processes
        self.processes = []
        for i in range(num_processes):
            self.processes.append({
                'name': f"P{i}",
                'state': "Ready",
                'action': "",
                'blocked_on': "",
                'progress': 0,
                'hold_start': None,
                'wait_since': None,
                'queue_pos': 0
            })

        self.update_state_table()
        self.timer.start(1000)
        self.start_button.setEnabled(False)
        self.pause_button.setEnabled(True)
        self.log(f"Simulation started with {num_processes} processes sharing {resource}")

    def pause_simulation(self):
        if self.timer.isActive():
            self.timer.stop()
            self.pause_button.setText("Resume")
            self.log("Simulation paused")
        else:
            self.timer.start(1000)
            self.pause_button.setText("Pause")
            self.log("Simulation resumed")

    def reset_simulation(self):
        self.timer.stop()
        self.processes = []
        self.time = 0
        self.state_table.setRowCount(0)
        self.timeline_label.setText("Timeline will appear here")
        self.log_output.clear()
        self.start_button.setEnabled(True)
        self.pause_button.setEnabled(False)
        self.pause_button.setText("Pause")

    def update_simulation(self):
        self.time += 1
        resource = self.resource_input.text()
        semaphore = self.semaphores.get(resource)
        
        if not semaphore:
            self.log("Error: No semaphore initialized!")
            return

        # Update all processes
        active_process = None
        for process in self.processes:
            # Update running processes
            if process['state'] == "Running":
                if process.get('hold_start') is None:
                    process['hold_start'] = self.time
                
                process['progress'] = min(process.get('progress', 0) + 1, self.WORK_UNITS)
                process['hold_time'] = self.time - process['hold_start']
                
                if (process['progress'] >= self.WORK_UNITS or 
                    process['hold_time'] >= self.MAX_HOLD_TIME):
                    
                    self.release_resource(process)
                    process.update({
                        'state': "Ready",
                        'progress': 0,
                        'hold_start': None,
                        'blocked_on': ""
                    })
                else:
                    active_process = process

            # Update blocked processes
            elif process['state'] == "Blocked":
                try:
                    process['queue_pos'] = semaphore.queue.index(process['name']) + 1
                except ValueError:
                    process['state'] = "Ready"
                    process['queue_pos'] = 0
                    process['wait_since'] = None

        # Assign resource if available
        if not active_process and semaphore.value > 0:
            # Find longest-waiting ready process
            oldest_waiting = None
            min_wait_time = float('inf')
            
            for process in self.processes:
                if process['state'] == "Ready":
                    if process.get('wait_since') is None:
                        process['wait_since'] = self.time
                    
                    wait_time = self.time - process['wait_since']
                    if wait_time < min_wait_time:
                        oldest_waiting = process
                        min_wait_time = wait_time
            
            if oldest_waiting and self.acquire_resource(oldest_waiting):
                oldest_waiting.update({
                    'state': "Running",
                    'action': f"Accessing {resource}",
                    'hold_start': self.time,
                    'wait_since': None,
                    'queue_pos': 0
                })

        # Update timeline
        timeline_text = f"Time {self.time}: "
        for process in self.processes:
            state_symbol = {
                "Running": "[Locked]",
                "Blocked": "[Waiting]",
                "Ready": "[Ready]"
            }.get(process['state'], "")
            timeline_text += f"{process['name']}{state_symbol} "
        
        self.timeline_label.setText(timeline_text)
        self.update_state_table()

    def acquire_resource(self, process):
        resource = self.resource_input.text()
        semaphore = self.semaphores.get(resource)
        
        if not semaphore:
            self.log(f"Error: No semaphore for {resource}")
            return False
            
        if semaphore.acquire(process['name']):
            self.log(f"{process['name']} acquired {resource} (Sem={semaphore.value+1}→{semaphore.value})")
            return True
        else:
            process['state'] = "Blocked"
            process['blocked_on'] = resource
            if process['wait_since'] is None:
                process['wait_since'] = self.time
            self.log(f"{process['name']} blocked (Queue pos: {len(semaphore.queue)})")
            return False

    def release_resource(self, process):
        resource = self.resource_input.text()
        semaphore = self.semaphores.get(resource)
        
        if semaphore:
            next_process = semaphore.release()
            self.log(f"{process['name']} released {resource} (Sem={semaphore.value-1}→{semaphore.value})")
            
            if next_process:
                self.log(f"Resource granted to {next_process}")
        else:
            self.log(f"Error: No semaphore to release for {resource}")

    def update_state_table(self):
        self.state_table.setRowCount(len(self.processes))
        for row, process in enumerate(self.processes):
            self.state_table.setItem(row, 0, QTableWidgetItem(process['name']))
            self.state_table.setItem(row, 1, QTableWidgetItem(process['state']))
            self.state_table.setItem(row, 2, QTableWidgetItem(process['action']))
            self.state_table.setItem(row, 3, QTableWidgetItem(process['blocked_on']))
            self.state_table.setItem(row, 4, QTableWidgetItem(str(process.get('queue_pos', 0))))

            # Color coding
            for col in range(5):
                item = self.state_table.item(row, col)
                if process['state'] == "Running":
                    item.setBackground(QColor(200, 255, 200))  # Light green
                elif process['state'] == "Blocked":
                    item.setBackground(QColor(255, 255, 150))  # Light yellow

    def log(self, message):
        self.log_output.append(f"[{self.time:03d}] {message}")

  
from PyQt5.QtGui import QPixmap, QPainter, QColor, QIntValidator

from PyQt5.QtWidgets import QMessageBox, QComboBox, QGridLayout

class MemoryBlock:
    def __init__(self, start, size, process=None):
        self.start = start
        self.size = size
        self.process = process  # None means free block
        self.next = None

class MemoryManagerTab(QWidget):
    def __init__(self):
        super().__init__()
        self.memory = None
        self.total_memory = 1024  # Default 1KB memory
        self.allocation_strategy = "First Fit"
        self.partition_type = "Variable"
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Configuration Panel
        config_group = QGroupBox("Memory Configuration")
        config_layout = QGridLayout()

        # Memory Size Input
        config_layout.addWidget(QLabel("Total Memory:"), 0, 0)
        self.memory_input = QLineEdit(str(self.total_memory))
        self.memory_input.setValidator(QIntValidator(100, 9999))
        config_layout.addWidget(self.memory_input, 0, 1)

        # Partition Type
        config_layout.addWidget(QLabel("Partition Type:"), 1, 0)
        self.partition_combo = QComboBox()
        self.partition_combo.addItems(["Variable", "Fixed"])
        self.partition_combo.currentTextChanged.connect(self.change_partition_type)
        config_layout.addWidget(self.partition_combo, 1, 1)

        # Fixed Partitions Configuration (hidden by default)
        self.fixed_partitions_group = QGroupBox("Fixed Partitions")
        fixed_layout = QHBoxLayout()
        self.partition_sizes_input = QLineEdit("100,200,300,200,100")
        fixed_layout.addWidget(QLabel("Partition Sizes:"))
        fixed_layout.addWidget(self.partition_sizes_input)
        self.fixed_partitions_group.setLayout(fixed_layout)
        self.fixed_partitions_group.hide()
        config_layout.addWidget(self.fixed_partitions_group, 2, 0, 1, 2)

        # Allocation Strategy
        config_layout.addWidget(QLabel("Allocation Strategy:"), 3, 0)
        self.strategy_combo = QComboBox()
        self.strategy_combo.addItems(["First Fit", "Best Fit", "Worst Fit"])
        config_layout.addWidget(self.strategy_combo, 3, 1)

        # Process Allocation Controls
        process_group = QGroupBox("Process Allocation")
        process_layout = QHBoxLayout()
        self.process_size_input = QLineEdit("100")
        self.process_size_input.setValidator(QIntValidator(1, 9999))
        self.allocate_btn = QPushButton("Allocate")
        self.allocate_btn.clicked.connect(self.allocate_memory)
        self.deallocate_btn = QPushButton("Deallocate")
        self.deallocate_btn.clicked.connect(self.deallocate_memory)
        process_layout.addWidget(QLabel("Process Size:"))
        process_layout.addWidget(self.process_size_input)
        process_layout.addWidget(self.allocate_btn)
        process_layout.addWidget(self.deallocate_btn)
        process_group.setLayout(process_layout)

        # Initialize Button
        init_btn = QPushButton("Initialize Memory")
        init_btn.clicked.connect(self.initialize_memory)

        # Memory Visualization
        self.memory_canvas = QLabel()
        self.memory_canvas.setMinimumHeight(200)
        self.memory_canvas.setStyleSheet("background-color: #f0f0f0; border: 1px solid #ccc;")

        # Fragmentation Info
        self.fragmentation_label = QLabel("Fragmentation: None")
        self.fragmentation_label.setStyleSheet("font-weight: bold;")

        # Process Table
        self.process_table = QTableWidget()
        self.process_table.setColumnCount(4)
        self.process_table.setHorizontalHeaderLabels(["Process", "Size", "Location", "Action"])
        self.process_table.verticalHeader().setVisible(False)

        # Add widgets to main layout
        layout.addWidget(config_group)
        config_group.setLayout(config_layout)
        layout.addWidget(init_btn)
        layout.addWidget(process_group)
        layout.addWidget(self.memory_canvas)
        layout.addWidget(self.fragmentation_label)
        layout.addWidget(self.process_table)
        self.setLayout(layout)

    def change_partition_type(self, text):
        self.partition_type = text
        if text == "Fixed":
            self.fixed_partitions_group.show()
        else:
            self.fixed_partitions_group.hide()

    def initialize_memory(self):
        try:
            self.total_memory = int(self.memory_input.text())
            
            if self.partition_type == "Variable":
                # Initialize as single free block
                self.memory = MemoryBlock(0, self.total_memory)
                self.log("Initialized variable partition memory")
            else:
                # Initialize fixed partitions
                sizes = [int(s.strip()) for s in self.partition_sizes_input.text().split(",")]
                if sum(sizes) > self.total_memory:
                    raise ValueError("Partitions exceed total memory")
                
                self.memory = None
                current = None
                start = 0
                for size in sizes:
                    block = MemoryBlock(start, size)
                    if self.memory is None:
                        self.memory = block
                        current = block
                    else:
                        current.next = block
                        current = block
                    start += size
                self.log(f"Initialized fixed partitions: {sizes}")
            
            self.update_visualization()
            self.update_fragmentation()
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Invalid memory configuration: {str(e)}")

    def allocate_memory(self):
        if not self.memory:
            QMessageBox.warning(self, "Error", "Memory not initialized!")
            return
            
        try:
            size = int(self.process_size_input.text())
            if size <= 0:
                raise ValueError("Size must be positive")
                
            process_id = f"P{len([b for b in self.get_blocks() if b.process]) + 1}"
            strategy = self.strategy_combo.currentText()
            
            if self.partition_type == "Variable":
                block = self.find_free_block_variable(size, strategy)
            else:
                block = self.find_free_block_fixed(size, strategy)
                
            if block:
                block.process = process_id
                remaining = block.size - size
                
                if remaining > 0 and self.partition_type == "Variable":
                    # Split the block
                    new_block = MemoryBlock(block.start + size, remaining)
                    new_block.next = block.next
                    block.next = new_block
                    block.size = size
                
                self.log(f"Allocated {size}KB to {process_id} using {strategy}")
                self.update_visualization()
                self.update_fragmentation()
                self.update_process_table()
            else:
                QMessageBox.warning(self, "Error", "No suitable block found for allocation!")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Allocation failed: {str(e)}")

    def find_free_block_variable(self, size, strategy):
        blocks = []
        current = self.memory
        while current:
            if current.process is None and current.size >= size:
                blocks.append(current)
            current = current.next
        
        if not blocks:
            return None
            
        if strategy == "First Fit":
            return next((b for b in blocks if b.size >= size), None)
        elif strategy == "Best Fit":
            return min((b for b in blocks if b.size >= size), key=lambda x: x.size, default=None)
        else:  # Worst Fit
            return max((b for b in blocks if b.size >= size), key=lambda x: x.size, default=None)

    def find_free_block_fixed(self, size, strategy):
        current = self.memory
        while current:
            if current.process is None and current.size >= size:
                return current
            current = current.next
        return None

    def deallocate_memory(self):
        if not self.memory:
            return
            
        selected = self.process_table.currentRow()
        if selected == -1:
            QMessageBox.warning(self, "Error", "No process selected!")
            return
            
        process_id = self.process_table.item(selected, 0).text()
        
        current = self.memory
        while current:
            if current.process == process_id:
                current.process = None
                self.log(f"Deallocated memory from {process_id}")
                
                if self.partition_type == "Variable":
                    self.coalesce_free_blocks()
                
                self.update_visualization()
                self.update_fragmentation()
                self.update_process_table()
                return
            current = current.next
        
        QMessageBox.warning(self, "Error", "Process not found in memory!")

    def coalesce_free_blocks(self):
        current = self.memory
        while current and current.next:
            if current.process is None and current.next.process is None:
                current.size += current.next.size
                current.next = current.next.next
            else:
                current = current.next

    def update_visualization(self):
        if not self.memory:
            return
            
        blocks = self.get_blocks()
        total_size = sum(b.size for b in blocks)
        scale = 500 / total_size
        
        pixmap = QPixmap(520, 100)
        pixmap.fill(Qt.white)
        painter = QPainter(pixmap)
        
        x = 10
        for block in blocks:
            width = max(10, int(block.size * scale))
            color = QColor(100, 200, 100) if block.process else QColor(200, 100, 100)
            painter.setBrush(color)
            painter.drawRect(x, 10, width, 80)
            
            text = f"{block.process or 'Free'}\n{block.size}KB"
            painter.drawText(x, 50, width, 40, Qt.AlignCenter, text)
            x += width + 2
        
        painter.end()
        self.memory_canvas.setPixmap(pixmap)

    def update_fragmentation(self):
        if not self.memory:
            return
            
        blocks = self.get_blocks()
        allocated = [b for b in blocks if b.process]
        free_blocks = [b for b in blocks if not b.process]
        
        if not free_blocks:
            self.fragmentation_label.setText("Fragmentation: None")
            return
            
        total_free = sum(b.size for b in free_blocks)
        max_free = max(b.size for b in free_blocks)
        
        if self.partition_type == "Variable":
            external_frag = total_free - max_free
            internal_frag = sum(b.size - b.process.size for b in allocated if hasattr(b.process, 'size'))
            self.fragmentation_label.setText(
                f"Fragmentation: External={external_frag}KB, Internal={internal_frag}KB"
            )
        else:
            internal_frag = sum(b.size - b.process.size for b in allocated if hasattr(b.process, 'size'))
            self.fragmentation_label.setText(
                f"Fragmentation: Internal={internal_frag}KB (Fixed partitions)"
            )

    def update_process_table(self):
        blocks = [b for b in self.get_blocks() if b.process]
        self.process_table.setRowCount(len(blocks))
        
        for row, block in enumerate(blocks):
            self.process_table.setItem(row, 0, QTableWidgetItem(block.process))
            self.process_table.setItem(row, 1, QTableWidgetItem(str(block.size)))
            self.process_table.setItem(row, 2, QTableWidgetItem(f"{block.start}-{block.start + block.size}"))
            
            btn = QPushButton("Deallocate")
            btn.clicked.connect(lambda _, r=row: self.deallocate_by_row(r))
            self.process_table.setCellWidget(row, 3, btn)

    def deallocate_by_row(self, row):
        self.process_table.selectRow(row)
        self.deallocate_memory()

    def get_blocks(self):
        blocks = []
        current = self.memory
        while current:
            blocks.append(current)
            current = current.next
        return blocks

    def log(self, message):
        print(f"[Memory] {message}")


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Operating System Project")
        self.setGeometry(100, 100, 1000, 800)
        
        self.tabs = QTabWidget()
        self.scheduling_tab = SchedulingTab()
        self.deadlock_tab = DeadlockTab()
        self.sync_tab = ProcessSyncTab() 
        self.memory_tab = MemoryManagerTab()

        self.tabs.addTab(self.scheduling_tab, "Process Scheduling")
        self.tabs.addTab(self.deadlock_tab, "Deadlock Detection")
        self.tabs.addTab(self.sync_tab, "Process Sync")  
        self.tabs.addTab(self.memory_tab, "Memory Manager")
        self.setCentralWidget(self.tabs)
        


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()