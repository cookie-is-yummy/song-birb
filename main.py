from discord.ext import commands, tasks
import discord
from cogs.music import Music
import os
import random
import pymongo
from pymongo import MongoClient
import re
from datetime import datetime
from token import token
from discord_components import *
intents = discord.Intents.default()
intents.members = True
bot = commands.Bot(command_prefix='=', help_command=None, case_insensitive=True, intents=intents)
@bot.event
async def on_ready():
    DiscordComponents(bot, change_discord_methods=True)
    print(f'Logged in as {bot.user.name} - {bot.user.id}')
    await bot.change_presence(activity=discord.Game(name='=help', type=2),
                                           status=discord.Status.online)
    await bot.user.edit(username="= | Song Bird Γ")

bot.load_extension("cogs.music")
bot.run(token)