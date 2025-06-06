﻿# Pong-sockets

This project is a networked version of the classic **Pong** game, implemented in **Python** using **UDP sockets** and **Pygame**. The game runs in real-time between two players and is coordinated by a central server.

## 📦 Technologies Used

- Python 3
- Pygame
- UDP Sockets (`socket` module)
- Multithreading (`threading` module)

## 🚀 Features

- Real-time two-player gameplay over a local network.
- Automatic countdown before the game starts.
- Centralized collision detection, ball movement, and scoring.
- Win detection with end-of-game message.
- Smooth graphics and controls using Pygame.
- UDP-based low-latency networking.

## 🧠 How It Works

- The **server** handles all the game logic: ball movement, paddle positions, score tracking, collision detection, and winner announcement.
- Each **client** connects to the server, renders the game with `Pygame`, and sends player input (up/down movement).
- The server constantly updates both clients with the current game state.

## ▶️ How to Run

### 1. Clone the Repository
```bash
git clone https://github.com/Andypj004/pong-sockets.git
cd pong-sockets
```

### 2. Install Dependencies
```bash
pip install pygame
```

### 3. Start the Server
```bash
python server.py
```

### 4. Start the Clients
- In two separate terminals or on different devices connected to the same local network:
```bash
python client.py
```

- By default, the clients connect to localhost, but you can change the IP to the server's IP address for LAN play.

## 🕹️ Controls

- Player 1: W (up), S (down)
- Player 2: Arrow ↑ (up), Arrow ↓ (down)

## ⚠️ Notes

- The game will not start until both players are connected.
- A countdown is shown once both players are ready.
- The game ends when a player reaches the winning score (default: 5 points).
- Smooth synchronization depends on local network speed and stability.
