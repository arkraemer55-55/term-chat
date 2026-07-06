import socket
import threading
import json

PORT = 50002
# Map sockets to usernames: { client_socket: username }
clients = {}


def broadcast_user_list():
    """Sends the current list of active usernames to all connected clients."""
    user_list = list(clients.values())
    # Wrap it in a JSON packet so the client knows it's a system event, not text chat
    packet = json.dumps({"type": "USERS", "data": user_list}).encode("utf-8")

    removable = []
    for client in clients:
        try:
            client.send(packet)
        except Exception:
            removable.append(client)

    for client in removable:
        del clients[client]


def broadcast_message(message_str, sender_socket=None):
    """Broadcasts a standard chat message string to everyone."""
    packet = json.dumps({"type": "MSG", "data": message_str}).encode("utf-8")

    removable = []
    for client in clients:
        if client != sender_socket:
            try:
                client.send(packet)
            except Exception:
                removable.append(client)

    for client in removable:
        del clients[client]


def handle_client(client_socket):
    """Handles data flow for a specific user."""
    # First thing the client sends is its username string
    try:
        username = client_socket.recv(1024).decode("utf-8").strip()
        if not username:
            username = "Unknown"
        clients[client_socket] = username
        print(f"🔌 {username} joined. Total users: {len(clients)}")

        # Notify everyone of the updated list
        broadcast_user_list()
    except Exception:
        client_socket.close()
        return

    while True:
        try:
            data = client_socket.recv(4096)
            if not data:
                break

            # Forward incoming message packet
            msg_str = data.decode("utf-8")
            broadcast_message(msg_str, sender_socket=client_socket)
        except Exception:
            break

    print(f"❌ {clients[client_socket]} disconnected.")
    del clients[client_socket]
    client_socket.close()
    broadcast_user_list()


def start_server():
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
