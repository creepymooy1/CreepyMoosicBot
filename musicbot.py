import os
import discord
from discord.ext import commands
from discord import Embed
import yt_dlp
import re
import asyncio
from youtube_search import YoutubeSearch

intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents)

currently_playing = {}
song_queue = {}
bot.search_results = {}

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')

@bot.command()
async def removequeue(ctx, number: int):
    guild_id = ctx.guild.id
    if guild_id in song_queue and 1 < number <= len(song_queue[guild_id]):
        removed_song = song_queue[guild_id].pop(number - 1)
        await ctx.send(f"Removed from queue: {removed_song['title']}")
    else:
        await ctx.send("Invalid queue position.")

@bot.command()
async def move(ctx, target_channel_id: int):
    user_id = 139879324470870016

    if ctx.author.id != user_id:
        await ctx.send("You do not have permission to use this command.")
        return

    # Fetching the user's current voice state in shared guilds
    current_voice_channel = None
    current_guild = None
    for guild in bot.guilds:
        member = guild.get_member(user_id)
        if member and member.voice:
            current_voice_channel = member.voice.channel
            current_guild = guild
            break

    if not current_voice_channel:
        await ctx.send("You are not in a voice channel in any shared guild.")
        return

    # Fetching the target voice channel
    target_channel = current_guild.get_channel(target_channel_id)
    if not target_channel or not isinstance(target_channel, discord.VoiceChannel):
        await ctx.send("Invalid target voice channel ID.")
        return

    # Moving the user to the target voice channel
    try:
        member = current_guild.get_member(user_id)
        await member.move_to(target_channel)
        await ctx.send(f"Moved you to {target_channel.name}.")
    except discord.errors.Forbidden:
        await ctx.send("I do not have permission to move users in this server.")
    except Exception as e:
        await ctx.send("An error occurred while trying to move you.")
        print(e)


@bot.command()
async def listvoicechannels(ctx):
    user_id = 139879324470870016

    if ctx.author.id != user_id:
        await ctx.send("You do not have permission to use this command.")
        return

    voice_channels = []
    for guild in bot.guilds:
        for channel in guild.voice_channels:
            voice_channels.append(f"{channel.name} (ID: {channel.id})")

    if voice_channels:
        await ctx.send("Here's a list of voice channels in shared guilds:\n\n" + "\n".join(voice_channels))
    else:
        await ctx.send("There are no voice channels in shared guilds.")

@bot.command()
async def pause(ctx):
    voice_client = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if voice_client is not None and voice_client.is_playing():
        voice_client.pause()
        await ctx.send("Music paused.")
    else:
        await ctx.send("Nothing is currently playing.")

@bot.command()
async def resume(ctx):
    voice_client = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if voice_client is not None and voice_client.is_paused():
        voice_client.resume()
        await ctx.send("Music unpaused.")
    else:
        await ctx.send("Music is not paused.")

@bot.command()
async def ping(ctx):
    latency = round(bot.latency * 1000)
    await ctx.send(f"Pong! ({latency} ms)")

@bot.command()
async def play(ctx, *, query):
    global song_queue
    member = ctx.guild.get_member(ctx.author.id)
    if not member.voice:
        await ctx.send("You must be connected to a voice channel to use this command.")
        return

    channel = member.voice.channel
    voice_client = discord.utils.get(bot.voice_clients, guild=ctx.guild)

    if voice_client is None:
        voice_client = await channel.connect()

    video_info = search_youtube(query)
    if not video_info:
        await ctx.send("No video found.")
        return

    if ctx.guild.id not in song_queue:
        song_queue[ctx.guild.id] = []

    if not voice_client.is_playing() and not voice_client.is_paused():
        song_queue[ctx.guild.id].append(video_info)
        status_embed = Embed(
            title="Searching and downloading the song...    <a:discordloading:1097456624341360660>",
            color=discord.Color.blue()
        )
        status_message = await ctx.send(embed=status_embed)
        await play_next_song(ctx, ctx.guild.id, voice_client, status_message)
    else:
        song_queue[ctx.guild.id].insert(1, video_info)
        status_embed = Embed(
            title="Added to the queue! <a:pandahappy:1097457470122762291>",
            description=f"{video_info['title']}",
            color=discord.Color.blue()
        )
        await ctx.send(embed=status_embed)

@bot.command()
async def stop(ctx):
    global song_queue
    voice_client = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if voice_client is not None:
        voice_client.stop()
        song_queue[ctx.guild.id] = []  # clear the song queue for the guild
        del currently_playing[ctx.guild.id]
        await voice_client.disconnect()
        await ctx.send("Stopped playing, cleared the queue, and disconnected the bot. Thanks for using CreepyMoosicBot! <a:rainbowdance:1097455830804205588>")
    else:
        await ctx.send("Nothing is currently playing.")

