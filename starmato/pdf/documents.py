# -*- coding: utf-8 -*-
import os.path, sys
import re
import HTMLParser
#
from django.conf import settings
from django.forms import ChoiceField
from django.utils.translation import ugettext as _
from django.utils.encoding import force_text
#
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4,landscape
from reportlab.lib.units import cm
from reportlab.lib.fonts import addMapping
from reportlab.pdfbase.pdfmetrics import stringWidth, registerFont
from reportlab.pdfbase.ttfonts import TTFont
#
from starmato.pdf.utils import hyphenate

d = os.path.dirname(sys.modules["reportlab"].__file__)
fonts = [('Vera', '%s/fonts/Vera.ttf' % d, 0, 0, 'StarMaTo'),
         ('Vera', '%s/fonts/VeraIt.ttf' % d, 0, 1, 'StarMaTo-Italic'),
         ('Vera', '%s/fonts/VeraBd.ttf' % d, 1, 0, 'StarMaTo-Bold'),
         ('Vera', '%s/fonts/VeraBI.ttf' % d, 1, 1, 'StarMaTo-BI'),
         ]

nopic = '%sadmin/images/nopic.png' % settings.STATIC_ROOT

for name, path, bold, italic, ref in fonts:
    registerFont(TTFont(ref, path))
    addMapping(name, bold, italic, ref)

