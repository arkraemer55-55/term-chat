import socket
import threading
import sys
import curses
from datetime import datetime

# =====================================================================
# SERVER CONFIGURATION (Hardcoded for a seamless user experience!)
# =====================================================================
SERVER_IP = "100.70.188.58"
PORT = 50002

messages = []
username = ""
client_socket = None

def receive_messages(stdscr, msg_win):
    """Continuously listens for incoming chat packets from the CasaOS server."""
    global messages
    while True:
        try:
            data = client_socket.recv(4096)
            if not data:
                break
            
            # Decode the message string from the server
            msg_str = data.decode('utf-8')
            messages.append(msg_str)
            
            # Redraw the message window with the new content
            draw_messages(msg_win)
        except Exception:
            break

def draw_messages(msg_win):
    """Renders the scrolling message feed inside the curses UI."""
    msg_win.erase()
    h, w = msg_win.getmaxyx()
    max_visible = h - 2  # Keep a small padding buffer
    
    # Get the latest messages that fit on the screen
    visible_messages = messages[-max_visible:] if len(messages) > max_visible else messages
    
    for idx, msg in enumerate(visible_messages):
        try:
            msg_win.addstr(idx + 1, 1, msg[:w-2])
        except curses.error:
            pass
    msg_win.box()
    msg_win.refresh()

def draw_input_box(input_win, current_text):
    """Updates the bottom text-input row box."""
    input_win.erase()
    h, w = input_win.getmaxyx()
    input_win.box()
    
    # Prompt string
    prompt = "Message: "
    try:
        input_win.addstr(1, 1, prompt)
        # Display typed text, scrolling horizontally if it's too long
        display_text = current_text[-(w - len(prompt) - 3):]
        input_win.addstr(1, 1 + len(prompt), display_text)
    except curses.error:
        pass
    input_win.refresh()

def curses_chat(stdscr):
    global messages, client_socket
    curses.curs_set(1)  # Show terminal text cursor
    stdscr.clear()
    
    # Calculate responsive window boundaries
    height, width = stdscr.getmaxyx()
    msg_win_height = height - 3
    
    # Build layout boxes
    msg_win = curses.newwin(msg_win_height, width, 0, 0)
    input_win = curses.newwin(3, width, msg_win_height, 0)
    
    # Initial UI draw
    draw_messages(msg_win)
    
    # Spin up background packet receiver thread
    recv_thread = threading.Thread(target=receive_messages, args=(stdscr, msg_win))
    recv_thread.daemon = True
    recv_thread.start()
    
    current_text = ""
    
    while True:
        draw_input_box(input_win, current_text)
        ch = input_win.getch()
        
        if ch in (10, 13):  # Enter key pressed
            if current_text.strip():
                if current_text.lower() == '/exit':
                    break
                
                # Format message with timestamp
                timestamp = datetime.now().strftime("%H:%M")
                formatted_msg = f"[{timestamp}] <{username}> {current_text}"
                
                # Append locally so the sender sees it instantly
                messages.append(formatted_msg)
                draw_messages(msg_win)
                
                # Ship it over the Tailscale network to the CasaOS server
                try:
                    client_socket.send(formatted_msg.encode('utf-8'))
                except Exception:
                    messages.append("⚠️ [System] Lost connection to server.")
                    draw_messages(msg_win)
                    
                current_text = ""
        elif ch in (8, 127, curses.KEY_BACKSPACE):  # Backspace handling
            current_text = current_text[:-1]
        elif 32 <= ch <= 126:  # Standard visible characters
            current_text += chr(ch)

def main():
    global username, client_socket
    
    # Simple clean CLI login phase before curses takes over layout
    print("====================================")
    print("       Welcome to Term-Chat!        ")
    print("====================================\n")
    username = input("Enter your username: ").strip()
    if not username:
        username = "Anonymous"
        
    print(f"\n🔄 Connecting to CasaOS Server at {SERVER_IP}...")
    
    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((SERVER_IP, PORT))
        print("✅ Connected securely via Tailscale!")
    except Exception as e:
        print(f"❌ Failed to reach the server: {e}")
        print("Make sure your Tailscale app is active and connected.")
        sys.exit(1)
        
    # Launch interface loop
    curses.wrapper(curses_chat)
    
    # Cleanup on close
    if client_socket:
        client_socket.close()
    print("\n👋 Disconnected from Term-Chat. Goodbye!")

if __name__ == "__main__":
    main()
