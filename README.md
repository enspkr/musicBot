# Discord Music Bot (Upgraded Version)

🎵 This is an upgraded version of an existing Discord music bot project.
I added new features and improved the bot to better suit my needs, while keeping the core functionality of the original project.

It’s built with **discord.py** and **yt-dlp** and includes features like queueing, playlist support, single/queue looping, and more!

## 🚀 Features
✅ Play music from YouTube links or search queries
✅ Play entire YouTube playlists
✅ Toggle loop for single songs
✅ Toggle loop for the entire queue
✅ Pause, resume, skip, and stop playback
✅ Works directly in your Discord server with slash commands

## 📦 Requirements
- Python 3.8+
- ffmpeg (installed and added to your PATH) https://www.ffmpeg.org/download.html

Install dependencies:
```bash
pip install -r requirements.txt
```

## 🏁 How to Run
```bash
python discord_bot_final.py
```

Make sure to **configure your bot token and the guild_id** in the `.py` file:
```
TOKEN = "YOUR_BOT_TOKEN"
GUILD_ID = YOUR_GUILD_ID
```

## ⚙️ Slash Commands Available
- `/play` – Play a song or add to the queue
- `/playlist` – Play a full YouTube playlist
- `/pause` – Pause playback
- `/resume` – Resume playback
- `/skip` – Skip the current song
- `/stop` – Stop playback and clear the queue
- `/loop` – Toggle looping the current song
- `/loopqueue` – Toggle looping the queue
- `/loopstatus` – Show loop status

## 🛠️ Contributing
Feel free to fork this project and submit a pull request if you’d like to add features or improvements!

---

Enjoy your music! 🎶
