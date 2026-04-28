from __future__ import annotations

import sys
import socket
import os
import threading

from PyQt6.QtCore import pyqtSignal # Сигнал безпечного закриття вікна
from PyQt6.QtGui import QCloseEvent # Подія закритя вікна
from PyQt6.QtWidgets import(
    QApplication,
    QHBoxLayout,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QLabel,
    QMainWindow,
    QVBoxLayout,
    QWidget)

from server import BUFFER_SIZE, HOST, PORT

DEFAULT_HOST = "127.0.0.1"

class ChatPage(QWidget):
    message_received =  pyqtSignal(str)
    connection_closed = pyqtSignal(str)

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Messanger - чат")
        self.client_socket: socket.socket | None = None
        self.is_closing = False
        
        title_lable = QLabel("Вікно чату")
        self.info_label = QLabel("Спочатку введи нікней і адресу серверу.")

        self.nickname_input = QLineEdit()
        self.nickname_input.setPlaceholderText("Нікнейм")
        self.nickname_input.setText(f"Клієнт {os.getpid()}")

        self.host_input = QLineEdit()
        self.host_input.setPlaceholderText("IP або домен сервера")
        self.host_input.setText(DEFAULT_HOST)

        self.port_input = QLineEdit()
        self.port_input.setPlaceholderText("Порт")
        self.port_input.setText(str(PORT))

        self.connect_button = QPushButton("Підключитися")
        self.connect_button.clicked.connect(self.connect_to_server)

        self.history_box = QPlainTextEdit()
        self.history_box.setReadOnly(True)
        self.history_box.setPlainText(
            "Система: Нік, адреса сервера, підключення.")
        
        self.message_input = QLineEdit()
        self.message_input.setPlaceholderText("Напиши повідомлення...")
        self.message_input.returnPressed.connect(self.send_message)

        self.send_button = QPushButton("Надіслати")
        self.send_button.clicked.connect(self.send_message)
        self.send_button.setEnabled(False)

        bottom_layout = QHBoxLayout()
        bottom_layout.addWidget(self.message_input, 1)
        bottom_layout.addWidget(self.send_button)

        connect_layout = QHBoxLayout()
        connect_layout.addWidget(self.nickname_input, 1)
        connect_layout.addWidget(self.host_input, 1)
        connect_layout.addWidget(self.port_input)
        connect_layout.addWidget(self.connect_button)

        layout = QVBoxLayout()
        layout.addWidget(title_lable)
        layout.addWidget(self.info_label)
        layout.addLayout(connect_layout)
        layout.addWidget(self.history_box, 1)
        layout.addLayout(bottom_layout)
        self.setLayout(layout)

        self.message_received.connect(self.history_box.appendPlainText)
        self.connection_closed(self.handle_disconnect)

    def connect_to_server(self) -> None:
        if self.client_socket is not None:
            self.history_box.appendPlainText("Система: Ви вже підключені")
            return
        
        nickname = self.nickname_input.text().strip()
        host = self.host_input.text().strip()

        try:
            port = int(self.port_input.text().strip())
        except ValueError:
            self.info_label.setText("Порт має бути числом")
            return
        
        if not nickname or not host:
            self.info_label.setText("Введіть нікнейм і адресу сервера")
            return
        
        try:
            client_socket = socket.socket(
                socket.AF_INET, socket.SOCK_STREAM)
            client_socket.connect((host, port))
        except OSError:
            self.info_label.setText("Сервер недоступний")
            self.history_box.appendPlainText(
                "Система: Не вдалось підключитись до сервера")
            return
       
        self.client_socket = client_socket
        self.info_label.setText(f"{nickname} підключено до {host}:{port}")
        self.history_box.appendPlainText("Система: Підключення успішне.")
        self.send_button.setEnabled(True)
        self.connect_button.setEnabled(False)
        self.nickname_input.setEnabled(False)
        self.host_input.setEnabled(False)
        self.port_input.setEnabled(False)

        listen_thread = threading.Thread(
            target=self.listen_for_messages,
            daemon=True
        )
        listen_thread.start()

    def listen_for_messages(self) -> None:
        if self.client_socket is None:
            return

        try:
            while True:
                data = self.client_socket.recv(BUFFER_SIZE)
                if not data:
                    break
                self.message_received.emit(data.decode("utf-8"))
        except OSError:
            pass


    def send_message(self) -> None:
        text = self.message_input.text().strip()
        if not text: 
            return
        
        self.history_box.appendPlainText(f"Ти: {text}")
        self.message_input.clear()

        if self.client_socket is None:
            self.history_box.appendPlainText("Система: Сервер недоступний")
            return
        try:
            message = f"{self.client_name}: {text}"
            self.client_socket.sendall(message.encode("utf-8"))
        except OSError:
            self.info_label.setText("З'єднання втрачено")
            self.history_box.appendPlainText("Система: Повідомлення не надіслано.")
            self.send_button.setEnabled(False)

    def receive_messages(self) -> None:
        if self.client_socket is None:
            return
        try:
            while True:
                data = self.client_socket.recv(BUFFER_SIZE)

                if not data:
                    break

                message = data.decode("utf-8")
                self.message_received.emit(message)
        
        except OSError:
            pass
        finally: 
            self.message_received.emit("Система: З'єднання з сервером закрито")

    def closeEvent(self, event: QCloseEvent) -> None:
        if self.client_socket is not None:
            self.client_socket.close()
            self.client_socket = None

        super().closeEvent(event)

def create_chat_window() -> QMainWindow:
    window = QMainWindow()
    window.setWindowTitle("Messanger - головне вікно")

    page = ChatPage()
    window.setCentralWidget(page)
    window.resize(640, 420)
    return window

def main() -> int:
    app = QApplication(sys.argv)
    window = create_chat_window()
    window.show()
    return app.exec()

if __name__ == "__main__":
    raise SystemExit(main())
