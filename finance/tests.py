from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.exceptions import ValidationError
from trip.models import Trip, TripCategory, Trip_Details, Trip_Members, TripBroadcastMessage
from member.models import Member, Coordinator, CoordinatorNotification
from finance.models import Expenses, ExpensesCategory
from finance.forms import ReimbursementRequestForm
from datetime import timedelta

class MemberReimbursementTestCase(TestCase):
    def setUp(self):
        # 1. Create Users
        self.coordinator_user = User.objects.create_user(
            username='coordinator',
            email='coordinator@test.com',
            password='password123',
            first_name='Coordinator',
            last_name='User'
        )
        self.member_user = User.objects.create_user(
            username='member',
            email='member@test.com',
            password='password123',
            first_name='Member',
            last_name='User'
        )
        self.non_member_user = User.objects.create_user(
            username='nonmember',
            email='nonmember@test.com',
            password='password123',
            first_name='Non',
            last_name='Member'
        )

        # 2. Create Profiles
        self.coord_profile = Coordinator.objects.create(
            user=self.coordinator_user,
            is_authorised=True,
            is_approved=True
        )
        self.member_profile = Member.objects.create(
            user=self.member_user,
            phone='9876543210'
        )
        self.non_member_profile = Member.objects.create(
            user=self.non_member_user,
            phone='1234567890'
        )

        # 3. Create Trip Setup
        self.category = TripCategory.objects.create(name='Adventure')
        self.trip = Trip.objects.create(
            title='Himalayan Trek',
            category=self.category,
            location_from_name='Delhi',
            location_to_name='Manali',
            distance=550.0,
            from_date=timezone.localdate() + timedelta(days=10),
            from_time=timezone.now().time(),
            to_date=timezone.localdate() + timedelta(days=15),
            to_time=timezone.now().time(),
            duration='5 Days',
            coordinator=self.coord_profile
        )

        self.trip_details = Trip_Details.objects.create(
            trip=self.trip,
            max_members=10,
            no_of_members=1,
            estimated_cost=5000.0
        )

        # 4. Set Membership status
        # Member is joined and approved (status=1)
        self.tm_member = Trip_Members.objects.create(
            trip=self.trip,
            member=self.member_profile,
            status=1,
            paid_amount=0.0
        )
        # Non-member has a pending request (status=0)
        self.tm_non_member = Trip_Members.objects.create(
            trip=self.trip,
            member=self.non_member_profile,
            status=0
        )

        # 5. Create Expense Category
        self.expense_category = ExpensesCategory.objects.create(
            name='Food',
            description='Trip related food expenses'
        )

        # HTTP Clients
        self.client = Client()

    def test_default_expense_fields(self):
        """
        Verify that creating a normal expense assigns appropriate defaults (backward-compatible).
        """
        expense = Expenses.objects.create(
            trip=self.trip,
            expense_category=self.expense_category,
            amount=250.0,
            description='Normal tea break'
        )
        self.assertEqual(expense.expense_type, 'NORMAL_EXPENSE')
        self.assertEqual(expense.approval_status, 'APPROVED')
        self.assertEqual(expense.reimbursement_status, 'NOT_REQUIRED')
        self.assertIsNone(expense.proof_file)

    def test_reimbursement_submission_permissions(self):
        """
        Joined member can submit requests, but non-members or anonymous users are rejected.
        """
        # Test anonymous user redirected to login
        response = self.client.post(
            reverse('submit_reimbursement', kwargs={'trip_id': self.trip.id}),
            {}
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)

        # Test non-member member (status=0) access denied
        self.client.login(username='nonmember', password='password123')
        response = self.client.post(
            reverse('submit_reimbursement', kwargs={'trip_id': self.trip.id}),
            {
                'title': 'Dinner for group',
                'amount': 1500.0,
                'expense_category': self.expense_category.id,
                'date_of_expense': timezone.localdate(),
                'description': 'Dinner paid on behalf',
                'proof_file': SimpleUploadedFile('bill.jpg', b'dummy_content', content_type='image/jpeg')
            }
        )
        self.assertEqual(response.status_code, 302) # redirects to trip page
        # Check that no expense was created
        self.assertFalse(Expenses.objects.filter(trip=self.trip, expense_type='MEMBER_REIMBURSEMENT').exists())

        # Test joined member (status=1) submits successfully
        self.client.login(username='member', password='password123')
        response = self.client.post(
            reverse('submit_reimbursement', kwargs={'trip_id': self.trip.id}),
            {
                'title': 'Dinner for group',
                'amount': 1500.0,
                'expense_category': self.expense_category.id,
                'date_of_expense': timezone.localdate(),
                'description': 'Dinner paid on behalf',
                'proof_file': SimpleUploadedFile('bill.jpg', b'dummy_content', content_type='image/jpeg')
            }
        )
        self.assertEqual(response.status_code, 302)
        # Check that expense is created and defaults to PENDING
        expense = Expenses.objects.filter(trip=self.trip, expense_type='MEMBER_REIMBURSEMENT').first()
        self.assertIsNotNone(expense)
        self.assertEqual(expense.title, 'Dinner for group')
        self.assertEqual(expense.amount, 1500.0)
        self.assertEqual(expense.approval_status, 'PENDING')
        self.assertEqual(expense.reimbursement_status, 'NOT_REQUIRED')
        self.assertEqual(expense.created_by, self.member_user)

        # Verify coordinator notification was sent
        notification = CoordinatorNotification.objects.filter(coordinator=self.coord_profile).first()
        self.assertIsNotNone(notification)
        self.assertIn('reimbursement request submitted', notification.message.lower())

    def test_duplicate_prevention_validation(self):
        """
        Verify that submitting an identical request within 5 minutes raises a form validation error.
        """
        # Create a pre-existing request
        Expenses.objects.create(
            trip=self.trip,
            expense_category=self.expense_category,
            title='Highway Lunch',
            amount=800.0,
            expense_type='MEMBER_REIMBURSEMENT',
            approval_status='PENDING',
            created_by=self.member_user,
            paid_by=self.member_user,
            date_of_expense=timezone.localdate()
        )

        # Instantiate a form with identical inputs
        form_data = {
            'title': 'Highway Lunch',
            'amount': 800.0,
            'expense_category': self.expense_category.id,
            'date_of_expense': timezone.localdate(),
            'description': 'Paid lunch',
        }
        file_data = {
            'proof_file': SimpleUploadedFile('receipt.jpg', b'img_data', content_type='image/jpeg')
        }
        
        # Test clean raises error due to duplicate
        form = ReimbursementRequestForm(
            data=form_data, 
            files=file_data, 
            trip=self.trip, 
            user=self.member_user
        )
        self.assertFalse(form.is_valid())
        self.assertIn('A similar reimbursement request has already been submitted', form.non_field_errors()[0])

    def test_proof_file_validation(self):
        """
        Verify that proof files are validated for size (max 5MB) and support only images or PDFs.
        """
        # 1. Invalid Extension
        form_data = {
            'title': 'Cab Fare',
            'amount': 400.0,
            'expense_category': self.expense_category.id,
            'date_of_expense': timezone.localdate(),
        }
        file_data = {
            'proof_file': SimpleUploadedFile('receipt.exe', b'malicious_script', content_type='application/octet-stream')
        }
        form = ReimbursementRequestForm(data=form_data, files=file_data, trip=self.trip, user=self.member_user)
        self.assertFalse(form.is_valid())
        self.assertIn('proof_file', form.errors)
        self.assertIn('Only PDF and images (JPG, PNG) are supported', form.errors['proof_file'][0])

        # 2. Size Limit Exceeded (6MB)
        oversized_data = b'0' * (6 * 1024 * 1024)
        file_data_oversized = {
            'proof_file': SimpleUploadedFile('large_bill.png', oversized_data, content_type='image/png')
        }
        form_oversized = ReimbursementRequestForm(data=form_data, files=file_data_oversized, trip=self.trip, user=self.member_user)
        self.assertFalse(form_oversized.is_valid())
        self.assertIn('proof_file', form_oversized.errors)
        self.assertIn('Max size allowed is 5MB', form_oversized.errors['proof_file'][0])

    def test_approval_workflow(self):
        """
        Coordinator can approve pending reimbursement, transitioning state, launching member secure alert,
        and triggering recalculations.
        """
        expense = Expenses.objects.create(
            trip=self.trip,
            expense_category=self.expense_category,
            title='Trek Supplies',
            amount=2000.0,
            expense_type='MEMBER_REIMBURSEMENT',
            approval_status='PENDING',
            reimbursement_status='NOT_REQUIRED',
            created_by=self.member_user,
            paid_by=self.member_user,
            date_of_expense=timezone.localdate()
        )

        # Login as coordinator
        self.client.login(username='coordinator', password='password123')
        response = self.client.post(
            reverse('approve_reimbursement', kwargs={'expense_id': expense.id})
        )
        self.assertEqual(response.status_code, 302)

        # Verify states changed
        expense.refresh_from_db()
        self.assertEqual(expense.approval_status, 'APPROVED')
        self.assertEqual(expense.reimbursement_status, 'PAYMENT_PENDING')
        self.assertEqual(expense.approved_by, self.coordinator_user)
        self.assertIsNotNone(expense.approved_at)

        # Verify member secure alert sent
        alert = TripBroadcastMessage.objects.filter(trip=self.trip, recipient=self.member_profile).first()
        self.assertIsNotNone(alert)
        self.assertIn('approved', alert.message.lower())

    def test_rejection_workflow(self):
        """
        Coordinator can reject a request, updating approval status and sending alerts.
        """
        expense = Expenses.objects.create(
            trip=self.trip,
            expense_category=self.expense_category,
            title='Extra baggage',
            amount=500.0,
            expense_type='MEMBER_REIMBURSEMENT',
            approval_status='PENDING',
            created_by=self.member_user,
            paid_by=self.member_user,
            date_of_expense=timezone.localdate()
        )

        self.client.login(username='coordinator', password='password123')
        response = self.client.post(
            reverse('reject_reimbursement', kwargs={'expense_id': expense.id})
        )
        self.assertEqual(response.status_code, 302)

        expense.refresh_from_db()
        self.assertEqual(expense.approval_status, 'REJECTED')
        
        # Verify alert
        alert = TripBroadcastMessage.objects.filter(trip=self.trip, recipient=self.member_profile).first()
        self.assertIsNotNone(alert)
        self.assertIn('rejected', alert.message.lower())

    def test_payment_settlement_workflow(self):
        """
        Coordinator can pay out approved request, setting reference, notes, and complete receipt logs.
        """
        expense = Expenses.objects.create(
            trip=self.trip,
            expense_category=self.expense_category,
            title='Fuel charge',
            amount=3000.0,
            expense_type='MEMBER_REIMBURSEMENT',
            approval_status='APPROVED',
            reimbursement_status='PAYMENT_PENDING',
            created_by=self.member_user,
            paid_by=self.member_user,
            date_of_expense=timezone.localdate()
        )

        self.client.login(username='coordinator', password='password123')
        response = self.client.post(
            reverse('pay_reimbursement', kwargs={'expense_id': expense.id}),
            {
                'payment_reference': 'UPI-9827491-XYZ',
                'payment_notes': 'Transferred to phone number'
            }
        )
        self.assertEqual(response.status_code, 302)

        # Verify fields
        expense.refresh_from_db()
        self.assertEqual(expense.reimbursement_status, 'PAID')
        self.assertEqual(expense.payment_reference, 'UPI-9827491-XYZ')
        self.assertEqual(expense.payment_notes, 'Transferred to phone number')
        self.assertIsNotNone(expense.reimbursement_paid_at)

        # Verify alert
        alert = TripBroadcastMessage.objects.filter(trip=self.trip, recipient=self.member_profile).first()
        self.assertIsNotNone(alert)
        self.assertIn('completed', alert.message.lower())

    def test_finance_calculation_integration(self):
        """
        Only approved member reimbursements affect the trip total expenses and member balances.
        Pending or rejected ones must be excluded.
        """
        # Recalculate initially with no expenses
        self.trip.recalculate_finance()
        self.tm_member.refresh_from_db()
        # Per head estimated cost = 5000.0. Member group size = 1. Member balance = 5000.0.
        self.assertEqual(self.tm_member.unpaid_amount, 5000.0)

        # 1. Add NORMAL_EXPENSE
        Expenses.objects.create(
            trip=self.trip,
            expense_category=self.expense_category,
            amount=1000.0,
            expense_type='NORMAL_EXPENSE'
        )
        self.tm_member.refresh_from_db()
        # Deficit = 1000.0. Split to 1 joined member = +1000.0. Total per head balance = 6000.0.
        self.assertEqual(self.tm_member.unpaid_amount, 6000.0)

        # 2. Add PENDING member reimbursement request (must have zero effect)
        pending_reimb = Expenses.objects.create(
            trip=self.trip,
            expense_category=self.expense_category,
            amount=2000.0,
            expense_type='MEMBER_REIMBURSEMENT',
            approval_status='PENDING',
            created_by=self.member_user,
            paid_by=self.member_user
        )
        self.tm_member.refresh_from_db()
        self.assertEqual(self.tm_member.unpaid_amount, 6000.0)

        # 3. Add REJECTED request (must have zero effect)
        Expenses.objects.create(
            trip=self.trip,
            expense_category=self.expense_category,
            amount=1200.0,
            expense_type='MEMBER_REIMBURSEMENT',
            approval_status='REJECTED',
            created_by=self.member_user,
            paid_by=self.member_user
        )
        self.tm_member.refresh_from_db()
        self.assertEqual(self.tm_member.unpaid_amount, 6000.0)

        # 4. Transition the pending request to APPROVED (should instantly affect finance)
        self.client.login(username='coordinator', password='password123')
        self.client.post(
            reverse('approve_reimbursement', kwargs={'expense_id': pending_reimb.id})
        )
        
        self.tm_member.refresh_from_db()
        # Deficit is now: 1000.0 (normal) + 2000.0 (approved reimbursement) = 3000.0.
        # Split to 1 joined member = +3000.0. Total per head balance = 5000.0 + 3000.0 = 8000.0.
        self.assertEqual(self.tm_member.unpaid_amount, 8000.0)
