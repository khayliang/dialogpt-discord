from transformers import AutoModelWithLMHead, AutoTokenizer
import torch
import discord
import time
import yaml

class ChatBot(object):
    def __init__(self, buffer=5, time=15):
        self.tokenizer = AutoTokenizer.from_pretrained("microsoft/DialoGPT-medium")
        self.model = AutoModelWithLMHead.from_pretrained("microsoft/DialoGPT-medium")
        self.bot_input_ids = None
        self.chat_history_ids = None
        self.buffer = buffer
        
        self.past_reply = ""

        self.buffer_count = 0

        self.friend = None
        self.time_upon_reply = None
        self.buffer_time = time

    def chat(self, message):
        if message.author == client.user:
            return

        if message.content.startswith('$imlonely'):
            self.friend = message.author
            self.time_upon_reply = time.time()
            return "Hey! I can chat with you."

        elif time.time() < self.time_upon_reply+self.buffer_time and message.author == self.friend:
            user_message = message.content
            reply = self.reply(user_message)
            self.time_upon_reply = time.time()
            return reply

        elif time.time() > self.time_upon_reply+self.buffer_time and message.author == self.friend:
            self.friend = None
            self.time_upon_reply = None
            return "Sorry, got to go. Start another conversation with $imlonely"

    def reply(self, message):
        new_user_input_ids = self.tokenizer.encode(message + self.tokenizer.eos_token, return_tensors='pt')

        self.bot_input_ids = torch.cat([self.chat_history_ids, new_user_input_ids], dim=-1) if self.buffer_count > 0 else new_user_input_ids
        self.chat_history_ids = self.model.generate(self.bot_input_ids, max_length=1000, pad_token_id=self.tokenizer.eos_token_id)

        reply = format(self.tokenizer.decode(self.chat_history_ids[:, self.bot_input_ids.shape[-1]:][0], skip_special_tokens=True))

        if self.past_reply == reply:
            self.buffer_count = 0

        self.past_reply = reply

        return reply

if __name__ == "__main__":

    with open('config.yaml') as f:   
        data = yaml.load(f, Loader=yaml.FullLoader)

    token = data['token']
    buffer = data['buffer']
    time = data['time']
    
    client = discord.Client()
    chatbot = ChatBot(buffer, time)
    
    @client.event
    async def on_ready():
        print('We have logged in as {0.user}'.format(client))

    @client.event
    async def on_message(message):
        reply = chatbot.chat(message)
        await message.channel.send(reply)

    try:
        client.run(token)
    except:
        print("Couldn't start bot. Check if your bot token is correct in config.yaml")