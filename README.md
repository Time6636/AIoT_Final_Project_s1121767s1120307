# Smart Energy-Efficient Air Conditioning Advisor System

## Project Overview
This project is an AIoT-based indoor environment monitoring system using Raspberry Pi 5 and a DHT11 sensor. The system measures temperature and humidity, stores data in SQLite, displays information on an LCD, visualizes historical data through Node-RED Dashboard, and provides environmental information through a LINE Bot.

## Hardware
- Raspberry Pi 5
- DHT11 Temperature and Humidity Sensor
- LCD Display (I2C)
- Breadboard and Jumper Wires

## Software
- Python
- SQLite
- Node-RED
- LINE Messaging API
- Ngrok

## Features
- Real-time temperature monitoring
- Real-time humidity monitoring
- LCD status display
- SQLite data storage
- Node-RED dashboard visualization
- LINE Bot query service
- Air conditioning usage recommendations

## Installation

### Install Python Packages

```bash
pip install adafruit-circuitpython-dht
pip install RPLCD
pip install flask
pip install line-bot-sdk
```

### Run the Main Program

```bash
python mainproject.py
```

### Node-RED

Import the file:

```text
flows.json
```

into Node-RED and deploy.

## LINE Bot Commands

- temp
- hum
- status

## Authors

- 林珮暄 (1120307)
- 岸珠杏 (1121767)

## Course

EEB340A AIoT Fundamentals  
Yuan Ze University
