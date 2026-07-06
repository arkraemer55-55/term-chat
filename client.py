import socket
import threading
import sys
import curses
import json
from datetime import datetime

SERVER_IP = "100.70.188.58"
PORT = 50002

messages = []
online_users = []
username = ""
client_socket = None


def receive_messages(stdscr, msg_win, user_win):
    """Listens for JSON data frames from the server and sorts them accordingly."""
    global messages, online_users
    while True:
        try:
            data = client_socket.recv(4096)
            if not data:
                break

            # Parse the server packet
            packet = json.loads(data.decode("utf-8"))

            if packet["type"] == "MSG":
                messages.append(packet["data"])
                draw_messages(msg_win)
            elif packet["type"] == "USERS":
                online_users = packet["data"]
                draw_users(user_win)

        except Exception:
            break


def draw_messages(msg_win):
    msg_win.erase()
    h, w = msg_win.getmaxyx()
    max_visible = h - 2

    visible_messages = (
        messages[-max_visible:] if len(messages) > max_visible else messages
    )
    for idx, msg in enumerate(visible_messages):
        try:
            msg_win.addstr(idx + 1, 1, msg[: w - 2])
        except curses.error:
            pass
    msg_win.box()
    msg_win.refresh()


def draw_users(user_win):
    """Renders the active users box list."""
    user_win.erase()
    h, w = user_win.getmaxyx()

    try:
        user_win.addstr(0, 1, " Active Users ")
    except curses.error:
        pass

    for idx, user in enumerate(online_users[: h - 2]):
        try:
            # Bullet point active users
            user_win.addstr(idx + 1, 1, f"• {user[: w - 3]}")
        except curses.error:
            pass
    user_win.box()
    user_win.refresh()


def draw_input_box(input_win, current_text):
    input_win.erase()
    h, w = input_win.getmaxyx()
    input_win.box()
    prompt = "Message: "
    try:
        input_win.addstr(1, 1, prompt)
        display_text = current_text[-(w - len(prompt) - 3) :]
        input_win.addstr(1, 1 + len(prompt), display_text)
    except curses.error:
        pass
    input_win.refresh()


def curses_chat(stdscr):
    global messages, client_socket
    curses.curs_set(1)
    stdscr.clear()

    height, width = stdscr.getmaxyx()
    msg_win_height = height - 3

    # 80/20 Layout Split for Chat window and Users Sidebar
    sidebar_width = 20 if width > 60 else 15
    chat_width = width - sidebar_width

    # Build our distinct layout elements
    msg_win = curses.newwin(msg_win_height, chat_width, 0, 0)
    user_win = curses.newwin(msg_win_height, sidebar_width, 0, chat_width)
    input_win = curses.newwin(3, width, msg_win_height, 0)

    # Draw empty panels initially
    draw_messages(msg_win)
    draw_users(user_win)

    recv_thread = threading.Thread(
        target=receive_messages, args=(stdscr, msg_win, user_win)
    )
    recv_thread.daemon = True
    recv_thread.start()

    current_text = ""

    while True:
        draw_input_box(input_win, current_text)
        ch = input_win.getch()

        if ch in (10, 13):  # Enter Key
            if current_text.strip():
                if current_text.lower() == "/exit":
                    break

                timestamp = datetime.now().strftime("%H:%M")
                formatted_msg = f"[{timestamp}] <{username}> {current_text}"

                messages.append(formatted_msg)
                draw_messages(msg_win)

                try:
                    client_socket.send(formatted_msg.encode("utf-8"))
                except Exception:
                    messages.append("⚠️ [System] Lost server connection.")
                    draw_messages(msg_win)

                current_text = ""
        elif ch in (8, 127, curses.KEY_BACKSPACE):
            current_text = current_text[:-1]
        elif 32 <= ch <= 126:
            current_text += chr(ch)


def main():
    global username, client_socket

    print("====================================")
    print("       Welcome to Term-Chat!        ")
    print("====================================\n")
    username = input("Enter your username: ").strip()
    if not username:
        username = "Anonymous"

    print(f"\n🔄 Connecting to Server at {SERVER_IP}...")

    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((SERVER_IP, PORT))

        # Send our handshake username packet immediately on connect
        client_socket.send(username.encode("utf-8"))
        print("✅ Connected securely via Tailscale!")
    except Exception as e:
        print(f"❌ Failed to reach the server: {e}")
        sys.exit(1)

    curses.wrapper(curses_chat)

    if client_socket:
        client_socket.close()
    print("\n👋 Disconnected. Goodbye!")


if __name__ == "__main__":
    main()
