import os
import discord
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv
import yt_dlp
from collections import deque
import asyncio

# Environment variables for tokens and other sensitive data
load_dotenv()
TOKEN = "YOUR_BOT_TOKEN" # Replace with your actual bot token
GUILD_ID = YOUR_GUILD_ID  # Replace with your actual guild ID

SONG_QUEUES = {}
LOOP_STATES = {} 

async def search_ytdlp_async(query, ydl_opts):
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, lambda: _extract(query, ydl_opts))

def _extract(query, ydl_opts):
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        return ydl.extract_info(query, download=False)

# Setup of intents. Intents are permissions the bot has on the server
intents = discord.Intents.default()
intents.message_content = True

# Bot setup
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"{bot.user} is online!")

@bot.tree.command(name="skip", description="Skips the current playing song")
async def skip(interaction: discord.Interaction):
    if interaction.guild.voice_client and (interaction.guild.voice_client.is_playing() or interaction.guild.voice_client.is_paused()):
        interaction.guild.voice_client.stop()
        await interaction.response.send_message("Skipped the current song.")
    else:
        await interaction.response.send_message("Not playing anything to skip.")

@bot.tree.command(name="pause", description="Pause the currently playing song.")
async def pause(interaction: discord.Interaction):
    voice_client = interaction.guild.voice_client
    if voice_client is None:
        return await interaction.response.send_message("I'm not in a voice channel.")
    if not voice_client.is_playing():
        return await interaction.response.send_message("Nothing is currently playing.")
    voice_client.pause()
    await interaction.response.send_message("Playback paused!")

@bot.tree.command(name="resume", description="Resume the currently paused song.")
async def resume(interaction: discord.Interaction):
    voice_client = interaction.guild.voice_client
    if voice_client is None:
        return await interaction.response.send_message("I'm not in a voice channel.")
    if not voice_client.is_paused():
        return await interaction.response.send_message("I’m not paused right now.")
    voice_client.resume()
    await interaction.response.send_message("Playback resumed!")

@bot.tree.command(name="stop", description="Stop playback and clear the queue.")
async def stop(interaction: discord.Interaction):
    voice_client = interaction.guild.voice_client
    if not voice_client or not voice_client.is_connected():
        return await interaction.response.send_message("I'm not connected to any voice channel.")
    guild_id_str = str(interaction.guild_id)
    if guild_id_str in SONG_QUEUES:
        SONG_QUEUES[guild_id_str].clear()
    if voice_client.is_playing() or voice_client.is_paused():
        voice_client.stop()
    await voice_client.disconnect()
    await interaction.response.send_message("Stopped playback and disconnected!")

@bot.tree.command(name="loop", description="Toggle looping of the current song.")
async def loop(interaction: discord.Interaction):
    guild_id = str(interaction.guild_id)
    current_state = LOOP_STATES.get(guild_id, False)
    LOOP_STATES[guild_id] = not current_state
    state_str = "enabled" if LOOP_STATES[guild_id] else "disabled"
    await interaction.response.send_message(f"Looping is now **{state_str}**.")

@bot.tree.command(name="loopqueue", description="Toggle looping the entire queue.")
async def loopqueue(interaction: discord.Interaction):
    guild_id = str(interaction.guild_id)
    current_state = LOOP_QUEUE_STATES.get(guild_id, False)
    LOOP_QUEUE_STATES[guild_id] = not current_state
    state_str = "enabled" if LOOP_QUEUE_STATES[guild_id] else "disabled"
    await interaction.response.send_message(f"Queue looping is now **{state_str}**.")

@bot.tree.command(name="play", description="Play a song or add it to the queue.")
@app_commands.describe(song_query="Search query or direct YouTube URL")
async def play(interaction: discord.Interaction, song_query: str):
    await interaction.response.defer()

    voice_channel = interaction.user.voice.channel
    if voice_channel is None:
        await interaction.followup.send("You must be in a voice channel.")
        return

    voice_client = interaction.guild.voice_client
    if voice_client is None:
        voice_client = await voice_channel.connect()
    elif voice_channel != voice_client.channel:
        await voice_client.move_to(voice_channel)

    ydl_options = {
        "format": "bestaudio/best",
        "noplaylist": True,
        "youtube_include_dash_manifest": False,
        "youtube_include_hls_manifest": False,
        "default_search": "ytsearch",
    }

    # Check if input is URL or search query
    if song_query.startswith("http"):
        query = song_query
    else:
        query = "ytsearch1: " + song_query

    results = await search_ytdlp_async(query, ydl_options)

    # Handle if it's a direct video (no entries list)
    if "entries" in results and results["entries"]:
        first_track = results["entries"][0]
    else:
        first_track = results

    audio_url = first_track["url"]
    title = first_track.get("title", "Untitled")

    guild_id = str(interaction.guild_id)
    if SONG_QUEUES.get(guild_id) is None:
        SONG_QUEUES[guild_id] = deque()

    SONG_QUEUES[guild_id].append((audio_url, title))

    if voice_client.is_playing() or voice_client.is_paused():
        await interaction.followup.send(f"Added to queue: **{title}**")
    else:
        await interaction.followup.send(f"Now playing: **{title}**")
        await play_next_song(voice_client, guild_id, interaction.channel)


@bot.tree.command(name="playlist", description="Play a full YouTube playlist.")
@app_commands.describe(playlist_url="YouTube playlist URL or search query")
async def playlist(interaction: discord.Interaction, playlist_url: str):
    await interaction.response.defer()
    voice_channel = interaction.user.voice.channel
    if voice_channel is None:
        await interaction.followup.send("You must be in a voice channel.")
        return
    voice_client = interaction.guild.voice_client
    if voice_client is None:
        voice_client = await voice_channel.connect()
    elif voice_channel != voice_client.channel:
        await voice_client.move_to(voice_channel)

    ydl_options = {
        "format": "bestaudio/best",
        "noplaylist": False,
        "youtube_include_dash_manifest": False,
        "youtube_include_hls_manifest": False,
    }

    results = await search_ytdlp_async(playlist_url, ydl_options)
    entries = results.get("entries", [])
    if not entries:
        await interaction.followup.send("No songs found in the playlist.")
        return

    guild_id = str(interaction.guild_id)
    if SONG_QUEUES.get(guild_id) is None:
        SONG_QUEUES[guild_id] = deque()
    for entry in entries:
        audio_url = entry["url"]
        title = entry.get("title", "Untitled")
        SONG_QUEUES[guild_id].append((audio_url, title))

    await interaction.followup.send(f"Added **{len(entries)}** songs to the queue.")
    if not (voice_client.is_playing() or voice_client.is_paused()):
        await play_next_song(voice_client, guild_id, interaction.channel)

async def play_next_song(voice_client, guild_id, channel):
    if SONG_QUEUES[guild_id]:
        audio_url, title = SONG_QUEUES[guild_id].popleft()
        ffmpeg_options = {
            "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
            "options": "-vn",
        }
        source = discord.FFmpegPCMAudio(audio_url, **ffmpeg_options)
        def after_play(error):
            if error:
                print(f"Error playing {title}: {error}")
            if LOOP_STATES.get(guild_id, False):
                SONG_QUEUES[guild_id].appendleft((audio_url, title))
            asyncio.run_coroutine_threadsafe(play_next_song(voice_client, guild_id, channel), bot.loop)
        voice_client.play(source, after=after_play)
        asyncio.create_task(channel.send(f"Now playing: **{title}**"))
    else:
        await voice_client.disconnect()
        SONG_QUEUES[guild_id] = deque()

bot.run(TOKEN)
