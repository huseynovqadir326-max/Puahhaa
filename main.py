import json
import os
import random
import threading
import time
import requests
from flask import Flask

# --- TƏNZİMLƏMƏLƏR ---
TOKEN = "BURAYA_BOT_TOKENINI_YAZ"
BOT_USERNAME = (  # Başında @ olmadan botun username-i (məsələn: SevgiBotu)
    "BotunUsername_Yaz"
)
ADMIN_ID = 8875706667
URL = f"https://api.telegram.org/bot{TOKEN}"

# Qovluq və verilənlər bazası
DB_FOLDER = "database"
if not os.path.exists(DB_FOLDER):
  os.makedirs(DB_FOLDER)

USERS_FILE = os.path.join(DB_FOLDER, "users_db.json")


def load_users():
  if os.path.exists(USERS_FILE):
    with open(USERS_FILE, "r", encoding="utf-8") as f:
      try:
        return {int(k): v for k, v in json.load(f).items()}
      except:
        return {}
  return {}


def save_users():
  with open(USERS_FILE, "w", encoding="utf-8") as f:
    json.dump(users_db, f, ensure_ascii=False, indent=4)


users_db = load_users()
active_chats = {}  # {user_id: partner_id}

TASKS = [
    "Bir-birinizə 3 dənə şirin xoş söz deyin! 🥰",
    "İlk görüşünüzü harada keçirəcəyinizi planlaşdırın! ☕",
    "Bir-birinizə virtual gül və şokolad hədiyyə edin! 🌹🍫",
    "Birgə hansı romantik filmə baxacağınızı seçin! 🎬",
    "Səsli şəkildə qısa bir iltifat ünvanlayın! 🎤",
]


# Faizə görə stiker/emoji və status təyini
def get_percentage_details(percentage):
  if percentage <= 10:
    return "💀", "Aranızda buz dağları var, işiniz çətindir!"
  elif percentage <= 20:
    return "🧊", "Hələ ki soyuq münasibət, bir az qızışmaq lazımdır."
  elif percentage <= 30:
    return "🥔", "Sadəcə tanışlar kimi görünürsünüz."
  elif percentage <= 40:
    return "🍫", "Şirin ünsiyyət qurmaq üçün potensial var."
  elif percentage <= 50:
    return "⏳", "Hər şey hələ qarşıdadır, bir-birinizi kəşf edirsiniz."
  elif percentage <= 60:
    return "✨", "Pis deyil, yavaş-yavaş alınır!"
  elif percentage <= 70:
    return "💖", "Çox gözəl cütlük olarsınız!"
  elif percentage <= 80:
    return "🔥", "Aranızda əsl ehtiras və sevgi alovu yanır!"
  elif percentage <= 90:
    return "💍", "Bir-biriniz üçün yaradılmısınız, demək olar ki, kındırsınız!"
  else:
    return "👑💘", "Əfsanəvi uyğunlaşma! Ruh ikiziniz tapıldı!"


def send_message(chat_id, text, reply_markup=None):
  data = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}
  if reply_markup:
    data["reply_markup"] = json.dumps(reply_markup)
  response = requests.post(f"{URL}/sendMessage", data=data)
  return response.json()


def get_updates(offset=None):
  params = {"timeout": 30, "offset": offset}
  try:
    response = requests.get(f"{URL}/getUpdates", params=params, timeout=35)
    return response.json()
  except:
    return {}


def find_user_by_input(target):
  target = target.strip()
  if target.startswith("@"):
    target = target[1:].lower()
    for uid, data in users_db.items():
      if data.get("username", "").lower() == target:
        return uid
  else:
    try:
      uid = int(target)
      if uid in users_db:
        return uid
    except:
      pass
  return None


