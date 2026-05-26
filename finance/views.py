from django.shortcuts import get_object_or_404
from django.views.generic import CreateView, DeleteView
from django.urls import reverse
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Expenses
from .forms import ExpenseForm
from trip.models import Trip

class ExpenseCreateView(LoginRequiredMixin, CreateView):
    model = Expenses
    form_class = ExpenseForm
    template_name = 'trip/trip_form.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = "Add Trip Expense"
        return context

    def form_valid(self, form):
        trip = get_object_or_404(Trip, pk=self.kwargs['trip_id'])
        form.instance.trip = trip
        return super().form_valid(form)
        
    def get_success_url(self):
        return reverse('trip_detail', kwargs={'pk': self.kwargs['trip_id']})

class ExpenseDeleteView(LoginRequiredMixin, DeleteView):
    model = Expenses
    template_name = 'trip/trip_confirm_delete.html'
    
    def get_success_url(self):
        return reverse('trip_detail', kwargs={'pk': self.object.trip.pk})
