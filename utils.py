#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Dec  9 11:13:14 2021

@author: edombek
"""

import html2text
import io
import email

def uploadDoc(filename, dat):
    global upload, peer_id
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
            if self.txttype == 'text/plain':
                self.text += f'{message.get_payload(decode=True).decode()}\n'
            else:
                self.text += f'{html2text.html2text(message.get_payload(decode=True).decode())}\n'

    def get(self):
        if self.from_ == 'none':
            return self.text
        return f'''
Тема: {self.subject}
От: {self.from_}
==========
{self.text}'''