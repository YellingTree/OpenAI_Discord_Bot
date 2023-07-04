import discord
bot_intents = discord.Intents.default()
bot_intents.message_content = True

discord_token = '' #Discord Bot Token
openai_api_key = ("") #OpenAI API key

chat_command = "/chat" #Conversation Command
reset_command = "/reset" #Reset Memory Command
max_characters = 2000 #Max discord message length 2000 is the max
mention_replacement = "ex. AI, bob" #Replaces the @user mention id for a plain name
delete_empty_messages = True #Determines if responses that consist of empty strings or only spaces should be saved.
crop_amount = 10 #Determines how many of the oldest messages get removed from the conversation upon token limits being reached

creation_model = "" #Completion Model you wish you use
token_usage_limit = 1500 #Max amount of tokens that can be used for each response
stop_generation = "END" #End variable for completion model, used to stop generation
top_prob = .9 #Probability mass, refer to openai docs
freq_pen = 1.8 #Repeated token use penalty
bias = {"21017": -100} #Example, the token for ### will never be generated
seperator = "\n\n###\n\n" #Denominator for separation of prompts and responses in training data



