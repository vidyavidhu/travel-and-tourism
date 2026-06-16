import uuid
import random
from django.utils import timezone
from payment.models import Payment

def generate_payment_id():
    """Generates a unique payment ID with prefix PAY-"""
    return f"PAY-{uuid.uuid4().hex[:12].upper()}"

def generate_transaction_id():
    """Generates a unique transaction ID with prefix TXN-"""
    return f"TXN-{uuid.uuid4().hex[:14].upper()}"

def create_payment(user, booking, amount, payment_method):
    """
    Initializes a new Payment record in the database with status PENDING.
    """
    payment = Payment.objects.create(
        user=user,
        booking=booking,
        payment_id=generate_payment_id(),
        transaction_id=generate_transaction_id(),
        amount=float(amount),
        payment_method=payment_method,
        payment_status='PENDING',
        currency='INR'
    )
    return payment

def process_mock_payment(payment, force_success=True):
    """
    Simulates mock payment processing logic.
    Updates the payment status to SUCCESS or FAILED.
    Fills mock_gateway_response with JSON metadata.
    """
    # Determine mock gateway response outcome
    if force_success:
        outcome = 'SUCCESS'
        error_code = None
        error_message = None
    else:
        # Simulate 85% success rate for natural mock testing
        is_success = random.choices([True, False], weights=[85, 15], k=1)[0]
        outcome = 'SUCCESS' if is_success else 'FAILED'
        error_code = None if is_success else 'ERR_INSUFFICIENT_FUNDS'
        error_message = None if is_success else 'The transaction failed because of insufficient funds.'

    payment.payment_status = outcome
    
    # Structure gateway response payload
    gateway_response = {
        'gateway_status': outcome,
        'gateway_transaction_id': f"GATEWAY-{uuid.uuid4().hex[:12].upper()}",
        'response_timestamp': timezone.now().isoformat(),
        'payment_method': payment.payment_method,
        'amount': payment.amount,
        'currency': payment.currency,
    }

    if error_code:
        gateway_response['error_code'] = error_code
        gateway_response['error_message'] = error_message
        payment.remarks = f"Payment failed: {error_message}"
    else:
        payment.remarks = "Payment processed successfully via Mock Payment Gateway."

    # Populate dummy credentials based on payment method
    if payment.payment_method == 'UPI':
        gateway_response['upi_vpa'] = f"{payment.user.username}@mockbank"
    elif payment.payment_method == 'CARD':
        gateway_response['card_last4'] = "4321"
        gateway_response['card_brand'] = "VISA"
    elif payment.payment_method == 'NETBANKING':
        gateway_response['bank_name'] = "Mock State Bank of India"
    elif payment.payment_method == 'WALLET':
        gateway_response['wallet_provider'] = "MockPay Wallet"

    payment.mock_gateway_response = gateway_response
    payment.save()

    # Trigger booking updates upon success
    if outcome == 'SUCCESS':
        update_booking_status(payment)

    return payment

def verify_payment(payment_id):
    """
    Retrieves and verifies a payment by payment_id.
    """
    try:
        return Payment.objects.get(payment_id=payment_id)
    except Payment.DoesNotExist:
        return None

def update_booking_status(payment):
    """
    Updates the booking (Trip_Members) payment_status and registration status.
    For advance payments (status=3), calculates remaining balance and sets final status.
    """
    booking = payment.booking
    if booking.status == 3:
        booking.paid_amount = payment.amount
        try:
            per_head_cost = booking.trip.trip_details.per_head_cost
        except Exception:
            per_head_cost = 0.0
        booking.unpaid_amount = max(0.0, (per_head_cost * booking.group_size) - payment.amount)
        if booking.unpaid_amount <= 0.01:
            booking.payment_status = 1  # PAID
        else:
            booking.payment_status = 0  # UNPAID / PARTIALLY PAID
            
        if getattr(booking.trip, 'approval_required', True):
            booking.status = 0  # Pending Approval
        else:
            booking.status = 1  # Joined
    else:
        booking.payment_status = 1  # 1 represents PAID
        
    booking.save()
