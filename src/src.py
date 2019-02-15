from discord.ext import commands
import discord
import aiohttp
import sqlite3
import os
import re
from contextlib import redirect_stdout
import io
import traceback
import textwrap

db = sqlite3.connect(f"{os.getcwd()}/db/go.db")
member_db = sqlite3.connect(f"{os.getcwd()}/db/member-test.db")
time_db = sqlite3.connect(f"{os.getcwd()}/db/timezones.db")
cur = db.cursor()
member_cur = member_db.cursor()
time_cur = time_db.cursor()


def clean(to_clean):
    to_clean = str(to_clean)
    to_clean = to_clean.replace("[", "")
    to_clean = to_clean.replace("]", "")
    to_clean = to_clean.replace("(", "")
    to_clean = to_clean.replace(")", "")
    to_clean = to_clean.replace("'", "")
    to_clean = to_clean.replace(",", "")

    return to_clean


def clean_comma(to_clean):
    to_clean = str(to_clean)
    to_clean = to_clean.replace("[", "")
    to_clean = to_clean.replace("]", "")
    to_clean = to_clean.replace("(", "")
    to_clean = to_clean.replace(")", "")
    to_clean = to_clean.replace("'", "")

    return to_clean


class src:
    def __init__(self, bot):
        self.bot = bot

    async def on_error(self, ctx, error):
        await ctx.send("An error has occurred!\n" + str(error))

    async def on_command_error(self, ctx, error):
        if str(error).startswith("Command") and str(error).endswith("is not found"):
            return await ctx.message.add_reaction("❌")
        elif str(error).startswith("Command raised an exception: OperationalError: table ") \
                and str(error).endswith("already exists"):
            return await ctx.send("This game already exists!")
        elif str(error).startswith("Command raised an exception: OperationalError: no such table:"):
            return await ctx.send('A database error occurred!\nEither you entered an invalid/mis-spelt game name, or '
                                  'something else has gone wrong!')
        elif str(error).startswith("Command raised an exception: OperationalError: no such column: "):
            print(error)
            return await ctx.send("A database error has occurred!")
        else:
            print(f"{ctx.author.name}: {ctx.message.content}\n{error}")
            await ctx.send("An unknown error has occurred!")
            await ctx.send(f"Error: `{error}`")

    @commands.command(hidden=True)
    async def reload(self, ctx, plugin: str):
        if ctx.message.author.id in self.bot.owner:
            self.bot.unload_extension(f"src.{plugin}")
            self.bot.load_extension(f"src.{plugin}")
            embed = discord.Embed(title="Reload", description="Reloaded `" + plugin + "`!", color=0xf20006)
            await ctx.send(embed=embed)
        else:
            await ctx.send("Only the owner of this bot can use this command ;(")

    @commands.command(pass_context=True, hidden=True, name='eval')
    async def _eval(self, ctx, *, body: str):
        """Evaluates a code"""
        if ctx.message.author.id in self.bot.owner:
            env = {
                'bot': self.bot,
                'ctx': ctx,
                'channel': ctx.channel,
                'author': ctx.author,
                'guild': ctx.guild,
                'message': ctx.message,
            }

            env.update(globals())

            stdout = io.StringIO()

            to_compile = f'async def func():\n{textwrap.indent(body, "  ")}'

            try:
                exec(to_compile, env)
            except Exception as e:
                return await ctx.send(f'```py\n{e.__class__.__name__}: {e}\n```')

            func = env['func']
            try:
                with redirect_stdout(stdout):
                    ret = await func()
            except Exception as e:
                value = stdout.getvalue()
                await ctx.send(f'```py\n{value}{traceback.format_exc()}\n```')
            else:
                value = stdout.getvalue()
                try:
                    await ctx.message.add_reaction('\u2705')
                except:
                    pass

                if ret is None:
                    if value:
                        try:
                            await ctx.send('```Python\n{}\n```'.format(value))
                        except Exception:
                            code = [value[i:i + 2000] for i in range(0, len(value), 2000)]
                            for i in code:
                                embed = discord.Embed(title="Evaluating Long Output (>2000)",
                                                      description='```Python\n{}\n```'.format(i),
                                                      colour=0xf20006)
                                await ctx.send(embed=embed)
        else:
            await ctx.send("Only the owner of this bot can use this command ;(")

    @commands.command(hidden=True)
    async def ping(self, ctx):
        latency = str(self.bot.latency * 1000)
        if latency[:-13].endswith("."):
            latency = latency[:-13] + "00000000000000"
        await ctx.send(content=f'\uD83C\uDFD3Pong, **{latency[:-13]}ms**')

    #@commands.command()
    #async def web_scraping_kill_me_please(self, ctx):
        #page = requests.get("https://www.oculus.com/experiences/go/section/1431986220442261#/?_k=qaq5qw")
        #tree = html.fromstring(page.content)
        # release1 = tree.xpath('//*[@id="mount"]/div/div[2]/div/div/div[2]/div[1]/div/div/div[1]/text()')
        #for i in tree.body:
            #for a in i.values:
                #print(a)
        # print(tree)

    @commands.command()
    async def when(self, ctx, *, text):
        game = re.match(r"was (.*) released\?", text)
        if game:
            game = str(game.group(1))
            game = game.replace(" ", "_")

            cur.execute(f"SELECT released FROM {game}")
            date = cur.fetchall()

            date = str(date)
            date = date.replace("[", "")
            date = date.replace("]", "")
            date = date.replace("(", "")
            date = date.replace(")", "")
            date = date.replace("'", "")
            date = date.replace(",", "")

            game = game.replace("_", " ")

            embed = discord.Embed(title="Game", description=f"{game} was released on: {date}",
                                                            color=0xf20006)
            await ctx.send(embed=embed)
        else:
            return await ctx.message.add_reaction("❌")

    @commands.command()
    async def add(self, ctx, *, text):
        if ctx.author.id not in self.bot.devs:
            return await ctx.send("Sorry! You aren't allowed to use this! Contact @Node#0721 to get "
                                  "yourself added as a dev!")

        game_name = re.match(r"game (.*)", text)
        if game_name:
            game_name = str(game_name.group(1))

            game_name = game_name.replace(" ", "_")

            cur.execute(f"""CREATE TABLE {game_name}
                            (released text, site text, genre text, author text, thumbnail text, count integer)""")
            cur.execute(f"INSERT INTO {game_name} VALUES (NULL, NULL, NULL, NULL, NULL, 0)")
            db.commit()

            game_name = game_name.replace("_", " ")
            embed = discord.Embed(title="Add Game", description=f"{game_name} added!",
                                  color=0xf20006)
            return await ctx.send(embed=embed)
        else:
            return await ctx.message.add_reaction("❌")

    @commands.command()
    async def what(self, ctx, *, text):
        text = text.replace("?", "")
        search = re.match(r"genre is (.*)", text)
        if str(text.lower()).startswith("games do you know"):
            cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
            games = cur.fetchall()

            game_list = []

            for i in games:
                game_list.append(i)

            game_list = str(game_list)
            game_list = game_list.replace("[", "")
            game_list = game_list.replace("]", "")
            game_list = game_list.replace("(", "")
            game_list = game_list.replace(")", "")
            game_list = game_list.replace("'", "")
            game_list = game_list.replace(",,", ",")
            game_list = game_list.replace("_", " ")

            embed = discord.Embed(title="Game List", description=f"Here is a list of all games "
                                                                 f"I have information on: {game_list}", color=0xf20006)
            await ctx.author.send(embed=embed)

        elif search:
            game = str(search.group(1))
            game = game.replace(" ", "_")

            cur.execute(f"SELECT genre FROM {game}")
            genre = cur.fetchall()
            genre = clean(str(genre))

            game = game.replace("_", " ")
            embed = discord.Embed(title="Game", description=f"{game}'s genre is: {genre}",
                                  color=0xf20006)
            return await ctx.send(embed=embed)

        search = re.match(r"is the website for (.*)", text)
        if search:
            game = str(search.group(1))
            game = game.replace(" ", "_")

            cur.execute(f"SELECT site FROM {game}")
            site = cur.fetchall()
            site = clean(str(site))

            game = game.replace("_", " ")
            embed = discord.Embed(title="Game", description=f"{game}'s site is: {site}",
                                  color=0xf20006)
            return await ctx.send(embed=embed)


    @commands.command()
    async def edit(self, ctx, *, text):
        if ctx.author.id not in self.bot.devs:
            return await ctx.send("Sorry! You aren't allowed to use this! Contact @Node#0721 to get "
                                  "yourself added as a dev!")

        search = re.match(r"(.*) release (.*)", text)
        if search:
            game = search.group(1)
            date = search.group(2)

            game = game.replace(" ", "_")

            cur.execute(f"""UPDATE {game}
                            SET released = '{date}'""")
            db.commit()

            cur.execute(f"SELECT * FROM {game}")
            result = cur.fetchall()
            result = clean_comma(str(result))

            game = game.replace("_", " ")
            embed = discord.Embed(title="Edit Game", description=f"{game} updated! New data: {result}.", color=0xf20006)
            return await ctx.send(embed=embed)

        search = re.match(r"(.*) site (.*)", text)
        if search:
            game = search.group(1)
            site = search.group(2)

            game = game.replace(" ", "_")

            cur.execute(f"""UPDATE {game}
                            SET site = '{site}'""")
            db.commit()

            cur.execute(f"SELECT * FROM {game}")
            result = cur.fetchall()
            result = clean_comma(str(result))

            game = game.replace("_", " ")
            embed = discord.Embed(title="Edit Game", description=f"{game} updated! New data: {result}.", color=0xf20006)
            return await ctx.send(embed=embed)

        search = re.match(r"(.*) genre (.*)", text)
        if search:
            game = search.group(1)
            genre = search.group(2)

            game = game.replace(" ", "_")

            cur.execute(f"""UPDATE {game}
                            SET genre = '{genre}'""")
            db.commit()

            cur.execute(f"SELECT * FROM {game}")
            result = cur.fetchall()
            result = clean_comma(str(result))

            game = game.replace("_", " ")
            embed = discord.Embed(title="Edit Game", description=f"{game} updated! New data: {result}.", color=0xf20006)
            return await ctx.send(embed=embed)

        search = re.match(r"(.*) author (.*)", text)
        if search:
            game = search.group(1)
            author = search.group(2)

            game = game.replace(" ", "_")

            cur.execute(f"""UPDATE {game}
                            SET author = '{author}'""")
            db.commit()

            cur.execute(f"SELECT * FROM {game}")
            result = cur.fetchall()
            result = clean_comma(str(result))

            game = game.replace("_", " ")
            embed = discord.Embed(title="Edit Game", description=f"{game} updated! New data: {result}.", color=0xf20006)
            return await ctx.send(embed=embed)

        search = re.match(r"(.*) thumbnail (.*)", text)
        if search:
            game = search.group(1)
            thumbnail = search.group(2)

            game = game.replace(" ", "_")

            cur.execute(f"""UPDATE {game}
                            SET thumbnail = '{thumbnail}'""")
            db.commit()

            cur.execute(f"SELECT * FROM {game}")
            result = cur.fetchall()
            result = clean_comma(str(result))

            game = game.replace("_", " ")
            embed = discord.Embed(title="Edit Game", description=f"{game} updated! New data: {result}.", color=0xf20006)
            return await ctx.send(embed=embed)


    @commands.command()
    async def tell(self, ctx, *, text):
        search = re.match(r"me about (.*)", text)
        if search:
            game = search.group(1)
            game = game.replace(" ", "_")

            cur.execute(f"SELECT released FROM {game}")
            date = cur.fetchall()
            date = clean(date)

            cur.execute(f"SELECT site FROM {game}")
            site = cur.fetchall()
            site = clean(site)

            cur.execute(f"SELECT genre FROM {game}")
            genre = cur.fetchall()
            genre = clean(genre)

            cur.execute(f"SELECT author FROM {game}")
            author = cur.fetchall()
            author = clean(author)

            url = "None"
            try:
                cur.execute(f"SELECT thumbnail FROM {game}")
                url = cur.fetchall()
                url = clean(str(url))
            except Exception:
                cur.execute(f"ALTER TABLE {game} ADD COLUMN thumbnail text")
                db.commit()

            count = 0
            try:
                cur.execute(f"SELECT count FROM {game}")
                count = cur.fetchall()
                count = clean(str(count))
            except Exception:
                cur.execute(f"ALTER TABLE {game} ADD COLUMN count integer")
                cur.execute(f"""UPDATE {game}
                                SET count = 0""")
                db.commit()

            game = game.replace("_", " ")

            embed = discord.Embed(title=f"__***{game}***__", description=f"__**Release Date**__"
                                                                         f"\n{date}\n\n__**Author**__\n{author}\n\n"
                                                                         f"__**Genre**__\n{genre}\n\n__**Website**__"
                                                                         f"\n{site}\n\n__**Known players in this server**__"
                                                                         f"\n{count}", color=0xf20006)
            if str(url) != "None":
                embed = embed.set_image(url=str(url))

            await ctx.send(embed=embed)

    @commands.command()
    async def help(self, ctx):
        embed = discord.Embed(title="__***Help***__", description="**Gamebot, what games do you know?**: Get a list of "
                                                                  "games the bot has information on.\n**Gamebot, when "
                                                                  "was (game name) released?**: Get the release "
                                                                  "date of a game.\n**Gamebot, what genre is "
                                                                  "(game name)?**: Get the genre of a game.\n"
                                                                  "**Gamebot, who (made/developed/wrote) (game_name)?"
                                                                  "**: Shows the developer of a game.\n**Gamebot, what "
                                                                  "is the website for (game name)?**: Shows the website "
                                                                  "for a game.\n**Gamebot, I don't/play (game name)**: "
                                                                  "Keeps track of how many people play certain games."
                                                                  "\n**Gamebot, time_convert (time) (timezone 1) "
                                                                  "(timezone 2)**: Convert a time from timezone 1 to "
                                                                  "timezone 2.\n**Gamebot, tell me about (game name)**"
                                                                  ": Get all information about a game.\n",
                              color=0xf20006)
        await ctx.send(embed=embed)

    @commands.command()
    async def who(self, ctx, *, text):
        text = text.replace("?", "")
        search = re.match(r"made (.*)", text)
        if search:
            game = str(search.group(1))
            game = game.replace(" ", "_")

            cur.execute(f"SELECT author FROM {game}")
            author = cur.fetchall()
            author = clean(author)

            game = game.replace("_", " ")
            embed = discord.Embed(title="Game", description=f"{game}'s developer is: {author}",
                                  color=0xf20006)
            await ctx.send(embed=embed)

        search = re.match(r"developed (.*)", text)
        if search:
            game = str(search.group(1))
            game = game.replace(" ", "_")

            cur.execute(f"SELECT author FROM {game}")
            author = cur.fetchall()
            author = clean(author)

            game = game.replace("_", " ")
            embed = discord.Embed(title="Game", description=f"{game}'s developer is: {author}",
                                  color=0xf20006)
            await ctx.send(embed=embed)

        search = re.match(r"wrote (.*)", text)
        if search:
            game = str(search.group(1))
            game = game.replace(" ", "_")

            cur.execute(f"SELECT author FROM {game}")
            author = cur.fetchall()
            author = clean(author)

            game = game.replace("_", " ")
            embed = discord.Embed(title="Game", description=f"{game}'s developer is: {author}",
                                  color=0xf20006)
            await ctx.send(embed=embed)

    @commands.command()
    async def I(self, ctx, *, text):
        text = text.replace("?", "")
        text = text.replace("'", "")
        search = re.match(r"play (.*)", text)
        if search:
            game = search.group(1)
            game = str(game).replace(" ", "_")

            cur.execute(f"SELECT count FROM {game}")
            count = cur.fetchall()
            count = clean(str(count))
            count = int(count)

            try:
                member_cur.execute(f"SELECT plays FROM '{ctx.author.name}_{ctx.author.id}'")
                plays = member_cur.fetchall()

                if game.lower() in clean(plays):
                    return await ctx.send("You already play this game!")
                else:
                    member_cur.execute(f"""INSERT INTO '{ctx.author.name}_{ctx.author.id}' (plays)
                                            VALUES ('{game.lower()}')
                                            """)
                    member_db.commit()
            except Exception as e:
                print(str(e))
                member_cur.execute(f"""CREATE TABLE '{ctx.author.name}_{ctx.author.id}'
                                        (plays text)""")
                member_cur.execute(f"""INSERT INTO '{ctx.author.name}_{ctx.author.id}' (plays)
                                        VALUES ('{game.lower()}')
                                        """)
                member_db.commit()

            count += 1
            cur.execute(f"""UPDATE {game}
                            SET count = {count}""")
            db.commit()

            embed = discord.Embed(title="Player Counter", description="Thanks! I'll save this information for later!",
                                  color=0xf20006)
            await ctx.send(embed=embed)

        search = re.match(r"dont play (.*)", text)
        if search:
            game = search.group(1)
            game = str(game).replace(" ", "_")

            cur.execute(f"SELECT count FROM {game}")
            count = cur.fetchall()
            count = clean(str(count))
            count = int(count)

            try:
                member_cur.execute(f"SELECT plays FROM '{ctx.author.name}_{ctx.author.id}'")
                plays = member_cur.fetchall()

                if game.lower() not in clean(plays):
                    return await ctx.send("I already knew that!")
                else:
                    member_cur.execute(f"""DELETE FROM '{ctx.author.name}_{ctx.author.id}'
                                            WHERE plays = '{game.lower()}'
                                            """)
                    member_db.commit()
            except Exception as e:
                print(str(e))
                member_cur.execute(f"""CREATE TABLE '{ctx.author.name}_{ctx.author.id}'
                                        (plays text)""")
                member_db.commit()
                return await ctx.send("I already knew that!")

            count -= 1
            cur.execute(f"""UPDATE {game}
                            SET count = {count}""")
            db.commit()

            embed = discord.Embed(title="Player Counter", description="Thanks! I'll save this information for later!",
                                  color=0xf20006)
            await ctx.send(embed=embed)

    @commands.command()
    async def time_convert(self, ctx, time: str, zone1, zone2):
        original_time = time
        time = time.replace(":", ".")
        time = float(time)
        if time >= 24 or time < 0:
            return await ctx.send("Please enter a valid time!")

        zone1 = zone1.lower()
        zone2 = zone2.lower()

        time_cur.execute(f"SELECT time FROM {zone1}")
        change = time_cur.fetchall()
        change = clean(change)
        change = int(change)

        if time - change < 0 and change != 0:
            loop1 = False
            loop2 = False
            remove = 0
            if remove > change:
                loop1 = True
            else:
                loop2 = True

            while loop1:
                if time - -1 < 0:
                    time = time + 24
                time = time - -1
                remove -= 1
                if remove == change:
                    loop1 = False

            while loop2:
                if time - 1 < 0:
                    time = time + 24
                time = time - 1
                remove += 1
                if remove == change:
                    loop2 = False
        else:
            time = time - change

        time_cur.execute(f"SELECT time FROM {zone2}")
        change = time_cur.fetchall()
        change = clean(change)
        change = int(change)

        if time + change < 0 and change != 0:
            loop1 = False
            loop2 = False
            remove = 0
            if remove > change:
                loop1 = True
            else:
                loop2 = True

            while loop1:
                if time + -1 < 0:
                    time = time + 24
                time = time + -1
                remove -= 1
                if remove == change:
                    loop1 = False

            while loop2:
                if time - 1 < 0:
                    time = time + 24
                time = time + 1
                remove += 1
                if remove == change:
                    loop2 = False
        else:
            time = time + change

        if time >= 24:
            time = time - 24

        time_str = "%.2f" % time
        time = time_str
        time = time.replace(".", ":")
        if time.endswith(":0"):
            time = time + "0"

        zone1 = zone1.upper()
        zone2 = zone2.upper()

        embed = discord.Embed(title="Time Conversion", description=f"{original_time} {zone1} is {time} {zone2}",
                              color=0xf20006)
        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(src(bot))
