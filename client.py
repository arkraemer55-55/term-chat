import socket
import threading
import sys
import curses
import json
import textwrap
import os  # Added to trigger system audio alerts
from datetime import datetime

SERVER_IP = "100.70.188.58"
PORT = 50002

messages = []
online_users = []
username = ""
client_socket = None


def play_alert_sound():
    import platform

    try:
        current_os = platform.system().lower()

        if "linux" in current_os:
            os.system(
                "play -q /usr/share/sounds/freedesktop/stereo/message-new-instant.oga &"
            )
        elif "darwin" in current_os:  # macOS
            os.system("afplay /System/Library/Sounds/Glass.aiff &")
        elif "windows" in current_os:
            # Uses a built-in PowerShell sound trigger for Windows
            os.system(
                "powershell -c (New-Object Media.SoundPlayer 'C:\Windows\Media\notify.wav').Play() &"
            )
    except Exception:
        pass


def receive_messages(stdscr, msg_win, user_win):
    global messages, online_users
    while True:
        try:
            data = client_socket.recv(4096)
            if not data:
                break

            packet = json.loads(data.decode("utf-8"))

            if packet["type"] == "MSG":
                messages.append(packet["data"])
                draw_messages(msg_win)
                # Play audio notification because an incoming packet just landed!
                play_alert_sound()
            elif packet["type"] == "USERS":
                online_users = packet["data"]
                draw_users(user_win)

        except Exception:
            break


def draw_messages(msg_win):
    """Renders wrapped message packets with distinct identity-based colors."""
    msg_win.erase()
    h, w = msg_win.getmaxyx()
    max_line_width = w - 3

    # We will store pairs of (text_line, color_pair_id)
    wrapped_lines = []

    for msg in messages:
        chunks = textwrap.wrap(msg, width=max_line_width)

        # Determine the color of this message block by scanning the owner tag
        # Your messages look like: "[12:34] <YourName> hello"
        user_tag = f"<{username}>"
        if user_tag in msg:
            color_id = 1  # Green for you
        else:
            color_id = 2  # Magenta for everyone else

        for chunk in chunks:
            wrapped_lines.append((chunk, color_id))

    max_visible = h - 2
    visible_lines = (
        wrapped_lines[-max_visible:]
        if len(wrapped_lines) > max_visible
        else wrapped_lines
    )

    for idx, (line, color_id) in enumerate(visible_lines):
        try:
            # Inject the custom color profile attribute natively into curses
            msg_win.addstr(idx + 1, 1, line, curses.color_pair(color_id))
        except curses.error:
            pass

    msg_win.box()
    msg_win.refresh()


def draw_users(user_win):
    user_win.erase()
    h, w = user_win.getmaxyx()

    try:
        user_win.addstr(0, 1, " Active Users ")
    except curses.error:
        pass

    for idx, user in enumerate(online_users[: h - 2]):
        try:
            # Let's highlight users in the sidebar using Magenta as well!
            user_win.addstr(idx + 1, 1, f"• {user[: w - 3]}", curses.color_pair(2))
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

    # 🎨 INITIALIZE TERMINAL COLORS MATRIX
    curses.start_color()
    curses.use_default_colors()
    # Pair 1: Green text, Default transparent background
    curses.init_pair(1, curses.COLOR_GREEN, -1)
    # Pair 2: Magenta text, Default transparent background
    curses.init_pair(2, curses.COLOR_MAGENTA, -1)

    curses.curs_set(1)
    stdscr.clear()

    height, width = stdscr.getmaxyx()
    msg_win_height = height - 3

    sidebar_width = 20 if width > 60 else 15
    chat_width = width - sidebar_width

    msg_win = curses.newwin(msg_win_height, chat_width, 0, 0)
    user_win = curses.newwin(msg_win_height, sidebar_width, 0, chat_width)
    input_win = curses.newwin(3, width, msg_win_height, 0)

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
