from django.contrib import admin
from .models import ExpensesCategory, Expenses

admin.site.register(ExpensesCategory)
admin.site.register(Expenses)
