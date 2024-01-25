import asyncio
import signal
import sys
import discord
from discord import app_commands
from discord.ext import commands, tasks
from dotenv import load_dotenv
import openai
import yaml
from sql import *
from utils import *
import logging

def signal_handler(sig, frame):
    sys.exit(0)


signal.signal(signal.SIGTERM, signal_handler)


load_dotenv()

with open('config.yml', 'r') as f:
    config = yaml.safe_load(f)


openai.api_key = os.getenv("OPENAI_API_KEY")
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_IDS = config['channel_ids']
COOLDOWN_DURATION = config['cooldown_duration']
PLAYING_STATUS = config['playing_status']
RANDOM_SENTENCES = config['random_sentences']
PAIENS_ID = config['paiens_id']


bot = commands.Bot(command_prefix='/',intents=discord.Intents.all())


@bot.event
async def on_ready():
    try:
        await bot.tree.sync()
    except Exception as e:
                print(f"An error occurred while syncing commands: {e}")
    await bot.change_presence(activity=discord.Game(name=PLAYING_STATUS))
    create_tables()
    check_for_new_pictures()
    await asyncio.sleep(wait_until_3am())
    count_reactions.start()


@bot.event
async def on_message(message):
    proba = random.random()

    '''
        if message.author.id == PAIENS_ID['Alexandre']:
        proba *= 0.2
    '''

    if  proba < 0.02:
        sentence = random.choice(RANDOM_SENTENCES)
        if type(sentence) == list:
            sentence = random.choice(sentence)

        await message.channel.send(sentence)

    await bot.process_commands(message)


@bot.tree.command(name="jouer",description="ca fait une p'tite game ouuuuuu?")
async def jouer(interaction: discord.Interaction):
    if interaction.channel_id not in CHANNEL_IDS:
        return
    await choose_and_tag_two_random_persons(interaction)


@bot.tree.command(name="chat",description="Besoin d'un ami? Je suis là pour toi!")
async def chat(interaction: discord.Interaction, demande: str):
    await interaction.response.defer()
    response=openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": demande.strip()}
        ]
    )
    if not isinstance(response, dict):
        raise TypeError("Expected a dictionary")
    message = str(response["choices"][0]["message"]["content"])
    parts = split_message_at_sentence_or_paragraph(message)
    
    for part in parts:
        await interaction.followup.send(part)


@bot.tree.command(name="cam", description="Je met ma cam (des fois je me trompe malheureusement)")
async def cam(interaction: discord.Interaction):    
    directory = 'pictures'
    image = select_image_and_update_weights()
    
    if not image:
        await interaction.response.send_message("No pictures available.")
        return
    path = os.path.join(directory, image)
    await interaction.response.send_message(file=discord.File(path))
    message = await interaction.original_response()
    save_message(message, image)
    await message.add_reaction('👍')
    await message.add_reaction('👎')


@bot.tree.command(name="kill",description="Je suis trop jeune pour mourir...")
async def kill(interaction: discord.Interaction):
    if interaction.user.id in [PAIENS_ID['Pierre'], PAIENS_ID['Yann']]:
        await interaction.response.send_message("D'accord, je m'en vais...")
        await bot.close()

    elif interaction.user.id == PAIENS_ID['Alexandre']:
        await interaction.response.send_message("Mais enfin, tu ne vas pas te suicider Alexandre ! Tu es trop beau pour ça..")

    elif random.random() < 0.99:
        await interaction.response.send_message("Tu peux pas me tuer, je suis Lelexou. Et je suis immortel.")

    else:
        await interaction.response.send_message("Tu m'as eu cette fois-ci, je m'en vais... ")
        await bot.close()


@bot.tree.command(name="chut", description="Franchement ? mérité")
@app_commands.describe(nom="Qui doit se taire ?")
@app_commands.choices(nom=[
    discord.app_commands.Choice(name="Lelio", value="Lelio"),
    discord.app_commands.Choice(name="Pierre", value="Pierre"),
    discord.app_commands.Choice(name="Yann", value="Yann")
])
async def tg(interaction: discord.Interaction, nom: discord.app_commands.Choice[str],):
    
    if interaction.user.id not in [PAIENS_ID['Pierre'], PAIENS_ID['Yann'], PAIENS_ID['Lelio']]:
        await interaction.response.send_message("Toi, tu te tais")
        return
    calomnied = None
    if isinstance(interaction.channel, (discord.TextChannel, discord.VoiceChannel)):
        calomnied = interaction.channel.guild.get_member(PAIENS_ID[nom.name])

    if calomnied is not None:
        if nom.name == "Lelio":
            nickname = ["bouclette", "bringy", "Lélio", "Le L"]
            await interaction.response.send_message(
                f"Tais-toi {random.choice(nickname)} !"
            )
        

        elif interaction.user.id == PAIENS_ID['Lelio']:
            demande = "écrit un message d'éloge et d'amour pour " + calomnied.mention + " en 3 lignes max"
            response=openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": demande.strip()}
            ]
            )
            if not isinstance(response, dict):
                raise TypeError("Expected a dictionary")
            message = str(response["choices"][0]["message"]["content"])
            await interaction.response.send_message(message)        
        
        else:
            await interaction.response.send_message(
                f"Tais-yoi {calomnied.mention}"
            )


