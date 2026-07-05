import socket
import json
import threading
from datetime import datetime

MY_USERNAME = input("Username: ")
TARGET_IP = "192.168.0.79"
PORT = 50002

GREEN = "\033[92m"
MAGENTA = "\033[95m"
GRAY = "\033[90m"
RESET = "\033[0m"


# Background Receiver
def listen_for_messages():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(("0.0.0.0", PORT))
    server.listen(5)

    while True:
        try:
            # Accept a connection from the other user
            client_socket, address = server.accept()
            raw_data = client_socket.recv(1024)
            message_string = raw_data.decode("utf-8")

            # Unpack the JSON packet
            received_packet = json.loads(message_string)
            sender = received_packet["user"]
            text = received_packet["message"]
            time_sent = received_packet.get("timestamp", "00.00")
            print(f"\n{GRAY}[{time_sent}]{RESET} {MAGENTA}[{sender}]:{RESET} {text}")

            # Print message cleanly to screen
            print(f"\n[{sender}]: {text}")
            client_socket.close()

        except json.JSONDecodeError:
            print("\n Received a corrupted message packet.")
        except Exception as e:
            pass


# Spinning up the background thread
receiver_thread = threading.Thread(target=listen_for_messages, daemon=True)
receiver_thread.start()

# Main Transmitter Loop
print("Messenger Initialized. Type a message and hit Enter to send: ")
while True:
    current_time = datetime.now().strftime("%H:%M")
    text_message = input("> ")
    if text_message.lower() == "quit":
        print("Shutting down Messenger")
        break
    if not text_message.strip():
        continue
    packet = {
        "user": MY_USERNAME,
        "message": text_message,
        "online_status": "active",
        "timestamp": current_time,
    }
    json_packet = json.dumps(packet)

    try:
        sender_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sender_socket.connect((TARGET_IP, PORT))
        sender_socket.send(json_packet.encode("utf-8"))
        sender_socket.close()
        print(f"{GRAY}[{current_time}]{RESET} {GREEN}[You]:{RESET} {text_message}")

    except ConnectionRefusedError:
        print("Could not connect to other user. Check connection.")
