import disnake
from disnake.ext import commands
from disnake.ext import tasks
from disnake.utils import find

from datetime import datetime
from markdownify import markdownify
from dotenv import load_dotenv
import os
import random

from oasis import getGrades
from tesla import getInternships, getInternshipInfos


load_dotenv()
# TOKEN = os.getenv('TOKEN')
TOKEN = os.environ['TOKEN']


bot = commands.Bot()


@tasks.loop(minutes=30)
async def tesla():
    internships = getInternships()

    ### Polytech
    guild = find(lambda g: 'PEIP' in g.name, bot.guilds)
    channel = find(lambda c: 'tesla' in c.name, guild.text_channels)
    
    messages = await channel.history(limit=None).flatten()
    
    previousListings = [
        int(message.embeds[0].footer.text)
        for message in messages
        if len(message.embeds)
    ]
    
    newListings = [l for l in internships if not int(l['id']) in previousListings]
    
    if len(newListings):
        await channel.send('||@everyone||')
    
    for listing in newListings:
        infosListing = getInternshipInfos(listing['id'])
        embed = disnake.Embed(
            title = f"Nouveau stage Tesla : {infosListing['title']}",
            color = 0xC90000,
            url = f'https://www.tesla.com/fr_FR/careers/search/job/{listing["id"]}',
            description = markdownify(
                infosListing['description']
                .replace('</div>', '</div> ')
            ),
            timestamp = datetime.now()
        )
        embed.set_thumbnail('https://www.tesla.com/themes/custom/tesla_frontend/assets/favicons/favicon-196x196.png')
        embed.set_footer(text=listing['id'])
        embed.add_field(name ='Localisation', value=infosListing['location'], inline=False)
        embed.add_field(name ='Département', value=infosListing['department'], inline=False)
        
        await channel.send(embed=embed)
        print(infosListing['title'])


@tasks.loop(minutes=10)
async def grades():
    grades = getGrades()

    ### Polytech
    guild = find(lambda g: 'PEIP' in g.name, bot.guilds)
    channel = find(lambda c: 'nouvelles-notes' in c.name, guild.text_channels)

    messages = await channel.history(limit=None).flatten()

    
    ### New Grades
    previousGrades = [
        message.embeds[0].footer.text
        for message in messages
        if len(message.embeds)
        and message.embeds[0].title.startswith('Nouvelle note')
    ]
    
    newGrades = [
        grade for grade in grades
        if not f"{grade['subject-id']} - {grade['name']}" in previousGrades
        and grade['grade'] is not None
    ]
    
    if len(newGrades):
        await channel.send('||@everyone||')
    
    for grade in newGrades:
        embed = disnake.Embed(
            title=f"Nouvelle note en {grade['subject']} !",
            color=0x00A8E8,
            url='https://oasis.polytech.universite-paris-saclay.fr/',
            description=grade['name'],
            timestamp=grade['date'],
        )

        oasis_icon = 'https://oasis.polytech.universite-paris-saclay.fr/prod/bo/picture/favicon/polytech_paris_oasis/favicon-194x194.png'
        embed.set_thumbnail(oasis_icon)
        embed.set_footer(text = f"{grade['subject-id']} - {grade['name']}")

        await channel.send(embed=embed)
        print(f"{grade['subject-id']} - {grade['name']}")
    
    
    ### Pending grades
    previousPendingGrades = [
        message.embeds[0].footer.text
        for message in messages
        if len(message.embeds)
        and 'bientôt' in message.embeds[0].title.lower()
    ]
    
    newPendingGrades = [
        grade for grade in grades
        if not f"{grade['subject-id']} - {grade['name']}" in previousPendingGrades
        and grade['grade'] is None
    ]

    for grade in newPendingGrades:
        embed = disnake.Embed(
            title=f"*Note bientôt disponible en {grade['subject']}*  👀",
            color=0x00A8E8,
            url='https://oasis.polytech.universite-paris-saclay.fr/',
            description=grade['name'],
            timestamp=grade['date'],
        )
        embed.set_footer(text = f"{grade['subject-id']} - {grade['name']}")

        await channel.send(embed=embed)
        print(f"[ SOON ] {grade['subject-id']} - {grade['name']}")


@tasks.loop(minutes=10)
async def bot_presence():
    '''Shows "Playing {message}" on Discord'''
    texts = [
        ("Regarde", "vos notes 👀"),
        ("Regarde", "les polys de cours 📖"),
        ("Regarde", "des stages pour cet été 🧑‍💼"),
        ("Regarde", "ta moyenne générale 📉"),
        ("Joue à", "réviser 📚"),
        ("Écoute", "le cours 🧑‍🏫"),
    ]
    text = random.choice(texts)
    
    if text[0] == "Joue à":
        await bot.change_presence(activity=disnake.Game(name=text[1]))
    elif text[0] == "Regarde":
        await bot.change_presence(activity=disnake.Activity(type=disnake.ActivityType.watching, name=text[1]))
    elif text[0] == "Écoute":
        await bot.change_presence(activity=disnake.Activity(type=disnake.ActivityType.listening, name=text[1]))

@bot.event
async def on_ready():
    bot_pr.start()
    tesla.start()
    grades.start()

bot.run(TOKEN)
