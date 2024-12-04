import discord
import os
import asyncio
import yt_dlp
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor
import tempfile

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
        print(f"Downloaded file path: {file_path}")
        return data

    async def play_next_song(guild_id, voice_client):
        """Play the next song in the queue."""
        if guild_id in song_queues and song_queues[guild_id]:
            next_song = song_queues[guild_id].pop(0)

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

                if message.guild.id not in voice_clients:
                    voice_client = await message.author.voice.channel.connect()
                    voice_clients[message.guild.id] = voice_client
                else:
                    voice_client = voice_clients[message.g