# --- BOTUN MƏNTİQİ ---
def run_bot():
  print("Super Sevgi botu işə düşdü...")
  offset = None
  while True:
    try:
      updates = get_updates(offset)
      if "result" in updates:
        for update in updates["result"]:
          offset = update["update_id"] + 1

          if "message" in update:
            msg = update["message"]
            chat_id = msg["chat"]["id"]
            text = msg.get("text", "")
            user_id = msg["from"]["id"]
            first_name = msg["from"].get("first_name", "İstifadəçi")
            username = msg["from"].get("username", "")
            chat_type = msg["chat"]["type"]

            if user_id in users_db:
              users_db[user_id]["name"] = first_name
              users_db[user_id]["username"] = username

            # /start əmri
            if text.startswith("/start"):
              if chat_type == "private":
                parts = text.split(" ")
                if len(parts) > 1 and parts[1].startswith("chat_"):
                  try:
                    partner_id = int(parts[1].split("_")[1])
                    if partner_id in users_db:
                      active_chats[user_id] = partner_id
                      active_chats[partner_id] = user_id
                      partner_name = users_db[partner_id]["name"]
                      send_message(
                          chat_id,
                          f"✨ **{partner_name}** ilə gizli söhbətə"
                          " qoşuldunuz!\nİndi buraya yazdığınız mesajlar birbaşa"
                          " ona gedəcək.\nÇıxmaq üçün `/qurtar` yazın.",
                      )
                      send_message(
                          partner_id,
                          f"✨ {first_name} sizinlə gizli söhbətə qoşuldu!",
                      )
                      continue
                  except:
                    pass

                if user_id not in users_db:
                  users_db[user_id] = {
                      "name": first_name,
                      "username": username,
                      "gender": None,
                  }
                  save_users()

                if users_db[user_id].get("gender") is None:
                  keyboard = {
                      "inline_keyboard": [
                          [
                              {
                                  "text": "Oğlan 👦",
                                  "callback_data": "gender_oglan",
                              },
                              {"text": "Qız 👧", "callback_data": "gender_qiz"},
                          ]
                      ]
                  }
                  send_message(
                      chat_id,
                      "Xoş gəldin! Qrupdakı sevgi oyununa qoşulmaq üçün cinsini"
                      " seç:",
                      keyboard,
                  )
                else:
                  help_text = (
                      f"👋 Salam, {first_name}!\n\n"
                      "❤️ `/sevgi` - Qrupda günün cütlüyünü tapır.\n"
                      "✉️ `/mesaj @username <mətn>` - İstənilən şəxsə mesaj"
                      " yazır.\n"
                      "🚪 `/qurtar` - Gizli söhbəti bitirir."
                  )
                  send_message(chat_id, help_text)
              else:
                help_text = (
                    "👋 Salam! Bütün özəlliklərdən yararlanmaq üçün məni şəxsi"
                    " mesajda aç:\n"
                    "❤️ `/sevgi` (Qrupda yazın)"
                )
                send_message(chat_id, help_text)

            elif text == "/qurtar":
              if chat_type == "private":
                if user_id in active_chats:
                  partner_id = active_chats[user_id]
                  del active_chats[user_id]
                  if partner_id in active_chats:
                    del active_chats[partner_id]
                  send_message(chat_id, "🔒 Gizli söhbət sonlandırıldı.")
                  send_message(
                      partner_id, "🔒 Qarşı tərəf gizli söhbəti sonlandırdı."
                  )
                else:
                  send_message(chat_id, "Aktiv gizli söhbətiniz yoxdur.")

            elif text.startswith("/mesaj"):
              if chat_type == "private":
                parts = text.split(" ", 2)
                if len(parts) < 3:
                  send_message(
                      chat_id,
                      "⚠️ Doğru format: `/mesaj @username Mətn` və ya `/mesaj"
                      " 12345678 Mətn`",
                  )
                  continue
                target_id = find_user_by_input(parts[1])
                if not target_id:
                  send_message(
                      chat_id,
                      "❌ İstifadəçi tapılmadı və ya bota start verməyib.",
                  )
                  continue
                if target_id == user_id:
                  send_message(chat_id, "Özünə mesaj göndərə bilməzsən! 😄")
                  continue

                active_chats[user_id] = target_id
                active_chats[target_id] = user_id
                send_message(
                    target_id,
                    f"📩 **Sizə yeni gizli mesaj var!**\nKimdən:"
                    f" [{first_name}](tg://user?id={user_id})\n\n>"
                    f" _{parts[2]}_",
                )
                send_message(chat_id, "✅ Mesajınız ötürüldü!")

            elif chat_type == "private" and user_id in active_chats:
              partner_id = active_chats[user_id]
              send_message(partner_id, f"💬 *{first_name}:* {text}")

            # /sevgi əmri
            elif text == "/sevgi":
              if chat_type == "private":
                send_message(
                    chat_id,
                    "Bu əmri yalnız qruplarda istifadə etmək olar! 😉",
                )
                continue

              if user_id not in users_db or users_db[user_id].get(
                  "gender"
              ) is None:
                send_message(
                    chat_id,
                    f"@{username or first_name}, səni hələ sistemdə"
                    " tapmadım! Şəxsi mesajımda `/start` yaz.",
                )
                continue

              user_gender = users_db[user_id]["gender"]
              opposite_gender = "Qız" if user_gender == "Oğlan" else "Oğlan"
              candidates = [
                  uid
                  for uid, d in users_db.items()
                  if d.get("gender") == opposite_gender and uid != user_id
              ]
              if not candidates:
                send_message(
                    chat_id,
                    "Təəssüf ki, qrupda əks cinsdən başqa qeydiyyatdan keçən"
                    " yoxdur! 😢",
                )
                continue

              partner_id = random.choice(candidates)
              partner_name = users_db[partner_id]["name"]

              # 0% - 99% arası faiz təyini
              percentage = random.randint(0, 99)
              sticker_emoji, status = get_percentage_details(percentage)
              task = random.choice(TASKS)

              # Qrup üçün düymə
              group_keyboard = {
                  "inline_keyboard": [
                      [
                          {
                              "text": "💬 Gizli Yazış",
                              "url": f"https://t.me/{BOT_USERNAME}?start=chat_{user_id}",
                          }
                      ]
                  ]
              }

              result_text = (
                  f"💘 **Günün Cütlüyü Elan Olunur!** 💘\n\n👤"
                  f" [{first_name}](tg://user?id={user_id}) 🤝"
                  f" [{partner_name}](tg://user?id={partner_id})\n\n{sticker_emoji}"
                  f" Uyğunlaşma Faiziniz: **%{percentage}**\n💬 **Rəy:**"
                  f" _{status}_\n🎯 **Tapşırıq:**\n_{task}_"
              )
              send_message(chat_id, result_text, reply_markup=group_keyboard)

              # ⭐ YENİLİK: Qarşı tərəfin (partnerin) şəxsi mesajına xəbərdarlıq göndərmək
              partner_keyboard = {
                  "inline_keyboard": [
                      [
                          {
                              "text": "💬 Gizli Yazış",
                              "url": f"https://t.me/{BOT_USERNAME}?start=chat_{user_id}",
                          }
                      ]
                  ]
              }
              private_notification = (
                  f"🎉 **Təbriklər! Sənin sevgilin tapıldı!** ❤️️\n\n"
                  f"Qrupda keçirilən sevgi testində səni"
                  f" [{first_name}](tg://user?id={user_id}) ilə uyğunlaşdırdılar!\n"
                  f"Uyğunlaşma Faiziniz: {sticker_emoji} **%{percentage}**\n\n"
                  "Birbaşa əlaqə qurmaq üçün aşağıdakı düyməyə basa"
                  " bilərsən:"
              )
              send_message(
                  partner_id,
                  private_notification,
                  reply_markup=partner_keyboard,
              )

          elif "callback_query" in update:
            query = update["callback_query"]
            user_id = query["from"]["id"]
            first_name = query["from"].get("first_name", "İstifadəçi")
            username = query["from"].get("username", "")
            data = query["data"]
            chat_id = query["message"]["chat"]["id"]
            message_id = query["message"]["message_id"]

            if data.startswith("gender_"):
              gender = "Oğlan" if data == "gender_oglan" else "Qız"
              if user_id not in users_db:
                users_db[user_id] = {}
              users_db[user_id]["name"] = first_name
              users_db[user_id]["username"] = username
              users_db[user_id]["gender"] = gender
              save_users()

              requests.post(
                  f"{URL}/editMessageText",
                  data={
                      "chat_id": chat_id,
                      "message_id": message_id,
                      "text": (
                          f"Təbriklər, uğurla qeydiyyatdan keçdin! ✨\nAdın:"
                          f" {first_name}\nCinsin: {gender}\n\nİndi hər şey"
                          " hazırdır!"
                      ),
                  },
              )
    except Exception as e:
      print(f"Xəta: {e}")
      time.sleep(3)


# --- FLASK SERVER ---
app = Flask(__name__)


@app.route("/")
def home():
  return "Super Sevgi Botu aktivdir! 🚀"


if __name__ == "__main__":
  t = threading.Thread(target=run_bot)
  t.daemon = True
  t.start()

  app.run(host="0.0.0.0", port=8080)
  