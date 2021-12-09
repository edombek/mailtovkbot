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
from utils import Mail, uploadDoc, fixFileExtent

conf = json.loads(open('config.json').read())

username = conf['username']
password = conf['password']
vk_token = conf['vk_token']
peer_id = conf['peer_id']
imapserver = conf['imapserver']

vk_session = vk_api.VkApi(token=vk_token)
vk = vk_session.get_api()
upload = vk_api.VkUpload(vk_session)


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
