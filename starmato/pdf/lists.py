# -*- coding: utf-8 -*-
import HTMLParser    
from django.conf import settings
#
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
#
from django.utils.translation import ugettext as _
from django.utils.encoding import smart_unicode, force_unicode
from django.utils.html import escape, conditional_escape
from django.utils.safestring import mark_safe
#
from django.contrib.admin.views.main import EMPTY_CHANGELIST_VALUE
from django.contrib.admin.util import lookup_field, display_for_field
from django.contrib.admin.templatetags.admin_list import ResultList, result_headers
#
from reportlab.lib.pagesizes import A4,landscape
from reportlab.lib.units import cm
#
from starmato.pdf.documents import StarmatoPDFDocument
from starmato.pdf.utils import hyphenate

import os

class StarmatoPDFList(StarmatoPDFDocument):
    w, h = A4
    def __init__(self, ofile, cl, logo=None, date='Today', header=None, footer=None, pagesize=A4, logo_x=.5*cm, logo_y=7*cm, logo_size=1.2*cm):
        super(StarmatoPDFList, self).__init__(ofile, logo, date, header, footer, pagesize)

        self.cl = cl
        self.headers = list(result_headers(cl))
        self.p.setLineWidth(0.5)
        self.line_height = .4*cm
        self.logo_x = logo_x
        self.logo_y = logo_y
        self.logo_size = logo_size
        self.draw_logo()
        self.draw_footer()
        self.draw_header()


    def _page_break(self):
        self.p.showPage()
        self.draw_logo()
        self.draw_footer()
        self.setFont(*self.dfont)
        

    def draw_list_header(self, dx, yp):
        xp = self.margin

#        self.p.rect(xp - .2*cm, yp-.4*cm, self.w - 2.6*cm, .8*cm, stroke=0, fill=1)
#        self.p.setFillColorRGB(1,1,1)
 
        self.p.setLineWidth(.8)
        self.p.line(1.8 *cm, yp + .5*cm, self.w - .8*cm, yp + .5*cm)
   
        self.setFont(*self.dfonti)

        for label in self.headers:
            self.drawString(xp, yp, label['text'])
            xp += dx

        self.setFont(*self.dfont)

#        self.p.setFillColorRGB(0,0,0)

    def draw_content(self):
        htmlparser = HTMLParser.HTMLParser()
        self.setFont(*self.dfont)
        rows = list(results(self.cl))

        if len(rows):
            yp = self.h - 2.5 * self.margin
            dx = (self.w - 2 * self.margin) / len(rows[0])
            xp = self.margin
            self.draw_list_header(dx, yp+.7*cm)

        for row in rows:
            if yp < self.margin + 2 * cm:
                self._page_break()
                yp = self.h - self.margin
                self.draw_list_header(dx, yp+.7*cm)

            xp = self.margin
            nb_lines = 1
            self.p.line(1.8 *cm, yp + .4*cm, self.w - .8*cm, yp + .4*cm)
            for col in row:
                if col.find('<img') >= 0:
                    picture = col[col.index('src="')+5:]
                    picture = settings.STATIC_DIR + picture[:picture.index('"')].replace(settings.STATIC_URL, '')
                    if os.path.exists(picture) and os.path.isfile(picture):
                        self.p.drawImage(
                            picture,
                            xp, yp-2*cm,
                            width=2*cm, height=2*cm,
                            preserveAspectRatio=True
                            )
                        nb_lines = 2/.4 + 1
                else:
                    lines = hyphenate(col, dx-.5*cm, *self.dfont, separator='([ @])')
                    cnt = 0
                    for line in lines:
                        cnt += self.drawString(xp, yp-cnt*.4*cm, line)
                        
                    nb_lines = max(nb_lines, cnt)

#                    cnt = 0
#                    pre_lines = col.split('<br />')
#                    for pre_line in pre_lines:
#                        lines = hyphenate(pre_line, dx-.2*cm, *self.dfont, separator='([ /@])')
#                        for line in lines:
#                            self.drawString(xp, yp - cnt*.4*cm, line)
#                            cnt += 1
#                        nb_lines = max(nb_lines, cnt)
                xp += dx
            yp -= (nb_lines + .5) * .4*cm

def items_for_result(cl, result):
    """
    Generates the actual list of data.
    """
    pk = cl.lookup_opts.pk.attname
    for field_name in cl.list_display:
        row_class = ''
        try:
            f, attr, value = lookup_field(field_name, result, cl.model_admin)
        except (AttributeError, ObjectDoesNotExist):
            result_repr = EMPTY_CHANGELIST_VALUE
        else:
            if f is None:
                if field_name == u'action_checkbox':
                    continue
                result_repr = mark_safe(smart_unicode(value))
            else:
                if isinstance(f.rel, models.ManyToOneRel):
                    field_val = getattr(result, f.name)
                    if field_val is None:
                        result_repr = EMPTY_CHANGELIST_VALUE
                    else:
                        result_repr = escape(field_val)
                else:
                    result_repr = display_for_field(value, f)
        if force_unicode(result_repr) == '':
            result_repr = mark_safe('-')
        result_repr = conditional_escape(result_repr)
        yield mark_safe(u'%s' % result_repr)

def results(cl):
    for res in cl.result_list:
        yield ResultList(None, items_for_result(cl, res))
