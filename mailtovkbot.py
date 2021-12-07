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
imapserver = conf['imapserver']

vk_session = vk_api.VkApi(token=vk_token)
vk = vk_session.get_api()
upload = vk_api.VkUpload(vk_session)


def uploadDoc(filename, dat):
    file = io.BytesIO(dat)
    file.name = filename
    doc = upload.document_message(
        file,
        title=filename,
        peer_id=peer_id
    )
    file.close()
    return f"doc{doc['doc']['owner_id']}_{doc['doc']['id']},"


def fixFileExtent(fname):
    ext = fname.split('.')[-1]
    return fname.replace(ext, ext.replace(' ', ''))


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
        self.txttype = 'text/plain'
        if message.is_multipart():
            for sub_message in message.get_payload():
                if sub_message.get_content_type() == 'text/html':
                    self.txttype = 'text/html'
                    break
            for sub_message in message.get_payload():
                self.add_content(sub_message)
        else:
            if message.get_content_type() == 'text/html':
                self.txttype = 'text/html'
            self.add_content(message)

    def add_content(self, message):
        if message.get_content_disposition() == 'attachment':
            self.attachments.append(
                (decode(message.get_filename()), message.get_payload(decode=True)))
            return
        if message.get_content_type() == 'multipart/alternative':
            m = Mail(message)
            self.text += f'{m.get()}\n'
            self.attachments += m.attachments
        if message.get_content_type() == self.txttype:
            self.text += f'{html2text.html2text(message.get_payload(decode=True).decode())}\n'

    def get(self):
        if self.from_ == 'none':
            return self.text
        return f'''
Тема: {self.subject}
От: {self.from_}
==========
{self.text}'''


# создаём класс IMAP4 с SSL
imap = imaplib.IMAP4_SSL(imapserver)
# автоизуемся
imap.login(username, password)

# то что уже в почте
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
    except Exception as e:
        print(e)
        print('reconect...')
        # переподключаемся
        imap = imaplib.IMAP4_SSL(imapserver)
        imap.login(username, password)
        continue
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
                    attachments += uploadDoc(fixFileExtent(filename), dat)
                    lenattachments += 1
                except Exception as e:
                    vk.messages.send(random_id=get_random_id(),
                                     peer_id=peer_id, message=f'Файл: {filename} не отправлен, проверьте почту...\n{e}')
                if lenattachments == 8:  # максимум в сообщении
                    vk.messages.send(random_id=get_random_id(),
                                     peer_id=peer_id, attachment=attachments)
                    attachments = ''
                    lenattachments = 0
            if lenattachments:
                vk.messages.send(random_id=get_random_id(),
                                 peer_id=peer_id, attachment=attachments)
    old_id_list = id_list
    sleep(30)
