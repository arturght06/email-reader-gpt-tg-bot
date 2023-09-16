import imaplib
# import socks
import getpass
# from pprint import pprint
import time
from time import sleep
import email
from email.header import decode_header
import base64
from saving import read_db, write_number_to_db
import quopri
import requests
from bs4 import BeautifulSoup
import openai
import json
from config import api_key
from imap_dicts import imap_dict



emails_file_name = "email_accounts.txt"
db_file_name = "db.json"

def imap_server(email_account):
    login, password = email_account.split(":")
    imap_server = imap_dict.get(login.split("@")[1])
    return imap_server

# print(read_db(db_file_name))


# global number_imap_connects
# number_imap_connects = [0]
global imap_list
imap_list = {}

def get_imap(email_account):
    if email_account in imap_list:
        return imap_list.get(email_account)
    else:
        imap = imaplib.IMAP4_SSL(imap_server(email_account))

        login, password = email_account.split(':')
        imap.login(login, password)
        imap_list[email_account] = imap
        return imap



def read_emails(email_account):
    # Разбиваем строку с почтой на части: почта и пароль
    

    # Создаем IMAP-сессию
    

    try:
        # Авторизуемся на почтовом аккаунте
        
        imap = get_imap(email_account)
        # print(imap)

        # Выбираем папку "INBOX" (входящие письма)
        imap.select("INBOX")

        # Получаем список всех писем в папке "INBOX"
        status, email_ids = imap.search(None, "ALL")

        if status == "OK":
            email_ids = str(email_ids[0]).replace("b'", "").replace("'", "").split()
            return [len(email_ids), email_ids]
            # for email_id in email_ids:
            #     # Получаем текст каждого письма
            #     status, email_data = imap.fetch(email_id, "(RFC822)")
            #     if status == "OK":
            #         email_message = email_data[0][1]
                    # pprint(email_message)
    finally:
        # Завершаем сессию и закрываем соединение с IMAP-сервером и прокси
        # imap.logout()
        pass

##################################################################3

def get_chatbot_response(letter_text, api_key):
    openai.api_key = api_key
    messages = [ {"role": "system", "content": 
                  "You are a part of program."} ]
    message = "".join(["Вот текст письма которое я получил, напиши в формате Facebook login-code: 123456 или Instagram registration code 123456, если письмо с каким-то кодом для login, registration or deposit-code etc. Если письмо с ссылкой для перехода то напиши в код ответа что-то такое: twitter login-link: https://twitter.com/login/auth... . Если письмо о другом то напиши максимум 3  слова и назвaние сервиса который это отправил в таком формате: название сервиса 3 главных слов описания код или ссылка из письма. Код из письма нужно подставить в ответ. Bот текст письма:", letter_text])
    messages.append( {"role": "user", "content": message}, )
    chat = openai.ChatCompletion.create( model="gpt-3.5-turbo", messages=messages )
    reply = chat.choices[0].message.content

    # print(reply)
    # answer = response_data['choices'][0]['message']['content']
    return reply



def from_subj_decode(msg_from_subj):
    if msg_from_subj:
        encoding = decode_header(msg_from_subj)[0][1]
        msg_from_subj = decode_header(msg_from_subj)[0][0]
        if isinstance(msg_from_subj, bytes):
            msg_from_subj = msg_from_subj.decode(encoding)
        if isinstance(msg_from_subj, str):
            pass
        msg_from_subj = str(msg_from_subj).strip("<>").replace("<", "")
        return msg_from_subj
    else:
        return None

from bs4 import BeautifulSoup


##################################################################3

def read_new_emails(email_account, id_s):
    # Создаем IMAP-сессию
    login, password = email_account.split(":")

    imap = get_imap(email_account)


    imap.select("INBOX")
    arr_all = []
    for email_id in id_s:
        mail_list = {}
        mail_list['id'] = email_id

        status, email_data = imap.fetch(str(email_id), "(RFC822)")
        # print(type(email_data[0][1]), email_data[0][1])
        msg = email.message_from_bytes(email_data[0][1])

        mail_list['from'] = msg["Return-path"]
        subject = from_subj_decode(msg["Subject"])
        # print(type(subject[0]), subject[0].decode(subject[1]))
        mail_list['subject'] = subject
        payload=msg.get_payload()
        soup = BeautifulSoup(payload, features="html.parser")    
        try:
            mail_text = soup.get_text().decode("utf-8")
        except:
            mail_text = soup.get_text()
        mail_list['text'] = mail_text
        text_by_chatgpt = get_chatbot_response(mail_text, api_key)
        mail_list['short'] = text_by_chatgpt
        mail_list['to'] = login

        arr_all.append(mail_list)
    return arr_all




if __name__ == "__main__":
    # imap_server = "outlook.office365.com"  # Замените на сервер вашей почты
    # email_account = input("Введите почту и пароль в формате email:password: ")

    # Грузим аккаунты в базу с количеством писем
    with open(emails_file_name, "r") as f:
        with open(db_file_name, "w") as read_file:
            pass
        print("Грузим аккаунты")
        arr_mails = (f.read()).split("\n")
        # print(arr_mails)
        for email_account in arr_mails:
            login, password = email_account.split(':')
            # start = time.time()
            number_mails = read_emails(email_account)

            write_number_to_db(db_file_name, email_account, number_mails)
            # print(f"{login}: {number_mails}")
            # print('mail_time:', time.time() - start)
        print(f"База успешно загружена!")

        while True:
            read_db_list = read_db(db_file_name)
            for email_account in read_db_list:
                number_new, number_ids_new = read_emails(email_account)

                number_old = read_db_list.get(email_account)[0]
                number_ids_old = read_db_list.get(email_account)[1]

                result = list(set(number_ids_new) - set(number_ids_old))

                if len(result) != 0:
                    # print(number_old, number_new) #, read_emails(email_account))
                    mail_number = read_emails(email_account)
                    result_arr = read_new_emails(email_account, result)
                    print("To:", result_arr[0]['to'], "-"*15, "NEW EMAIL", "-"*15)
                    print(result_arr[0]['short'])


                    write_number_to_db(db_file_name, email_account, mail_number)

                    

            sleep(10)