@bot.tree.command(name="delay", description="Temps avant, ou depuis le début de l'arc")
@app_commands.describe(arc="Choisis ton arc ouuuuuu")
@app_commands.choices(arc=[
    discord.app_commands.Choice(name="Jeajeanne", value="Jeajeanne"),
    discord.app_commands.Choice(name="Projet Secret", value="Projet Secret")
])
async def delay(interaction: discord.Interaction, arc: discord.app_commands.Choice[str],):

    if arc.name == "Jeajeanne":
        now = datetime.now()
        start = datetime(2023, 11, 6, 0, 34, 0)
        delta = now - start
        timeString = format_remaining_time(delta.total_seconds())
        string = f"L'arc Jeajeanne a démarré depuis {timeString} 👀"
        await interaction.response.send_message(string)

    else:
        now = datetime.now()
        end = datetime(2024, 5, 8, 22, 0, 0)
        lelexou = None
        if isinstance(interaction.channel, (discord.TextChannel, discord.VoiceChannel)):
            lelexou = interaction.channel.guild.get_member(PAIENS_ID['Alexandre'])
            delta = end - now
            timeSeconds = delta.total_seconds()
            timeString = format_remaining_time(timeSeconds)

            if timeSeconds >= 0:
                if lelexou is None:
                    string = f"Il te reste {timeString} !"
                else:
                    string = f"Il te reste {timeString} !\n{lelexou.mention}"

                if interaction.user.id == PAIENS_ID['Alexandre']:
                    string += "\n Crois en toi, n'écoute pas les autres, tu vas y arriver !"

                await interaction.response.send_message(string)

            else:
                if interaction.user.id == PAIENS_ID['Thomas']:
                    await interaction.response.send_message("Comment tu vas beau brun 👀 ?")
                    return
                
                await interaction.response.send_message("Le temps est écoulé malheureusement...")

    
@bot.tree.command(name="clear")
@app_commands.describe(amount="The amount of messages to clear")
@commands.is_owner()
async def clear(interaction:discord.Interaction, amount:int = 5):
    try:
        await interaction.response.defer()
        if isinstance(interaction.channel, discord.TextChannel):
            await interaction.channel.purge(limit=amount)
        else:
            await interaction.followup.send("Cette commande ne peut être utilisée que dans un salon textuel.")
    except Exception as e:
        print(f"Une erreur est survenue lors de la suppression des messages: {e}")

async def choose_and_tag_two_random_persons(interaction):
    channel = interaction.channel
    members_with_access = channel.members
    eligible_members = [member for member in members_with_access if not member.bot and member.id != interaction.user.id and 
                        member.status != discord.Status.offline and member.id not in [PAIENS_ID['Thomas'], PAIENS_ID['Alexandre']]]
    
    if len(eligible_members) < 2:
        await interaction.response.send_message("Il n'y a pas assez de gens cools en ligne.")
        return

    chosen_members = random.sample(eligible_members, 2)
    member1, member2 = chosen_members

    '''
    if PAIENS_ID['Alexandre'] in [member1.id, member2.id]:
        if PAIENS_ID['Alexandre'] == member2.id:
            member1, member2 = member2, member1
        
        await interaction.response.send_message(f"{member1.mention} tu veux pas réinstaller LoL pour jouer avec {member2.mention} ?")
    else:
        await interaction.response.send_message(f"{member1.mention} tu joues pas avec {member2.mention} ?")
    '''
    await interaction.response.send_message(f"{member1.mention} tu joues pas avec {member2.mention} ?")

@tasks.loop(hours=24)
async def count_reactions():
    log("Updating reactions...")
    conn = sqlite3.connect('lelexou.db')
    c = conn.cursor()
    c.execute("SELECT * FROM messages")
    rows = c.fetchall()
    up, down = 0, 0
    for row in rows:
        channel = bot.get_channel(CHANNEL_IDS[1])
        if isinstance(channel, discord.TextChannel):
            try:
                message = await channel.fetch_message(row[0])
                reactions = message.reactions

                for reaction in reactions:
                    if reaction.emoji == '👍':
                        up = reaction.count 

                    elif reaction.emoji == '👎':
                        down = reaction.count 

                ratio = up/down

                c.execute("UPDATE pictures SET coefficient = coefficient * ? WHERE path = ?", (ratio, row[1]))

                log(f"Updated coefficient of {row[1]} with ratio: {ratio}")


            except Exception:
                c.execute("DELETE FROM messages WHERE id = ?", (row[0],))
    c.execute("DELETE FROM messages")
    conn.commit()
    conn.close()
    log( "Reactions updated successfully")
    log(f"number of rows in messages: {len(rows)}")
    log("")
    check_for_new_pictures()




if __name__ == '__main__':
    logging.basicConfig(filename='lelexou.log', level=logging.WARNING,
                    format='%(asctime)s - %(levelname)s - %(message)s')
    bot.run(str(BOT_TOKEN))

