# imports
import discord
import asyncio
from discord.ext import commands, tasks
import random
import datetime
import time
from datetime import datetime
from pymongo import MongoClient
from random import shuffle
from discord_components import Button
import yt_dlp
import youtube_dl
from .loading_bar import *
from yt_dlp import YoutubeDL
from yt_dlp import utils
import yt_dlp
import spotipy
import re
from spotipy.oauth2 import SpotifyOAuth
from spotdl import __main__ as start
from spotdl.search import SongObject

scope = ""

sp = spotipy.Spotify(auth_manager=SpotifyOAuth(scope=scope,client_id = "673850c9d4f04a2d9fc5865b125ebebb", client_secret = "de3280b1ebf54276815cfd2dc03f6bec", redirect_uri = "http://localhost:8888/callback"))
from musixmatch import Musixmatch
musixmatch = Musixmatch("feee63df2060a6cc31bf2471ffa2b935")



# Queue class
class Queue:
    def __init__(self, queue=None, playing=None):
        if queue is None:
            queue = []
        if playing is None:
            playing = False
        self.queue = queue
        self.playing = playing

    def getsongs(self):
        return len(self.queue)

    def setplaying(self, bool):
        self.playing = bool

    def getplaying(self):
        return self.playing

    def get_estimated_total_time(self):
        total_duration = 0
        for song in self.queue:
            total_duration += song[4]
        return total_duration

    def get_queue(self):
        return self.queue

    def add_song(self, song_query, user):
        info = ydl.extract_info(f"ytsearch:{song_query}", download=False)['entries'][0]
        video_actual_url = "https://www.youtube.com/watch?v=" + info['id']
        video_url = info['url']
        self.queue.append([video_actual_url, user.id, info['title'], video_url, info['duration'], info['id']])
        return video_actual_url

    def remove_song(self, position):
        try:
            songtitle = self.queue[position - 1][2]
            del self.queue[position - 1]
            return songtitle
        except:
            return True

    def clearqueue(self):
        self.queue = []

    def updatequeue(self, queue):
        self.queue = queue

    def removeabsent(self, channel):
        members = channel.members
        mems = []
        for member in members:
            mems.append(member)
        for song in self.queue:
            if song[1] not in mems:
                self.queue.remove(song)

    def undo(self, user):
        queuedsongs = []
        for song in self.queue:
            if song[1] == user:
                queuedsongs.append(song)
        self.queue.remove(queuedsongs[-1])

    def move(self, pos1, pos2):
        self.queue[pos1], self.queue[pos2] = self.queue[pos2], self.queue[pos1]


YTDL_OPTIONS = {'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
                'match_filter': youtube_dl.utils.match_filter_func('!is_live'),
                'external_downloader': 'wget'}
FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}

ydl = YoutubeDL(YTDL_OPTIONS)


# convert seconds to a string displaying the time.
def secondstotime(seconds):
    hours = seconds // 3600
    seconds -= hours * 3600
    minutes = seconds // 60
    seconds = seconds - minutes * 60
    if hours == 0:
        if minutes == 0:
            duration = str(int(seconds)) + "s"
        else:
            duration = str(int(minutes)) + "m " + str(int(seconds)) + "s"
    else:
        duration = str(int(hours)) + "h " + str(int(minutes)) + "m " + str(int(seconds)) + "s"
    return duration


