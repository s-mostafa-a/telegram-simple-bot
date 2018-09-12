import threading
import time

import requests


class BotHandler:
    def __init__(self, token):
        self.token = token
        self.api_url = "https://api.telegram.org/bot{}/".format(token)
        self.chats = []
        self.messages = []
        self.updates = []
        self.first_unread_message = 0

    def get_updates(self, offset=None, timeout=30):
        method = 'getUpdates'
        params = {'timeout': timeout, 'offset': offset}
        try:
            resp = requests.get(self.api_url + method, params)
        except requests.exceptions.ConnectionError:
            print("could not connect to telegram!")
            return []
        result_json = resp.json()['result']
        for key in result_json:
            kl = key.keys()
            if key['update_id'] not in self.updates and 'message' in kl:
                self.updates.append(key['update_id'])
                self.messages.append(key['message'])
                if key['message']['chat']['id'] not in self.chats:
                    self.chats.append(key['message']['chat'])
        return result_json

    def send_message(self, chat_id, text):
        params = {'chat_id': chat_id, 'text': text}
        method = 'sendMessage'
        resp = requests.post(self.api_url + method, params)
        return resp

    def get_unread_messages(self):
        self.get_updates()
        new_messages = []

        while self.messages and self.first_unread_message < len(self.messages):
            new_messages.append(self.messages[self.first_unread_message])
            self.first_unread_message += 1

        return new_messages


my_bot = BotHandler("<your_bot_token>")


class Printer(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)

    def run(self):
        while True:
            messages = my_bot.get_unread_messages()
            for message in messages:
                last_chat_text = message['text']
                last_chat_name = message['chat']['first_name']
                print(last_chat_name + ": " + last_chat_text)


class Writer(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)

    def run(self):
        while True:
            while not my_bot.chats:
                print("No chat found! check your connection or maybe your bot has no audience!")
                time.sleep(2)

            print("You have these audiences:\n")
            chat_ids = []
            for chat in my_bot.chats:
                if chat['id'] not in chat_ids:
                    chat_ids.append(chat['id'])
                    print(chat['first_name'] + ": " + str(chat['id']) + "\n")
            user_chat_id = input("Enter a chat id: (or type all for all of your audiences)\n")
            message = input("Enter your message:\n")
            if user_chat_id == "all":
                for chat in chat_ids:
                    my_bot.send_message(chat, message)
            elif int(user_chat_id) in chat_ids:
                my_bot.send_message(user_chat_id, message)
            else:
                print("Did not find similar chat id!\n")


def main():
    Writer().start()
    Printer().start()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        exit()
