import discord, os, re, random, keep_alive

client = discord.Client()

polls = {}

@client.event
async def on_ready():
    print(f'{client.user} has connected to Discord!')
    await client.change_presence(activity=discord.Game(name='Type [poll] for help'))

@client.event
async def on_raw_reaction_add(payload):
    if payload.message_id in polls:
        if payload.emoji.id in [e.id for e in polls[payload.message_id]['emojis']]:
            author = polls[payload.message_id]['author']
            title = polls[payload.message_id]['title']
            question = polls[payload.message_id]['question']
            options = polls[payload.message_id]['options']
            emojis = polls[payload.message_id]['emojis']
            emoji_to_option = polls[payload.message_id]['emoji_to_option']
            polls[payload.message_id]['options'][emoji_to_option[payload.emoji.id]] += 1
            await polls[payload.message_id]['message'].edit(embed=prettyPrintEmbed(payload.message_id, author, title, question, options, emojis))

@client.event
async def on_raw_reaction_remove(payload):
    if payload.message_id in polls:
        if payload.emoji.id in [e.id for e in polls[payload.message_id]['emojis']]:
            author = polls[payload.message_id]['author']
            title = polls[payload.message_id]['title']
            question = polls[payload.message_id]['question']
            options = polls[payload.message_id]['options']
            emojis = polls[payload.message_id]['emojis']
            emoji_to_option = polls[payload.message_id]['emoji_to_option']
            polls[payload.message_id]['options'][emoji_to_option[payload.emoji.id]] -= 1
            await polls[payload.message_id]['message'].edit(embed=prettyPrintEmbed(payload.message_id, author, title, question, options, emojis))

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith('[poll]'):
        if message.content == '[poll]':
            await message.channel.send(embed=displayHelp())
            return
        if message.content.startswith('[poll] clear'):
            for poll in polls:
                author = polls[poll]['author']
                title = polls[poll]['title']
                question = polls[poll]['question']
                options = polls[poll]['options']
                emojis = polls[poll]['emojis']
                emoji_to_option = polls[poll]['emoji_to_option']
                await polls[poll]['message'].edit(embed=prettyPrintEmbed(poll, author, title + ' [inactive]', question, options, emojis))
            polls.clear()
            return
        if message.content.startswith('[poll] inactive'):
            poll_id = int(message.content[len('[poll] inactive '):])
            author = polls[poll_id]['author']
            title = polls[poll_id]['title']
            question = polls[poll_id]['question']
            options = polls[poll_id]['options']
            emojis = polls[poll_id]['emojis']
            emoji_to_option = polls[poll_id]['emoji_to_option']
            await polls[poll_id]['message'].edit(embed=prettyPrintEmbed(poll_id, author, title + ' [inactive]', question, options, emojis))
            del polls[poll_id]
            return
        if message.content.startswith('[poll] active'):
            await message.channel.send([p for p in polls])
            return
        user_input = list(map(lambda x : x.strip('[]'), re.findall('\[.+?\]', message.content[len('[poll] '):])))
        if len(user_input) < 2:
            await message.channel.send('Not enough info. Need [title] [question] [option1] [option2] ...')
            return
        title, question = user_input[0:2]
        options = {o : 0 for o in user_input[2:]}
        emojis = list(e for e in message.guild.emojis if not e.animated)
        random.shuffle(emojis)
        emojis = emojis[0:len(options)]
        emoji_to_option = dict(zip([e.id for e in emojis], options))
        m = await message.channel.send(embed=prettyPrintEmbed(message.id, message.author, title, question, options, emojis))
        polls[m.id] = {'message': m, 'author': message.author, 'title': title, 'question': question, 'options': options, 'emojis': emojis, 'emoji_to_option': emoji_to_option}
        await m.edit(embed=prettyPrintEmbed(m.id, message.author, title, question, options, emojis))
    
def prettyPrintEmbed(poll_id, author, title, question, options, emojis):
    embed = discord.Embed(title=f'{title} (id: ||{poll_id}||)', description=f'**{question}**\nTubby who asked: {author}', color = 0x0000ff)
    for option, emoji in zip(options, emojis):
        embed.add_field(name='\u200b', value=f'{emoji} {option} - **{options[option]}**', inline=True)
    return embed

def displayHelp():
    text = '''[poll] [title] [question] [option1] ... [option25]
    [poll] active (list active polls)
    [poll] inactive <id> (make poll with id inactive)
    [poll] clear (make all polls inactive)
    '''
    embed = discord.Embed(title='For Dummies', color = 0x00ff00)
    embed.add_field(name='Commands', value=text, inline=False)
    return embed

keep_alive.keep_alive()

client.run(os.getenv('CLIENT_TOKEN'))