class   StarmatoPDFDocument(object):
    """
    PDF base class (empty document).
    """
    # Metrics
    w, h = A4
    margin = 2*cm
    ch = .8*cm              # col height
    # fonts
    hfont = ('StarMaTo', 20) # Header font
    hfonti = ('StarMaTo-Italic', 20) # Header font italic
    lfont = ('StarMaTo', 18) # Large font
    lfonti = ('StarMaTo-Italic', 18) # Large font
    rfont = ('StarMaTo', 11) # Row font
    rfonti = ('StarMaTo-Italic', 11) # Row font italic
    dfont = ('StarMaTo', 9) # Description font
    dfonti = ('StarMaTo-Italic', 9) # Description font
    ffont = ('StarMaTo', 7) # Footer font
    ffonti = ('StarMaTo-Italic', 7) # Footer font
    line_height = .6*cm
    # internal variable, defining the current y position
    dy = 0
    #
    header = ['', '']
    footer = [_(u'poweredfooter'),]
    logo = 'starmato300dpi.png'

    current_font = dfont

    def __init__(self, ofile, logo=None, date='Today', header=None, footer=None, pagesize=A4, header_first_page_only=True):
        self.date = date
        self.pagesize = pagesize
        self.header_first_page_only = header_first_page_only
        if header is not None:
            self.header = header
        if footer is not None:
            self.footer = footer
        if logo is not None:
            self.logo = logo
        self.logo_size = 1.2*cm
        self.logo_x = .6*cm
        self.logo_y = self.h - self.logo_size * 3.43 - cm #(self.h - self.logo_size * 3.43) / 2
        #
        self.p = canvas.Canvas(ofile, pagesize=pagesize)
        self.htmlparser = HTMLParser.HTMLParser()

    ########################################
    # Generic functions for formatting
    ########################################
    def setFont(self, *font):
        self.current_font = font
        self.p.setFont(*font)

    def _html_to_pdf(self, obj, string):
        reg = 0
        cnt = 1
        tokens = re.split('(<.*?>)', string)
        obj.setFont(self.current_font[0], self.current_font[1])
        obj.setRise(0);
        for token in tokens:
            if token == "</sup>" or token == "</sub>" or token == "</small>":
                obj.setFont(self.p._fontname, self.p._fontsize)
                self.current_font = (self.p._fontname, self.p._fontsize)
                obj.setRise(0)
            elif token == "<sub>" or token == "<small>":
                obj.setFont(self.p._fontname, self.p._fontsize - 2)
                self.current_font = (self.p._fontname, self.p._fontsize - 2)
            elif token == "<sup>":
                obj.setFont(self.p._fontname, self.p._fontsize - 2)
                self.current_font = (self.p._fontname, self.p._fontsize - 2)
                obj.setRise(2)
            elif token == "<p>" or token == "<br />" or token == "<br>":
                obj.moveCursor(0, self.line_height)
                cnt += 1
            elif len(token) and token[0] == "<":
                # ignore other html tags
                continue
            else:
                obj.textOut(token)
        return obj, cnt

    def drawString(self, xp, yp, string):
        cnt = 1
        if string.find('<.*?>'):
            obj = self.p.beginText(xp, yp)
            obj, cnt = self._html_to_pdf(obj, string)
            self.p.drawText(obj)
        else:
            self.p.drawString(xp, yp, string)
        return cnt * self.line_height

    def drawLeftString(self, xp, yp, string):
        return self.drawString(xp, yp, string)

    def drawRightString(self, xp, yp, string):
        str_width = stringWidth(string, self.p._fontname, self.p._fontsize)
        self.drawString(xp - str_width, yp, string)

    def drawCenteredString(self, xp, yp, string):
        str_width = stringWidth(re.sub('<.*?>', '', string), self.p._fontname, self.p._fontsize)
        self.drawString(xp - 0.5*str_width, yp, string)

    ########################################
    # Generic draw functions
    ########################################
    def draw_logo(self):
        if self.logo:
            self.p.translate(0, 0)
            self.p.drawImage(
                os.path.join(settings.STATIC_ROOT, self.logo),
                self.logo_x, self.logo_y,
                width=self.logo_size, height=self.logo_size * 3.43,
                preserveAspectRatio=True,
                mask='auto',
                )
            self.setFont(*self.rfont)

    def draw_footer(self):
        self.setFont(*self.ffont)

        if self.footer is not None:
            for cnt, footer in enumerate(self.footer):
                self.drawCenteredString(self.w / 2.0, self.margin - .6 * (cnt-1) * cm, footer)

    def draw_header(self):
        if self.header:
            xp = self.w - self.margin
            yp = self.h-self.margin
            self.p.translate(0, 0)
            self.setFont(*self.hfont)
            self.drawRightString(xp, yp, self.header[0])
            self.drawRightString(xp, yp-1.2*cm, self.header[1])
            self.setFont(*self.rfont)

    def draw_content(self):
        raise NotImplementedError
                
    def update_page_counter(self, current, total):
        self.setFont(*self.rfont)
        self.drawRightString(self.w-2.5*cm, 1.5*cm, "Page %d / %d" % (current, total))

    def _page_break(self):
        self.p.showPage()
        self.draw_logo()
        if self.header_first_page_only == False:
            self.draw_header()
        self.draw_footer()
        self.setFont(*self.rfont)

    def finish(self):
        self.p.save()

# pdf class to easily print a db.Model from a change_list admin view
class   StarmatoPDFModel(StarmatoPDFDocument):
    def __init__(self, ofile, logo=None, date='Today', header=None, footer=None, pagesize=A4, logo_x=.5*cm, logo_y=7*cm):
        super(StarmatoPDFModel, self).__init__(ofile, logo, date, header, footer, pagesize)

        self.draw_logo()
        self.draw_footer()

    def _page_break(self):
        self.p.showPage()
        self.draw_logo()
        self.draw_footer()
        self.setFont(*self.dfont)

    def draw_fieldset_header(self, dx, yp, name):
        xp = self.margin

