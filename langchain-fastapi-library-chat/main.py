"""Boot the server, play scripted visitor conversations through POST /chat, shut down."""
import threading
import time

import httpx
import uvicorn

PORT = 4170

CONVERSATIONS = {
    "visitor-cozy-weekend": [
        "Hi! I want something cozy and small-town for a snowy weekend.",
        "Anything less romantic? More of a mystery.",
        "Is the first one you mentioned on the shelf right now?",
    ],
    "visitor-kids-science": [
        "Do you have science books for my 8 year old?",
        "She also likes dragons. Anything funny?",
        "Thanks! What about something for me, with maps and history?",
    ],
}


def main() -> None:
    server = uvicorn.Server(uvicorn.Config("app:app", port=PORT, log_level="warning"))
    threading.Thread(target=server.run, daemon=True).start()
    while not server.started:
        time.sleep(0.1)
    try:
        with httpx.Client(base_url=f"http://127.0.0.1:{PORT}", timeout=60) as client:
            for session_id, turns in CONVERSATIONS.items():
                print(f"\n=== {session_id} ===")
                for text in turns:
                    reply = client.post("/chat", json={"message": text, "session_id": session_id})
                    reply.raise_for_status()
                    print(f"visitor: {text}\nMarlow:  {reply.json()['reply']}\n")
    finally:
        server.should_exit = True
        time.sleep(0.5)


if __name__ == "__main__":
    main()
