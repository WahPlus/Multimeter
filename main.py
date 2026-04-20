import json
import random

import nextcord
from nextcord.ext import commands
import re
import textrace
import asyncio

ongoing_races = {}

bot = commands.Bot(intents=nextcord.Intents.all())

class TokenError(Exception):
    pass

with open("db.json") as f:
    db = json.load(f)

tag_db = db["tag_servers"]

# Valid tokens
condition_tokens = {
    "&",
    "|",
    "^"
}
variable_tokens = {
    "msg"
}
match_tokens = {
    "has",
    "HAS",
    "startswith",
    "STARTSWITH",
    "hasword",
    "HASWORD",
    "regex",
    "=",
    "=="
}
action_tokens = {
    "say": 2,
    "reply": 2,
    "react": 2
}
setting_tokens = {
    "check_self": 2
}

def tokenize(multimod: str):
    tokenized = {}
    regex_output = re.findall(r"^\s*(.+?)\s*{\s*(.+)\s*}\s*$", multimod)
    if not regex_output:
        raise TokenError("condition-action structure not found")
    tokenized["condition"] = regex_output[0][0]
    tokenized["action"] = regex_output[0][1]
    if tokenized["condition"].count("\"") % 2 or tokenized["condition"].count("'") % 2:
        raise TokenError("condition contains unclosed quotes")
    tokenized["condition"] = re.findall(r"\"[^\"]*\"|'[^\"]*'|[|&^]|[^\s|&^\"]+", tokenized["condition"])
    for i, condition_token in enumerate(tokenized["condition"]):
        tokenized["condition"][i] = condition_token.strip("\"").strip("'")
    grouped = []
    current_group = []
    for token in tokenized["condition"]:
        if token in condition_tokens:
            if current_group:
                grouped.append(current_group)
                current_group = []
            grouped.append(token)
        else:
            current_group.append(token)
    if current_group:
        grouped.append(current_group)
    tokenized["condition"] = grouped

    if tokenized["action"].count("\"") % 2 or tokenized["action"].count("'") % 2:
        raise TokenError("action contains unclosed quotes")
    tokenized["action"] = re.split(r";\s*", tokenized["action"])
    for i, action in enumerate(tokenized["action"]):
        tokenized["action"][i] = re.findall(r"\"[^\"]*\"|'[^\"]*'|[^\s\"]+", action)
        for i2, action_token in enumerate(tokenized["action"][i]):
            tokenized["action"][i][i2] = action_token.strip("\"").strip("'")

    # Check that everything is valid
    if type(tokenized["condition"][0]) == str or type(tokenized["condition"][len(tokenized["condition"]) - 1]) == str:
        raise TokenError("unexpected condition token at start or end of condition")

    for condition_group in tokenized["condition"]:
        if type(condition_group) == list:
            if len(condition_group) != 3:
                raise TokenError(f"3 tokens expected in condition group, got {len(condition_group)}")
            if condition_group[0] not in variable_tokens:
                raise TokenError(f"unknown token where variable token expected: {condition_group[0]}")
            if condition_group[1] not in match_tokens:
                raise TokenError(f"unknown token where match token expected: {condition_group[1]}")
        elif type(condition_group) == str:
            if condition_group not in condition_tokens:
                raise TokenError(f"unknown token where condition token expected: {condition_group}")

    for action in tokenized["action"]:
        if action[0] not in action_tokens and action[0] not in setting_tokens:
            raise TokenError(f"unknown token where action or setting token expected: {action[0]}")
        if len(action) != action_tokens[action[0]] and len(action) != setting_tokens[action[0]]:
            raise TokenError(f"{action_tokens[action[0]] or setting_tokens[action[0]]} tokens expected in action group, got {len(action)}")
    return tokenized

def detokenize(items):
    result = []
    for item in items:
        if isinstance(item, list):
            result.append(detokenize(item))
        else:
            result.append(item)
    return " ".join(result)

@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')
    await bot.get_channel(1359151976994308219).send("It seems I have woken up in a 2008 Dacia Sandero.")

@bot.slash_command()
async def tag(interaction: nextcord.Interaction):
    pass

@tag.subcommand(description="Add a tag")
async def add(interaction: nextcord.Interaction, tag: str):
    await interaction.response.defer(ephemeral=True)
    try:
        tokenized = tokenize(tag)
    except TokenError as e:
        await interaction.send(f"Malformed tag: {e}")
    else:
        await interaction.send(f"Tag added!\n`{tokenized}`")
        if not str(interaction.guild_id) in tag_db:
            tag_db[str(interaction.guild_id)] = []
        tag_db[str(interaction.guild_id)].append(tokenized)
        with open("db.json", "w") as f:
            json.dump(db, f)

