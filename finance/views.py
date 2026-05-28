from django.shortcuts import get_object_or_404, redirect, render
from django.views.generic import CreateView, DeleteView
from django.urls import reverse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db import transaction
from .models import Expenses
from .forms import ExpenseForm, ReimbursementRequestForm
from trip.models import Trip, Trip_Members, TripBroadcastMessage
from member.models import Member, CoordinatorNotification

class ExpenseCreateView(LoginRequiredMixin, CreateView):
    model = Expenses
    form_class = ExpenseForm
    template_name = 'trip/trip_form.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = "Add Trip Expense"
        context['cancel_url'] = reverse('trip_detail', kwargs={'pk': self.kwargs['trip_id']}) + '?tab=details'
        return context

    def form_valid(self, form):
        trip = get_object_or_404(Trip, pk=self.kwargs['trip_id'])
        form.instance.trip = trip
        # Normal expenses created by coordinators are automatically APPROVED
        form.instance.expense_type = 'NORMAL_EXPENSE'
        form.instance.approval_status = 'APPROVED'
        form.instance.reimbursement_status = 'NOT_REQUIRED'
        form.instance.created_by = self.request.user
        form.instance.paid_by = self.request.user
        return super().form_valid(form)
        
    def get_success_url(self):
        return reverse('trip_detail', kwargs={'pk': self.kwargs['trip_id']}) + '?tab=details'

class ExpenseDeleteView(LoginRequiredMixin, DeleteView):
    model = Expenses
    template_name = 'trip/trip_confirm_delete.html'
    
    def get_success_url(self):
        return reverse('trip_detail', kwargs={'pk': self.object.trip.pk})


@login_required
def submit_reimbursement(request, trip_id):
    """
    Allows a joined and approved member to submit a reimbursement request for a trip.
    """
    trip = get_object_or_404(Trip, pk=trip_id)
    
    # 1. Permission check: user must have a Member profile and must be joined (status == 1)
    try:
        member = request.user.member
    except Member.DoesNotExist:
        messages.error(request, "Access denied. Only registered members can submit reimbursement requests.")
        return redirect('home_trip_details', pk=trip.id)
        
    tm = Trip_Members.objects.filter(trip=trip, member=member).first()
    if not tm or tm.status != 1:
        messages.error(request, "Access denied. Only joined and approved members of this trip can submit reimbursement requests.")
        return redirect('home_trip_details', pk=trip.id)
        
    if request.method == 'POST':
        form = ReimbursementRequestForm(request.POST, request.FILES, trip=trip, user=request.user)
        if form.is_valid():
            with transaction.atomic():
                expense = form.save(commit=False)
                expense.trip = trip
                expense.expense_type = 'MEMBER_REIMBURSEMENT'
                expense.approval_status = 'PENDING'
                expense.reimbursement_status = 'NOT_REQUIRED' # transitions to PAYMENT_PENDING on approval
                expense.created_by = request.user
                expense.paid_by = request.user
                expense.save()
                
                # Send notification to the trip's coordinator
                if trip.coordinator:
                    message_text = (
                        f"New reimbursement request submitted by {request.user.first_name or request.user.username} "
                        f"for trip '{trip.title}'. Amount: ₹{expense.amount:.2f}. Title: '{expense.title}'"
                    )
                    CoordinatorNotification.objects.create(
                        coordinator=trip.coordinator,
                        message=message_text
                    )
                    
            messages.success(request, "Reimbursement request submitted successfully and is pending coordinator approval.")
        else:
            # Gather and present form errors
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field.capitalize()}: {error}")
                    
    return redirect('home_trip_details', pk=trip.id)


