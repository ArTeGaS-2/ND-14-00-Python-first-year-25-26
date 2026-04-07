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

class ChatPage(QWidget):
    message_received =  pyqtSignal(str)

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Messanger - чат")
        self.client_name = f"Клієнт {os.getpid()}"

        self.client_socket: socket.socket | None = None

        self.reply_index = 0
        self.replies = [
            "Бубузян: Ми захопимо всесвіт!",
            "Ізюбрь: Дєд, пий таблетки.",
            "Кукуха: Бліцкріг!!!"
        ]
        
        title_lable = QLabel("Вікно чату")
        self.info_label = QLabel("Перша версія: один чат без БД")

        self.history_box = QPlainTextEdit()
        self.history_box.setReadOnly(True)
        self.history_box.setPlainText(
            "Бубузян: Привіт! Це перша версія чату. \n"
            "Ти: Тут уже можна писати повідомлення.")
        
        self.message_input = QLineEdit()
        self.message_input.setPlaceholderText("Напиши повідомлення...")
        self.message_input.returnPressed.connect(self.send_message)

        send_button = QPushButton("Надіслати")
        send_button.clicked.connect(self.send_message)

        bottom_layout = QHBoxLayout()
        bottom_layout.addWidget(self.message_input, 1)
        bottom_layout.addWidget(send_button)

        layout = QVBoxLayout()
        layout.addWidget(title_lable)
        layout.addWidget(self.info_label)
        layout.addWidget(self.history_box, 1)
        layout.addLayout(bottom_layout)
        self.setLayout(layout)

        self.message_received.connect(self.history_box.appendPlainText)
        self.connect_to_server()

    def connect_to_server(self) -> None:
        try:
            self.client_socket = socket.socket(
                socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.connect((HOST, PORT))
        except OSError:
            self.info_label.setText("Сервер недоступний")
            self.history_box.appendPlainText(
                "Система: Не вдалось підключитись до сервера")
            return
        self.info_label.setText(
            f"{self.client_name} підключено до {HOST}:{PORT}")

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

        if self.client_socket is not None:
            try:
                self.client_socket.sendall(
                    f"{self.client_name}: {text}".encode("utf-8"))
            except OSError:
                self.history_box.appendPlainText(
                    "Система: Не вдалось надіслати повідомлення")
                return

        self.history_box.appendPlainText(f"{self.client_name}: {text}")
        self.message_input.clear()

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
