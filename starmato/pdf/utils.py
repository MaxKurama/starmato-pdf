# -*- coding: utf-8 -*-
import re, htmllib
#
from django.conf import settings
from reportlab.pdfbase.pdfmetrics import stringWidth

p = re.compile(r'<.*?>')
def hyphenate(text, width, font, size, separator='([ ])'):
    if text == None:
        return []
    text = texts[0]
    
    words = re.split(separator, text)#, p.sub('', text))
    lines = [words[0]]
    line_cnt = 0
    word_cnt = 1
    current_line_cnt = 0
    while word_cnt < len(words):
        if stringWidth(p.sub('', lines[line_cnt]+words[word_cnt]), font, size) > width:
            line_cnt += 1
            lines.append(words[word_cnt])
        else:
            lines[line_cnt] += words[word_cnt]
        word_cnt += 1

    if len(texts) > 1:
        return lines + hyphenate(texts[1], width, font, size, separator)
    
    return lines

def number_with_spaces(num, decimals=0, separator=' '):
    try:
        if type(num) is not str:
            num = str(num)
        num = num[::-1]
        num = re.sub("([0-9]{3})", "\\1%c" % separator, num, re.DOTALL)
        num = num[::-1]
        num = re.search("[0-9].*", num).group(0)
    
        tokens = re.split('\.', num)
    except:
        tokens = ['0', '00']
    if decimals == 0:
        return tokens[0]
    else:
        return tokens[0]+"."+tokens[1][:decimals]

def unescape(s):
    p = htmllib.HTMLParser(None)
    p.save_bgn()
    p.feed(s)
    return p.save_end()