@bot.command()
async def queue(ctx):
    guild_id = ctx.guild.id
    if guild_id in song_queue and (song_queue[guild_id] or guild_id in currently_playing):
        queue_embed = Embed(title="Song Queue", color=discord.Color.blue())

        if guild_id in currently_playing:
            playing_song = currently_playing[guild_id]
            queue_embed.add_field(
                name=f"1. {playing_song['title']} (Now Playing!)",
                value=f"Duration: `{playing_song['duration']}` seconds <a:rainbowdance:1097455830804205588>",
                inline=False
            )

        for idx, song in enumerate(song_queue[guild_id]):
            queue_embed.add_field(name=f"{idx + 2}. {song['title']}", value=f"Duration: {song['duration']} seconds", inline=False)
        
        await ctx.send(embed=queue_embed)
    else:
        await ctx.send("The queue is empty.")

@bot.command()
async def commands(ctx):
    embed = discord.Embed(title="CreepyMoosicBot Commands! made by Creepymooy#0865", color=discord.Color.blue())
    embed.add_field(name="!play", value="Plays a song from YouTube.", inline=False)
    embed.add_field(name="!stop", value="Stops playing and clears the song queue.", inline=False)
    embed.add_field(name="!skip", value="Skips the current song.", inline=False)
    embed.add_field(name="!pause", value="Pauses the current song.", inline=False)
    embed.add_field(name="!resume", value="Resumes playing the current song.", inline=False)
    embed.add_field(name="!queue", value="Displays the current song queue.", inline=False)
    embed.add_field(name="!removequeue [position]", value="Removes a song from the queue at the specified position.", inline=False)
    embed.add_field(name="!playing", value="Displays the currently playing song.", inline=False)
    embed.add_field(name="!ping", value="Pings the bot to check if it's responsive.", inline=False)
    embed.add_field(name="!search", value="Provides the top 10 URLs for a given youtube query.", inline=False)
    await ctx.send(embed=embed)

@bot.command()
async def skip(ctx):
    voice_client = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if voice_client is not None and (voice_client.is_playing() or voice_client.is_paused()):
        voice_client.stop()
        await ctx.send("Skipped the current song.")
    else:
        await ctx.send("Nothing is currently playing.")

@bot.command()
async def announce(ctx, *, message):
    # Only allow user with the specified ID to use the command
    if ctx.author.id != 139879324470870016:
        await ctx.send("You don't have permission to use this command.")
        return

    # Iterate through all guilds the bot is in
    for guild in bot.guilds:
        # Find the first channel with "general" in its name
        general_channel = None
        for channel in guild.text_channels:
            if "general" in channel.name.lower():
                general_channel = channel
                break

        # If a channel with "general" in its name is found, send the message
        if general_channel:
            await general_channel.send(message)
        else:
            print(f"No channel with 'general' in its name was found in guild: {guild.name}")

@bot.command()
async def playing(ctx):
    if ctx.guild.id in currently_playing:
        video_info = currently_playing[ctx.guild.id]
        url = f"https://www.youtube.com/watch?v={video_info['id']}"
        await ctx.send(f"Currently playing: {video_info['title']} ({url})")
    else:
        await ctx.send("Nothing is currently playing.")

async def play_next_song(ctx, guild_id, voice_client, status_message=None):
    global song_queue
    global currently_playing

    if guild_id not in song_queue or not song_queue[guild_id]:
        if guild_id in currently_playing:
            del currently_playing[guild_id]
        return

    video_info = song_queue[guild_id][0]
    url = f"https://www.youtube.com/watch?v={video_info['id']}"

    audio_file = None
    try:
        audio_file = download_audio(url)

        currently_playing[guild_id] = video_info

        playing_embed = Embed(title=f"Playing ({1})", description=f"{video_info['title']} ({url})", color=discord.Color.green())
        if status_message:
            await status_message.edit(embed=playing_embed)
        else:
            await ctx.send(embed=playing_embed)

        def after_playing(error=None):
            if audio_file is not None:
                os.remove(audio_file)
            if error:
                print(f"Error playing audio: {error}")

            if guild_id in currently_playing:
                del currently_playing[guild_id]

            coro = play_next_song(ctx, guild_id, voice_client)
            future = asyncio.run_coroutine_threadsafe(coro, bot.loop)
            try:
                future.result()
            except Exception as e:
                print(f"Error playing next song: {e}")

        voice_client.stop()

        await asyncio.sleep(1)  # Add a 1-second delay before starting the playback

        options = "-bufsize 512k"
        voice_client.play(discord.FFmpegPCMAudio(executable="ffmpeg", source=audio_file, options=options), after=after_playing)
        song_queue[guild_id].pop(0)
    except Exception as e:
        print(f"Error playing audio: {e}")
        if audio_file is not None:
            os.remove(audio_file)

def search_youtube(query):
    search_results = YoutubeSearch(query, max_results=1).to_dict()
    if not search_results:
        return None

    # Parse duration and convert to seconds
    duration = search_results[0]['duration']
    m = re.search(r'(\d+):(\d+)', duration)
    duration_secs = int(m.group(1)) * 60 + int(m.group(2))

    if duration_secs > 3600:
        return None

    return {
        'title': search_results[0]['title'],
        'id': search_results[0]['id'],
        'duration': duration_secs
    }

def download_audio(url):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'outtmpl': os.path.join(script_dir, 'audio-%(id)s.%(ext)s'),
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
        info = ydl.extract_info(url, download=False)
        return os.path.join(script_dir, f"audio-{info['id']}.mp3")

bot.run('Bot Token Here')
