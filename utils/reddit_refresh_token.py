import random
import socket
import sys

import praw

from config import REDDIT_CONFIG

REDIRECT_URI = 'http://localhost:8080/'
DURATION = 'permanent'
SCOPES = ["read"]
STATE = str(random.randint(0, 65000))


def main():
    """Provide the program's entry point when directly executed."""

    reddit = praw.Reddit(
        client_id=REDDIT_CONFIG.client_id,
        client_secret=REDDIT_CONFIG.client_secret,
        redirect_uri=REDIRECT_URI,
        user_agent=f"get refresh token/v0 by u/{REDDIT_CONFIG.username}",
    )
    url = reddit.auth.url(duration=DURATION, scopes=SCOPES, state=STATE)
    print(f"Now open this url in your browser: {url}")

    client = receive_connection()
    data = client.recv(1024).decode("utf-8")
    print(data)
    print("_" * 80)
    param_tokens = data.split(" ", 2)[1].split("?", 1)[1].split("&")
    params = {
        key: value for (key, value) in [token.split("=") for token in param_tokens]
    }

    refresh_token = reddit.auth.authorize(params["code"])
    send_message(client, f"Refresh token: {refresh_token}")
    return 0


def receive_connection():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(("localhost", 8080))
    server.listen(1)
    client = server.accept()[0]
    server.close()
    return client


def send_message(client, message):
    """Send message to client and close the connection."""
    print(message)
    print("_" * 80)
    client.send(f"HTTP/1.1 200 OK\r\n\r\n{message}".encode("utf-8"))
    client.close()


if __name__ == "__main__":
    sys.exit(main())
