import discord
import os
import asyncio
import yt_dlp
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor
import tempfile  # For temporary audio storage

def run_bot():
    load_dotenv()
    TOKEN = os.getenv('discord_token')
    intents = discord.Intents.default()
    intents.message_content = True
    intents.voice_states = True  # Ensure voice intents are enabled
    client = discord.Client(intents=intents)

    voice_clients = {}
    song_queues = {}
    yt_dlp_options = {
        "format": "bestaudio/best",
        "outtmpl": tempfile.gettempdir() + "/%(id)s.%(ext)s",  # Save to temp directory
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }],
        "quiet": True,  # Suppress yt_dlp logs
        "cookiefile": "/home/ec2-user/music_bot/cookies.txt",  # Required for YouTube
    }
    ytdl = yt_dlp.YoutubeDL(yt_dlp_options)
    ffmpeg_options = {'options': '-vn'}
    executor = ThreadPoolExecutor()

    async def download_song(url):
        """Download a song or playlist using yt_dlp."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(executor, lambda: ytdl.extract_info(url, download=True))

    async def play_next_song(guild_id, voice_client):
        """Play the next song in the queue."""
        if guild_id in song_queues and song_queues[guild_id]:
            next_song = song_queues[guild_id].pop(0)

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
                await text_channel.send(f"Now casting: {next_song['title']}")

    async def get_text_channel(guild_id):
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
                await message.channel.send("You must be in a voice channel to cast Fire 4!")
                return

            try:
                url = message.content.split()[1]

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
                await message.channel.send("There was an error trying to process the request.")

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