#        self.p.setLineWidth(.8)
#        self.p.line(xp, yp-.1*cm, self.w - xp, yp-.1*cm)

        self.p.setFillColorRGB(.8,.8,.8)
        self.p.rect(xp - .2*cm, yp-.2*cm, self.w - 2.6*cm, .8*cm, stroke=0, fill=1)
    
        self.p.setFillColorRGB(0,0,0)
        self.drawString(xp, yp, name)


    def draw_fieldset(self, xp, yp, fieldset, inline=False):
        l = []
        for line in fieldset:
            for field in line:
                if type(field.field) == dict:
                    label = field.field["label"]
                    value = ""
                    if hasattr(field.field, "value"):
                        value = field.field["value"]
                else:
                    label = force_text(field.field.label)
                    value = field.field.value()
                if type(value) == bool:
                    if value == True:
                        value = _("Yes")
                    else:
                        value = _("No")
                elif hasattr(field.field, "field") and hasattr(field.field.field, "choices"):
                    values = []
                    if hasattr(value, '__iter__'):
                        choices = [force_text(e) for e in value]
                    else:
                        choices = [force_text(value)]
                    for choice in choices:
                        for (val, desc) in field.field.field.choices:
                            if hasattr(desc, '__iter__'):
                                for (val, desc) in desc:
                                    if force_text(val) == choice:
                                        values.append(desc)
                            else:
                                if force_text(val) == choice:
                                    values.append(desc)

                    value = ", ".join(values)
                else:
                    value = force_text(value)
                empty = type(value) == None or value == None or len(value) == 0 or value == "None"
                if not empty:
                    l.append((label, value))
                
        if len(l) > 0:
            if inline == False:
                t = type(fieldset.name)
                if t == str or t == unicode:
                    self.draw_fieldset_header(xp, yp, fieldset.name)
                elif "name" in fieldset.name:
                    self.draw_fieldset_header(xp, yp, fieldset.name["name"])
                yp -= 1.5 * self.line_height

            for (label, value) in l:
                if yp < self.margin + 2 * cm:
                    self._page_break()
                    yp = self.h - self.margin

                self.setFont(*self.rfonti)


                yp -= self.drawString(xp, yp, label)
                self.setFont(*self.rfont)

                lines = hyphenate(self.htmlparser.unescape(value), self.w-3*self.margin, *self.dfont, separator='([ /@])')
                for line in lines:
                    yp -= self.drawString(xp, yp, line)
                yp -= self.line_height / 2
            yp -= self.line_height
        return yp

    def draw_inlines(self, xp, yp):
        for formset in self.inline_formsets:
            if yp < self.margin + 2 * cm:
                self._page_break()
                yp = self.h - self.margin

            typ = yp
            first = True
            for form in formset:
                if form.original or first == True:
                    for fieldset in form:
                        yp = self.draw_fieldset(xp, yp, fieldset, inline=True)
                first = False

            if typ != yp:
                if formset.opts.max_num == 1:
                    self.draw_fieldset_header(xp, typ, formset.opts.verbose_name)
                else:
                    self.draw_fieldset_header(xp, typ, formset.opts.verbose_name_plural)
        return yp

    def draw_content(self, adminform, inline_formsets):
        if hasattr(self, "adminform"):
            self._page_break()
        self.adminform = adminform
        self.inline_formsets = inline_formsets
        if self.header == None:
            self.header = [adminform.model_admin.model._meta.verbose_name, 
                           unicode(adminform.form.instance)]
        else:
            try:
                self.header[0] = eval(self.header[0])
            except:
                pass
            try:
                self.header[1] = eval(self.header[1])
            except:
                pass
        self.draw_header()

        yp = self.h - 3 * self.margin
        xp = self.margin

        for fieldset in self.adminform:
            if yp < self.margin + 2 * cm:
                self._page_break()
                yp = self.h - self.margin

            if fieldset.name == "related_go_here":
                yp = self.draw_inlines(xp, yp)
                yp += 2 * self.line_height
            else:
                yp = self.draw_fieldset(xp, yp, fieldset)

#                if col.find('<img') >= 0:
#                    picture = col[col.index('src="')+5:]
#                    picture = settings.STATIC_DIR + picture[:picture.index('"')].replace(settings.STATIC_URL, '')
#                    if os.path.exists(picture) and os.path.isfile(picture):
#                        self.p.drawImage(
#                            picture,
#                            xp, yp-2*cm,
#                            width=2*cm, height=2*cm,
#                            preserveAspectRatio=True
#                            )
#                        nb_lines = 2/.4 + 1
#                else:
        
from starmato.pdf.lists import StarmatoPDFList