@login_required
def approve_reimbursement(request, expense_id):
    """
    Coordinator approves a pending member reimbursement request.
    """
    expense = get_object_or_404(Expenses, pk=expense_id, expense_type='MEMBER_REIMBURSEMENT')
    trip = expense.trip
    
    # Permission check: must be coordinator of this trip or admin/staff
    is_coordinator = request.user.is_superuser or request.user.is_staff or (trip.coordinator and trip.coordinator.user == request.user)
    if not is_coordinator:
        messages.error(request, "You do not have permission to perform this action.")
        return redirect('home')
        
    if expense.approval_status != 'PENDING':
        messages.error(request, "This reimbursement request has already been processed.")
        return redirect(reverse('trip_detail', kwargs={'pk': trip.pk}) + '?tab=details')
        
    with transaction.atomic():
        expense.approval_status = 'APPROVED'
        expense.reimbursement_status = 'PAYMENT_PENDING'
        expense.approved_by = request.user
        expense.approved_at = timezone.now()
        expense.save()
        
        # Send direct TripBroadcastMessage alert to the member
        try:
            member = expense.created_by.member
            TripBroadcastMessage.objects.create(
                trip=trip,
                sender=request.user,
                recipient=member,
                message=f"Your reimbursement request for '{expense.title}' (Amount: ₹{expense.amount:.2f}) has been APPROVED! Payment is now pending."
            )
        except Exception:
            pass
            
    messages.success(request, f"Successfully approved reimbursement request for '{expense.title}'.")
    return redirect(reverse('trip_detail', kwargs={'pk': trip.pk}) + '?tab=details')


@login_required
def reject_reimbursement(request, expense_id):
    """
    Coordinator rejects a pending member reimbursement request.
    """
    expense = get_object_or_404(Expenses, pk=expense_id, expense_type='MEMBER_REIMBURSEMENT')
    trip = expense.trip
    
    # Permission check: must be coordinator of this trip or admin/staff
    is_coordinator = request.user.is_superuser or request.user.is_staff or (trip.coordinator and trip.coordinator.user == request.user)
    if not is_coordinator:
        messages.error(request, "You do not have permission to perform this action.")
        return redirect('home')
        
    if expense.approval_status != 'PENDING':
        messages.error(request, "This reimbursement request has already been processed.")
        return redirect(reverse('trip_detail', kwargs={'pk': trip.pk}) + '?tab=details')
        
    with transaction.atomic():
        expense.approval_status = 'REJECTED'
        expense.save()
        
        # Send direct TripBroadcastMessage alert to the member
        try:
            member = expense.created_by.member
            TripBroadcastMessage.objects.create(
                trip=trip,
                sender=request.user,
                recipient=member,
                message=f"Your reimbursement request for '{expense.title}' (Amount: ₹{expense.amount:.2f}) has been REJECTED by the coordinator."
            )
        except Exception:
            pass
            
    messages.warning(request, f"Reimbursement request for '{expense.title}' has been rejected.")
    return redirect(reverse('trip_detail', kwargs={'pk': trip.pk}) + '?tab=details')


@login_required
def pay_reimbursement(request, expense_id):
    """
    Coordinator marks a pending payment reimbursement as PAID.
    """
    expense = get_object_or_404(Expenses, pk=expense_id, expense_type='MEMBER_REIMBURSEMENT')
    trip = expense.trip
    
    # Permission check: must be coordinator of this trip or admin/staff
    is_coordinator = request.user.is_superuser or request.user.is_staff or (trip.coordinator and trip.coordinator.user == request.user)
    if not is_coordinator:
        messages.error(request, "You do not have permission to perform this action.")
        return redirect('home')
        
    if expense.approval_status != 'APPROVED' or expense.reimbursement_status != 'PAYMENT_PENDING':
        messages.error(request, "This reimbursement is not in a payment pending state.")
        return redirect(reverse('trip_detail', kwargs={'pk': trip.pk}) + '?tab=details')
        
    if request.method == 'POST':
        payment_reference = request.POST.get('payment_reference', '').strip()
        payment_notes = request.POST.get('payment_notes', '').strip()
        
        if not payment_reference:
            messages.error(request, "Payment Reference is required.")
            return redirect(reverse('trip_detail', kwargs={'pk': trip.pk}) + '?tab=details')
            
        with transaction.atomic():
            expense.reimbursement_status = 'PAID'
            expense.reimbursement_paid_at = timezone.now()
            expense.payment_reference = payment_reference
            expense.payment_notes = payment_notes
            expense.save()
            
            # Send direct TripBroadcastMessage alert to the member
            try:
                member = expense.created_by.member
                TripBroadcastMessage.objects.create(
                    trip=trip,
                    sender=request.user,
                    recipient=member,
                    message=(
                        f"Payment for your reimbursement request '{expense.title}' (Amount: ₹{expense.amount:.2f}) "
                        f"has been marked as COMPLETED! Ref: {payment_reference}"
                    )
                )
            except Exception:
                pass
                
        messages.success(request, f"Successfully marked reimbursement for '{expense.title}' as paid.")
        
    return redirect(reverse('trip_detail', kwargs={'pk': trip.pk}) + '?tab=details')

