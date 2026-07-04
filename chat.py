import json

username = input("Enter your username: ")
text_message = input(" Type your message: ")
packet = {"user": username, "message": text_message, "online_status": "active"}

# test incoming strings below:
network_stream = [
    '{"user": "Dad", "message": "Hey kiddo!", "online_status": "active"}',
    '{"user": "Dad", "message": "Did you see my last text?", "online_status": "active"}',
    '{"user": "Dad", "message": "Hey k',  # Oh no, another corrupted packet!
    '{"user": "Dad", "message": "Sorry, lost signal for a second.", "online_status": "active"}',
]

json_packet = json.dumps(packet)
print(json_packet)

# incoming_reply = '{"user": "Dad", "message": "Hey kiddo! Terminal app looks great.", "online_status": "active"}'
# broken_reply = '{"user": "Dad", "message": "Hey kid'

for packet_string in network_stream:
    try:
        received_packet = json.loads(packet_string)

        sender = received_packet["user"]
        text = received_packet["message"]

        print(f"{sender}: {text}")

    except json.JSONDecodeError:
        print("Error: Could not decode incoming message.")