class Music(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.voice_client = None
        self.play_next.start()
        self.queue_obj = Queue()
        self.textchannel = None
        self.title = None
        self.duration = None
        self.startmusictime = None
        self.url = None
        self.proper_url = None
        self.thumbnail = None
        self.author = None
        self.artist = None
        self.paused = False
        self.nomoresonginqueuemessagesent = True

    # Playback Commands

    @commands.command(aliases = ['h'])
    async def help(self, ctx, cmd = None):
        if cmd == None:
            playback = "``"
            playback_embed = discord.Embed(title = 'Help - **Playback**', description = "`play` : Finds and plays the provided song query / URL\n`")

    @commands.command(aliases=["connect", "c"])
    async def join(self, ctx, check = True, message = None):
        if ctx.author.voice == None:
            if message != None:
                await message.edit("You need to be in a voice channel in order to use the bot!")
            else:
                await ctx.reply("You need to be in a voice channel in order to use the bot!")
            return False
        elif ctx.author.voice.channel == None:
            if message != None:
                await message.edit("You need to be in a voice channel in order to use the bot!")
            else:
                await ctx.reply("You need to be in a voice channel in order to use the bot!")
            return False
        elif ctx.voice_client != None:
            if message != None:
                await message.edit("Bot is already in a voice channel!")
            else:
                await ctx.reply("Bot is already in a voice channel!")
            return False
        else:
            channel = ctx.author.voice.channel
            self.textchannel = ctx.channel
            if check == True:
                await ctx.message.add_reaction("✅")
            else:
                pass
            try:
                await channel.connect(timeout=60, reconnect=True)
            except Exception as e:
                print(e)
            self.voice_client = ctx.voice_client
            return True

    @commands.command(aliases=["disconnect", "dc"])
    async def leave(self, ctx):
        if ctx.voice_client == None:
            await ctx.reply("Bot is not in a voice channel!")
        else:
            if ctx.author.voice != None:
                if (ctx.author.voice.channel and ctx.author.voice.channel == ctx.voice_client.channel):
                    for x in self.bot.voice_clients:
                        await x.disconnect(force=True)
                    await ctx.message.add_reaction("✅")
                else:
                    await ctx.reply("You need to be in the same voice channel as the bot in order to use this command!")
            else:
                await ctx.reply("You need to be in a voice channel with the bot in order to use this command!")

    @commands.command(aliases=["p"])
    async def play(self, ctx, *, song):
        if song.startswith("https://open.spotify.com/track/"):
            try:
                song_id = re.sub("https://open.spotify.com/track/", "", song)
                track = "spotify:track:"+song_id
                track = sp.track(track)
                print(track)
                track_name = track['name']
                print(track_name)
                track_artist = track['album']['artists'][0]['name']
                print(track_artist)
                searchquery = track_name + " - " + track_artist
                print(searchquery)
                await self.play(ctx = ctx, song = searchquery)
            except Exception as e:
                await ctx.reply("Uh oh! A problem has occured!")
                print(e)
        else:
            message = await ctx.reply(content="Processing...")
            if ctx.voice_client is None:
                await self.join(ctx, False, message)
            elif ctx.author.voice is None:
                await message.edit("You need to be in a voice channel in order to use the bot!")
            elif not (ctx.author.voice.channel and ctx.author.voice.channel == ctx.voice_client.channel):
                await message.edit("You need to be in the same voice channel as the bot in order to use this command.")
            self.textchannel = ctx.channel
            notlivestream = True
            num = 0
            info = ydl.extract_info(f"ytsearch:{song}", download=False)['entries'][num]
            if info['duration'] == None:
                while notlivestream:
                    info = ydl.extract_info(f"ytsearch3:{song}", download=False)['entries'][num]
                    if info['duration'] == None:
                        num += 1
                    else:
                        notlivestream = False
                        video_url = info['url']
            else:
                video_url = info['url']
            self.proper_url = video_url
            source = discord.FFmpegPCMAudio(video_url,
                                            **FFMPEG_OPTIONS)  # converts the youtube audio source into a source discord can use
            if self.queue_obj.getplaying() == True:
                if self.startmusictime == None:
                    self.startmusictime = datetime.now()
                time = datetime.now() - self.startmusictime
                seconds = self.duration - time.total_seconds()
                estimated_tot = self.queue_obj.get_estimated_total_time() + seconds
                estimated_tot = secondstotime(estimated_tot)
                em = discord.Embed(title=f"Song Added to Queue!", url=self.queue_obj.add_song(song, ctx.author),
                                   description=f"{info['title']} \n **Estimated time until play:** `{estimated_tot}`")
                await message.edit(content = "", embed=em)
            else:
                try:
                    ctx.voice_client.play(source)
                    self.queue_obj.setplaying(True)
                    video_actual_url = "https://www.youtube.com/watch?v=" + info['id']
                    self.title = info['title']
                    self.duration = info['duration']
                    self.url = video_actual_url
                    self.thumbnail = f"https://img.youtube.com/vi/{info['id']}/1.jpg"
                    if info['duration'] == None:
                        em = discord.Embed(title=f"Now Playing:", url=video_actual_url,
                                           description=f"{info['title']} \n **Duration:** `None - Livestream`")
                    else:
                        em = discord.Embed(title=f"Now Playing:", url=video_actual_url,
                                           description=f"{info['title']} \n **Duration:** `{secondstotime(info['duration'])}`")
                    em.set_thumbnail(url=f"https://img.youtube.com/vi/{info['id']}/1.jpg")
                    em.set_author(name=f"Queued by {ctx.author.name}#{ctx.author.discriminator}",
                                  url="https://youtube.com/watch?v=dQw4w9WgXcQ",
                                  icon_url=ctx.author.avatar_url)

                    await message.edit(content = "", embed=em)
                    self.startmusictime = datetime.now()
                    self.author = ctx.author
                    # asyncio.create_task(await self.play_next(ctx.voice_client))
                except Exception as e:
                    print(e)
                    self.title = info['title']
                    self.duration = info['duration']
                    video_actual_url = "https://www.youtube.com/watch?v=" + info['id']
                    self.url = video_actual_url

                    self.thumbnail = f"https://img.youtube.com/vi/{info['id']}/1.jpg"
                    self.queue_obj.setplaying(True)
                    channel = ctx.author.voice.channel
                    await channel.connect(timeout=60, reconnect=True)
                    title = info['title']
                    duration = info['duration']
                    if info['duration'] == None:
                        em = discord.Embed(title=f"Now Playing:", url=video_actual_url,
                                           description=f"{info['title']} \n **Duration:** `None - Livestream`")
                    else:
                        em = discord.Embed(title=f"Now Playing:", url=video_actual_url,
                                           description=f"{info['title']} \n **Duration:** `{secondstotime(info['duration'])}`")
                    em.set_thumbnail(url=f"https://img.youtube.com/vi/{info['id']}/1.jpg")
                    em.set_author(name=f"Queued by {ctx.author.name}#{ctx.author.discriminator}",
                                  url="https://youtube.com/watch?v=dQw4w9WgXcQ",
                                  icon_url=ctx.author.avatar_url)
                    await message.edit(content = "", embed=em)
                    ctx.voice_client.play(source)
                    self.author = ctx.author
                    self.startmusictime = datetime.now()
                # asyncio.create_task(await self.play_next(ctx.voice_client))

    # @commands.commands(aliases = ["v"])
    # async def volume(self, ctx):
    #     pass

    @commands.command(aliases=["af"])
    async def artistfind(self, ctx, *, artist = None):
        interaction_exist = False
        message = False
        if artist == None:
            await ctx.reply("Please add the artist that you would like to find in the command!")
        else:

            try:
                artist_id = sp.search(q=artist, type="artist", limit=10)["artists"]["items"][0]["id"]
                artist_name = sp.search(q=artist, type="artist", limit=10)["artists"]["items"][0]["name"]
                artist_top_tracks = sp.artist_top_tracks(artist_id, country='US')
                embed = discord.Embed(title = f"**Artist - {artist_name}**", description = f"Top 5 tracks by {artist_name}: \n")
                embed1 = discord.Embed(title="\u200b", description="`1`")
                embed1.add_field(name = f'__{artist_top_tracks["tracks"][0]["name"]}__',
                                 value = f"Duration: `{secondstotime(artist_top_tracks['tracks'][0]['duration_ms']/1000)}`")
                embed1.set_thumbnail(url = artist_top_tracks["tracks"][0]["album"]["images"][0]["url"])
                embed2 = discord.Embed(title = "\u200b", description = "`2`")
                embed2.add_field(name = f'__{artist_top_tracks["tracks"][1]["name"]}__',
                                 value = f"Duration: `{secondstotime(artist_top_tracks['tracks'][1]['duration_ms']/1000)}`")
                embed2.set_thumbnail(url = artist_top_tracks["tracks"][1]["album"]["images"][0]["url"])
                embed3 = discord.Embed(title="\u200b", description="`3`")
                embed3.add_field(name=f'__{artist_top_tracks["tracks"][2]["name"]}__',
                                 value=f"Duration: `{secondstotime(artist_top_tracks['tracks'][2]['duration_ms'] / 1000)}`")
                embed3.set_thumbnail(url = artist_top_tracks["tracks"][2]["album"]["images"][0]["url"])
                embed4 = discord.Embed(title="\u200b", description="`4`")
                embed4.add_field(name=f'__{artist_top_tracks["tracks"][3]["name"]}__',
                                 value=f"Duration: `{secondstotime(artist_top_tracks['tracks'][3]['duration_ms'] / 1000)}`")
                embed4.set_thumbnail(url = artist_top_tracks["tracks"][3]["album"]["images"][0]["url"])
                embed5 = discord.Embed(title="\u200b", description="`5`")
                embed5.add_field(name=f'__{artist_top_tracks["tracks"][4]["name"]}__',
                                 value=f"Duration: `{secondstotime(artist_top_tracks['tracks'][4]['duration_ms'] / 1000)}`")
                embed5.set_thumbnail(url = artist_top_tracks["tracks"][4]["album"]["images"][0]["url"])
                embed5.set_footer(text = "Select a number (song) that you would like to play, if any.")
                await ctx.reply(embed=embed)
                await ctx.send(embed=embed1)
                await ctx.send(embed=embed2)
                await ctx.send(embed=embed3)
                await ctx.send(embed=embed4)
                message = await ctx.send(embed=embed5, components = [[Button(label = "1"), Button(label = "2"), Button(label = "3"), Button(label = "4"), Button(label = "5")]])
                try:
                    interaction = await self.bot.wait_for("button_click")
                    if interaction:
                        if interaction.user == ctx.author:
                            interaction_exist = True
                            if interaction.component.label == "1":
                                query = artist_top_tracks["tracks"][0]["name"] + " - " + artist_name
                            elif interaction.component.label == "2":
                                query = artist_top_tracks["tracks"][1]["name"] + " - " + artist_name
                            elif interaction.component.label == "3":
                                query = artist_top_tracks["tracks"][2]["name"] + " - " + artist_name
                            elif interaction.component.label == "4":
                                query = artist_top_tracks["tracks"][3]["name"] + " - " + artist_name
                            elif interaction.component.label == "5":
                                query = artist_top_tracks["tracks"][4]["name"] + " - " + artist_name
                            await interaction.respond(type=6)
                            await self.play(ctx=ctx, song=query)
                            await message.edit(
                                components=[[Button(label="1", disabled=True), Button(label="2", disabled=True),
                                             Button(label="3", disabled=True), Button(label="4", disabled=True),
                                             Button(label="5", disabled=True)]])
                        else:
                            await interaction.respond(content = "This is not for you!")
                except asyncio.TimeoutError:
                    await message.edit(components = [[Button(label = "1", disabled = True), Button(label = "2", disabled = True), Button(label = "3", disabled = True), Button(label = "4", disabled = True), Button(label = "5", disabled = True)]])

            except Exception as e:
                print(e)
                if interaction_exist == False:
                    await ctx.send("Cannot find artist!")
                if message != False:
                    await message.edit(
                        components=[[Button(label="1", disabled=True), Button(label="2", disabled=True),
                                     Button(label="3", disabled=True), Button(label="4", disabled=True),
                                     Button(label="5", disabled=True)]])

    # @commands.command(aliases=["pp", "playpodcast", "playpodcasts"])
    # async def podcastplay(self):
    #     pass



    @commands.command()
    async def pause(self, ctx):
        try:
            if ctx.voice_client != None:
                if self.paused == True:
                    await ctx.reply("The music is already paused!")
                else:
                    self.paused = True
                    ctx.voice_client.pause()
                    await ctx.message.add_reaction("✅")
            else:
                await ctx.reply("The bot isn't playing any music!")
        except Exception as e:
            print(e)
            if ctx.voice_client != None:
                if self.paused == True:
                    await ctx.reply("The music is already paused!")
                else:
                    self.paused = True
                    ctx.voice_client.pause()
                    await ctx.message.add_reaction("✅")
            else:
                await ctx.reply("The bot isn't playing any music!")

    @commands.command()
    async def resume(self, ctx):
        try:
            if ctx.voice_client != None:
                if self.paused == True:
                    self.paused = False
                    ctx.voice_client.resume()
                    await ctx.message.add_reaction("✅")
                else:
                    await ctx.reply("The music isn't paused!")
            else:
                await ctx.reply("The bot isn't playing any music!")
        except Exception as e:
            print(e)
            if ctx.voice_client != None:
                if self.paused == True:
                    self.paused = False
                    ctx.voice_client.resume()
                    await ctx.message.add_reaction("✅")
                else:
                    await ctx.reply("The music isn't paused!")
            else:
                await ctx.reply("The bot isn't playing any music!")

    @commands.command()
    async def skip(self, ctx):
        try:
            if ctx.voice_client != None:
                ctx.voice_client.stop()
                self.paused = False
                await ctx.message.add_reaction("✅")
            else:
                await ctx.reply("The bot isn't playing any music!")
        except Exception as e:
            print(e)
            if ctx.voice_client != None:
                ctx.voice_client.stop()
                self.paused = False
                await ctx.message.add_reaction("✅")
            else:
                await ctx.reply("The bot isn't playing any music!")

    @commands.command()
    async def stop(self, ctx):
        try:
            if ctx.voice_client != None:
                if ctx.voice_client.is_playing != False:
                    message = await ctx.reply(content="Are you sure you would like to stop playing music and also remove the entire queue?",
                                              components=[Button(label="Confirm", style=3),
                                                          Button(label="Cancel", style=4)])

                    def check():
                        return ctx.author == interaction.user

                    try:
                        interaction = await self.bot.wait_for('button_click', timeout=60.0)
                        if interaction:
                            if interaction.component.label == "Confirm":
                                if interaction.user == ctx.author:
                                    ctx.voice_client.stop()
                                    self.queue_obj.clearqueue()
                                    await ctx.voice_client.disconnect(force = True)
                                    await ctx.message.add_reaction("✅")
                                    await interaction.respond(type=6)
                                    await message.edit(components=[Button(label="Confirm", style=3, disabled=True),
                                                                   Button(label="Cancel", style=4, disabled=True)])
                                else:
                                    await interaction.respond(type = 4, content = "This isn't your message!")
                            else:
                                await ctx.reply("Action Cancelled.")
                                await message.edit(components=[Button(label="Confirm", style=3, disabled=True),
                                                               Button(label="Cancel", style=4, disabled=True)])
                    except asyncio.TimeoutError:
                        await ctx.reply("Timed out. ")
                else:
                    await ctx.reply("The bot isn't playing music currently!")
            else:
                await ctx.reply("The bot isn't playing any music!")
        except Exception as e:
            print(e)
            if ctx.voice_client != None:
                if ctx.voice_client.is_playing != False:
                    channel = ctx.author.voice.channel
                    await channel.connect(timeout=60, reconnect=True)
                    message = await ctx.reply(
                        content="Are you sure you would like to stop playing music and also remove the entire queue?",
                        components=[Button(label="Confirm", style=3),
                                    Button(label="Cancel", style=4)])

                    def check(interaction):
                        return ctx.author == interaction.user

                    try:
                        interaction = await self.bot.wait_for('button_click', timeout=60.0, check=check)
                        if interaction:
                            if interaction.component.label == "Confirm":
                                ctx.voice_client.stop()
                                self.queue_obj.clearqueue()
                                await ctx.message.add_reaction("✅")
                                await message.edit(components=[Button(label="Confirm", style=3, disabled=True),
                                                               Button(label="Cancel", style=4, disabled=True)])
                            else:
                                await ctx.reply("Action Cancelled.")
                                await message.edit(components=[Button(label="Confirm", style=3, disabled=True),
                                                               Button(label="Cancel", style=4, disabled=True)])
                    except asyncio.TimeoutError:
                        await ctx.reply("Timed out. ")
                else:
                    await ctx.reply("The bot isn't playing music currently!")
            else:
                await ctx.reply("The bot isn't playing any music!")

    @commands.command()
    async def seek(self, ctx, timestamp = None):
        message = await ctx.reply("Processing... ")
        if self.voice_client.is_playing == False:
            await message.edit("You can only use this command when the song you want to seek from is playing!")
        else:
            if timestamp == None:
                await message.edit("You have to specify a specific time to seek in the video!")
            else:
                try:
                    timething = datetime.strptime(timestamp[:8], '%H:%M:%S')
                    a_timedelta = timething - datetime(1900, 1, 1)
                    seconds = a_timedelta.total_seconds()
                    if seconds > self.duration:
                        await message.edit("Invalid timestamp: Video is shorter than the given timestamp.")
                        return
                except ValueError:
                    await message.edit('Invalid timestamp')
                else:
                    FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
                                  'options': f'-vn -ss {timestamp}'}
                    info = ydl.extract_info(self.url, download=False)
                    video_url = info['url']
                    source = discord.FFmpegPCMAudio(video_url,
                                                    **FFMPEG_OPTIONS)
                    ctx.voice_client.stop()
                    ctx.voice_client.play(source)
                    self.startmusictime = datetime.now() - a_timedelta
                    await message.edit(f"Successfully skipped to {timestamp}! \n Sidenote: If you have skipped by more than a few minutes, give the music some time to load.")

    @commands.command()
    async def lyrics(self, ctx):
        try:
            lyrics = musixmatch.track_lyrics_get(musixmatch.matcher_track_get(self.title, '')['message']['body']['track']['track_id'])['message']['body']['lyrics']['lyrics_body']
            print(musixmatch.track_lyrics_get(musixmatch.matcher_track_get(self.title, '')['message']['body']['track']['track_id'])['message']['body']['lyrics'])
            embed = discord.Embed(title="Lyrics", description=lyrics)
        except:
            embed = discord.Embed(title = "Lyrics", description = "There are no lyrics!")
        await ctx.send(embed = embed)

    @tasks.loop(seconds=3, reconnect=True)
    async def play_next(self):
        voice_client = self.voice_client
        try:
            channel = self.voice_client.channel
            members = channel.members  # finds members connected to the channel
            memids = []  # (list)
            for member in members:
                memids.append(member.id)
            if len(memids) == 1 and self.bot.user.id in memids:
                await self.textchannel.send("Stopped playing music and left the channel. \n `Reason: No members inside the channel.`")
                await voice_client.disconnect(force=True)

            if len(self.queue_obj.get_queue()) == 0 and voice_client.is_playing() == False:
                self.queue_obj.setplaying(False)
                if self.nomoresonginqueuemessagesent == False:
                    embed = discord.Embed(title = "No more songs in queue")
                    await self.textchannel.send(embed=embed)
                    self.nomoresonginqueuemessagesent = True

            else:
                self.nomoresonginqueuemessagesent = False
                if self.paused == True:
                    pass
                else:
                    queue = self.queue_obj.get_queue()
                    song = queue[0]
                    voice_client.play(discord.FFmpegPCMAudio(song[3], **FFMPEG_OPTIONS))
                    self.title = song[2]
                    self.duration = song[4]
                    self.startmusictime = datetime.now()
                    self.url = song[0]
                    self.thumbnail = f"https://img.youtube.com/vi/{song[5]}/1.jpg"
                    if song[4] == None:
                        em = discord.Embed(title=f"Now Playing:", url=song[0],
                                           description=f"{song[2]} \n **Duration:** `None - Livestream`")
                    else:
                        em = discord.Embed(title=f"Now Playing:", url=song[0],
                                           description=f"{song[2]} \n **Duration:** `{secondstotime(song[4])}`")
                    em.set_thumbnail(url=f"https://img.youtube.com/vi/{song[5]}/1.jpg")
                    author = await self.bot.fetch_user(song[1])
                    em.set_author(name=f"Queued by {author.name}#{author.discriminator}",
                                  url="https://youtube.com/watch?v=dQw4w9WgXcQ",
                                  icon_url=author.avatar_url)
                    await self.textchannel.send(embed=em)
                    self.author = author
                    self.queue_obj.remove_song(1)
        except Exception as e:
            print(e)

    @play_next.before_loop
    async def play_next_before(self):
        await self.bot.wait_until_ready()

    # Queue commands
    @commands.command()
    async def now(self, ctx):
        time = datetime.now() - self.startmusictime
        seconds = time.total_seconds()
        if int(self.duration) < seconds:
            seconds = int(self.duration)
        time = secondstotime(seconds)
        if self.voice_client.is_playing == False:
            em = discord.Embed(title="Now Playing: ", url="https://youtube.com/watch?v=dQw4w9WgXcQ", description = "Bot is not curently playing any music!")
            em.set_author(name=f"Not playing any songs!")
        else:
            if self.duration == None:
                em = discord.Embed(title="Now Playing: ", url=self.url,
                                   description=f"{self.title}\n {fraction_to_optimized(1)} `{time}/{time}`")
            else:
                em = discord.Embed(title="Now Playing: ", url=self.url,
                                   description=f"{self.title}\n {fraction_to_optimized(seconds / int(self.duration))} `{time}/{secondstotime(int(self.duration))}`")
            em.set_thumbnail(url=self.thumbnail)
            em.set_author(name=f"Queued by {self.author.name}#{self.author.discriminator}",
                          url="https://youtube.com/watch?v=dQw4w9WgXcQ",
                          icon_url=self.author.avatar_url)
        await ctx.reply(embed=em)

    @commands.command()
    async def clearqueue(self, ctx):
        message = await ctx.reply(content = "Are you sure you would like to clear the entire queue?", components = [Button(label = "Confirm", style = 3), Button(label = "Cancel", style = 4)])

        def check():
            return ctx.author == interaction.user

        try:
            interaction = await self.bot.wait_for('button_click', timeout=60.0, check=check)
            if interaction:
                if interaction.component.label == "Confirm":
                    self.queue_obj.clearqueue()
                    await ctx.message.add_reaction("✅")
                    await message.edit(components = [Button(label = "Confirm", style = 3, disabled = True), Button(label = "Cancel", style = 4, disabled = True)])
                else:
                    await ctx.reply("Action Cancelled.")
                    await message.edit(components=[Button(label="Confirm", style=3, disabled=True),
                                                   Button(label="Cancel", style=4, disabled=True)])
        except asyncio.TimeoutError:
            await ctx.reply("Timed out. ")

    @commands.command(aliases=["dd"])
    async def deduplicate(self, ctx):
        queue = self.queue_obj.get_queue()
        for tracka in queue:
            for trackb in queue:
                if tracka[0] == trackb[0]:
                    index = queue.index(tracka)
                    queue.remove(tracka)
                    await ctx.reply(f"Successfully removed duplicate song {tracka[0]} (index {index})")
        self.queue_obj.updatequeue(queue)
        await ctx.message.add_reaction("✅")

    @commands.command(aliases=["mv"])
    async def move(self, ctx, pos1, pos2):
        try:
            pos1 = int(pos1)
        except:
            await ctx.reply("The position values have to be an integer! ")
            return

        try:
            pos2 = int(pos2)
        except:
            await ctx.reply("The position values have to be an integer! ")
            return

        queue = self.queue_obj.get_queue()
        queuelen = len(queue)
        if (pos1 - 1) > queuelen:
            await ctx.reply("The position value is invalid!")
            return
        elif (pos2 - 1) > queuelen:
            await ctx.reply("The position value is invalid!")
            return
        else:
            self.queue_obj.move(pos1 - 1, pos2 - 1)
            await ctx.reply(f"Successfully swapped song index {pos1} with song index {pos2}")
            await ctx.message.add_reaction("✅")

    @commands.command(aliases=["rm", "r", "uq", "unqueue"])
    async def remove(self, ctx, pos):
        try:
            pos = int(pos)
        except:
            await ctx.reply("Invalid index! Please try again.")
            return
        test = self.queue_obj.remove_song(pos)
        if test == True:
            await ctx.reply("Invalid index! Please try again.")
        else:
            await ctx.reply(f"Removed Song: {test}.")

    @commands.command(aliases = ["q"])
    async def queue(self, ctx):
        queue = self.queue_obj.get_queue()
        queue_desc = ["","","",""]
        x = 1
        for item in queue:
            queue_desc[math.floor(x/10)] += f"`{x}` [{item[2]}]({item[0]}) <@!{item[1]}> \n "
            x += 1
        if len(queue) == 0:
            pages = 0
            page = 0
        else:
            pages = math.floor(x/10)+1
            page = 1

        if pages == 0:
            em = discord.Embed(title = f"Queue", description = "Queue is currently empty! Use =play to add songs to the queue!", footer = f"Page 0 / 0")
        else:
            em = discord.Embed(title = f"Queue ({self.queue_obj.getsongs()} song(s), {secondstotime(self.queue_obj.get_estimated_total_time())})", description = f"{queue_desc[0]}", footer = f"Page {page} / {pages}")
        if pages <= 1:
            await ctx.reply(embed = em, components = [[Button(label = "<", style = 1, disabled = True), Button(label = ">", style = 1, disabled = True)]])
        else:
            message = await ctx.reply(embed=em, components=[
                [Button(label="<", style=1, disabled=True), Button(label=">", style=1)]])
            try:
                while True:
                    interaction = await self.bot.wait_for('button_click', timeout=15.0)
                    if interaction:
                        if interaction.user == ctx.author:
                            if interaction.component.label == "<":
                                if page > 1:
                                    page -= 1
                                    em = discord.Embed(
                                            title=f"Queue ({self.queue_obj.getsongs()} song(s), {secondstotime(self.queue_obj.get_estimated_total_time())})",
                                            description=f"{queue_desc[page-1]}", footer=f"Page {page} / {pages}")
                                if page == 1:
                                    await message.edit(embed = em, components=[
                                        [Button(label="<", style=1, disabled=True), Button(label=">", style=1)]])
                                    await interaction.respond(type=6)
                                else:
                                    await message.edit(embed=em)
                                    await interaction.respond(type=6)
                            if interaction.component.label == ">":
                                if page < pages:
                                    page += 1
                                    em = discord.Embed(
                                        title=f"Queue ({self.queue_obj.getsongs()} song(s), {secondstotime(self.queue_obj.get_estimated_total_time())})",
                                        description=f"{queue_desc[page-1]}", footer=f"Page {page} / {pages}")
                                if page == pages:
                                    await message.edit(embed=em, components=[
                                        [Button(label="<", style=1), Button(label=">", style=1, disabled=True)]])
                                    await interaction.respond(type=6)
                                else:
                                    await message.edit(embed=em)
                                    await interaction.respond(type=6)
                        else:
                            interaction.respond(type=4,
                                                content="This isn't for you! If you would like to see the queue, use =queue.")
            except asyncio.TimeoutError:
                await message.edit(components=[
                [Button(label="<", style=1, disabled=True), Button(label=">", style=1, disabled = True)]])






def setup(bot):
    bot.add_cog(Music(bot))
