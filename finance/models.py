from django.db import models
from trip.models import Trip

class ExpensesCategory(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(null=True, blank=True) 

    class Meta:
        verbose_name_plural = "Expenses Categories"

    def __str__(self):
        return self.name

class Expenses(models.Model):
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE)
    expense_category = models.ForeignKey(ExpensesCategory, on_delete=models.CASCADE)
    amount = models.FloatField()
    description = models.TextField(null=True, blank=True) 
    status = models.IntegerField(default=1) 

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
        return self.expense_category.name
