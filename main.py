import os
import sys
import re
import json
import creds
import shutil
import requests
import subprocess
import numpy as np
import pandas as pd
from PyQt5 import QtGui
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from graphviz import Source
from datetime import datetime
from PyQt5.QtWidgets import *
from bs4 import BeautifulSoup
from termcolor import colored
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from pyvis.network import Network
from matplotlib import image as mpimg
from PyQt5.QtWebEngineWidgets import *
from PyQt5.QtWidgets import QFileDialog
from PyQt5.QtNetwork import QHostAddress
from sklearn.impute import SimpleImputer
from sklearn.ensemble import IsolationForest
from PyQt5.QtWebSockets import QWebSocketServer


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Spyder")
        self.setGeometry(100, 100, 1350, 800)
        icon = QIcon(r"Icons\app.png")
        self.setWindowIcon(icon)
        
        toolbar = QToolBar()
        self.addToolBar(toolbar)
        
        self.setStyleSheet("""
            QMainWindow {
                background-color: white;
            }
            QSplitter::handle {
                background-color: white;
            }
            QScrollBar:vertical {
                background-color: #F0F0F0;
                width: 12px; 
            }
            QScrollBar::handle:vertical {
                background-color: #CCCCCC;
                border-radius: 6px;
            }
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {
                background-color: #F0F0F0;
            }
            QScrollBar:horizontal {
                background-color: #F0F0F0;
                height: 12px;
            }
            QScrollBar::handle:horizontal {
                background-color: #CCCCCC;
                border-radius: 6px;
            }
            QScrollBar::add-line:horizontal,
            QScrollBar::sub-line:horizontal {
                background-color: #F0F0F0;
            }

        """)

        menu_bar = self.menuBar()
        file_menu = QMenu("File", self)
        menu_bar.addMenu(file_menu)

        self.save_action = QAction("&Save Project", self)
        self.save_action.triggered.connect(self.SaveProject)
        file_menu.addAction(self.save_action)
        self.save_action.setEnabled(False)

        load_action = QAction("&Load Project", self)
        load_action.triggered.connect(self.LoadProject)
        file_menu.addAction(load_action)

        help_menu = QMenu("About", self)
        menu_bar.addMenu(help_menu)

        ver_action = QAction("&Version", self)
        help_menu.addAction(ver_action)
        ver_action.triggered.connect(self.applicationInfo)
        

        button1 = QAction(QIcon(r"Icons\search.png"), "Search Wallet Address", self)
        button1.triggered.connect(self.search_address_popup)
        
        self.button2 = QAction(QIcon(r"Icons\timeline.png"), "Timeline Graph", self)
        self.button2.triggered.connect(lambda: self.get_transactions(self.current_tab, 'Timeline'))

        self.button3 = QAction(QIcon(r"Icons\profile.png"), "Search Profile", self)
        self.button3.triggered.connect(self.show_ProfileWindow)

        self.button4 = QAction(QIcon(r"Icons\crosshair.png"), "Crosshair", self)
        self.button4.triggered.connect(self.flag_suspicious_activity)

        self.button5 = QAction(QIcon(r"Icons\Transaction.png"), "Find Transaction", self)
        self.button5.triggered.connect(self.show_TransactionWindow)

        self.button6 = QAction(QIcon(r"Icons\filter.png"), "Filter Information", self)
        self.button6.triggered.connect(self.Filter)

        self.SaveButton = QAction(QIcon(r"Icons\save.png"), "Save", self)
        self.SaveButton.triggered.connect(self.SaveProject)

        self.LoadButton = QAction(QIcon(r"Icons\load.png"), "Load", self)
        self.LoadButton.triggered.connect(self.LoadProject)
        
        

        self.button2.setEnabled(False)
        self.button3.setEnabled(True)
        self.button4.setEnabled(False)
        self.button6.setEnabled(False)
        self.SaveButton.setEnabled(False)

        toolbar.addAction(button1)
        toolbar.addAction(self.SaveButton)
        toolbar.addAction(self.LoadButton)
        toolbar.addAction(self.button3)
        toolbar.addAction(self.button5)
        toolbar.addAction(self.button2)
        toolbar.addAction(self.button4)
        toolbar.addAction(self.button6)
        
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search")
        self.search_bar.setMaximumWidth(300)
        
        self.search_bar.textChanged.connect(lambda text: self.Search(text, self.tab_widget.currentIndex()))

        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        toolbar.addWidget(spacer)

        toolbar.addWidget(self.search_bar)
        
        static_spacer = QWidget()
        static_spacer.setFixedSize(10, 0)

        toolbar.addWidget(static_spacer)

        splitter = QSplitter(Qt.Horizontal)

        self.web_widget = QWebEngineView()
        self.web_widget.setMinimumSize(800, 300)
        self.web_widget.setStyleSheet("background-color: white;")
        self.web_widget.setFocusPolicy(Qt.NoFocus)

        self.tab_widget = QTabWidget()
        self.tab_widget.setMaximumHeight(800)
        self.tab_widget.setTabEnabled(0, False)
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.tabCloseRequested.connect(lambda index: self.remove_tab(index, self.tab_widget.tabText(index)))
        self.tabs = []
        self.tab_widget.currentChanged.connect(self.current_tab_name)

        self.text_widget = QTextEdit()
        self.text_widget.setMaximumHeight(100)
        self.text_widget.setMaximumWidth(750)

        table_text_widget = QWidget()
        table_text_widget.setMaximumWidth(750)
        table_text_layout = QVBoxLayout()
        table_text_layout.addWidget(self.tab_widget)
        table_text_layout.addWidget(self.text_widget)
        table_text_widget.setLayout(table_text_layout)
        
        splitter.addWidget(self.web_widget)
        splitter.addWidget(table_text_widget)

        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 1)

        self.setCentralWidget(splitter)
        
        self.Visited = []
        self.filter_values = {}
        self.unique_values = {}
        self.contracts = []
        self.Parents = []
        self.createContextMenu()

    def remove_tab(self, tab_index, tab):
        print(tab)
        print(self.Visited)
        self.Visited.remove(tab)
        if not self.Visited:
            self.web_widget.setHtml("")
        else:
            self.get_transactions(self.Visited[0])
        self.tab_widget.removeTab(tab_index)

    def Search(self, search_text, tab_index):
        filtered_nodes = []
        if search_text != '':
            for index in range(self.tab_widget.count()):
                tab_widget = self.tab_widget.widget(index)
                if isinstance(tab_widget, QTableWidget):
                    table_widget = tab_widget
                    column_names = [table_widget.horizontalHeaderItem(column).text().lower() for column in range(table_widget.columnCount())]
                    from_column_index = column_names.index('from')
                    to_column_index = column_names.index('to')
                    date_column_index = column_names.index('date')
                    time_column_index = column_names.index('time')
                    value_column_index = column_names.index('value (eth)')
                    for row in range(table_widget.rowCount()):
                        visible = False
                        from_item = table_widget.item(row, from_column_index)
                        to_item = table_widget.item(row, to_column_index)
                        date_item = table_widget.item(row, date_column_index)
                        time_item = table_widget.item(row, time_column_index)
                        value_item = table_widget.item(row, value_column_index)
                        
                        if from_item is not None and search_text.lower() in from_item.text().lower():
                            visible = True
                            filtered_nodes.append(from_item.text())
                            filtered_nodes.append(to_item.text())
                        elif to_item is not None and search_text.lower() in to_item.text().lower():
                            visible = True
                            filtered_nodes.append(from_item.text())
                            filtered_nodes.append(to_item.text())
                        elif date_item is not None and search_text in date_item.text():
                            visible = True
                            filtered_nodes.append(from_item.text())
                            filtered_nodes.append(to_item.text())
                        elif time_item is not None and search_text in time_item.text():
                            visible = True
                            filtered_nodes.append(from_item.text())
                            filtered_nodes.append(to_item.text())
                        elif value_item is not None and search_text in value_item.text():
                            visible = True
                            filtered_nodes.append(from_item.text())
                            filtered_nodes.append(to_item.text())
                        
                        table_widget.setRowHidden(row, not visible)
                else:
                    print("Invalid tab widget type")

            self.create_graph(self.transactions, set(filtered_nodes))

        else:
            for index in range(self.tab_widget.count()):
                tab_widget = self.tab_widget.widget(index)
                if isinstance(tab_widget, QTableWidget):
                    table_widget = tab_widget
                    for row in range(table_widget.rowCount()):
                        table_widget.setRowHidden(row, False)

            self.create_graph(self.transactions, None)


    
    def current_tab_name(self, index):
        self.current_tab = self.tab_widget.tabText(index)

    def pan_zoom_handler(self, ax):
        press = None
        x0 = None
        y0 = None

        def connect():
            nonlocal press, x0, y0
            cidpress = ax.figure.canvas.mpl_connect('button_press_event', on_press)
            cidrelease = ax.figure.canvas.mpl_connect('button_release_event', on_release)
            cidmotion = ax.figure.canvas.mpl_connect('motion_notify_event', on_motion)
            cidscroll = ax.figure.canvas.mpl_connect('scroll_event', on_scroll)

        def on_press(event):
            nonlocal press, x0, y0
            if event.button == 1:
                press = event.x, event.y
                x0 = ax.get_xlim()
                y0 = ax.get_ylim()

        def on_release(event):
            nonlocal press
            if event.button == 1:
                press = None

        def on_motion(event):
            nonlocal press
            if press is None:
                return
            if event.button != 1:
                return

            dx = event.x - press[0]
            dy = event.y - press[1]
            scale_x = (x0[1] - x0[0]) / ax.bbox.width
            scale_y = (y0[1] - y0[0]) / ax.bbox.height
            ax.set_xlim(x0[0] - dx * scale_x, x0[1] - dx * scale_x)
            ax.set_ylim(y0[0] - dy * scale_y, y0[1] - dy * scale_y)
            ax.figure.canvas.draw_idle()

        def on_scroll(event):
            if event.button == 'up':
                _zoom(0.9)
            elif event.button == 'down':
                _zoom(1.1)

        def _zoom(zoom_factor):
            nonlocal x0, y0
            x_center = np.mean(ax.get_xlim())
            y_center = np.mean(ax.get_ylim())

            ax.set_xlim(x_center - (x_center - ax.get_xlim()[0]) * zoom_factor,
                        x_center + (ax.get_xlim()[1] - x_center) * zoom_factor)
            ax.set_ylim(y_center - (y_center - ax.get_ylim()[0]) * zoom_factor,
                        y_center + (ax.get_ylim()[1] - y_center) * zoom_factor)
            ax.figure.canvas.draw_idle()

        connect()   
    
    def create_timeline(self, transactions, address):
        dates = [datetime.fromtimestamp(int(tx['timeStamp'])) for tx in transactions]
        dates_sorted = sorted(dates)
        
        levels = np.tile([-0.6, 0.6, -0.4, 0.4, -0.2, 0.2],
                        int(np.ceil(len(dates_sorted) / 6)))[:len(dates_sorted)]

        
        fig, ax = plt.subplots(figsize=(14, 6), constrained_layout=True)

        ax.vlines(dates_sorted, 0, levels, color="k")
        ax.plot(dates_sorted, np.zeros_like(dates_sorted), "-o",
                color="k", markerfacecolor="w")

        for d, l, tx in zip(dates, levels, transactions):
            amount = float(tx['value']) / 10 ** 18
            timestamp = int(tx['timeStamp'])

            date = datetime.fromtimestamp(timestamp)

            formatted_date = date.strftime("%d/%m/%y")
            formatted_time = date.strftime("%I:%M %p")

            annotation = None
            if tx['from'].lower() == address.lower():
                annotation = f"(Sent)\nAmount: {amount:.2f} ETH\nDate: {formatted_date}\nTime: {formatted_time}"
            else:
                annotation = f"(Received)\nAmount: {amount:.2f} ETH\nDate: {formatted_date}\nTime: {formatted_time}"

            bbox_props = dict(boxstyle="round", fc="w", ec="gray", lw=0.5)
            ax.annotate(annotation, xy=(d, l),
                        xytext=(-3, np.sign(l) * 2), textcoords="offset points",
                        fontsize=7,
                        ha='center',
                        va='top',
                        bbox=bbox_props)

        ax.xaxis.set_major_locator(mdates.DayLocator())
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%d %b '%y"))
        plt.setp(ax.get_xticklabels(), rotation=90, ha="right", fontsize=8)

        ax.yaxis.set_visible(False)
        ax.spines[["left", "top", "right"]].set_visible(False)

        num_values_to_show = 7
        if len(dates_sorted) >= num_values_to_show:
            ax.set_xlim(dates_sorted[0], dates_sorted[num_values_to_show - 1])
        else:
            ax.set_xlim(dates_sorted[0], dates_sorted[-1])

        self.pan_zoom_handler(ax)
        plt.gcf().canvas.setWindowTitle("Timeline For" + address)
        plt.show()
    
    def SaveProject(self):
        folder_path = QFileDialog.getExistingDirectory(self, "Select Directory")
        if folder_path:
            now = datetime.now()
            folder_name = now.strftime("%Y-%m-%d_%H-%M-%S")
            folder_path = os.path.join(folder_path, folder_name)
            os.makedirs(folder_path)

            for tab_index in range(self.tab_widget.count()):
                table_widget = self.tab_widget.widget(tab_index)
                df = pd.DataFrame(columns=[table_widget.horizontalHeaderItem(col).text() for col in range(table_widget.columnCount())])
                table_name = self.tab_widget.tabText(tab_index)
                for row in range(table_widget.rowCount()):
                    row_data = []
                    for col in range(table_widget.columnCount()):
                        item = table_widget.item(row, col)
                        if item is not None:
                            row_data.append(item.text())
                        else:
                            row_data.append('')
                    df.loc[len(df)] = row_data

                file_name = f"{table_name}.xlsx"
                file_path = os.path.join(folder_path, file_name)
                df.to_excel(file_path, index=False)

            graph_file_name = "graph.html"
            graph_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), graph_file_name)
            shutil.copy(graph_file_path, folder_path)

            icons_folder_name = "Icons"
            icons_folder_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), icons_folder_name)
            shutil.copytree(icons_folder_path, os.path.join(folder_path, icons_folder_name))

            QMessageBox.information(self, "Save", "Project saved successfully.")

    
    def LoadProject(self):
        folder_path = QFileDialog.getExistingDirectory(self, "Select Directory")
        if folder_path:
            self.tab_widget.clear()
            
            graph_file_name = "graph.html"
            graph_file_path = os.path.join(folder_path, graph_file_name)
            main_directory = os.path.dirname(os.path.abspath(__file__))
            main_graph_file_path = os.path.join(main_directory, graph_file_name)
            shutil.copy(graph_file_path, main_graph_file_path)

            self.web_widget.load(QUrl.fromLocalFile(main_graph_file_path))
            
            excel_files = [file for file in os.listdir(folder_path) if file.endswith(".xlsx")]
            for excel_file in excel_files:
                file_path = os.path.join(folder_path, excel_file)
                table_name = os.path.splitext(excel_file)[0]
                df = pd.read_excel(file_path)
                self.get_transactions(table_name, 'Load')

                table_widget = QTableWidget()
                table_widget.setMinimumSize(500, 500)
                table_widget.setMaximumWidth(750)
                table_widget.setEditTriggers(QAbstractItemView.NoEditTriggers)
                table_widget.cellClicked.connect(self.RowSelection)

                table_widget.setSelectionBehavior(QAbstractItemView.SelectRows)
                table_widget.setSelectionMode(QAbstractItemView.ExtendedSelection)
                
                table_widget.setColumnCount(df.shape[1])
                table_widget.setRowCount(df.shape[0])
                table_widget.setHorizontalHeaderLabels(df.columns)

                for row in range(df.shape[0]):
                    for col in range(df.shape[1]):
                        item = QTableWidgetItem(str(df.iloc[row, col]))
                        table_widget.setItem(row, col, item)

                        header = table_widget.horizontalHeaderItem(col).text()
                        value = item.text()
                        if header not in self.unique_values:
                            self.unique_values[header] = set()
                        self.unique_values[header].add(value)

                self.tab_widget.addTab(table_widget, table_name)
            self.enable_buttons()
            QMessageBox.information(self, "Load", "Project loaded successfully.")



    def Filter(self):
        dialog = QDialog(self)
        layout = QFormLayout()

        for key, values in self.unique_values.items():
            if key == 'Time':
                start_label = QLabel('Start ' + key)
                end_label = QLabel('End ' + key)
                start_time_layout = QHBoxLayout()
                end_time_layout = QHBoxLayout()

                start_time = QComboBox()
                start_time.addItems(['All'] + [str(i) for i in range(1, 13)])
                start_time.setCurrentIndex(self.filter_values.get(key, 0))
                start_time_layout.addWidget(start_time)

                end_time = QComboBox()
                end_time.addItems(['All'] + [str(i) for i in range(1, 13)])
                end_time.setCurrentIndex(self.filter_values.get(key + '_end', 0))
                end_time_layout.addWidget(end_time)

                start_am_pm = QComboBox()
                start_am_pm.addItems(['AM', 'PM'])
                
                end_am_pm = QComboBox()
                end_am_pm.addItems(['AM', 'PM'])
                
                start_time_layout.addWidget(start_am_pm)
                end_time_layout.addWidget(end_am_pm)

                layout.addRow(start_label, start_time_layout)
                layout.addRow(end_label, end_time_layout)

                # start_time.currentIndexChanged.connect(lambda value, key=key: self.filter_values.update({key: value}))
                # end_time.currentIndexChanged.connect(lambda value, key=key + '_end': self.filter_values.update({key: value}))
                # am_pm.currentIndexChanged.connect(lambda value, key=key + '_am_pm': self.filter_values.update({key: value}))

            elif key == 'Date':
                date_layout = QHBoxLayout()
                label = QLabel(key)
                
                start_date = QComboBox()
                start_date.addItems(['All'] + list(values))
                start_date.setCurrentIndex(self.filter_values.get(key, 0))
                
                end_date = QComboBox()
                end_date.addItems(['All'] + list(values))
                end_date.setCurrentIndex(self.filter_values.get(key, 0))
                
                date_layout.addWidget(start_date)
                date_layout.addWidget(end_date)
                
                layout.addRow(label, date_layout)
            
            else:
                label = QLabel(key)
                combo_box = QComboBox()
                combo_box.addItems(['All'] + list(values))
                combo_box.setCurrentIndex(self.filter_values.get(key, 0))
                layout.addRow(label, combo_box)

        button_layout = QHBoxLayout()
        FilterButton = QPushButton("Filter")
        ClearButton = QPushButton("Clear All")
        button_layout.addWidget(FilterButton)
        button_layout.addWidget(ClearButton)

        layout.addRow(button_layout)

        dialog.setLayout(layout)
        dialog.setWindowTitle("Filter")
        dialog.show()


    
    def applicationInfo(self):
        dialog = QDialog(self)
        dialog.setStyleSheet("background-color: white;")
        dialog.setWindowTitle("Spyder")
        dialog.setWindowIcon(QIcon(r"Icons\app.png"))
        dialog.setFixedSize(500, 200)
        layout = QVBoxLayout(dialog)
        horizontal_layout = QHBoxLayout()
        image_label = QLabel()
        pixmap = QPixmap(r"Icons\appVersion.png")
        resized_pixmap = pixmap.scaled(280, 300)
        image_label.setPixmap(resized_pixmap)
        horizontal_layout.addWidget(image_label)
        text_label = QLabel("Spyder® 0.1\nBlockChain Forensics & Visualization Tool\nHuthaifa Mohammad")
        horizontal_layout.addWidget(text_label)
        layout.addLayout(horizontal_layout)
        dialog.show()
        
    def createContextMenu(self):
        self.tab_widget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tab_widget.customContextMenuRequested.connect(self.showContextMenu)

    def showContextMenu(self, pos):
        menu = QMenu(self)
        analyze_transaction = menu.addAction("Analyze Transaction")
        analyze_transaction.triggered.connect(self.AnalyzeTransaction)
        remove = menu.addAction("Remove trasaction(s) from scope")

        current_tab_index = self.tab_widget.currentIndex()
        table_widget = self.tab_widget.widget(current_tab_index)
        selection_model = table_widget.selectionModel()

        selected_rows = [index.row() for index in selection_model.selectedRows()]
        
        for row in selected_rows:
            column = 5
            item = table_widget.item(row, column)
            if item is not None:
                text = item.text()
                if text:
                    self.hash = text


        menu.exec_(self.tab_widget.mapToGlobal(pos))

    def AnalyzeTransaction(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Transaction Analysis Window")
        dialog.setWindowIcon(QIcon(r"Icons\app.png"))
        dialog.setFixedSize(400, 550)
        
        
        selected_transaction = None
        for transaction in self.transactions:
            if transaction['hash'] == self.hash:
                selected_transaction = transaction
                break
        to = None
        fromtext = None
        if selected_transaction is not None:
            layout = QFormLayout()
            for key, value in selected_transaction.items():
                if key == "from":
                    label = QLabel(key + ':')
                    text = QLineEdit()
                    text.setMaximumWidth(253)
                    text.setReadOnly(True)
                    text.setText(value)
                    button1 = QPushButton()
                    button1.setIcon(QIcon(r"Icons\analyze.png"))
                    button1.setMaximumWidth(30)
                    button1.setEnabled(True)
                    button1.setToolTip('Generate Profile Report')
                    fromtext = text.text()
                    
                    hbox = QHBoxLayout()
                    hbox.addWidget(label)
                    hbox.addWidget(text)
                    hbox.addWidget(button1)

                    layout.addRow(hbox)

                elif key == "to":
                    label = QLabel(key + ':')
                    text = QLineEdit()
                    text.setMaximumWidth(253)
                    text.setReadOnly(True)
                    text.setText(value)
                    button2 = QPushButton()
                    button2.setIcon(QIcon(r"Icons\analyze.png"))
                    button2.setMaximumWidth(30)
                    button2.setEnabled(True)
                    button2.setToolTip('Generate Profile Report')
                    to = text.text()
                    
                    hbox = QHBoxLayout()
                    hbox.addWidget(label)
                    hbox.addWidget(text)
                    hbox.addWidget(button2)

                    layout.addRow(hbox)

                elif key == "transactionIndex":
                    label = QLabel("Index:")
                    text = QLineEdit()
                    text.setMaximumWidth(300)
                    text.setReadOnly(True)
                    text.setText(value)
                    layout.addRow(label, text)
                
                elif key == "cumulativeGasUsed":
                    label = QLabel("cGasUsed:")
                    text = QLineEdit()
                    text.setMaximumWidth(300)
                    text.setReadOnly(True)
                    text.setText(value)
                    layout.addRow(label, text)
                
                else:
                    label = QLabel(key + ':')
                    text = QLineEdit()
                    text.setMaximumWidth(300)
                    text.setReadOnly(True)
                    text.setText(value)
                    layout.addRow(label, text)
            dialog.setLayout(layout)
        
        button1.clicked.connect(lambda: self.GenerateReport(fromtext))
        button2.clicked.connect(lambda: self.GenerateReport(to))
        dialog.show()
        

    def SearchAddress(self, address, action):
        Ethplorer_API = creds.Ethplorer_API
        if action == 'Website':
            url = f'https://api.ethplorer.io/getTokenInfo/{address}?apiKey={Ethplorer_API}'
        elif action == 'Account':
            url = f'https://api.ethplorer.io/getAddressInfo/{address}?apiKey={Ethplorer_API}&showETHTotals=true&showTxsCount=true'
        elif action == 'Type':
            Etherscan_API = creds.Etherscan_API
            url = f'https://api.etherscan.io/api?module=contract&action=getcontractcreation&contractaddresses={address}&apikey={Etherscan_API}'
        elif action == 'Transactions':
            Etherscan_API = creds.Etherscan_API
            url = f'https://api.etherscan.io/api?module=account&action=txlist&address={address}&apikey={Etherscan_API}'
        elif action == 'Contracts':
            Etherscan_API = creds.Etherscan_API
            url = f'https://api.etherscan.io/api?module=account&action=txlistinternal&address={address}&startblock=0&endblock=99999999&page=1&offset=1000&sort=asc&apikey={Etherscan_API}'
        try:
            response = requests.get(url)
            data = response.json()
            return data
        except requests.exceptions.RequestException as e:
            print(f"Error occurred: {e}")

    def GetAccountActivity(self, data):
        if 'error' not in data:
            AddressActivity = {}
            Balances = {}

            AddressActivity['Total In'] = "{:f}".format(data['ETH']['totalIn'])
            AddressActivity['Total Out'] = "{:f}".format(data['ETH']['totalOut'])
            AddressActivity['Transactions'] = data['countTxs']
            Balances['ETH'] = {"balance": "{:f}".format(data['ETH']['balance']) + ' ETH'}
            
            if 'tokens' in data:
                for token in data['tokens']:
                    if 'name' in token['tokenInfo']:
                        token_name = token['tokenInfo']['name']
                        Balances[token_name] = {"balance": "{:f}".format(token['balance']) + ' ' + token['tokenInfo']['symbol']}
                        if 'image' in token['tokenInfo']:
                            Balances[token_name]['image'] = token['tokenInfo']['image']

            return AddressActivity, Balances
        
        else:
            
            return None

    def CheckType(self, data):
        if data['status'] == '1':
            wallet_type = 'Contract'
            return wallet_type
        else:
            wallet_type = 'Address'
            return wallet_type
    
    def GetName(self, data):
        if 'error' not in data:
            wallet_tag = data['name']
            return wallet_tag
        else:
            wallet_tag = ''
            return wallet_tag

    def GetCreator(self, data):
        if data['status'] == '1':
            result = data['result'][0]
            ContractCreator = result['contractCreator']
            return ContractCreator
        else:
            ContractCreator = ''
            return ContractCreator

    def GetWebsite(self, data):
        if 'website' in data:
            website = data['website']
            return website
        else:
            website = ''
            return website
    
    def analyzeProfile(self, address):
        self.GenerateReport(address)

    def scrape_wallet_tag(self, address):
        url = 'https://etherscan.io/address/' + address
        headers = {
            'Cookie': 'ASP.NET_SessionId=eosrt10a1bqudqgn1wdwsoqd; amp_fef1e8=a7e3b843-0b2f-4bf2-8d8f-bdc1fd42a17eR...1h37mraqn.1h37mraqr.3.2.5; __cuid=2c82c9af5ffc4323ab5db8acc49db778; __cflb=02DiuFnsSsHWYH8WqVXaqGvd6BSBaXQLTLDHf853rGYoN; __cf_bm=wHTcLBtrA85t2pyAQiUdcuFdCUPq.6nhqVCIpE7wbDQ-1687112319-0-AePicdKEFAxg7XXqMIOSVC0kcg7LxqtHo0Hbg9go/75bCmOp5QMZd3uyZOkx2ulAYw==',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/114.0',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Referer': 'https://etherscan.io/tx/0xeaf5423392c70d58e0bee7d93c0e972a7118fe17872279fb54306cee5d7ad30d',
            'Dnt': '1',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-User': '?1',
            'Sec-Gpc': '1',
            'Te': 'trailers',
            'Connection': 'close'
        }

        max_retries = 20
        retry_count = 0

        while retry_count < max_retries:
            try:
                response = requests.get(url, headers=headers)
                content = response.text
                soup = BeautifulSoup(response.content, 'html.parser')
            
                title_tag = soup.title
                if title_tag:
                    title = title_tag.string
                    title_parts = title.split('|')  
                    if len(title_parts) > 2:
                        
                        alert_type = ['danger', 'dark', 'warning']
                        for alert in alert_type:
                            alert_code = "<div class='alert alert-{} alert-dismissible fade show mb-3' role='alert'>".format(alert)
                            if alert_code in content:
                                lines = [line for line in content.split('\n') if alert_code in line]
                                for line in lines:
                                    start_index = line.find(alert_code) + len(alert_code)
                                    end_index = line.find("<button")
                                    self.Tooltip = line[start_index:end_index]
                                wallet_owner = title_parts[0].strip() + ' (Suspicious)'
                                return wallet_owner
                        
                        else:
                            wallet_owner = title_parts[0].strip()
                            return wallet_owner

                break

            except requests.exceptions.RequestException as e:
                retry_count += 1
        else:
            print("Failed to establish a connection.")
    
    def GenerateReport(self, address):
        self.Tooltip = None
        report = QDialog(self)
        report.setWindowTitle(address)
        
        report.setMaximumHeight(900)
        report.setMinimumWidth(800)
        report.setMaximumWidth(800)
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        widget = QWidget()
        layout = QFormLayout(widget)
        scroll_area.setWidget(widget)

        wallet_tag = self.scrape_wallet_tag(address)
        if wallet_tag != '' and wallet_tag is not None:
            WalletOwnerLabel = QLabel(wallet_tag)
            hbox = QHBoxLayout()
            verified = QPushButton()
            if 'Suspicious' in wallet_tag:
                verified.setIcon(QIcon(r"Icons\caution.png"))
                if self.Tooltip is not None:
                    verified.setToolTip(self.Tooltip)
                else:
                    verified.setToolTip('Suspicious')
            else:
                verified.setIcon(QIcon(r"Icons\verified.png"))
                verified.setToolTip('Verified')
            verified.setMaximumWidth(30)
            verified.setEnabled(True)
            verified.setStyleSheet("color: white; background-color: transparent; border: none;")
            hbox.addWidget(WalletOwnerLabel)
            hbox.addWidget(verified)
            hbox.setSpacing(0)
            hbox.addStretch()
            layout.addRow(hbox)

        Website = self.SearchAddress(address, 'Website')
        contract_website = self.GetWebsite(Website)
        if contract_website != '' and contract_website is not None:
            websiteLabel = QLabel('Website:')
            websiteText = QLineEdit(contract_website)
            layout.addRow(websiteLabel, websiteText)

        self.verified_source_code = False
        source_code = self.SourceCode(address)
        WalletType = self.SearchAddress(address, 'Type')
        wallet_type = self.CheckType(WalletType)
        TypeLabel = QLabel('Type:')
        TypeText = QLineEdit()
        TypeText.setText(str(wallet_type))

        if self.verified_source_code == True:
            hbox2 = QHBoxLayout()
            view_source = QPushButton()
            view_source.setIcon(QIcon(r"Icons\source.png"))
            view_source.setMaximumWidth(30)
            view_source.setEnabled(True)
            view_source.setToolTip('View Source Code')
            view_source.clicked.connect(lambda: self.SourceCodeWindow(source_code))
            TypeText.setMaximumWidth(241)
            hbox2.addWidget(TypeLabel)
            hbox2.addWidget(TypeText)
            hbox2.addWidget(view_source)
            layout.addRow(hbox2)
        else:
            layout.addRow(TypeLabel, TypeText)

        WalletAddressLabel = QLabel('Address:')
        WalletAddressText = QLineEdit()
        WalletAddressText.setText(address)
        layout.addRow(WalletAddressLabel, WalletAddressText)

        contract_creator = self.GetCreator(WalletType)
        if contract_creator != '' and contract_creator is not None:
            hbox3 = QHBoxLayout()
            AnalyzeProfile = QPushButton()
            AnalyzeProfile.setIcon(QIcon(r"Icons\analyze.png"))
            AnalyzeProfile.setMaximumWidth(30)
            AnalyzeProfile.setEnabled(True)
            AnalyzeProfile.setToolTip('Generate Profile Report')
            AnalyzeProfile.clicked.connect(lambda: self.analyzeProfile(ContractCreatorText.text()))
            ContractCreatorLabel = QLabel('Creator:')
            ContractCreatorText = QLineEdit()
            ContractCreatorText.setText(contract_creator)
            ContractCreatorText.setMaximumWidth(241)
            hbox3.addWidget(ContractCreatorLabel)
            hbox3.addWidget(ContractCreatorText)
            hbox3.addWidget(AnalyzeProfile)
            layout.addRow(hbox3)
        
        AccountData = self.SearchAddress(address, 'Account')
        AccountActivity, Balances = self.GetAccountActivity(AccountData)
        
        for key, value in AccountActivity.items():
            Label = QLabel(key + ':')
            Text = QLineEdit(str(value))
            layout.addRow(Label, Text)
        
        balances_scroll_area = QScrollArea()
        balances_scroll_area.setWidgetResizable(True)
        balances_widget = QWidget()
        balances_layout = QFormLayout(balances_widget)
        balances_scroll_area.setWidget(balances_widget)
        
        for key, value in Balances.items():
            Label = QLabel(key + ':')
            Label.setMaximumWidth(100)
            Text = QLineEdit(str(value['balance']))
            balances_layout.addRow(Label, Text)



        profile_groupbox = QGroupBox("Profile")
        profile_layout = QVBoxLayout()
        profile_layout.addWidget(widget)
        profile_groupbox.setLayout(profile_layout)

        balances_groupbox = QGroupBox("Balances")
        balances_groupbox_layout = QVBoxLayout()
        balances_groupbox_layout.addWidget(balances_scroll_area)
        balances_groupbox.setLayout(balances_groupbox_layout)

        main_layout = QHBoxLayout(report)
        main_layout.addWidget(profile_groupbox)
        main_layout.addWidget(balances_groupbox)

        report.setLayout(main_layout)
        report.show()

    def GenerateGraph(self):
        if os.path.isfile('inheritance') is True:
            os.remove('inheritance')
        os.system("slither contract.sol --print inheritance-graph")
        graph_path = os.path.join(os.getcwd(), 'contract.sol.inheritance-graph.dot')
        Graph = Source.from_file(graph_path)
        Graph.render('Inheritance', format='jpg', view=True)
        
        
    def SourceCodeWindow(self, code):
        self.SourceCodeExplorer = QMainWindow(self)
        self.SourceCodeExplorer.setWindowTitle('Source Code Analysis')
        self.SourceCodeExplorer.setFixedSize(900, 800)
        flags, strings = self.analyze_contract_source_code(code)
        layout = QVBoxLayout()
        toolbar = QToolBar()
        relationship_graph_action = QAction(QIcon(r"Icons\relationship.png"), "Load", self)
        relationship_graph_action.triggered.connect(self.GenerateGraph)
        toolbar.addAction(relationship_graph_action)
        self.SourceCodeExplorer.addToolBar(toolbar)
        
        text_edit = QTextEdit()
        text_edit.setStyleSheet("font-family: Cascadia Mono; font-size: 8pt;")
        palette = text_edit.palette()
        palette.setColor(QPalette.Text, QColor("white"))
        palette.setColor(QPalette.Base, QColor("black"))
        text_edit.setPalette(palette)
        text_edit.setPlainText(code)
        text_edit.setReadOnly(True)

        layout.addWidget(text_edit)

        self.highlight_suspicious_lines(text_edit, strings)

        flag_text = QTextEdit()
        flag_text.setMaximumHeight(200)
        flag_text.setReadOnly(True)
        flag_text.setStyleSheet("font-family: Cascadia Mono; font-size: 8pt;")
        palette = flag_text.palette()
        palette.setColor(QPalette.Text, QColor("red"))
        palette.setColor(QPalette.Base, QColor("black"))
        flag_text.setPalette(palette)

        flags_with_symbol = [f"{flag}\n" for flag in flags]
        flag_text.setPlainText("\n".join(flags_with_symbol))

        layout.addWidget(flag_text)

        central_widget = QWidget(self.SourceCodeExplorer)
        central_widget.setLayout(layout)
        self.SourceCodeExplorer.setCentralWidget(central_widget)
        self.SourceCodeExplorer.show()

    def highlight_suspicious_lines(self, text_edit, strings):
        format = QTextCharFormat()
        format.setBackground(QColor(226, 91, 116))

        for flag in strings:
            cursor = text_edit.document().find(flag)
            while not cursor.isNull():
                cursor.mergeCharFormat(format)
                cursor = text_edit.document().find(flag, cursor)
    
    def SourceCode(self, address):
        Etherscan_API = creds.Etherscan_API
        url = f'https://api.etherscan.io/api?module=contract&action=getsourcecode&address={address}&apikey={Etherscan_API}'

        try:
            response = requests.get(url)
            content = response.json()
            if 'SourceCode' in content['result'][0]:
                if content['result'][0]['SourceCode'] != 'Contract source code not verified' :
                    if content['result'][0]['SourceCode'] != '':
                        source_code = content['result'][0]['SourceCode']
                        formatted_code = '\n'.join(['    ' + line for line in source_code.split('\n')])
                        self.verified_source_code = True
                        
                        with open('contract.sol', 'w', encoding='utf-8') as file:
                            file.write(source_code)
                        
                        return formatted_code
            else:
                self.verified_source_code = False
                    
        except requests.exceptions.RequestException as e:
            print("API request error:", e)

    def analyze_contract_source_code(self, source_code):
        suspicious_flags = []
        strings_to_highlight = []
        contract_file = open('contract.sol', 'r', encoding='utf-8')
        content = contract_file.readlines()
        for line in content:
            if 'pragma solidity' in line:
                numbers = re.findall(r'\d+',line)
                version = '.'.join(numbers)

        os.system("solc-select install {}".format(version))
        os.system("solc-select use {}".format(version))

        suspicious_flags.append("----------------------------------------------------------VUNERABILITIES----------------------------------------------------------")
        output = subprocess.getoutput("slither contract.sol")
        vulnerabilities = output.splitlines()
        exclude = ["'solc --version' running", "INFO:Detectors:"]
        for line in vulnerabilities:
            if line not in exclude and 'solc contract.sol --combined-json' not in line:
                suspicious_flags.append(line)
                start_index = line.find('"')
                end_index = line.rfind('"')
                if start_index != -1 and end_index != -1:
                    rule = line[start_index + 1: end_index]
                    if "(contract.sol#" in rule:
                        rule = rule[:rule.index("(contract.sol#")]
                        if 'uint256' in rule:
                            rule = rule.replace('uint256', 'uint')
                        strings_to_highlight.append(rule.strip())
                
                elif '-' in line:
                    parts = line.split('-')
                    rule = parts[1]
                    if "(contract.sol#" in rule:
                        rule = rule[:rule.index("(contract.sol#")]
                        if 'uint256' in rule:
                            rule = rule.replace('uint256', 'uint')
                        strings_to_highlight.append(rule.strip())
        
        rules = [
            ("'pragma solidity ^0.8' not in source_code", "Outdated Solidity version used"),
            ("'library SafeMath' in source_code and 'SafeMath for uint256' not in source_code", "Custom SafeMath library used"),
            ("'is Ownable' in source_code and 'transferOwnership' in source_code", "Ownership transfer mechanism present"),
            ("'BlackList' in source_code and 'destroyBlackFunds' in source_code", "Blacklist and destroy funds feature present"),
            ("'deprecated' in source_code and 'upgradeTo' in source_code", "Deprecated and upgraded contract feature present"),
            ("'selfdestruct(' in source_code", "Potential self-destruct vulnerability"),
            ("'call.value(' in source_code", "Potential re-entrancy vulnerability"),
            ("'DAO' in source_code", "DAO"),
            ("'Parity' in source_code", "Parity wallet"),
            ("'overflow' in source_code or 'underflow' in source_code", "Potential arithmetic overflow/underflow vulnerability"),
            ("'revert()' in source_code", "Potential unhandled revert vulnerability"),
            ("'block.timestamp' in source_code", "Reliance on block.timestamp for critical functionality"),
            ("'tx.origin' in source_code", "Reliance on tx.origin for authorization"),
            ("'assembly' in source_code", "Use of assembly code, which can be error-prone"),
            ("'gasleft()' in source_code", "Reliance on gasleft() for critical functionality"),
            ("'contract Balance' in source_code", "Contract Balance pattern found, which may indicate unintended behavior"),
            ("'revert(' in source_code and 'require(' in source_code", "Mixed usage of revert and require, which can lead to inconsistent state"),
            ("'suicide(' in source_code", "Use of suicide (self-destruct) function, which can lead to unintended consequences"),
            ("'modifier onlyOwner' in source_code", "Ownership modifier present, which may not be properly secured"),
            ("'mapping(address => uint)' in source_code", "Use of mapping with address keys, which may be vulnerable to certain attacks"),
            ("'if (msg.value > 0)' in source_code", "Direct comparison of msg.value without proper validation"),
            ("'transfer(' in source_code", "Use of transfer function, which can lead to lost funds"),
            ("'abi.encodePacked(' in source_code", "Use of abi.encodePacked, which may result in unexpected behavior"),
            ("'this.call(' in source_code", "Reliance on this.call, which can introduce vulnerabilities"),
            ("'emit' in source_code", "Use of emit keyword without event declaration"),
            ("'assert(true)' in source_code", "Use of assert(true), which has no effect"),
            ("'keccak256(' in source_code", "Use of keccak256 without proper hashing"),
            ("'require(' in source_code and 'revert(' in source_code", "Mixed usage of require and revert, which can lead to inconsistent state"),
            ("'playerExist' in source_code", "Use of boolean flag playerExist without proper validation"),
            ("'msg.sender.transfer(' in source_code", "Use of transfer function directly on msg.sender, which can lead to lost funds"),
            ("'address(this).balance >= _earnings' in source_code", "Direct balance comparison without considering gas stipend"),
            ("'public' in source_code", "Use of public visibility for sensitive state variables"),
            ("'now > player[_playerAddress].lastSettledTime + payoutPeriod' in source_code", "Reliance on now for time-based operations without considering timestamp manipulation"),
            ("'player[_playerAddress].incomeLimitLeft >= amount.div(2)' in source_code", "Reliance on incomeLimitLeft for referral bonus calculations without proper validation"),
        ]
        


        for rule in rules:
            if eval(rule[0]):
                suspicious_flags.append(' + ' + rule[1])
                match = re.findall(r"'(.*?)'", rule[0])
                if match:
                    strings_to_highlight.extend(match)
        
        return suspicious_flags, strings_to_highlight
    
    
    
    def RowSelection(self, row, column):
        current_tab_index = self.tab_widget.currentIndex()
        table_widget = self.tab_widget.widget(current_tab_index)
        
        for r in range(table_widget.rowCount()):
            for c in range(table_widget.columnCount()):
                item = table_widget.item(r, c)
                if item is not None:
                    item.setBackground(QtGui.QColor(255, 255, 255))
                    item.setToolTip('')

        selected_row_data = []
        for c in range(table_widget.columnCount()):
            item = table_widget.item(row, c)
            if item is not None:
                selected_row_data.append(item.text())
            else:
                selected_row_data.append("")

        selected_hash = selected_row_data[5]
        selected_transaction = None
        for transaction in self.transactions:
            if transaction['hash'] == selected_hash:
                selected_transaction = transaction
                break

        if selected_transaction is not None:
            transaction_lines = []
            for key, value in selected_transaction.items():
                transaction_lines.append(f"{key}: {value}")
            transaction_text = '\n'.join(transaction_lines)
            self.text_widget.setText(transaction_text)
    
    def findTransaction(self, Thash):
        Etherscan_API = creds.Etherscan_API
        url = f'https://api.etherscan.io/api?module=proxy&action=eth_getTransactionByHash&txhash={Thash}&apikey={Etherscan_API}'
        try:
            response = requests.get(url)
            data = response.json()
            if 'error' not in data:
                transaction = data['result']
                self.AnalyzeTransaction2(transaction)

        except requests.exceptions.RequestException as e:
            print("API request error:", e)

    def show_TransactionWindow(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Search Transaction")
        dialog.setWindowIcon(QIcon(r"Icons\app.png"))
        dialog.setFixedSize(500, 100)
        layout = QVBoxLayout()
        
        label = QLabel("Enter Transaction Hash:")
        address = QLineEdit()
        button = QPushButton("Find Transaction")
        
        layout.addWidget(label)
        layout.addWidget(address)
        layout.addWidget(button)
        
        button.clicked.connect(lambda: self.findTransaction(address.text()))
        button.clicked.connect(dialog.accept)
        
        dialog.setLayout(layout)
        dialog.show()
    
    def show_ProfileWindow(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Analyze Profile")
        dialog.setWindowIcon(QIcon(r"Icons\app.png"))
        dialog.setFixedSize(500, 100)
        layout = QVBoxLayout()
        
        label = QLabel("Enter Wallet Address:")
        address = QLineEdit()
        address.setText("0x0ffEf1bF3a19DD96310194E73B38c069d1D1c31F")
        button = QPushButton("Analyze Profile")
        
        layout.addWidget(label)
        layout.addWidget(address)
        layout.addWidget(button)
        
        
        button.clicked.connect(lambda: self.analyzeProfile(address.text()))
        button.clicked.connect(dialog.accept)
        
        dialog.setLayout(layout)
        
        dialog.show()
    
    def AnalyzeTransaction2(self, transaction):
        dialog = QDialog(self)
        dialog.setWindowTitle("Transaction Analysis Window")
        dialog.setWindowIcon(QIcon(r"Icons\app.png"))
        dialog.setFixedSize(400, 550)
        
        to = None
        fromtext = None
        layout = QFormLayout()

        for key, value in transaction.items():
            if key == "from":
                label = QLabel(key + ':')
                text = QLineEdit()
                text.setMaximumWidth(260)
                text.setReadOnly(True)
                text.setText(str(value))
                button1 = QPushButton()
                button1.setIcon(QIcon(r"Icons\analyze.png"))
                button1.setMaximumWidth(30)
                button1.setEnabled(True)
                button1.setToolTip('Generate Profile Report')
                fromtext = text.text()
                
                hbox = QHBoxLayout()
                hbox.addWidget(label)
                hbox.addWidget(text)
                hbox.addWidget(button1)

                layout.addRow(hbox)

            elif key == "to":
                label = QLabel(key + ':')
                text = QLineEdit()
                text.setMaximumWidth(260)
                text.setReadOnly(True)
                text.setText(str(value))
                button2 = QPushButton()
                button2.setIcon(QIcon(r"Icons\analyze.png"))
                button2.setMaximumWidth(30)
                button2.setEnabled(True)
                button2.setToolTip('Generate Profile Report')
                to = text.text()
                
                hbox = QHBoxLayout()
                hbox.addWidget(label)
                hbox.addWidget(text)
                hbox.addWidget(button2)

                layout.addRow(hbox)
            
            elif key == "maxPriorityFeePerGas":
                label = QLabel('MaxPriority:')
                text = QLineEdit()
                text.setMaximumWidth(300)
                text.setReadOnly(True)
                text.setText(str(value))
                layout.addRow(label, text)
            
            elif key == "transactionIndex":
                label = QLabel('Index:')
                text = QLineEdit()
                text.setMaximumWidth(300)
                text.setReadOnly(True)
                text.setText(str(value))
                layout.addRow(label, text)

            else:
                label = QLabel(key + ':')
                text = QLineEdit()
                text.setMaximumWidth(300)
                text.setReadOnly(True)
                text.setText(str(value))
                layout.addRow(label, text)
        
        dialog.setLayout(layout)
        button1.clicked.connect(lambda: self.analyzeProfile(fromtext))
        button2.clicked.connect(lambda: self.analyzeProfile(to))
        dialog.show()
    
    def enable_buttons(self):
        self.button2.setEnabled(True)
        self.button3.setEnabled(True)
        self.button4.setEnabled(True)
        self.button6.setEnabled(True)
        self.SaveButton.setEnabled(True)
        self.save_action.setEnabled(True)

    def search_address_popup(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Search Wallet Address")
        dialog.setFixedSize(500, 100)
        layout = QVBoxLayout()

        label = QLabel("Enter A Wallet Address:")
        address = QLineEdit()
        address.setText('0xB3764761E297D6f121e79C32A65829Cd1dDb4D32')

        search_transactions_button = QPushButton("Search Wallet Address")
        search_transactions_button.clicked.connect(lambda: self.set_parent(address.text()))
        search_transactions_button.clicked.connect(lambda: self.get_transactions(address.text()))
        search_transactions_button.clicked.connect(dialog.accept)
        search_transactions_button.clicked.connect(self.enable_buttons)

        search_new = QPushButton("Start a New Search")
        search_new.clicked.connect(lambda: self.set_parent(address.text(), cond='New'))
        search_new.clicked.connect(lambda: self.get_transactions(address.text(), cond='New'))
        search_new.clicked.connect(dialog.accept)
        search_new.clicked.connect(self.enable_buttons)

        button_layout = QHBoxLayout()
        button_layout.addWidget(search_transactions_button)
        button_layout.addWidget(search_new)

        layout.addWidget(label)
        layout.addWidget(address)
        layout.addLayout(button_layout)

        dialog.setLayout(layout)
        dialog.exec_()

    def set_parent(self, address, cond=None):
        if cond == 'New':
            self.Parents.clear()
        self.Parents.append(address.lower())
    
    def get_transactions(self, address, cond = None):
        Etherscan_API = creds.Etherscan_API
        responses = []
        self.transactions = []
        if cond == 'New':
            self.Visited.clear()
            self.tab_widget.clear()
        if address not in self.Visited:
            self.Visited.append(address)
        if cond == 'Load':
            for i in set(self.Visited):
                url = f'https://api.etherscan.io/api?module=account&action=txlist&address={i}&apikey={Etherscan_API}'
                response = requests.get(url)
                if response.status_code == 200:
                    responses.append(response)
                    data = json.loads(response.text)
                    if data["status"] == "1":
                        self.transactionInfo = data["result"]
                        self.transactions.extend(self.transactionInfo)
                        return
        
        if cond == 'Timeline':
            Etherscan_API = creds.Etherscan_API
            url = f'https://api.etherscan.io/api?module=account&action=txlist&address={address}&startblock=0&endblock=99999999&sort=asc&apikey={Etherscan_API}'
            response = requests.get(url)
            data = response.json()

            if data['status'] == '1':
                transactions = data['result']
                self.create_timeline(transactions, address)
        
        for i in set(self.Visited):
            url = f'https://api.etherscan.io/api?module=account&action=txlist&address={i}&apikey={Etherscan_API}'
            response = requests.get(url)
            if response.status_code == 200:
                responses.append(response)
                data = json.loads(response.text)
                if data["status"] == "1":
                    self.transactionInfo = data["result"]
                    self.display_transactions(self.transactionInfo, i)
                    self.transactions.extend(self.transactionInfo)
                else:
                    print("No transactions found for the given wallet address.")
            else:
                print("Error occurred while fetching transactions.")
        
        self.create_graph(self.transactions)
        

    def display_transactions(self, data, address):
        for tab_index in range(self.tab_widget.count()):
            if self.tab_widget.tabText(tab_index) == address:
                table_widget = self.tab_widget.widget(tab_index)
                table_widget.clearContents()
                break
        else:
            table_widget = QTableWidget()
            table_widget.setMinimumSize(500, 500)
            table_widget.setMaximumWidth(750)
            font = QFont()
            font.setPointSize(7)
            table_widget.setFont(font)

            table_widget.setEditTriggers(QAbstractItemView.NoEditTriggers)
            table_widget.cellClicked.connect(self.RowSelection)
            table_widget.setColumnCount(7)
            table_widget.setHorizontalHeaderLabels(['Date', 'Time', 'From', 'To', 'Value (ETH)', 'Transaction Hash', 'Block Number'])

            table_widget.setSelectionBehavior(QAbstractItemView.SelectRows)
            table_widget.setSelectionMode(QAbstractItemView.ExtendedSelection)

            self.tab_widget.addTab(table_widget, address)
            

        for row, transaction in enumerate(data):
            timestamp = int(transaction['timeStamp'])
            time = QDateTime.fromSecsSinceEpoch(timestamp).toString('h:mm AP')
            date = QDateTime.fromSecsSinceEpoch(timestamp).toString('dd/MM/yyyy')
            table_widget.setRowCount(row + 1)
            table_widget.setItem(row, 0, QTableWidgetItem(date))
            table_widget.setItem(row, 1, QTableWidgetItem(time))
            table_widget.setItem(row, 2, QTableWidgetItem(transaction['from']))
            table_widget.setItem(row, 3, QTableWidgetItem(transaction['to']))
            value = float(transaction['value']) / 1000000000000000000.0
            table_widget.setItem(row, 4, QTableWidgetItem(f"{value:.8f}"))
            table_widget.setItem(row, 5, QTableWidgetItem(transaction['hash']))
            table_widget.setItem(row, 6, QTableWidgetItem(transaction['blockNumber']))
           
            for column, header in enumerate(['Date', 'Time', 'From', 'To', 'Value (ETH)', 'Transaction Hash', 'Block Number']):
                if header not in self.unique_values:
                    self.unique_values[header] = set()

                self.unique_values[header].add(table_widget.item(row, column).text())
        

    def create_graph(self, data, filtered_nodes=None):
        hidden = []
        df = pd.DataFrame(columns=['Source', 'Target', 'Date', 'Time', 'Value (ETH)'])
        
        for transaction in data:
            value_eth = float(transaction['value']) / 1000000000000000000.0
            if value_eth != 0:
                new_row = {
                    'Source': transaction['from'],
                    'Target': transaction['to'],
                    'Date': QDateTime.fromSecsSinceEpoch(int(transaction['timeStamp'])).toString('dd/MM/yyyy'),
                    'Time': QDateTime.fromSecsSinceEpoch(int(transaction['timeStamp'])).toString('h:mm:ss'),
                    'Value (ETH)': value_eth
                }
                df = df._append(new_row, ignore_index=True)
        
        self.net = Network(height='980px', width='100%', directed=False)
        sources = df['Source'].unique()
        targets = df['Target'].unique()
        nodes = list(set(list(sources) + list(targets)))

        self.net.barnes_hut()
        
        for node in nodes:
            if filtered_nodes is not None and node not in filtered_nodes:
                hidden.append(node)

            else:
                
                if node in self.Visited and node not in self.Parents:
                    self.net.add_node(node, label=node, title=node, shape='image', image=r"Icons\userNodeExpand.png", font={'color': 'black', 'size': 50}, borderWidth=0, size=180, shapeProperties={'borderRadius': 50}, escape=False, color='red')
                elif node in self.Parents:
                    self.net.add_node(node, label=node, title=node, shape='image', image=r"Icons\parent.png", font={'color': 'black', 'size': 50}, borderWidth=0, size=180, shapeProperties={'borderRadius': 50}, escape=False, color='red')
                else:
                    self.net.add_node(node, label=node, title=node, shape='image', image=r"Icons\user.png", font={'color': 'black', 'size': 50}, borderWidth=0, size=140, shapeProperties={'borderRadius': 50}, escape=False)

        intermediate_nodes = []

        for _, row in df.iterrows():
            if row['Source'] in nodes and row['Target'] in nodes:
                if row['Source'] not in hidden and row['Target'] not in hidden:
                    intermediate_node = f"{row['Source']}-{row['Target']}-{row['Time']}"
                    intermediate_nodes.append(intermediate_node)
                    label = f"{row['Value (ETH)']:.3f} ETH\nDate: {row['Date']}\nTime: {datetime.strptime(row['Time'], '%H:%M:%S').strftime('%I:%M %p')}"

                    self.net.add_node(intermediate_node, label=label, font={'color':'black', 'size': 50}, shape='image', image=r'Icons\eth.png', borderWidth=0, size=120, shapeProperties={'borderRadius': 50}, escape=False)
                    
                    self.net.add_edge(row['Source'], intermediate_node, color='#111111', width=0.003)

                    self.net.add_edge(intermediate_node, row['Target'], color='#111111', arrows={'to': {'enabled': True, 'type': 'vee', 'scaleFactor': 3}}, arrowStrikethrough=False, width=0.003)
            

        for node in self.net.nodes:
            if '-' in node['id']:
                split_id = node['id'].split('-')
                source = split_id[0]
                target = split_id[1]
                if filtered_nodes is not None and target is not None and target not in filtered_nodes or source in hidden:
                    node['hidden'] = 'True'
                    hidden.append(node)
                
        graph_file = 'graph.html'
        self.net.save_graph(graph_file)

        if self.net.save_graph:
            graph_path = os.path.join(os.getcwd(), graph_file)
            self.web_widget.load(QUrl.fromLocalFile(graph_path))
            self.modify_html_file(r"graph.html")
            

    def modify_html_file(self, html_file_path):
        with open(html_file_path, "r") as file:
            html_content = file.read()


        soup = BeautifulSoup(html_content, "html.parser")
        loading_bar = soup.select_one("#loadingBar")
        if loading_bar:
            css_mods_exist = True
            loading_bar["style"] = "height: 1px;"     
            
        bar = soup.select_one("#bar")
        if bar:
            bar["style"] = "background: rgb(179,25,255);"

        outerBorder = soup.select_one("div.outerBorder")
        if outerBorder:
            outerBorder["style"] = "height: 60px;"
    
        
        mod = str(soup)

        if "var socket = new WebSocket(" not in mod:
            modified_html_content = mod.replace(
                "</body>",
                """
                <script type="text/javascript">
                    document.body.style.overflow = "hidden";
                    
                    var socket = new WebSocket("ws://localhost:8765/");
                    socket.onopen = function() {
                        console.log("WebSocket connection established");
                    };

                    socket.onmessage = function(event) {
                        var message = event.data;
                        console.log("Received message from Python:", message);
                    };

                    function sendMessage(elementId) {
                        socket.send(elementId);
                    }

                    network.on("click", function(params) {
                        if (params.nodes.length > 0) {
                            var clickedNodeId = params.nodes[0];
                            sendMessage(clickedNodeId);
                        }
                    });

                    network.on("doubleClick", function(params) {
                        if (params.nodes.length > 0) {
                            var clickedNodeId = params.nodes[0];
                            sendMessage("Doubleclick" + clickedNodeId);
                        }
                    });
                    
                    document.addEventListener("DOMContentLoaded", function() {
                        var container = document.getElementById("mynetwork");
                        var windowHeight = window.innerHeight || document.documentElement.clientHeight || document.body.clientHeight;
                        container.style.height = (windowHeight - container.offsetTop - 10) + "px";
                    });
                    
                    window.addEventListener("resize", function() {
                        var container = document.getElementById("mynetwork");
                        var windowHeight = window.innerHeight || document.documentElement.clientHeight || document.body.clientHeight;
                        container.style.height = (windowHeight - container.offsetTop - 10) + "px";
                    
                    });

                </script>
                </body>
                """
            )
            modified_html_content = modified_html_content.replace(
                "</style>",
                """:focus {
				  outline: 0;
				  outline-color: transparent;
				  outline-style: none;
				}
            </style>"""
            )

        if """document.getElementById('loadingBar').removeAttribute("style");""" in modified_html_content:
            modified_html_content = modified_html_content.replace("""document.getElementById('loadingBar').removeAttribute("style");""", "")

        with open(html_file_path, "w") as file:
            file.write(modified_html_content)


    def flag_suspicious_activity(self):
        data = self.transactions
        if len(data) == 0:
            print("No transactions found for the given wallet address.")
            return

        features = []
        for transaction in data:
            feature = {
                "timestamp": int(transaction["timeStamp"]),
                "value": float(transaction["value"]) / 10 ** 18,
                "gas_price": int(transaction["gasPrice"])
            }
            features.append(feature)

        df = pd.DataFrame(features)

        df.sort_values("timestamp", inplace=True)

        df["value_diff_cumulative"] = df["value"].diff().fillna(0).cumsum()

        imputer = SimpleImputer(strategy="mean")
        df_imputed = imputer.fit_transform(df[["value_diff_cumulative", "gas_price"]])
        df[["value_diff_cumulative", "gas_price"]] = df_imputed

        clf = IsolationForest(contamination=0.05)
        df["anomaly"] = clf.fit_predict(df[["value_diff_cumulative", "gas_price"]])

        threshold_value = 0.5
        threshold_gas_price = 100

        for tab_index in range(self.tab_widget.count()):
            table_widget = self.tab_widget.widget(tab_index)
            for i, transaction in enumerate(data):
                if df.at[i, "anomaly"] == -1:
                    reasons = []
                    if df.at[i, "value_diff_cumulative"] > threshold_value:
                        reasons.append("Transaction value is higher than the average")
                    if df.at[i, "gas_price"] > threshold_gas_price:
                        reasons.append("Transaction gas price is higher than the average")
                    if reasons:
                        reason_str = " & ".join(reasons)
                        self.highlight_transaction(table_widget, i, reason_str)

    def highlight_transaction(self, table_widget, row_index, reason):
        for column in range(table_widget.columnCount()):
            item = table_widget.item(row_index, column)
            if item is not None:
                item.setBackground(QColor("#E25B74"))
                item.setToolTip(reason)
            else:
                item = QTableWidgetItem("")
                item.setBackground(QColor("#E25B74"))
                table_widget.setItem(row_index, column, item)
    
    def start_websocket_server(self, address, port):
        self.server = QWebSocketServer("WebSocketServer", QWebSocketServer.NonSecureMode, self)
        self.server.listen(QHostAddress(address), port)
        self.server.newConnection.connect(self.handle_new_connection)
        self.server.clients = []  # Track the connected clients

    def handle_new_connection(self):
        client_socket = self.server.nextPendingConnection()
        client_socket.textMessageReceived.connect(self.handle_message)
        client_socket.disconnected.connect(self.handle_disconnection)
        self.server.clients.append(client_socket)
        print(colored("Connection established", 'green'))

    def handle_message(self, message):
        client_socket = self.server.sender()
        if 'Doubleclick' in message:
            message = message.replace('Doubleclick', '')
            self.search_bar.clear()
            self.get_transactions(message)
        else:
            for tab_index in range(self.tab_widget.count()):
                table_widget = self.tab_widget.widget(tab_index)
                for row in range(table_widget.rowCount()):
                    row_matched = False
                    for column in range(table_widget.columnCount()):
                        item = table_widget.item(row, column)
                        if item is not None and message in item.text():
                            row_matched = True
                            break
                    if row_matched:
                        for column in range(table_widget.columnCount()):
                            item = table_widget.item(row, column)
                            if item is not None:
                                item.setBackground(QColor('#b319ff'))
                    else:
                        for column in range(table_widget.columnCount()):
                            item = table_widget.item(row, column)
                            item.setToolTip('')
                            item.setBackground(QColor('#FFFFFF'))
                            item.setForeground(QColor('#000000'))

    def handle_disconnection(self):
        client_socket = self.server.sender()
        self.server.clients.remove(client_socket)
        client_socket.deleteLater()
        if len(self.server.clients) == 0:
            if QApplication.instance().closingDown():
                print("Application is closing. Stopping the server...")
                self.server.close()



app = QApplication(sys.argv)
window = MainWindow()
window.show()
window.start_websocket_server("localhost", 8765)
sys.exit(app.exec_())

