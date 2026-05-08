# 📺 LG webOS TV Timer (lg-webos-timer)

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.8%2B-brightgreen)
![Platform](https://img.shields.io/badge/platform-Termux%20%7C%20Linux%20%7C%20Raspberry%20Pi-lightgrey)

A lightweight Flask-based Web UI and CLI tool that lets you set screen-time limits and remotely power off LG webOS Smart TVs over your local network.

> Built for students, families, and productivity-focused users who want a simple way to control TV usage without extra hardware.

**Made By Aryan**

---

# ✨ Overview

LG webOS TVs are excellent for streaming, but they lack proper built-in usage management features. There is no easy way to enforce app limits, study sessions, bedtime restrictions, or viewing timers like modern smartphones.

This project solves that problem by using the official `pywebostv` API to send a graceful software-level shutdown command to your TV after a custom countdown expires.

Instead of cutting physical power using risky smart switches or DIY hardware mods, this tool safely powers off the TV using the TV's own network API.

---

# 🎯 Why Use This?

## 📚 Students

* Prevent accidental YouTube or Netflix binge sessions.
* Create focused study blocks with automatic shutdown timers.
* Reduce distractions during late-night study sessions.

## 👨‍👩‍👧 Families

* Set viewing limits for children.
* Create bedtime TV timers.
* Allow non-technical family members to use a simple browser interface.

## 🔋 Low Power & Budget Friendly

* No dedicated server required.
* Works perfectly on:

  * Android phones using Termux
  * Raspberry Pi
  * Linux laptops/desktops
  * Home mini servers

---

# 🛠️ Features

## 🌐 Modern Web Dashboard

A responsive Tailwind CSS powered UI accessible from any phone or computer on your local network.

## ⏳ Background Countdown

The timer continues running even if you close the browser.

## 🔐 Security Focused

Includes:

* Login authentication
* CSRF protection
* Safe Jinja2 rendering
* Local-only network usage

Default credentials:

```txt
Username: admin
Password: admin123
```

Password can be changed directly from:

```txt
auth.txt
```

> Change the default password before exposing the panel to other users.

## 🔄 Persistent TV Pairing

The TV pairing token is stored locally inside:

```txt
.tv_key.json
```

TV IP configuration is stored inside:

```txt
tv_config.json
```

You can also change the TV IP directly from the web panel without editing files manually.

## 📱 Mobile Friendly

Optimized for smartphones and lightweight browsers.

## 🧩 CLI + Web Support

Can be used both:

* Through the browser dashboard
* Directly from the terminal

---

# 🧠 How It Works

The tool communicates with your LG webOS TV using the local network API exposed by webOS.

Flow:

```text
User Sets Timer
        ↓
Flask Server Starts Countdown
        ↓
Countdown Expires
        ↓
pywebostv Sends Power-Off Command
        ↓
TV Gracefully Shuts Down
```

No cloud services are used.
No external API calls are made.
Everything stays inside your local network.

---

# 🚀 Installation

## 📋 Prerequisites

### 1. Enable Network Control on the TV

On your LG webOS TV:

```text
Settings → General → Network
```

OR on some models:

```text
Settings → Devices → External Devices
```

Enable:

```text
LG Connect Apps
```

or

```text
TV On With Mobile
```

> This step is mandatory.

---

### 2. Ensure Same Network

The TV and the device running the script must be connected to the same:

* Wi-Fi network
* Mobile hotspot
* Local LAN

---

# ⚙️ Setup

## 🐧 Linux / Raspberry Pi / Termux

### Clone the repository

```bash
git clone https://github.com/yourusername/lg-webos-timer.git
cd lg-webos-timer
```

### Install dependencies

```bash
pip install -r requirements.txt
```

### Start the server

```bash
python3 main.py
```

---

# 📱 Running on Android with Termux

This project works extremely well on old Android devices.

## Install Termux

Recommended source:

* F-Droid version of Termux

## Install Python

```bash
pkg update && pkg upgrade
pkg install python git
```

## Prevent Android from Killing the Timer

Before starting the server:

```bash
termux-wake-lock
```

This prevents Android battery optimization from stopping the countdown while the screen is off.

---

# 🌍 Accessing the Web Panel

After starting the Flask server, open:

```text
http://YOUR_LOCAL_IP:5000
```

Example:

```text
http://192.168.1.5:5000
```

Anyone on the same local network can access the dashboard using their browser.

---

# 🔒 HTTPS Support

By default, Flask runs over HTTP.

For most local home networks this is acceptable, but if you want encrypted HTTPS access without dealing with self-signed certificates directly inside Flask, you can use an external HTTPS reverse proxy.

Suggested companion project:

[https://github.com/giriaryan694-a11y/http2https](https://github.com/giriaryan694-a11y/http2https)

Run:

* `lg-webos-timer` on port `5000`
* HTTPS proxy in front of it

This gives you secure encrypted local access.

---

# 🔐 Security Notes

Although this project is designed for local networks, basic security practices are still important.

Recommendations:

* Change default credentials
* Do not expose the Flask port directly to the internet
* Use HTTPS if accessing from shared networks
* Keep your TV and Python dependencies updated

---

# 🧪 Example Use Cases

## 🎓 Study Session

Set a 45-minute TV timer before studying.
When the timer ends, the TV automatically shuts down.

## 👶 Kids Screen Time

Parents can enforce strict bedtime viewing limits remotely.

## 💤 Sleep Timer

Fall asleep watching content without leaving the TV running overnight.

## 🏠 Shared Living Spaces

Roommates can schedule shared usage limits fairly.

---

# ⚡ Tech Stack

* Python 3
* Flask
* pywebostv
* Tailwind CSS
* HTML/Jinja2

---

# 📜 License

This project is licensed under the MIT License.

See the `LICENSE` file for more information.

---

# ⚠️ Disclaimer

This tool is intended for:

* Educational use
* Personal automation
* Local network device management

The project:

* Does NOT bypass TV security
* Does NOT collect analytics
* Does NOT send data externally
* Only interacts with devices on your own local network

Use responsibly.

---

# 👨‍💻 Author

**Aryan**

Built to make screen-time control simple, lightweight, and accessible without expensive hardware.
