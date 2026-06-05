from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from django.core import mail

class PasswordResetTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='testuser@example.com',
            password='oldpassword123'
        )

    def test_password_reset_view_loads(self):
        url = reverse('password_reset')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'member/password_reset_form.html')

    def test_password_reset_submission_sends_email(self):
        url = reverse('password_reset')
        # Submit valid email
        response = self.client.post(url, {'email': 'testuser@example.com'})
        self.assertEqual(response.status_code, 302)  # Redirects to success url
        self.assertRedirects(response, reverse('password_reset_done'))
        
        # Verify email is sent
        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertEqual(email.subject, 'Password reset on Trip Weaver')
        self.assertIn(self.user.username, email.body)
        
        # Verify the html version is included
        self.assertEqual(len(email.alternatives), 1)
        html_content, mimetype = email.alternatives[0]
        self.assertEqual(mimetype, 'text/html')
        self.assertIn('TRIP', html_content)
        self.assertIn('WEAVER', html_content)

    def test_password_reset_done_view(self):
        url = reverse('password_reset_done')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'member/password_reset_done.html')

    def test_password_reset_complete_view(self):
        url = reverse('password_reset_complete')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'member/password_reset_complete.html')

class SignupPasswordValidationTests(TestCase):
    def test_signup_password_too_short(self):
        url = reverse('member_signup')
        data = {
            'first_name': 'Test',
            'last_name': 'User',
            'email': 'signupuser@example.com',
            'username': 'signupuser',
            'password': '123',
            'confirm_password': '123',
            'is_coordinator': 'False'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Password must be at least 8 characters long.")

    def test_signup_password_entirely_numeric(self):
        url = reverse('member_signup')
        data = {
            'first_name': 'Test',
            'last_name': 'User',
            'email': 'signupuser@example.com',
            'username': 'signupuser',
            'password': '123456789',
            'confirm_password': '123456789',
            'is_coordinator': 'False'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Password cannot be entirely numeric.")

    def test_signup_password_no_letters(self):
        url = reverse('member_signup')
        data = {
            'first_name': 'Test',
            'last_name': 'User',
            'email': 'signupuser@example.com',
            'username': 'signupuser',
            'password': '12345678!',
            'confirm_password': '12345678!',
            'is_coordinator': 'False'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Password must contain at least one letter.")

