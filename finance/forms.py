from django import forms
from .models import Expenses

class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Expenses
        fields = ['expense_category', 'amount', 'description']
        widgets = {
            'expense_category': forms.Select(attrs={'class': 'form-control'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
