import socket
import json
import threading
import curses
import time
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
    curses.curs_set(1)
    # Make getch() non-blocking so our loop can check for screen resizes constantly
    # stdscr.nodelay(True)

    # We move window creation into a helper inner-function so we can re-run it when resizing!
    def create_layout():
        max_y, max_x = stdscr.getmaxyx()
        chat_w = int(max_x * 0.70)  # Lowered slightly to guarantee sidebar visibility
        user_w = max_x - chat_w
        body_h = max_y - 4

        stdscr.clear()
        h_win = curses.newwin(3, max_x, 0, 0)
        c_win = curses.newwin(body_h, chat_w, 3, 0)
        u_win = curses.newwin(body_h, user_w, 3, chat_w)
        i_win = curses.newwin(1, max_x, max_y - 1, 0)

        c_win.scrollok(True)

        # Redraw borders
        h_win.box()
        h_win.addstr(1, 2, f"🏁 TERM-CHAT v2.0 | User: {MY_USERNAME}", curses.A_BOLD)
        h_win.refresh()

        u_win.box()
        u_win.addstr(1, 1, "👥 ONLINE PEERS", curses.A_BOLD)
        # Re-populate existing users on resize
        for idx, username in enumerate(ACTIVE_USERS.keys(), start=2):
            if idx < body_h - 1:  # Prevent crashing if window is too short
                u_win.addstr(idx, 1, f"• {username}")
        u_win.refresh()

        return h_win, c_win, u_win, i_win

    header_win, chat_win, user_win, input_win = create_layout()
    input_win.nodelay(True)

    # Spin up background receiver
    receiver_thread = threading.Thread(
        target=listen_for_messages, args=(chat_win, user_win), daemon=True
    )
    receiver_thread.start()

    input_buffer = ""

    while True:
        # 1. Handle Responsive Window Resizing
        ch = input_win.getch()
        if ch == curses.KEY_RESIZE:
            curses.update_lines_cols()
            header_win, chat_win, user_win, input_win = create_layout()
            # Re-pass fresh windows to our background thread safely
            continue

        # 2. Render the Input Bar dynamically
        input_win.clear()
        input_win.addstr(0, 0, f"> {input_buffer}")
        input_win.refresh()

        # 3. Custom Input Reader (to capture keystrokes smoothly alongside thread updates)
        if ch != -1:
            if ch in (10, 13):  # Enter Key pressed
                text_message = input_buffer.strip()
                input_buffer = ""  # Clear buffer

                if not text_message:
                    continue

                # Flexible Exit Conditions!
                if text_message.lower() in ("/exit", "exit", "quit"):
                    break

                current_time = datetime.now().strftime("%H:%M")
                packet = {
                    "user": MY_USERNAME,
                    "message": text_message,
                    "timestamp": current_time,
                }

                try:
                    sender_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sender_socket.connect((TARGET_IP, PORT))
                    sender_socket.send(json.dumps(packet).encode("utf-8"))
                    sender_socket.close()

                    chat_win.addstr(f"[{current_time}] [You]: {text_message}\n")
                    chat_win.refresh()
                except ConnectionRefusedError:
                    chat_win.addstr("❌ Could not connect.\n")
                    chat_win.refresh()

            elif ch in (263, 127, 8):  # Backspace handling
                input_buffer = input_buffer[:-1]
            elif 32 <= ch <= 126:  # Regular typing characters
                input_buffer += chr(ch)
        if ch == -1:
            time.sleep(0.02)


# This is the magic wrapper that safely boots up and shuts down curses
# so your terminal doesn't get permanently broken if your code crashes.
if __name__ == "__main__":
    curses.wrapper(main_app)
