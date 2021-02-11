#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Feb 11 11:14:54 2021

@author: edombek
"""

import imaplib
import email
from email.header import decode_header
#import webbrowser
#import os
import io
from time import sleep
import json
import vk_api
from vk_api.utils import get_random_id

conf = json.loads(open('config.json').read())

# из конфига
username = conf['username']
password = conf['password']
vk_token = conf['vk_token']
peer_id = conf['peer_id']

#подключаем ВК
vk_session = vk_api.VkApi(token = vk_token)
vk = vk_session.get_api()
upload = vk_api.VkUpload(vk_session)

def uploadDoc(filename, dat):
    file = io.BytesIO(dat)
    doc = upload.document_message(
        file,
        title=filename,
        peer_id=peer_id
    )
    file.close()
    return f"doc{doc['doc']['owner_id']}_{doc['doc']['id']},"

def clean(text):
    # clean text for creating a folder
    return "".join(c if c.isalnum() else "_" for c in text)

def decode(bitesandencoding):
    b, encoding = bitesandencoding
    s = ''
    if isinstance(b, bytes):
        if encoding == None:
            s = b.decode()
        else:
            s = b.decode(encoding)
    else:
        s = str(b)
    return s

def newMsg(msg):
    vk_msg = ''
    attachments = ''
    for response in msg:
        if isinstance(response, tuple):
            # генерируем письмо
            msg = email.message_from_bytes(response[1])
            # получаем тему письма
            try:
                subject = decode(decode_header(msg["Subject"])[0])
            except:
                subject = 'None'
            # получаем отправителя
            try:
                From = decode(decode_header(msg.get("From"))[0])
            except:
                From = 'None'
            try:
                mail = decode(decode_header(msg.get("From"))[1])
            except:
                mail = 'None'
            print("Тема:", subject)
            print("От кого:", From)
            vk_msg = f'Тема: {subject}\nОт кого: {From} {mail}\n'
            # получаем тип сообщения
            content_type = msg.get_content_type()
            # если сообщение электронной почты составное
            if msg.is_multipart():
                # проходимя по всем частям
                for part in msg.walk():
                    content_disposition = str(part.get("Content-Disposition"))
                    try:
                        # пытаемся получить содержимое
                        body = part.get_payload(decode=True).decode()
                        print(body)
                        vk_msg += f'\n{body}'
                    except:
                        pass
                    if "attachment" in content_disposition:
                        # скачиваем вложения
                        filename = part.get_filename()
                        data = part.get_payload(decode=True)
                        try:
                            attachments+=uploadDoc(filename, data)
                        except:
                            pass
                        
            else:
                # получаем содержимое
                body = msg.get_payload(decode=True).decode()
                if content_type == "text/plain":
                    # выводим только текстовые части электронного письма
                    print(body)
                    vk_msg += f'\n{body}'
            if content_type == "text/html":
                # отображение письма в браузере (законспектированно)
                # if it's HTML, create a new HTML file and open it in browser
                #folder_name = clean(subject)
                #if not os.path.isdir(folder_name):
                    # make a folder for this email (named after the subject)
                    #os.mkdir(folder_name)
                filename = "index.html"
                #filepath = os.path.join(folder_name, filename)
                # write the file
                print(body)
                vk_msg += f'\n{body}'
                #open(filepath, "w").write(body)
                # open in the default browser
                #webbrowser.open(filepath)
            print("="*100)
    return vk_msg, attachments

# создаём класс IMAP4 с SSL
imap = imaplib.IMAP4_SSL("imap.gmail.com")
# автоизуемся
imap.login(username, password)

#то что уже вы почте
status, messages = imap.select("INBOX")
result, data = imap.search(None, "ALL")
old_id_list = data[0].split()

print('Бот запущен')

#цикл получения новых писем
while True:
    #получаем список новых писем
    status, messages = imap.select("INBOX")
    result, data = imap.search(None, "ALL")
    id_list = data[0].split() # Разделяем ID писем
    new_id_list = list(set(id_list).difference(set(old_id_list)))
    for id in new_id_list:
        # получаем письмо по ID
        res, msg = imap.fetch(id, "(RFC822)")
        # обрабатываем письмо
        vk_msg, attachments = newMsg(msg)
        vk_msg = vk_msg.replace('<br />', '\n')
        vk.messages.send(random_id=get_random_id(), peer_id=peer_id,
                         message=vk_msg, attachment=attachments)
    old_id_list = id_list
    sleep(5)
# закрываем соединение и выходим, (но зачем после вечного цикла?) )))
imap.close()
imap.logout()