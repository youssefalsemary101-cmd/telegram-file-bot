
import json
import os
import urllib.request
import urllib.parse

TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
API = f"https://api.telegram.org/bot{TOKEN}/"
STATE_FILE = "state.json"


def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, encoding="utf-8") as f:
            return json.load(f)
    return {"offset": 0, "files": []}


def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def api(method, data=None):
    payload = json.dumps(data or {}).encode()
    req = urllib.request.Request(
        API + method,
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=30) as response:
        result = json.load(response)
    if not result.get("ok"):
        raise RuntimeError("Telegram API request failed")
    return result["result"]


def send_text(chat_id, text):
    api("sendMessage", {"chat_id": chat_id, "text": text})


def process_channel_post(post, state):
    media_types = (
        "document", "video", "audio", "animation",
        "voice", "video_note", "photo"
    )

    if not any(key in post for key in media_types):
        return

    title = post.get("caption") or post.get("text") or ""

    item = {
        "chat_id": post["chat"]["id"],
        "message_id": post["message_id"],
        "title": title,
    }

    # Avoid indexing the same post twice.
    if not any(
        f["chat_id"] == item["chat_id"]
        and f["message_id"] == item["message_id"]
        for f in state["files"]
    ):
        state["files"].append(item)


def process_message(message, state):
    chat_id = message["chat"]["id"]
    text = (message.get("text") or "").strip()

    if not text:
        return

    if text.startswith("/start"):
        send_text(
            chat_id,
            "أهلاً بك في بوت البحث عن الملفات 📚\n"
            "اكتب اسم الكتاب أو المذكرة التي تبحث عنها."
        )
        return

    query = text.casefold()
    matches = [
        f for f in state["files"]
        if query in f["title"].casefold()
    ]

    if not matches:
        send_text(
            chat_id,
            "لم أجد ملفًا مطابقًا في الملفات التي فهرسها البوت حتى الآن.\n"
            "جرّب كتابة جزء أقصر من الاسم."
        )
        return

    send_text(chat_id, f"وجدت {len(matches)} نتيجة:")
    for item in matches[:5]:
        api("copyMessage", {
            "chat_id": chat_id,
            "from_chat_id": item["chat_id"],
            "message_id": item["message_id"],
        })


def main():
    state = load_state()

    # Process only updates that have not been handled yet.
    updates = api("getUpdates", {
        "offset": state["offset"],
        "timeout": 0,
        "allowed_updates": ["message", "channel_post"],
    })

    for update in updates:
        try:
            if "channel_post" in update:
                process_channel_post(update["channel_post"], state)
            elif "message" in update:
                process_message(update["message"], state)

            state["offset"] = update["update_id"] + 1
            save_state(state)

        except Exception as exc:
            # Stop without skipping the failed update.
            print("Update processing failed:", type(exc).__name__)
            raise


if __name__ == "__main__":
    main()
