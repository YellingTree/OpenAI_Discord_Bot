import os
import discord
import openai

#region Global Vars

#Log program and bot response types to a logfile, does not write conversation data to log.
logging = False

#Discord Bot Intents and Key, defined in code bc lazy
discord_token = 'YOUR_BOT_KEY'
bot_intents = discord.Intents.default()
bot_intents.message_content = True
Discord_Client = discord.Client(intents=bot_intents)

chat_command = "/c" #Defines what a message needs to start with for ai to respond to a message.
reset_command = "/reset" #Defines the reset command for the conversation history of the bot.

#OpenAI API compleation Variables and API key, again in code bc lazy
openai.api_key = ("YOUR_OPENAI_API_KEY")
ai_model = "Your-Compleation-model"
token_limit = 1500 #Refer to openai api docs for the token limits of your base model
stop_generation = "END" #Defines the stop word for the api to end text generation
top_prob = .9 #Defines the probability mass used for text generation, refer to openai doc for more info
freq_penailty = 1.8 #Defines the penailty for reused tokens, refer to openai docs.
bias = {"21017": -100} #Defines tokens that should not be generated, currently the tokens for '###' have a 100% chance of NEVER appaering. Refer to openai docs for more info

#endregion

#region Conversation Management

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

#endregion

#region Discord Events

#Startup event
@Discord_Client.event
async def on_ready():
    print(Discord_Client.user, " has connected to Discord servers.")

#Bot response event
@Discord_Client.event
async def on_message(message):
    if message.content.startswith(chat_command):
        server_id = message.guild.id
        formatting = " \n\n###\n\n" # Seporator used to seperate each message.

        conversation = GetConversation(server_id)
        user_message = message.content #Content of message send on discord server
        user_message = user_message[2:] # Removes chat command from message

        prompt = conversation + user_message + formatting #Conversation must be added to begining of prompt. fomatting added to the end to prep for next message.
        failed = False
        #This whole try expect block attempts to get a response from the model, it trys a second time when the api throws an error, most likely max tokens
        #It tries twice, editing the conversation to the last 10 messages on the second attempt to try and reduce token usage
        #If that fails it wipes the conversation, warning the user and setting failed to True, saving the empty conversation to the chat history file.
        #Otherwise it will just update the chat history file with the formatting required to keep the chat history concise.
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
        #Discord won't let you send a message with nothing in it, models sometimes will respond with an empty string, this checks for this and warns the user.
        if response == "" or response == " ":
            response = "Attempted to send empty message"
            await message.channel.send(response)
        #This is checking to make sure the response doesn't hit discord's max character limit of 2000, with a double check for part 2 of the response.
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
    #Resets the conversation file apon a reset commmand
    if message.content.startswith(reset_command):
        GetConversation(server_id)
        ClearConversation(server_id)
        alert = "Conversation reset"
        await message.channel.send(alert)

#endregion

Discord_Client.run(discord_token)
