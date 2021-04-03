import discord, dns, os, re, random, keep_alive
from pymongo import MongoClient

cluster = MongoClient(os.getenv('MONGO_URL'))
db = cluster['dev']
collection = db['polls']

client = discord.Client()

@client.event
async def on_ready():
    print(f'{client.user} has connected to Discord!')
    await client.change_presence(activity=discord.Game(name='Type [poll] for help'))

@client.event
async def on_raw_reaction_add(payload):
    channel = client.get_channel(payload.channel_id)
    msg = await channel.fetch_message(payload.message_id)
    poll = collection.find_one({'_id': payload.message_id})
    if poll and payload.emoji.id in poll['emoji_ids']:
        option = poll['emoji_to_option'][str(payload.emoji.id)]
        poll['options'][option] += 1
        collection.update_one({'_id': poll['_id']}, {'$inc': {f"options.{option}": 1}})
        await msg.edit(embed=prettyPrintEmbed(poll['_id'], poll['author'], poll['title'], poll['question'], poll['options'], poll['emoji_ids']))

@client.event
async def on_raw_reaction_remove(payload):
    channel = client.get_channel(payload.channel_id)
    msg = await channel.fetch_message(payload.message_id)
    poll = collection.find_one({'_id': payload.message_id})
    if poll and payload.emoji.id in poll['emoji_ids']:
        option = poll['emoji_to_option'][str(payload.emoji.id)]
        poll['options'][option] -= 1
        collection.update_one({'_id': poll['_id']}, {'$inc': {f"options.{option}": -1}})
        await msg.edit(embed=prettyPrintEmbed(poll['_id'], poll['author'], poll['title'], poll['question'], poll['options'], poll['emoji_ids']))

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith('[poll]'):
        if message.content == '[poll]':
            await message.channel.send(embed=displayHelp())
            return
        if message.content.startswith('[poll] active'):
            await message.channel.send([p['_id'] for p in collection.find()])
            return
        if message.content.startswith('[poll] inactive'):
            poll_id = int(message.content[len('[poll] inactive '):])
            poll = collection.find_one({'_id': poll_id})
            if poll:
                try:
                    msg = await message.channel.fetch_message(poll['_id'])
                    await msg.edit(embed=prettyPrintEmbed(poll['_id'], poll['author'], poll['title'] + ' [inactive]', poll['question'], poll['options'], poll['emoji_ids']))
                except:
                    pass
                finally:
                    collection.delete_one({'_id': poll_id})
            return
        if message.content.startswith('[poll] clear'):
            active_poll_exists = False
            for poll in collection.find():
                active_poll_exists = True
                try:
                    msg = await message.channel.fetch_message(poll['_id'])
                    await msg.edit(embed=prettyPrintEmbed(poll['_id'], poll['author'], poll['title'] + ' [inactive]', poll['question'], poll['options'], poll['emoji_ids']))
                except:
                    pass
            if active_poll_exists:
                collection.delete_many({})
            return
        if message.content.startswith('[test] pin'):
            poll_id = int(message.content[len('[poll] pin '):])
            try:
                msg = await message.channel.fetch_message(poll_id)
                if msg:
                    await msg.pin()
            except:
                pass
            return
        user_input = list(map(lambda x : x.strip('[]'), re.findall('\[.+?\]', message.content[len('[poll] '):])))
        if len(user_input) < 2:
            await message.channel.send('Not enough info dummy! Need [title] [question] [option1] [option2] ...')
            return
        title, question = user_input[0:2]
        options = {o : 0 for o in user_input[2:]}
        emojis = list(e for e in message.guild.emojis if not e.animated)
        random.shuffle(emojis)
        emoji_ids = [e.id for e in emojis[0:len(options)]]
        emoji_to_option = dict(zip(map(str, emoji_ids), options))
        m = await message.channel.send(embed=prettyPrintEmbed(message.id, str(message.author), title, question, options, emoji_ids))
        poll = {'_id': m.id, 'author': str(message.author), 'title': title, 'question': question, 'options': options, 'emoji_ids': emoji_ids, 'emoji_to_option': emoji_to_option}
        await m.edit(embed=prettyPrintEmbed(m.id, str(message.author), title, question, options, emoji_ids))
        collection.insert_one(poll)
    
def prettyPrintEmbed(poll_id, author, title, question, options, emoji_ids):
    embed = discord.Embed(title=f'{title} (id: ||{poll_id}||)', description=f'**{question}**\nTubby who asked: {author}', color = 0x0000ff)
    for option, emoji_id in zip(options, emoji_ids):
        emoji = client.get_emoji(emoji_id)
        embed.add_field(name='\u200b', value=f'{emoji} {option} - **{options[option]}**', inline=True)
    return embed

def displayHelp():
    text = '''[poll] [title] [question] [option1] ... [option25]
    [poll] active (list active polls)
    [poll] inactive <id> (make poll with id inactive)
    [poll] clear (make all polls inactive)
    [poll] pin <id> (pin poll with id)
    '''
    embed = discord.Embed(title='For Dummies', color = 0x00ff00)
    embed.add_field(name='Commands', value=text, inline=False)
    return embed

keep_alive.keep_alive()

client.run(os.getenv('CLIENT_TOKEN'))
