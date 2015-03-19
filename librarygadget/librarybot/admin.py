from librarybot.models import Library, LibraryRequest
from librarybot.models import AccessLog
from librarybot.models import Patron
from django.contrib import admin
import django.forms as forms
from django.forms import ModelForm, Textarea
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin
from librarybot.models import UserProfile

admin.site.unregister(User)

class UserProfileInline(admin.StackedInline):
    model = UserProfile

class PatronInline(admin.StackedInline):
    model = Patron

class UserProfileAdmin(UserAdmin):
    list_display = ('id', 'username', 'date_joined')
    ordering = ['-date_joined']
    inlines = [UserProfileInline, PatronInline]

admin.site.register(User, UserProfileAdmin)

class LibraryAdminForm(ModelForm):
    regional_system = forms.ModelChoiceField(required=False, queryset=Library.objects.order_by('name'))

    class Meta:
        model = Library

class LibraryAdmin(admin.ModelAdmin):
    form = LibraryAdminForm
    list_display = ['id', 'name', 'state', 'regional_system','catalogurl', 'librarysystem']
    list_filter = ['librarysystem', 'state']
    search_fields = ['name']
    ordering = ['name']

def library_id(obj):
    return obj.library.id

def library_name(obj):
    return obj.library.name

def library_catalogurl(obj):
    return obj.library.catalogurl

def library_system(obj):
    return obj.library.librarysystem

def patron_id(obj):
    return obj.patron.patronid

class AccessLogForm(ModelForm):
    class Meta:
        model = AccessLog
        widgets = {
            'error_stacktrace': Textarea(attrs={'cols': 80, 'rows': 20}),
        }



class AccessLogAdmin(admin.ModelAdmin):
    form = AccessLogForm
    list_display = (patron_id, library_id, library_name, library_system, 'viewfunc', 'date')
    list_filter = ('viewfunc',)
    date_hierarchy = 'date'
    search_fields = ('error_stacktrace', )
    raw_id_fields = ('patron',)


class PatronAdmin(admin.ModelAdmin):
    list_display = (library_id, 'get_username', 'patronid', 'lastchecked')
    ordering = ['-lastchecked']
    list_filter = ('patronid',)

    def get_username(self, obj):
        return "%s" % obj.user.username

class LibraryRequestAdmin(admin.ModelAdmin):
    list_display = ('date', 'get_username', 'libraryname', 'catalogurl')
    date_hierarchy = 'date'

    def get_username(self, obj):
        return "%s" % obj.user.username


admin.site.register(Library, LibraryAdmin)
admin.site.register(AccessLog, AccessLogAdmin)
admin.site.register(Patron, PatronAdmin)
admin.site.register(LibraryRequest, LibraryRequestAdmin)
