import openai
import telebot
import uuid
import os
from pydub import AudioSegment


token_bot = open('gpt token tg bot', 'r').read()
token_gpt = open('gpt token', 'r').read()
bot = telebot.TeleBot(token_bot)
openai.api_key = token_gpt


@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message,
                 "Введите запрос, чтобы обратиться к chatGPT или /image, чтобы обратиться к DALL-E. Чтобы очистить историю запросов к chatGPT, напишите /clear")



@bot.message_handler(commands=['image'])
def send_image(message):
    try:
        bot.send_message(message.chat.id, 'Обрабатываю запрос')
        message.text = message.text.replace('/image', '')
        response = openai.Image.create(prompt=message.text, n=1, size="1024x1024")
        image_url = response['data'][0]['url']
        bot.send_photo(message.chat.id, image_url)
    except:
        bot.send_message(message.chat.id, 'Не получилось обработать запрос, попробуйте позже')


user_messages = {}


@bot.message_handler(commands=['clear'])
def clear_history(message):
    user_messages[message.from_user.id] = []
    bot.send_message(message.chat.id, 'История запросов очищена.')


@bot.message_handler(content_types=['voice'])
def voice_processing(message):
    try:
        bot.send_message(message.chat.id, 'Обрабатываю голосовой запрос')
        file_name_ogg = str(uuid.uuid4()) + '.ogg'
        file_name_mp3 = str(uuid.uuid4()) + '.mp3'
        file_info = bot.get_file(message.voice.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        with open(file_name_ogg, 'wb') as new_file:
            new_file.write(downloaded_file)
            AudioSegment.from_ogg(file_name_ogg).export(file_name_mp3, format="mp3")
        with open(file_name_mp3, "rb") as audio_file:
            transcript = openai.Audio.transcribe("whisper-1", audio_file)
        request = transcript.text
        completion = openai.ChatCompletion.create(model="gpt-3.5-turbo",
                                                  messages=[{'role': 'user', 'content': request}])
        print(completion, request)
        bot.send_message(message.chat.id, completion["choices"][0]["message"]["content"])
        os.remove(file_name_ogg)
        os.remove(file_name_mp3)
    except:
        bot.send_message(message.chat.id, 'Не получилось обработать запрос, попробуйте позже')


@bot.message_handler(func=lambda message: True)
def send_answer(message):
    global user_messages
    try:
        if message.from_user.id not in user_messages:
            user_messages[message.from_user.id] = []
        user_messages[message.from_user.id].append({'role': 'user', 'content': message.text})
        bot.send_message(message.chat.id, 'Обрабатываю запрос.')
        completion = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=user_messages[message.from_user.id])
        print(completion)
        bot.send_message(message.chat.id, completion["choices"][0]["message"]["content"])
        user_messages[message.from_user.id].append(
            {'role': 'assistant', 'content': completion["choices"][0]["message"]["content"]})
    except:
        bot.send_message(message.chat.id, 'Не получилось обработать запрос, попробуйте позже')


bot.polling()
