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


class SignupNameValidationTests(TestCase):
    def test_signup_first_name_numeric(self):
        url = reverse('member_signup')
        data = {
            'first_name': 'John123',
            'last_name': 'User',
            'email': 'signupuser@example.com',
            'username': 'signupuser',
            'password': 'password123',
            'confirm_password': 'password123',
            'is_coordinator': 'False'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "First name should not include numeric or special characters.")

    def test_signup_first_name_special_char(self):
        url = reverse('member_signup')
        data = {
            'first_name': 'John@',
            'last_name': 'User',
            'email': 'signupuser@example.com',
            'username': 'signupuser',
            'password': 'password123',
            'confirm_password': 'password123',
            'is_coordinator': 'False'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "First name should not include numeric or special characters.")

    def test_signup_last_name_numeric(self):
        url = reverse('member_signup')
        data = {
            'first_name': 'John',
            'last_name': 'User123',
            'email': 'signupuser@example.com',
            'username': 'signupuser',
            'password': 'password123',
            'confirm_password': 'password123',
            'is_coordinator': 'False'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Last name should not include numeric or special characters.")

    def test_signup_last_name_special_char(self):
        url = reverse('member_signup')
        data = {
            'first_name': 'John',
            'last_name': 'User#',
            'email': 'signupuser@example.com',
            'username': 'signupuser',
            'password': 'password123',
            'confirm_password': 'password123',
            'is_coordinator': 'False'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Last name should not include numeric or special characters.")

    def test_signup_names_with_spaces_valid(self):
        url = reverse('member_signup')
        data = {
            'first_name': 'Mary Ann',
            'last_name': 'De Silva',
            'email': 'signupuser@example.com',
            'username': 'signupuser',
            'password': 'password123',
            'confirm_password': 'password123',
            'is_coordinator': 'False'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)  # Redirects on success


class ProfileEditNameValidationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='profileuser',
            email='profileuser@example.com',
            password='password123',
            first_name='John',
            last_name='Doe'
        )
        self.client.login(username='profileuser', password='password123')

    def test_profile_edit_first_name_numeric(self):
        url = reverse('member_profile_edit')
        data = {
            'first_name': 'John123',
            'last_name': 'Doe',
            'dob': '1990-01-01',
            'gender': 'Male',
            'phone': '1234567890',
            'bgroup': 'O+',
            'address': 'Test Address',
            'emergency_name': 'Emergency Contact',
            'emergency_contact': '0987654321',
            'description': 'About user'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "First name should not include numeric or special characters.")

    def test_profile_edit_last_name_special_char(self):
        url = reverse('member_profile_edit')
        data = {
            'first_name': 'John',
            'last_name': 'Doe$',
            'dob': '1990-01-01',
            'gender': 'Male',
            'phone': '1234567890',
            'bgroup': 'O+',
            'address': 'Test Address',
            'emergency_name': 'Emergency Contact',
            'emergency_contact': '0987654321',
            'description': 'About user'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Last name should not include numeric or special characters.")


