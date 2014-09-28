# The `pdf` module

The `pdf` module provides simple tools to export pdf from django admin views
Two different kinds of pdf can be automatically generated:
- a list of models, from the admin change_list view
- a model, from the admin change_view view

In the first case, an action is added to the change list
  "Export selected <objects> (csv)"
The list of fields to export is found by looking for, in order of priority:
	- modeladmin.export_pdf_fields
	- modeladmin.export_fields
	- modeladmin.list_display

In the second case, the usage of StarmatoModelAdmin change_form template is required
to display an extra action bar before the usual one (to save the model).
This bar contains a button to a view that prints the model using the fieldsets defined
in the modeladmin.

## Quick Start

1. Add `starmato.pdf` to your settings like this:

        INSTALLED_APPS = (
            ...
            'django.contrib.admin',
            'starmato.admin',
	    'starmato.pdf',
        )

2. Use StarmatoPDFAdmin:

	from starmato.admin.options import StarmatoModelAdmin
	from starmato.pdf.options import StarmatoPDFAdmin

        class MyAdmin(StarmatoModelAdmin, StarmatoPDFAdmin):

   StarmatoPDFAdmin gets the list of fields to export by looking for, in order of priority:
	- modeladmin.export_pdf_fields
	- modeladmin.export_fields
	- modeladmin.list_display


3. Customize by defining your list of fields:

        class MyAdmin(StarmatoModelAdmin, StarmatoPDFAdmin):
	      def print_list_action(self, request, queryset):
			return print_list(request, queryset, self)
	
	      export_pdf_fields = ('field1', 'field3', 'field4')

3. Customize by defining your own exportation function:

        class MyAdmin(StarmatoModelAdmin, StarmatoPDFAdmin):
	      def print_list_action(self, request, queryset):
			...
