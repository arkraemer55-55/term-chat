import socket
import json


username = input("Enter your username: ")
text_message = input(" Type your message: ")
packet = {"user": username, "message": text_message, "online_status": "active"}
json_packet = json.dumps(packet)

SERVER_IP = "127.0.0.1"
PORT = 50001

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect((SERVER_IP, PORT))
client.send(json_packet.encode("utf-8"))

client.close()
print("Message transmitted successfully!")
