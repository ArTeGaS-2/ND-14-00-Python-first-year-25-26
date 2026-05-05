from __future__ import annotations

import socket # Це кожен окремий клієнт
import threading # Відгалуження

HOST = "0.0.0.0" # сервер що працює саме на цьому комп'ютері
PORT = 5000 # порт, для клієнтів
BUFFER_SIZE = 1024 # максимум інформації за раз у байтах

clients: list[socket.socket] = [] # список підключених клієнтів
clients_lock = threading.Lock() # захист списку від одночасних змін

def broadcast(message: bytes, sender: socket.socket) -> None:
    # message - це байти, які сервер отримав від одного з клієнтів.
    # sender - це сокет клієнта, який надіслав повідомлення

    with clients_lock:
        for client in clients:
            # Відправнику його ж повідомлення не відправляємо
            if client is sender:
                continue

            try:
                # надсилаємо байти іншому клієнту
                client.sendall(message)
            except OSError:
                # якщо сокет є недайсним
                pass

def remove_client(client_socket: socket.socket) -> None:
    with clients_lock:
        if client_socket in clients:
            clients.remove(client_socket)

    client_socket.close()

def handle_client(client_socket: socket.socket) -> None:
    # Читаємо через цей метод повідомлення клієнта
    try:
        while True:
            try:
                # приймає наступний шматок байтів від користувача.
                data = client_socket.recv(BUFFER_SIZE)
            except ConnectionResetError:
                # часто трапляється коли юзер закриває вікно програми у Windows
                break
            
            if not data:
                break

            broadcast(data, sender=client_socket)
    
    finally:
        remove_client(client_socket)

def main() -> None:
    # TCP сокет
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    server_socket.bind((HOST, PORT))

    server_socket.listen()

    print(f"Server started on {HOST}:{PORT}")

    try:
        while True:
            client_socket, client_address = server_socket.accept()
            print(f"Client connected:  {client_address}")

            # Додаємо сокет нового клієнта в список
            with clients_lock:
                clients.append(client_socket)

            # Для кожного клієнта запускаємо окремий потік
            client_thread = threading.Thread(
                target=handle_client, # Яку функцію запускати в новому потоці
                args=(client_socket,), # Які аргументи передати в handle_client
                daemon=True # Потік не заважає завершити програму
            )
            client_thread.start()
    except KeyboardInterrupt:
        print("Server stopped")
    finally:
        # При завершенні закриваємо всі клієнтські сокети
        with clients_lock:
            for client in clients:
                client.close()
            clients.clear()
        # І наприкінці закриваємо сам серверний сокет
        server_socket.close()

if __name__ == "__main__":
    main() 
