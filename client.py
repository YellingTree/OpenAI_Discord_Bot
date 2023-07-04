import discord
import conversation as convers
import config

discord_client = discord.Client(intents=config.bot_intents)

@discord_client.event
async def on_message(message):
    if message.content.startswith(config.chat_command) or discord_client.user in message.mentions or message.reference is not None and message.author != discord_client.user:
        mention_string = f'<@{discord_client.user.id}>'
        server_id = message.guild.id
        conversation = convers.MemoryManagement.get_conversation(server_id)
        user_message = message.content
        if mention_string in user_message:
            user_message = user_message.replace(mention_string, config.mention_replacement)
        if config.chat_command in message.content:
            user_message = user_message[len(config.chat_command):]
        prompt = conversation + user_message + config.seperator
        response, failstate = await convers.ResponseManagement.create_response(server_id, conversation, user_message, prompt)
        message_blocks = []
        message_blocks = convers.ResponseManagement.create_messages(server_id, response, conversation, user_message, failstate)
        for block in message_blocks:
            await message.channel.send(block)
    if message.content.startswith(config.reset_command):
        server_id = message.guild.id
        convers.MemoryManagement.clear_conversation(server_id)
        await message.channel.send("Conversation reset, memory cleared.")
discord_client.run(config.discord_token)
