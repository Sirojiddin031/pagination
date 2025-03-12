from django.contrib import admin
from .models import *

class CategoriesAdmin(admin.ModelAdmin):
    pass
    
admin.site.register(Categories, CategoriesAdmin)
admin.site.register(News)

# Register your models here.
