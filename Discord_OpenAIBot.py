import os
import discord
import openai

#Log program and bot response types to a logfile, does not write conversation data to log.
logging = False

#Discord Bot Intents and Key, defined in code bc lazy
discord_token = 'YOUR_BOT_KEY'
bot_intents = discord.Intents.default()
bot_intents.message_content = True
Discord_Client = discord.Client(intents=bot_intents)

#OpenAI API compleation Variables and API key, again in code bc lazy
openai.api_key = ("YOUR_OPENAI_API_KEY")
ai_model = "Your-Compleation-model"
token_limit = 1500 #Refer to openai api docs for the token limits of your base model
stop_generation = "END" #Defines the stop word for the api to end text generation
top_prob = .9 #Defines the probability mass used for text generation, refer to openai doc for more info
freq_penailty = 1.8 #Defines the penailty for reused tokens, refer to openai docs.
bias = {"21017": -100} #Defines tokens that should not be generated, currently the tokens for '###' have a 100% chance of NEVER appaering. Refer to openai docs for more info

####Functions for Chat History Management####

#Get conversation file for the discord server bot is called from or create an empty file for new servers.
def GetConversation(server_id):
    conversation = ""
    file_path = "./chats/" + str(server_id) + ".txt"
    if os.path.isfile(file_path):
        with open(file_path, "r") as conversation_file:
            conversation = conversation_file.read()
    else:
        with open(file_path, "w") as new_file:
            new_file.write("")
    return(conversation)

#Save conversation to chat file based on orgin server ID
def SaveConversation(server_id, conversation):
    file_path = "./chats/" + str(server_id) + ".txt"
    with open(file_path, "w") as conversation_file:
        conversation_file.write(conversation)

#Edit the conversation once a max_token expection has been hit to preserve short term memory.
def EditConversation(conversation):
    mark = "###" #Seperator used in training data/conversation format.
    count = 10 #How many interations of mark to preserve. Data between marks is saved.
    conversation = str(conversation) #sanity check
    parts = conversation.rsplit(mark, count)
    conversation = mark.join(parts[-count:])
    return(conversation)

#Clear the conversation from the orgin server
def ClearConversation(server_id):
    file_path = "./chats/" + str(server_id) + ".txt"
    with open(file_path, "w") as conversation_file:
        conversation_file.write("")
    conversation = ""
    return(conversation)
#OpenAI API request for AI response
def OpenaiApiRequest(api_prompt):
    response = openai.Completion.create(model=ai_model, prompt=api_prompt, max_tokens=token_limit, stop=stop_generation, top_p=top_prob, frequency_penalty=freq_penailty, logit_bias=bias)
    response = response['choices'][0]['text']
    return(response)

####Discord Client and Chat Logic####

#Startup event
@Discord_Client.event
async def on_ready():
    print(Discord_Client.user, " has connected to Discord servers.")

#Bot response event
@Discord_Client.event
async def on_message(message):
    if message.content.startswith('/c').lower():
        server_id = message.guild.id
        formatting = " \n\n###\n\n"

        conversation = GetConversation(server_id)
        user_message = message.content
        user_message = user_message[2:] # Removes /c from message

        prompt = conversation + user_message + formatting
        failed = False
        try:
            response = OpenaiApiRequest(prompt)
        except:
            conversation = EditConversation(conversation)
            new_prompt = conversation + user_message + formatting
            try:
                response = OpenaiApiRequest(new_prompt)
            except:
                response = "Edit Error, clearing conversation to continue."
                conversation = ClearConversation(server_id)
                failed = True
        if failed:
            SaveConversation(server_id, conversation)
        else:
            SaveConversation(server_id, conversation + user_message + formatting + response + stop_generation + formatting)
        if response == "" or response == " ":
            response = "Attempted to send empty message"
            await message.channel.send(response)
        elif len(response) > 2000:
            length = len(response)
            part1 = response[:2000]
            part2 = response[2000:length]
            if len(part2) > 2000:
                part2len = len(part2)
                part2 = response[2000:4000]
                part3 = response[4000:part2len]
                await message.channel.send(part1)
                await message.channel.send(part2)
                await message.channel.send(part3)
            else:
                await message.channel.send(part1)
                await message.channel.send(part2)
        else:
            await message.channel.send(response)
    if message.content.startswith("/reset"):
        GetConversation(server_id)
        ClearConversation(server_id)
        alert = "Conversation reset"
        await message.channel.send(alert)
Discord_Client.run(discord_token)