@tag.subcommand(description="Remove a tag")
async def remove(interaction: nextcord.Interaction, tag: int):
    await interaction.response.defer(ephemeral=True)
    if not interaction.user.guild_permissions.manage_guild:
        await interaction.send("You need the Manage Server permission to manage tags")
        return
    if tag_db[str(interaction.guild_id)] and tag_db[str(interaction.guild_id)][tag]:
        tag_db[str(interaction.guild_id)].pop(tag)
        with open("db.json", "w") as f:
            json.dump(db, f)
        await interaction.send(f"Tag removed!\n")
    else:
        await interaction.send(f"No such tag ")

@tag.subcommand(name="list", description="List tags")
async def list_(interaction: nextcord.Interaction):
    await interaction.response.defer(ephemeral=True)
    string = ""
    if tag_db[str(interaction.guild_id)]:
        for i, tag in enumerate(tag_db[str(interaction.guild_id)]):
            string += f"{i} - `{detokenize(tag["condition"]) + " {" + detokenize(tag["action"]) + "}"}`\n"
    else:
        string = "No tags for this server."
    await interaction.send(embed=nextcord.Embed(color=nextcord.Color.blue(), title="Tag list", description=string))

@tag.subcommand(description="Export tags to a txt file")
async def export(interaction: nextcord.Interaction):
    await interaction.send("Maybe in 2027")

@tag.subcommand(name="import", description="Import tags from a txt file")
async def import_(interaction: nextcord.Interaction, file: nextcord.Attachment):
    await interaction.send("Maybe in 2027")

@bot.event
async def on_message(message: nextcord.Message):
    if message.author != bot.user:
        for guild in tag_db:
            if str(message.guild.id) == guild:
                tags = tag_db[guild]
                for tag in tags:
                    for condition_group in tag["condition"]:
                        last_operator = None
                        condition = None
                        if type(condition_group) == list:
                            if condition_group[0] == "msg":
                                comparing_var = message.content

                            previous_condition = condition

                            if condition_group[1] == "has":
                                condition = condition_group[2].lower() in comparing_var.lower()
                            if condition_group[1] == "HAS":
                                condition = condition_group[2] in comparing_var
                            if condition_group[1] == "startswith":
                                condition = comparing_var.lower().startswith(condition_group[2].lower())
                            if condition_group[1] == "STARTSWITH":
                                condition = comparing_var.startswith(condition_group[2])
                            if condition_group[1] == "hasword":
                                condition = all(elem in comparing_var.lower().split() for elem in condition_group[2].lower().split())
                            if condition_group[1] == "HASWORD":
                                condition = all(elem in comparing_var.lower().split() for elem in condition_group[2].split())
                            if condition_group[1] == "regex":
                                condition = bool(re.search(condition_group[2], comparing_var, re.IGNORECASE))
                            if condition_group[1] == "REGEX":
                                condition = bool(re.search(condition_group[2], comparing_var))
                            if condition_group[1] == "=":
                                condition = comparing_var.lower() == condition_group[2].lower()
                            if condition_group[1] == "==":
                                condition = comparing_var == condition_group[2]

                            if last_operator == "|":
                                condition = previous_condition or condition
                            if last_operator == "&":
                                condition = previous_condition and condition
                            if last_operator == "^":
                                condition = bool(previous_condition) ^ condition

                        elif type(condition_group) == str:
                            last_operator = condition_group

                    if condition:
                        for action in tag["action"]:
                            if action[0] == "say":
                                await message.channel.send(action[1])
                            if action[0] == "reply":
                                await message.reply(action[1])
                            if action[0] == "react":
                                await message.add_reaction(action[1])

        if message.channel.id in ongoing_races:
            for race in ongoing_races[message.channel.id]:
                if message.content.lower() == race["answer"].lower():
                    ongoing_races.pop(message.channel.id)
                    if not "users" in db:
                        db["users"] = {}
                    if str(message.author.id) not in db["users"]:
                        db["users"][str(message.author.id)] = {}
                    if "balance" not in db["users"][str(message.author.id)]:
                        db["users"][str(message.author.id)]["balance"] = 0
                    db["users"][str(message.author.id)]["balance"] = round(db["users"][str(message.author.id)]["balance"] + race["prize"], 2)
                    with open("db.json", "w") as f:
                        json.dump(db, f)

                    await message.channel.send(f"**{message.author.name}** has won the race! {race["prize"]} internet points have been deposited into **{message.author.name}**'s account.")
        elif random.randint(1, 100) == 1:
            # Start text race
            internet_value, text, image_buffer = textrace.generate_image()
            await message.channel.send(f"**TEXT RACE!**\nType this text in 60 seconds to get {internet_value} internet points!", file=nextcord.File(image_buffer, filename="bumbler.png"))
            if message.channel.id not in ongoing_races:
                ongoing_races[message.channel.id] = []
            ongoing_races[message.channel.id].append({"answer": text, "prize": internet_value})
            await asyncio.sleep(60)
            race_still_going = False
            if message.channel.id in ongoing_races and {"answer": text, "prize": internet_value} in ongoing_races[message.channel.id]:
                ongoing_races.pop(message.channel.id)
                await message.channel.send(f"**Time's up!**\nThe answer was **{text}**.")

with open("token.txt") as f:
    token = f.read()

bot.run(token)
