from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from .models import Trip
from .forms import TripForm, TripFilterForm

class TripListView(ListView):
    model = Trip
    template_name = 'trip/trip_list.html'
    context_object_name = 'trips'
    paginate_by = 10

    def get_queryset(self):
        queryset = super().get_queryset()
        self.filter_form = TripFilterForm(self.request.GET)
        
        if self.filter_form.is_valid():
            title = self.filter_form.cleaned_data.get('title')
            location = self.filter_form.cleaned_data.get('location')
            from_date = self.filter_form.cleaned_data.get('from_date')
            to_date = self.filter_form.cleaned_data.get('to_date')
            status = self.filter_form.cleaned_data.get('status')
            
            if title:
                queryset = queryset.filter(title__icontains=title)
            if location:
                queryset = queryset.filter(location__icontains=location)
            if from_date:
                queryset = queryset.filter(from_date__gte=from_date)
            if to_date:
                queryset = queryset.filter(to_date__lte=to_date)
            if status:
                queryset = queryset.filter(status=status)
                
        return queryset.order_by('-id')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filter_form'] = getattr(self, 'filter_form', TripFilterForm(self.request.GET))
        return context

class TripDetailView(DetailView):
    model = Trip
    template_name = 'trip/trip_detail.html'
    context_object_name = 'trip'

class TripCreateView(CreateView):
    model = Trip
    form_class = TripForm
    template_name = 'trip/trip_form.html'
    success_url = reverse_lazy('trip_list')

class TripUpdateView(UpdateView):
    model = Trip
    form_class = TripForm
    template_name = 'trip/trip_form.html'
    success_url = reverse_lazy('trip_list')

class TripDeleteView(DeleteView):
    model = Trip
    template_name = 'trip/trip_confirm_delete.html'
    success_url = reverse_lazy('trip_list')
