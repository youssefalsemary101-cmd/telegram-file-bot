
import json
import os
import urllib.request

TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
API = f"https://api.telegram.org/bot{TOKEN}/"
STATE_FILE = "state.json"


def api(method, data=None):
    request = urllib.request.Request(
        API + method,
        data=json.dumps(data or {}).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        result = json.load(response)

    if not result.get("ok"):
        raise RuntimeError(f"Telegram API error: {method}")

    return result["result"]


def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, encoding="utf-8") as file:
            return json.load(file)

    return {"offset": 0, "files": []}


def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as file:
        json.dump(state, file, ensure_ascii=False, indent=2)


def send_text(chat_id, text):
    api("sendMessage", {
        "chat_id": chat_id,
        "text": text,
    })


def index_channel_post(post, state):
    media = None

    for kind in (
        "document", "video", "audio", "animation",
        "voice", "video_note", "photo"
    ):
        if kind in post:
            media = post[kind]
            break

    if media is None:
        return

    if isinstance(media, list):
        media = media[-1]

    caption = post.get("caption", "")
    file_name = media.get("file_name", "")
    title = f"{file_name} {caption}".strip()

    if not title:
        title = "ملف بدون اسم"

    item = {
        "chat_id": post["chat"]["id"],
        "message_id": post["message_id"],
        "title": title,
    }

    for old in state["files"]:
        if (
            old["chat_id"] == item["chat_id"]
            and old["message_id"] == item["message_id"]
        ):
            return

    state["files"].append(item)


def search_files(chat_id, query, state):
    matches = [
        item for item in state["files"]
        if query.casefold() in item["title"].casefold()
    ]

    if not matches:
        send_text(
            chat_id,
            "لم أجد الملف في الفهرس الحالي.\n"
            "جرّب اسمًا أقصر أو جزءًا من اسم الملف."
        )
        return

    send_text(chat_id, f"وجدت {len(matches)} نتيجة:")

    for item in matches[:5]:
        api("copyMessage", {
            "chat_id": chat_id,
            "from_chat_id": item["chat_id"],
            "message_id": item["message_id"],
        })


def process_message(message, state):
    chat_id = message["chat"]["id"]
    text = (message.get("text") or "").strip()

    if not text:
        return

    if text.startswith("/start"):
        send_text(
            chat_id,
            "أهلًا بك في بوت البحث عن الملفات 📚\n"
            "اكتب اسم الكتاب أو المذكرة التي تريدها."
        )
        return

    search_files(chat_id, text, state)


def main():
    state = load_state()

    updates = api("getUpdates", {
        "offset": state["offset"],
        "timeout": 0,
        "allowed_updates": ["message", "channel_post"],
    })

    for update in updates:
        if "channel_post" in update:
            index_channel_post(update["channel_post"], state)

        elif "message" in update:
            process_message(update["message"], state)

        state["offset"] = update["update_id"] + 1
        save_state(state)


if __name__ == "__main__":
    main()
