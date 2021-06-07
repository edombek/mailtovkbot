#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Feb 11 11:14:54 2021

@author: edombek
"""

import imaplib
import email
from time import sleep
import json
import vk_api
from vk_api.utils import get_random_id
import html2text
import io

conf = json.loads(open('config.json').read())

username = conf['username']
password = conf['password']
vk_token = conf['vk_token']
peer_id = conf['peer_id']

vk_session = vk_api.VkApi(token=vk_token)
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


def decode(s):
    if not type(s) == str:
        return "none"
    h = email.header.decode_header(s)
    s = ''
    for b, encoding in h:
        try:
            s += b.decode(encoding)+' '
        except:
            if isinstance(b, bytes):
                s += b.decode()+' '
            else:
                s += str(b)+' '
    return s


class Mail:
    def __init__(self, message):
        self.from_ = decode(message["from"])
        self.subject = decode(message["subject"])
        self.attachments = []  # (filename, data)
        self.text = ''
        if message.is_multipart():
            for sub_message in message.get_payload():
                self.add_content(sub_message)
        else:
            self.add_content(message)

    def add_content(self, message):
        #self.text += f'{message.get_content_disposition()} - {message.get_content_type()}\n'
        if message.get_content_disposition() == None and message.get_content_type() == 'text/html':
            self.text += f'{html2text.html2text(message.get_payload(decode=True).decode())}\n'
        if message.get_content_disposition() == None and message.get_content_type() == 'multipart/alternative':
            m = Mail(message)
            self.text += f'{m.get()}\n'
        if message.get_content_disposition() == 'attachment':
            self.attachments.append(
                (decode(message.get_filename()), message.get_payload(decode=True)))

    def get(self):
        if self.from_ == 'none':
            return self.text
        return f'''
Тема: {self.subject}
От: {self.from_}
==========
{self.text}'''


# создаём класс IMAP4 с SSL
imap = imaplib.IMAP4_SSL("imap.gmail.com")
# автоизуемся
imap.login(username, password)

# то что уже вы почте
status, messages = imap.select("INBOX")
result, data = imap.search(None, "ALL")
old_id_list = data[0].split()
#old_id_list = []
print('Бот запущен')

msg = ''
# цикл получения новых писем
while True:
    try:
        # получаем список новых писем
        status, messages = imap.select("INBOX")
        result, data = imap.search(None, "ALL")
        id_list = data[0].split()  # Разделяем ID писем
        new_id_list = list(set(id_list).difference(set(old_id_list)))
        for id in new_id_list:
            res, msg = imap.fetch(id, "(RFC822)")
            for response in msg:
                if not isinstance(response, tuple):
                    continue
                message = email.message_from_bytes(response[1])
                mail = Mail(message)
                vk_msg = mail.get()
                print(vk_msg)
                attachments = ''
                lenattachments = 0
                while len(vk_msg):
                    vk_msg_ = vk_msg[:4000]
                    vk_msg = vk_msg[4000:]
                    vk.messages.send(random_id=get_random_id(), peer_id=peer_id,
                                     message=vk_msg_)
                for filename, dat in mail.attachments:
                    try:
                        attachments += uploadDoc(filename, dat)
                        lenattachments += 1
                        if lenattachments == 8:  # максимум в сообщении
                            vk.messages.send(random_id=get_random_id(),
                                             peer_id=peer_id, attachment=attachments)
                            attachments = ''
                            lenattachments = 0
                    except:
                        vk.messages.send(random_id=get_random_id(),
                                         peer_id='Не все файлы отправлены, проверьте почту...')
                    if lenattachments:
                        vk.messages.send(random_id=get_random_id(),
                                         peer_id=peer_id, attachment=attachments)
        old_id_list = id_list
    except:
        print('reconect...')
        # переподключаемся
        imap = imaplib.IMAP4_SSL("imap.gmail.com")
        imap.login(username, password)
    sleep(5)
