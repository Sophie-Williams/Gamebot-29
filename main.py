import json
import os
import discord
from discord.ext import commands
import asyncio


class goBot(commands.Bot):
    def __init__(self, prefix, server_conf, conf):
        # Creates a copy of class command.Bot
        commands.Bot.__init__(self, command_prefix=prefix)
        self.remove_command('help')
        self.owner = server_conf["owner"]
        self.devs = server_conf["devs"]
        self.version = conf["version"]
        # Store Plugins
        plugins = ['src']
        # Load Plugins
        for plugin in plugins:
            self.load_extension(f"src.{plugin}")

    async def on_ready(self):
        print(f"""
        Logged in as: {self.user.name} - {self.user.id}\n
        | Connected to {len(self.guilds)} guilds | Connected to {sum(
        1 for m in set(self.get_all_members()) if m.status != discord.Status.offline
        )} Online users | Total Users {len(set(self.get_all_members()))} |
        Rewrite Version: {discord.__version__}
        \nUse this link to invite {self.user.name}:
        https://discordapp.com/oauth2/authorize?client_id={self.user.id}&scope=bot&permissions=3525696
        --------
        Successfully logged in and booted...!
        --------
        """)


loop = asyncio.get_event_loop()
with open(f'{os.getcwd()}/dir/config.json') as f:
    data = json.load(f)
    gobot = goBot(data["prefix"], data["server"], data)
    loop.run_until_complete(gobot.run(data["botkey"]))
