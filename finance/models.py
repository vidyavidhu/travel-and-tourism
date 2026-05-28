from django.db import models
from django.contrib.auth.models import User
from trip.models import Trip

class ExpensesCategory(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(null=True, blank=True) 

    class Meta:
        verbose_name_plural = "Expenses Categories"

    def __str__(self):
        return self.name

class Expenses(models.Model):
    EXPENSE_TYPES = [
        ('NORMAL_EXPENSE', 'Normal Expense'),
        ('MEMBER_REIMBURSEMENT', 'Member Reimbursement'),
    ]

    APPROVAL_STATUSES = [
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    ]

    REIMBURSEMENT_STATUSES = [
        ('NOT_REQUIRED', 'Not Required'),
        ('PAYMENT_PENDING', 'Payment Pending'),
        ('PAID', 'Paid'),
    ]

    trip = models.ForeignKey(Trip, on_delete=models.CASCADE)
    expense_category = models.ForeignKey(ExpensesCategory, on_delete=models.CASCADE)
    title = models.CharField(max_length=150, null=True, blank=True)
    amount = models.FloatField()
    description = models.TextField(null=True, blank=True) 
    status = models.IntegerField(default=1) 
    
    expense_type = models.CharField(
        max_length=50, 
        choices=EXPENSE_TYPES, 
        default='NORMAL_EXPENSE'
    )
    created_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='created_expenses'
    )
    paid_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='paid_expenses'
    )
    approval_status = models.CharField(
        max_length=50, 
        choices=APPROVAL_STATUSES, 
        default='APPROVED'
    )
    reimbursement_status = models.CharField(
        max_length=50, 
        choices=REIMBURSEMENT_STATUSES, 
        default='NOT_REQUIRED'
    )
    approved_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='approved_expenses'
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    reimbursement_paid_at = models.DateTimeField(null=True, blank=True)
    payment_reference = models.CharField(max_length=255, null=True, blank=True)
    payment_notes = models.TextField(null=True, blank=True)
    proof_file = models.FileField(upload_to='proof_files/', null=True, blank=True)
    date_of_expense = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)

    class Meta:
        verbose_name_plural = "Expenses"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.trip.recalculate_finance()

    def delete(self, *args, **kwargs):
        trip = self.trip
        super().delete(*args, **kwargs)
        trip.recalculate_finance()

    def __str__(self):
        if self.title:
            return f"{self.title} ({self.expense_category.name})"
        return self.expense_category.name

