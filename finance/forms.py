from django import forms
from .models import Expenses
import os

class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Expenses
        fields = ['expense_category', 'amount', 'description']
        widgets = {
            'expense_category': forms.Select(attrs={'class': 'form-control'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class ReimbursementRequestForm(forms.ModelForm):
    class Meta:
        model = Expenses
        fields = ['title', 'amount', 'expense_category', 'date_of_expense', 'description', 'proof_file']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Fuel payment / Dinner for group'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': '0.00'}),
            'expense_category': forms.Select(attrs={'class': 'form-control'}),
            'date_of_expense': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Please describe what was paid for...'}),
            'proof_file': forms.ClearableFileInput(attrs={'class': 'form-control', 'accept': 'image/*,application/pdf'}),
        }

    def __init__(self, *args, **kwargs):
        self.trip = kwargs.pop('trip', None)
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        self.fields['proof_file'].required = True

    def clean_proof_file(self):
        proof = self.cleaned_data.get('proof_file')
        if not proof:
            raise forms.ValidationError("Proof of payment upload is mandatory.")
        
        # Check size (5MB max)
        if proof.size > 5 * 1024 * 1024:
            raise forms.ValidationError("Uploaded file is too large. Max size allowed is 5MB.")
            
        # Check extension
        ext = os.path.splitext(proof.name)[1].lower()
        valid_extensions = ['.pdf', '.jpg', '.jpeg', '.png']
        if ext not in valid_extensions:
            raise forms.ValidationError("Unsupported file type. Only PDF and images (JPG, PNG) are supported.")
            
        return proof

    def clean(self):
        cleaned_data = super().clean()
        amount = cleaned_data.get('amount')
        category = cleaned_data.get('expense_category')
        date_of_expense = cleaned_data.get('date_of_expense')
        
        if self.trip and self.user and amount and category and date_of_expense:
            # Check if an identical request was submitted in the last 5 minutes
            from django.utils import timezone
            from datetime import timedelta
            five_minutes_ago = timezone.now() - timedelta(minutes=5)
            
            duplicates = Expenses.objects.filter(
                trip=self.trip,
                created_by=self.user,
                amount=amount,
                expense_category=category,
                date_of_expense=date_of_expense,
                created_at__gte=five_minutes_ago
            )
            if duplicates.exists():
                raise forms.ValidationError("A similar reimbursement request has already been submitted by you in the last 5 minutes. Please avoid submitting duplicates.")
        
        return cleaned_data

