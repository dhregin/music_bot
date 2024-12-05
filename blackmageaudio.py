import discord
import os
import asyncio
import yt_dlp
import subprocess
from cookies import login_youtube
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor
import tempfile


def update_cookies_if_needed():
    try:
        cookies_last_updated = "/home/ec2-user/music_bot/cookies_last_updated.txt"
        if not os.path.exists(cookies_last_updated):
            print("Cookies timestamp not found. Updating cookies.")
            login_youtube()
        else:
            with open(cookies_last_updated, "r") as f:
                last_updated = datetime.fromisoformat(f.read().strip())
            # Refresh cookies if older than 12 hours
            if (datetime.utcnow() - last_updated).total_seconds() > 43200:
                print("Cookies are older than 12 hours. Updating cookies.")
                login_youtube()
            else:
                print("Cookies are up-to-date.")
    except Exception as e:
        print(f"Error in update_cookies_if_needed: {e}")

        
def run_bot():
    # Load environment variables
    load_dotenv(dotenv_path="/home/ec2-user/music_bot/.env")
    TOKEN = os.getenv('discord_token')

    if not TOKEN:
        print("Error: Discord token not found in .env file.")
        return

    # Discord bot setup
    intents = discord.Intents.default()
    intents.message_content = True
    intents.voice_states = True
    client = discord.Client(intents=intents)

    # Variables for song queues and voice clients
    voice_clients = {}
    song_queues = {}

    # yt_dlp options for downloading and cookies handling
    yt_dlp_options = {
        "format": "bestaudio/best",
        "outtmpl": tempfile.gettempdir() + "/%(id)s.%(ext)s",
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }
        ],
        "quiet": True,
        "cookiefile": "/home/ec2-user/music_bot/cookies.txt",
    }
    ytdl = yt_dlp.YoutubeDL(yt_dlp_options)
    ffmpeg_options = {'options': '-vn'}

    # Executor for handling downloads
    executor = ThreadPoolExecutor(max_workers=5)

    async def download_song(url):
        """Download a song or playlist using yt_dlp."""
        loop = asyncio.get_event_loop()
        data = await loop.run_in_executor(executor, lambda: ytdl.extract_info(url, download=True))
        file_path = ytdl.prepare_filename(data)
        
        if not file_path.endswith(".mp3"):
            file_path = file_path.rsplit(".", 1)[0] + ".mp3"
            
        print(f"Downloaded file path: {file_path}")
        return {
        "file": file_path,
        "title": data.get("title", "Unknown Title"),
    }

    async def play_next_song(guild_id, voice_client):
        """Play the next song in the queue."""
        if guild_id in song_queues and song_queues[guild_id]:
            next_song = song_queues[guild_id].pop(0)
            file_path = nexts_song["file"]

            # Debugging: Check the file path
            print(f"Attempting to play file: {next_song['file']}")

            if not os.path.exists(next_song["file"]):
                print(f"Error: File not found - {next_song['file']}")
                return

            player = discord.FFmpegPCMAudio(next_song["file"], **ffmpeg_options)
            voice_client.play(player, after=lambda e: asyncio.run_coroutine_threadsafe(
                play_next_song(guild_id, voice_client), client.loop
            ))

            try:
                os.remove(next_song["file"])
                print(f"Deleted temporary file: {next_song['file']}")
            except Exception as e:
                print(f"Error deleting file: {e}")

            text_channel = await get_text_channel(guild_id)
            if text_channel:
                await text_channel.send(f"Now playing: {next_song['title']}")

    async def get_text_channel(guild_id):
        """Find a text channel in the guild where the bot can send messages."""
        guild = client.get_guild(guild_id)
        if guild:
            for channel in guild.text_channels:
                if channel.permissions_for(guild.me).send_messages:
                    return channel
        return None

    @client.event
    async def on_message(message):
        if message.author.bot:
            return

        if message.content.startswith("?play"):
            if not message.author.voice or not message.author.voice.channel:
                await message.channel.send("You must be in a voice channel to use `?play`!")
                return

            try:
                url = message.content.split()[1]
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(None, update_cookies_if_needed)

                if message.guild.id not in voice_clients:
                    voice_client = await message.author.voice.channel.connect()
                    voice_clients[message.guild.id] = voice_client
                else:
                    voice_client = voice_clients[message.guild.id]

                if message.guild.id not in song_queues:
                    song_queues[message.guild.id] = []

                data = await download_song(url)

                if "entries" in data:
                    await message.channel.send(f"Found a playlist with {len(data['entries'])} songs. Queuing them...")
                    for entry in data["entries"]:
                        song = {
                            "file": ytdl.prepare_filename(entry),
                            "title": entry.get("title", "Unknown Title")
                        }
                        song_queues[message.guild.id].append(song)
                else:
                    song = {
                        "file": ytdl.prepare_filename(data),
                        "title": data.get("title", "Unknown Title")
                    }
                    song_queues[message.guild.id].append(song)

                if not voice_client.is_playing():
                    await play_next_song(message.guild.id, voice_client)
                else:
                    await message.channel.send(f"Added to queue: {song['title']}")

            except Exception as e:
                print(f"Error in ?play: {e}")
                await message.channel.send("There was an error processing your request.")

        if message.content.startswith("?pause"):
            try:
                if message.guild.id in voice_clients and voice_clients[message.guild.id].is_playing():
                    voice_clients[message.guild.id].pause()
                    await message.channel.send("Playback paused.")
                else:
                    await message.channel.send("No audio is playing.")
            except Exception as e:
                print(f"Error in ?pause: {e}")

        if message.content.startswith("?resume"):
            try:
                if message.guild.id in voice_clients and voice_clients[message.guild.id].is_paused():
                    voice_clients[message.guild.id].resume()
                    await message.channel.send("Playback resumed.")
                else:
                    await message.channel.send("Audio is not paused.")
            except Exception as e:
                print(f"Error in ?resume: {e}")

        if message.content.startswith("?stop"):
            try:
                if message.guild.id in voice_clients:
                    voice_clients[message.guild.id].stop()
                    await voice_clients[message.guild.id].disconnect()
                    del voice_clients[message.guild.id]
                    song_queues.pop(message.guild.id, None)
                    await message.channel.send("Playback stopped and disconnected.")
                else:
                    await message.channel.send("I'm not in a voice channel.")
            except Exception as e:
                print(f"Error in ?stop: {e}")

    client.run(TOKEN)
