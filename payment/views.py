from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from trip.models import Trip_Members
from payment.models import Payment
from payment.services import payment_service

@login_required
def initiate_payment(request, booking_id):
    """
    Renders the Payment Method Selection Page.
    Validates ownership of the booking and checks if payment is needed.
    """
    booking = get_object_or_404(Trip_Members, pk=booking_id)
    
    # Security: Validate booking ownership
    if booking.member.user != request.user:
        messages.error(request, "Access denied. You do not own this trip booking.")
        return redirect('home_trip_details', pk=booking.trip.id)
        
    # Check if already paid or has no pending balance
    if booking.payment_status == 1 or booking.unpaid_amount <= 0:
        messages.info(request, "This trip booking is already fully paid!")
        return redirect('home_trip_details', pk=booking.trip.id)

    if request.method == 'POST':
        payment_method = request.POST.get('payment_method')
        force_success = request.POST.get('force_success') == 'true'
        
        if payment_method not in ['UPI', 'CARD', 'NETBANKING', 'WALLET']:
            messages.error(request, "Invalid payment method selected.")
            return redirect('initiate_payment', booking_id=booking.id)
            
        # Create payment instance via service layer
        payment = payment_service.create_payment(
            user=request.user,
            booking=booking,
            amount=booking.unpaid_amount,
            payment_method=payment_method
        )
        
        # Store force_success preference in session temporarily for the next processing view
        request.session[f'force_success_{payment.id}'] = force_success
        
        return redirect('process_payment', payment_id=payment.id)
        
    context = {
        'booking': booking,
        'unpaid_amount': booking.unpaid_amount,
    }
    return render(request, 'payment/payment_page.html', context)

@login_required
def process_payment(request, payment_id):
    """
    Simulates payment processing. Displays a loader screen, and on POST processing,
    triggers mock service gateway logic and redirects to success or failure page.
    """
    payment = get_object_or_404(Payment, pk=payment_id)
    
    # Security: Validate ownership
    if payment.user != request.user:
        messages.error(request, "Access denied.")
        return redirect('home')

    force_success = request.session.get(f'force_success_{payment.id}', True)

    if request.method == 'POST':
        # Execute mock payment gateway logic via Service Layer
        processed_payment = payment_service.process_mock_payment(
            payment=payment,
            force_success=force_success
        )
        
        # Clean up session
        if f'force_success_{payment.id}' in request.session:
            del request.session[f'force_success_{payment.id}']
            
        if processed_payment.payment_status == 'SUCCESS':
            return redirect('payment_success', payment_id=processed_payment.id)
        else:
            return redirect('payment_failed', payment_id=processed_payment.id)

    context = {
        'payment': payment,
        'force_success': force_success,
    }
    return render(request, 'payment/processing.html', context)

@login_required
def payment_success(request, payment_id):
    """
    Renders a stunning Payment Success Screen.
    """
    payment = get_object_or_404(Payment, pk=payment_id)
    
    # Security: Validate ownership
    if payment.user != request.user:
        messages.error(request, "Access denied.")
        return redirect('home')
        
    if payment.payment_status != 'SUCCESS':
        return redirect('payment_failed', payment_id=payment.id)
        
    context = {
        'payment': payment,
    }
    return render(request, 'payment/success.html', context)

@login_required
def payment_failed(request, payment_id):
    """
    Renders a stunning Payment Failed Screen.
    """
    payment = get_object_or_404(Payment, pk=payment_id)
    
    # Security: Validate ownership
    if payment.user != request.user:
        messages.error(request, "Access denied.")
        return redirect('home')
        
    if payment.payment_status != 'FAILED':
        return redirect('payment_success', payment_id=payment.id)
        
    context = {
        'payment': payment,
    }
    return render(request, 'payment/failed.html', context)

@login_required
def payment_history(request):
    """
    Renders a table dashboard of the user's past payments.
    """
    payments = Payment.objects.filter(user=request.user).order_by('-created_at')
    context = {
        'payments': payments,
    }
    return render(request, 'payment/history.html', context)

@login_required
def download_invoice(request, payment_id):
    """
    Renders a printable invoice page.
    """
    payment = get_object_or_404(Payment, pk=payment_id)
    
    # Security: Validate ownership
    if payment.user != request.user:
        messages.error(request, "Access denied.")
        return redirect('home')
        
    context = {
        'payment': payment,
        'booking': payment.booking,
        'trip': payment.booking.trip,
    }
    return render(request, 'payment/invoice.html', context)
