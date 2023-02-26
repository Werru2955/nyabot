#!/usr/bin/env python3

import discord
import json
import random

import data_manager
import interaction_views

intents = discord.Intents.default()
intents.message_content = True

bot = discord.Bot(intents=intents)

gifs = {}
with open("gifs.json") as file:
    gifs = json.load(file)

lines = {}
with open("lines.json") as file:
    lines = json.load(file)

HELP_MESSAGE = """
Gif commands:
```
hug - Hugs target user
kiss - Kisses target user 
cuddle - Cuddles with target user 
hold - Hold target user's hand 
pat - Gives the targeted user headpats 
wag - Makes the target user's tail wag  
fuck - Does some "stuff" to the target user 😳 
flush - Makes the target user blush 
lewd - Makes you say that it's too lewd 
boop - Boops target user
```

Slash commands:
```
/help - Shows this message
/marry - Marries someone
```
"""


def __find_mariage_for_member_id(member_id: int) -> list[int]:
    data = data_manager.get_data()
    if "marriages" not in data:
        data["marriages"] = []
        with data_manager.DataWriter() as writer:
            writer.set_data(data)
        return []

    for marriage in data["marriages"]:
        if member_id in marriage:
            return marriage

    return []


# Slash commands


@bot.slash_command()
@discord.guild_only()
@discord.option(
    "target", type=discord.Member,
    description="Which user to marry",
    required=True,
)
async def marry(
        context: discord.ApplicationContext, member_to_marry: discord.Member
):
    # TODO: Refactor marriage system
    # This function is massive, it should be split up, and probably in another file!

    # Check if the person asked in mariage is interested
    marriage_asker = context.author
    if marriage_asker is None:
        await context.respond("ow :/ something went wonky wonky, try again!")
        return

    askers_marriage = __find_mariage_for_member_id(marriage_asker.id)
    askees_marriage = __find_mariage_for_member_id(member_to_marry.id)

    if member_to_marry.id in askers_marriage:  # Already married
        await context.respond(f"u are already married to {member_to_marry.mention}, silly!")
        return

    marriage_confirmation = interaction_views.MariageConfirmationView(
        member_to_marry
    )
    await context.respond(
        f"{member_to_marry.mention}, would you like to marry"
        + f" {marriage_asker.mention}?", view=marriage_confirmation)

    await marriage_confirmation.wait()
    if marriage_confirmation.user_accepted is None:
        await context.respond("silly little bug going on :3 try again l8er :3")
        return

    if marriage_confirmation.user_accepted == False:
        await context.respond(
            "no consent == no marriage! consent is key to a happy life :3"
        )

    # Marriage was accepted, yay :3!
    # Now check for polycules
    if len(askers_marriage) == 0 and len(askees_marriage) == 0:
        # No polycules, just update the records to marry the two :3
        data = data_manager.get_data()
        data["marriages"].append([marriage_asker.id, member_to_marry.id])
        with data_manager.DataWriter() as writer:
            writer.set_data(data)

        await context.respond(
            f"{marriage_asker.mention} married {member_to_marry.mention}"
        )

        return

    users_who_confirmed_the_marriage = [marriage_asker.id, member_to_marry.id]

    users_who_need_to_allow_marriage = askees_marriage
    users_who_need_to_allow_marriage += askers_marriage

    for user_to_ask in users_who_need_to_allow_marriage:
        if user_to_ask in users_who_confirmed_the_marriage:
            continue

        user_to_ask_as_member = await bot.fetch_user(user_to_ask)

        polycule_confirmation_view = interaction_views.PolyculeMemberJoinConfirmationView(
            user_to_ask_as_member)

        member_to_add_to_polycule = member_to_marry if member_to_marry.id not in __find_mariage_for_member_id(
            user_to_ask) else marriage_asker

        await context.respond(
            f"{user_to_ask_as_member.mention}, do you agree to adding "
            + f"{member_to_add_to_polycule.mention} to the polycule?",
            view=polycule_confirmation_view
        )

        await polycule_confirmation_view.wait()

        if polycule_confirmation_view.user_accepted is None:
            await context.respond("you hit a bug owo. nothing i can do, try again!")
            return

        if polycule_confirmation_view.user_accepted == False:
            await context.respond(f"seems like {user_to_ask_as_member} doesn't want " +
                                  "to take new people in the polycule yet... can't proceed with mariage")
            return

        users_who_confirmed_the_marriage.append(user_to_ask)

    # Everyone agrees, let's register the marriage
    data = data_manager.get_data()

    # Disband existing marriages with members of the new polycule to avoid issues
    id_of_marriages_to_disband = []
    for index, marriage in enumerate(data["marriages"]):
        for user in users_who_confirmed_the_marriage:
            if user in marriage:
                id_of_marriages_to_disband.append(index)
    for i in id_of_marriages_to_disband:
        if len(data["marriages"]) <= 0:
            # No marriages left, so nothing to disband!
            break
        data["marriages"].pop(i)

    # Register the new marriage
    data["marriages"].append(users_who_confirmed_the_marriage)

    with data_manager.DataWriter() as writer:
        writer.set_data(data)

    formated_polycule_list = '\n'.join(
        [f"- <@{user_id}>" for user_id in users_who_confirmed_the_marriage])
    await context.respond(f"woo! a new polycule was formed! members:\n{formated_polycule_list}")


@bot.slash_command()
async def help(ctx: discord.ApplicationContext):
    await ctx.respond(HELP_MESSAGE)

# Commands


async def gif_command_handler(message: discord.Message, command: list[str]):
    command_typed = command[0]

    target = message.author.name
    sender = message.author.name
    if len(message.mentions) > 0:
        target = message.mentions[0].name

    if command_typed == "help":
        await message.reply(HELP_MESSAGE)
        return

    if command_typed not in gifs:
        await message.reply(
            "im so sorry, i have no such thing to give you for now... come back later :3")
        return

    choosen_gif = random.choice(gifs[command_typed])
    choosen_line = random.choice(lines[command_typed])
    choosen_line = choosen_line.replace("$1", sender)
    choosen_line = choosen_line.replace("$2", target)
    await message.reply(f"{choosen_line}\n{choosen_gif}")

GIF_COMMANDS = [
    "hug",
    "kiss",
    "cuddle",
    "hold",
    "pat",
    "wag",
    "fuck",
    "blush",
    "lewd",
    "boop",
]

# Discord events


@bot.event
async def on_message(message: discord.Message):
    if message.author.bot == True:
        return

    # TODO: Do proper parsing of the message
    message_as_command = message.content.split(" ")

    command = message_as_command[0]
    if command in GIF_COMMANDS:
        await gif_command_handler(message, message_as_command)


bot.run(open("token").read())
