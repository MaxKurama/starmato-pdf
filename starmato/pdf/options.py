# -*- coding: utf-8 -*-
from functools import update_wrapper
#
from django.http import HttpResponse
from django.contrib.contenttypes.models import ContentType
from django.contrib import admin
from django.utils.translation import ugettext as _
from django.utils.encoding import force_text
from django.contrib.admin.util import unquote
from django.contrib.admin import helpers
#
from starmato.pdf.documents import StarmatoPDFList, StarmatoPDFModel

class   StarmatoPDFAdmin(admin.ModelAdmin):
    # Add urls to print objects
    def get_urls(self):
        from django.conf.urls import patterns, url

        def wrap(view):
            def wrapper(*args, **kwargs):
                return self.admin_site.admin_view(view)(*args, **kwargs)
            return update_wrapper(wrapper, view)

        info = self.model._meta.app_label, self.model._meta.module_name

        urlpatterns = patterns('',
            url(r'^(.+)/print/$',
                wrap(self.print_model),
                name='%s_%s_print' % info),
        )
        return urlpatterns + super(StarmatoPDFAdmin, self).get_urls()

    def get_form_and_inlines(self, request, object_id):
        model = self.model
        opts = self.model._meta
        obj = self.get_object(request, unquote(object_id))
        pk_value = obj._get_pk_val()

        if obj is None:
            raise Http404(_('%(name)s object with primary key %(key)r does not exist.') % {'name': force_text(opts.verbose_name), 'key': escape(object_id)})

        ModelForm = self.get_form(request, obj)
        formsets = []
        inline_instances = self.get_inline_instances(request, obj)

        form = ModelForm(instance=obj)
        prefixes = {}
        for FormSet, inline in zip(self.get_formsets(request, obj), inline_instances):
            prefix = FormSet.get_default_prefix()
            prefixes[prefix] = prefixes.get(prefix, 0) + 1
            if prefixes[prefix] != 1 or not prefix:
                prefix = "%s-%s" % (prefix, prefixes[prefix])
            formset = FormSet(instance=obj, prefix=prefix,
                              queryset=inline.get_queryset(request))
            formsets.append(formset)

        adminForm = helpers.AdminForm(form, self.get_fieldsets(request, obj),
            self.get_prepopulated_fields(request, obj),
            self.get_readonly_fields(request, obj),
            model_admin=self)
        media = self.media + adminForm.media

        inline_admin_formsets = []
        for inline, formset in zip(inline_instances, formsets):
            fieldsets = list(inline.get_fieldsets(request, obj))
            readonly = list(inline.get_readonly_fields(request, obj))
            prepopulated = dict(inline.get_prepopulated_fields(request, obj))
            inline_admin_formset = helpers.InlineAdminFormSet(inline, formset,
                fieldsets, prepopulated, readonly, model_admin=self)
            inline_admin_formsets.append(inline_admin_formset)
            media = media + inline_admin_formset.media

        return adminForm, inline_admin_formsets

    # Add view to print an object
    def print_model(self, request, object_id, outname="model.pdf", extra_context=None):
        "The 'print' admin view for this model."
        adminForm, inline_admin_formsets = self.get_form_and_inlines(request, object_id)
        response = HttpResponse(mimetype='application/pdf')
        response['Content-Disposition'] = "attachment; filename=" + outname
        header = None
        logo = None
        footer = None
        if hasattr(self, "pdf_header"):
            header = self.pdf_header
        if hasattr(self, "pdf_footer"):
            footer = self.pdf_footer
        if hasattr(self, "pdf_logo"):
            logo = self.pdf_logo
        else:
            from starmato.admin.models import get_starmato_option
            logo = get_starmato_option("project_logo")
 
        doc = StarmatoPDFModel(response, logo=logo, header=header, footer=footer)
        doc.draw_content(adminForm, inline_admin_formsets)
        doc.finish()

        return response

    def print_list_default_action(self, request, queryset, outname="list.pdf", header=None):
        ct = ContentType.objects.get_for_model(queryset.model)
        model = ct.model_class()
        response = HttpResponse(mimetype='application/pdf')
        response['Content-Disposition'] = "attachment; filename=" + outname

        header = None
        logo = None
        footer = None
        if hasattr(self, "pdf_header"):
            header = self.pdf_header
        if hasattr(self, "pdf_footer"):
            footer = self.pdf_footer
        if hasattr(self, "pdf_logo"):
            logo = self.pdf_logo
        else:
            from starmato.admin.models import get_starmato_option
            logo = get_starmato_option("project_logo")
        
        ChangeList = self.get_changelist(request)
        FormSet = self.get_changelist_formset(request)
        if hasattr(self, 'export_pdf_fields'):
            fieldlist = self.export_pdf_fields
        elif hasattr(self, 'export_fields'):
            fieldlist = self.export_fields
        else:
            fieldlist = self.list_display
            
        cl = ChangeList(request, model, fieldlist, [],
                        [], [], [], [],
                        '0', [], [], self)
        cl.formset = FormSet(queryset=queryset)
        cl.queryset = queryset
        cl.get_results(request)
            
        if header is None:
            header=[_('List of'), self.model._meta.verbose_name_plural]
                
        doc = StarmatoPDFList(response,
                              cl=cl,
                              header=header,
                              footer=footer,
                              logo=logo,
                              )
        
        doc.draw_content()
        doc.finish()

        return response

    def _print_list(self, request, queryset):
        if hasattr(self, 'print_list_action'):
            return self.print_list_action(request, queryset)
        else:
            return self.print_list_default_action(request, queryset)
    _print_list.short_description = _(u'Print selected %(verbose_name_plural)s (pdf list)')

    def _print_documents(self, request, queryset):
        response = HttpResponse(mimetype='application/pdf')
        response['Content-Disposition'] = "attachment; filename=models.pdf"
        header = None
        logo = None
        if hasattr(self, "pdf_header"):
            header = self.pdf_header
        if hasattr(self, "pdf_logo"):
            logo = self.pdf_logo
        doc = StarmatoPDFModel(response, logo=logo, header=header)
        for obj in queryset:
            adminForm, inline_admin_formsets = self.get_form_and_inlines(request, "%d" % obj.id)
            doc.draw_content(adminForm, inline_admin_formsets)
        doc.finish()

        return response

    _print_documents.short_description = _(u'Print selected %(verbose_name_plural)s (pdf forms)')



    # TODO: For a yet unknown reason, __init__ is called twice, causing
    # self.addActionRow to raise an exception. That is why the
    # safe param is added but it ruins the flexibility of the concept
    def __init__(self, model, admin_site):
        super(StarmatoPDFAdmin, self).__init__(model, admin_site)
        self.addActionRow("StarMaToPrint", css_class="print-row", safe=True)
        self.addActionToRow("StarMaToPrint", _(u"Print"), "print/", safe=True)


    actions = ['_print_list', '_print_documents']
