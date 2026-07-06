import socket
import threading
import json

PORT = 50002
clients = set()  # Keeps track of active client connections


def broadcast(message_bytes, sender_socket):
    """Sends a message to every connected client except the sender."""
    removable = set()
    for client in clients:
        if client != sender_socket:
            try:
                client.send(message_bytes)
            except Exception:
                removable.add(client)

    # Clean up disconnected sockets safely
    for client in removable:
        clients.remove(client)


def handle_client(client_socket):
    """Handles the continuous incoming data flow from a specific client."""
    clients.add(client_socket)
    print(f"🔌 New connection established. Total clients: {len(clients)}")

    while True:
        try:
            data = client_socket.recv(4096)
            if not data:
                break
            # Forward the incoming chat packet to everyone else
            broadcast(data, client_socket)
        except Exception:
            break

    clients.remove(client_socket)
    client_socket.close()
    print(f"❌ Connection closed. Total clients: {len(clients)}")


def start_server():
    # Bind to 0.0.0.0 so it listens on all available networks (Local Wi-Fi and Tailscale)
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(("0.0.0.0", PORT))
    server.listen()
    print(f"📡 Term-Chat Master Server running on port {PORT}...")

    while True:
        client_socket, _ = server.accept()
        thread = threading.Thread(target=handle_client, args=(client_socket,))
        thread.daemon = True
        thread.start()


if __name__ == "__main__":
    start_server()
