import socket
import json
import threading
import curses
from datetime import datetime


MY_USERNAME = input("Username: ")
TARGET_IP = input("Enter the IP address of th person you want to chat with: ")
PORT = 50002

GREEN = "\033[92m"
MAGENTA = "\033[95m"
GRAY = "\033[90m"
RESET = "\033[0m"

ACTIVE_USERS = {}


# ==========================================
# PILLAR 1: THE BACKGROUND RECEIVER
# ==========================================
def listen_for_messages(chat_win, user_win):
    # Create the TCP socket server
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(("0.0.0.0", PORT))
    server.listen(5)

    while True:
        try:
            client_socket, address = server.accept()
            message_bytes = client_socket.recv(1024)
            message_string = message_bytes.decode("utf-8")
            client_socket.close()

            # Unpack JSON
            received_packet = json.loads(message_string)
            sender = received_packet["user"]
            text = received_packet["message"]
            time_sent = received_packet.get("timestamp", "00:00")

            # Update online user directory
            ACTIVE_USERS[sender] = time_sent

            # Update the Active Users sidebar window
            user_win.clear()
            user_win.box()
            user_win.addstr(1, 1, "👥 ONLINE PEERS", curses.A_BOLD)
            for idx, username in enumerate(ACTIVE_USERS.keys(), start=2):
                user_win.addstr(idx, 1, f"• {username}")
            user_win.refresh()

            # Print the message to the main chat window
            chat_win.addstr(f"[{time_sent}] [{sender}]: {text}\n")
            chat_win.refresh()

        except Exception:
            pass


# ==========================================
# PILLAR 2: THE UI ENGINE & TRANSMITTER
# ==========================================
def main_app(stdscr):
    # Hide the default terminal cursor blinking randomly
    curses.curs_set(1)

    # Get total layout dimensions of your terminal window
    max_y, max_x = stdscr.getmaxyx()

    # Define window dimensions based on screen size
    # chat_win takes up most of the screen, user_win takes a right-side panel
    chat_w = int(max_x * 0.75)
    user_w = max_x - chat_w
    body_h = max_y - 4  # Reserve space at the top/bottom for titles and input

    # Create the Sub-Windows: (height, width, start_y, start_x)
    header_win = curses.newwin(3, max_x, 0, 0)
    chat_win = curses.newwin(body_h, chat_w, 3, 0)
    user_win = curses.newwin(body_h, user_w, 3, chat_w)
    input_win = curses.newwin(1, max_x, max_y - 1, 0)

    # Enable automatic scrolling in the chat body window
    chat_win.scrollok(True)

    # Draw static UI borders and headers
    header_win.box()
    header_win.addstr(1, 2, f"🏁 TERM-CHAT v2.0 | User: {MY_USERNAME}", curses.A_BOLD)
    header_win.refresh()

    user_win.box()
    user_win.addstr(1, 1, "👥 ONLINE PEERS", curses.A_BOLD)
    user_win.refresh()

    # Spin up our background receiver thread, passing it our fresh layout windows
    receiver_thread = threading.Thread(
        target=listen_for_messages, args=(chat_win, user_win), daemon=True
    )
    receiver_thread.start()

    # The Main Input Transmitter Loop
    while True:
        # Reset the input bar row
        input_win.clear()
        input_win.addstr(0, 0, "> ")
        input_win.refresh()

        # Capture keystrokes from the user inside our input box window
        curses.echo()
        text_message = input_win.getstr(0, 2).decode("utf-8").strip()
        curses.noecho()

        if not text_message:
            continue

        if text_message.lower() == "/exit":
            break

        current_time = datetime.now().strftime("%H:%M")

        # Construct the outbound packet
        packet = {
            "user": MY_USERNAME,
            "message": text_message,
            "timestamp": current_time,
        }
        json_packet = json.dumps(packet)

        try:
            sender_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sender_socket.connect((TARGET_IP, PORT))
            sender_socket.send(json_packet.encode("utf-8"))
            sender_socket.close()

            # Print your own message locally in the chat window cleanly
            chat_win.addstr(f"[{current_time}] [You]: {text_message}\n")
            chat_win.refresh()

        except ConnectionRefusedError:
            chat_win.addstr("❌ Could not connect to the other user.\n")
            chat_win.refresh()


# This is the magic wrapper that safely boots up and shuts down curses
# so your terminal doesn't get permanently broken if your code crashes.
if __name__ == "__main__":
    curses.wrapper(main_app)
