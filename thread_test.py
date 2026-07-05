import threading
import time


def background_listener():
    while True:
        print("\n (background) Checking for new messages...")
        time.sleep(2)


network_thread = threading.Thread(target=background_listener, daemon=True)
network_thread.start()

while True:
    user_input = input("Type something: ")
    print(f"You typed: {user_input}")
