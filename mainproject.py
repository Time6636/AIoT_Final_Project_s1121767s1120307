#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import time
import logging
import threading
import sqlite3
from datetime import datetime

from dotenv import load_dotenv
from flask import Flask, request, abort

from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

import board
import adafruit_dht

DB_PATH = "sensor.db"

# LCD
import lcd_driver   # 同じフォルダに lcd_driver.py を置く

# ------------------ 初始設定 ------------------ #

load_dotenv()

CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")

if not CHANNEL_ACCESS_TOKEN or not CHANNEL_SECRET:
    print("請先在 .env 中設定 LINE_CHANNEL_ACCESS_TOKEN 和 LINE_CHANNEL_SECRET")
    sys.exit(1)

line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)

logging.basicConfig(level=logging.INFO)

app = Flask(__name__)

# DHT11 接在 GPIO24
dht_device = adafruit_dht.DHT11(board.D24)

# LCD 初始化
lcd = lcd_driver.LCD(i2c_addr=0x27)


# ------------------ 判斷狀態 ------------------ #

def get_status(temp, hum):
    if hum > 70:
        return "Too Humid"
    elif hum < 40:
        return "Too Dry"
    elif temp > 28:
        return "Too Hot"
    elif temp < 24:
        return "Too Cold"
    else:
        return "Comfortable"

# ------------------ 判斷建議 ------------------ #
def get_advice(temp, hum):
    if hum > 70:
        return "Use Dry Mode"
    elif hum < 40:
        return "Use Humidifier"
    elif temp > 28:
        return "Turn On AC"
    elif temp < 24:
        return "Increase Room Temp"
    else:
        return "No Action Needed"

# ------------------ DHT11 讀取 ------------------ #

def read_temperature_and_humidity():
    try:
        temperature_c = dht_device.temperature
        humidity = dht_device.humidity

        print(f"Temperature: {temperature_c:.1f}°C")
        print(f"Humidity: {humidity:.1f}%")

        if temperature_c is None or humidity is None:
            return None, None, "DHT11 read failed", "Check Sensor"

        status = get_status(temperature_c, humidity)
        advice = get_advice(temperature_c, humidity)

        return temperature_c, humidity, status, advice

    except Exception as e:
        logging.warning(f"DHT11 讀取錯誤：{e}")
        return None, None, "Sensor Error", "Check Sensor"

# ------------------ SQL Lite ------------------ #
def init_db():
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS sensor_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            temperature REAL,
            humidity REAL,
            status TEXT,
            advice TEXT
        )
    """)

    con.commit()
    con.close()

def save_to_db(temp, hum, status, advice):
    if temp is None or hum is None:
        return

    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()

    cur.execute("""
            INSERT INTO sensor_data
            (timestamp, temperature, humidity, status, advice)
            VALUES (?, ?, ?, ?, ?)
        """, (
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            temp,
            hum,
            status,
            advice
        ))

    con.commit()
    con.close()  

# ------------------ LCD 顯示 ------------------ #

def update_lcd(temp, hum, status):
    lcd.clear()

    if temp is None or hum is None:
        lcd.message("Sensor Error", 1)
        lcd.message("Try again", 2)
    else:
        lcd.message(f"T:{temp:.1f}C H:{hum:.0f}%", 1)
        lcd.message(status[:16], 2)

def lcd_loop():
    while True:
        temp, hum, status, advice = read_temperature_and_humidity()

        update_lcd(temp, hum, status)

        save_to_db(temp, hum, status, advice)

        time.sleep(60)


# ------------------ Flask 路由 ------------------ #

@app.route("/", methods=["GET"])
def index():
    return "LINE Bot is running.", 200


@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers.get("X-Line-Signature", "")
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return "OK"


# ------------------ LINE 事件處理 ------------------ #

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_text = event.message.text.strip().lower()

    temp, hum, status, advice = read_temperature_and_humidity()
    update_lcd(temp, hum, status)

    if temp is None or hum is None:
        reply_text = "DHT11 讀取失敗，請稍後再試一次。"

    elif user_text == "temp" or user_text == "溫度":
        reply_text = f"溫度: {temp:.1f}°C"

    elif user_text == "hum" or user_text == "濕度":
        reply_text = f"濕度: {hum:.1f}%RH"

    elif user_text == "status" or user_text == "狀態" or user_text == "advice" or user_text == "建議":
        reply_text = (
            f"目前溫度：{temp:.1f}°C\n"
            f"目前濕度：{hum:.1f}%RH\n"
            f"狀態：{status}\n"
            f"建議：{advice}"
        )

    else:
        reply_text = (
            "可用指令：\n"
            "- temp / 溫度：查看目前溫度\n"
            "- hum / 濕度：查看目前濕度\n"
            "- status / 狀態：查看目前狀態與建議"
        )

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply_text)
    )


# ------------------ 主程式 ------------------ #

if __name__ == "__main__":

    init_db()

    threading.Thread(
        target=lcd_loop,
        daemon=True
    ).start()

    app.run(host="0.0.0.0", port=5001)