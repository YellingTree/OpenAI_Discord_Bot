import os
import openai
import config

openai.api_key = config.openai_api_key
class MemoryManagement():
    #Gather conversation from file using server id for filenames
    def get_conversation(server_id: str):
        conversation = _IO.manage_file(server_id, "r")
        return(conversation)
    #Cuts the top part of the conversation off to reduce length while saving newer messages
    def crop_conversation(conversation: str):
        conversation = str(conversation)
        parts = conversation.rsplit(config.seperator, config.crop_amount)
        conversation = config.seperator.join(parts[-config.crop_amount])
        return(conversation)
    #Saves conversation to file.
    def save_conversation(server_id: str, conversation: str):
        _IO.manage_file(server_id, "w", conversation)
    #Clears the conversation file with an empty string
    def clear_conversation(server_id):
        _IO.manage_file(server_id, "w", "")

class ResponseManagement():
    #Request an response from OpenAI servers and formatting to a basic string
    async def _api_request(prompt: str):
        response = openai.Completion.create(model = config.creation_model, prompt = prompt, max_tokens = config.token_usage_limit, stop = config.stop_generation, top_p = config.top_prob, frequency_penalty = config.freq_pen, logit_bias = config.bias)
        response = response['choices'][0]['text']
        return(response)
    #Attempts to create a response, shortening the conversation if tokens are hit or alerting a user to an issue.
    async def create_response(server_id: str, conversation, user_message, prompt):
        processing_error = False
        try:
            response = await ResponseManagement._api_request(prompt)
        except openai.error.InvalidRequestError as e:
            if 'tokens' in str(e):
                conversation = MemoryManagement.crop_conversation(conversation)
                new_prompt = conversation + user_message + config.seperator
                response = await ResponseManagement._api_request(new_prompt)
            else:
                response = "An unknow error has occured."
                processing_error = True
        except openai.error.RateLimitError as e:
            response = "The response generation is being rate-limited, try again later."
        except openai.error.OpenAIError as e:
            response = "An error has occured on OpenAI servers, try again later."
        return(response, processing_error)
    #Creates a list of messages to be sent out, splitting the response into 2000 char blocks to allow them to be sent via discord
    def create_messages(server_id: str, response: str, conversation: str, user_message: str, failstate: bool):
        if response == "" or response == " ":
            response = "Generated an empty message."
            failstate = config.delete_empty_messages
        if failstate:
            MemoryManagement.save_conversation(server_id, conversation)
        else:
            updated_conversation = conversation + user_message + config.seperator + response + config.stop_generation + config.seperator
            MemoryManagement.save_conversation(server_id, updated_conversation)
        message_blocks = []
        if len(response) < config.max_characters:
            message_blocks.append(response)
        else:
            i=0
            while i < len(response):
                block = response[i:i+config.max_characters]
                message_blocks.append(block)
                i += config.max_characters
        return(message_blocks)
           
class _IO():
    #Checks to make sure conversation file exists, creating one if not
    def _file_check(server_id: str):
        current_directory = os.path.dirname(os.path.abspath(__file__))
        chats_dir = os.path.join(current_directory, "chats")
        if not os.path.exists(chats_dir):
            os.makedirs(chats_dir)
        file_path = os.path.join(chats_dir, str(server_id) + ".txt")
        if not os.path.exists(file_path):
            with open(file_path, "w") as conversation_file:
                conversation_file.write("")
        return(file_path)
    #Manages the conversation file for ease of use.
    def manage_file(server_id :str, operation: str, data: str = ""):
        file_path = _IO._file_check(server_id)
        with open(file_path, operation) as managed_file:
            if operation == "w" or operation == "a":
                managed_file.write(data)
                managed_file.close
            if operation == "r":
                retrived_data = managed_file.read()
                managed_file.close()
                return(retrived_data)
    
