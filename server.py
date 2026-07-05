import socket
import json

SERVER_IP = "127.0.0.1"
PORT = 50001

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((SERVER_IP, PORT))
server.listen(1)
print(f"Server is online and listening on {SERVER_IP}:{PORT}...")

client_socket, client_address = server.accept()
print(f"Connection established with {client_address}!")

raw_data = client_socket.recv(1024)
message = raw_data.decode("utf-8")

# Between these comments is the json parser tool

try:
    received_packet = json.loads(message)
    sender = received_packet["user"]
    text = received_packet["message"]

    print(f"{sender}: {text}")

except json.JSONDecodeError:
    print("Error: Could not decode incoming message.")

# Between these comments is the json parser tool

client_socket.close()
server.close()

print("Server shut down cleanly.")
