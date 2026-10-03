from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

User = get_user_model()


class UserAuthTests(APITestCase):
    def setUp(self):
        self.register_url = "/api/v1/auth/register/"
        self.login_url = "/api/v1/auth/login/"

    def test_register_buyer_successfully(self):
        """Test registering a standard buyer user."""
        payload = {
            "username": "johndoe",
            "email": "johndoe@example.com",
            "password": "StrongPassword123!",
            "role": "BUYER",
        }
        response = self.client.post(self.register_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(username="johndoe", role="BUYER").exists())
        # Ensure password is encrypted
        user = User.objects.get(username="johndoe")
        self.assertTrue(user.check_password("StrongPassword123!"))

    def test_register_seller_successfully(self):
        """Test registering a seller user."""
        payload = {
            "username": "store_owner",
            "email": "owner@example.com",
            "password": "StrongPassword123!",
            "role": "SELLER",
        }
        response = self.client.post(self.register_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(username="store_owner", role="SELLER").exists())

    def test_jwt_login_success(self):
        """Test that active users receive access and refresh JWTs upon login."""
        User.objects.create_user(
            username="testuser",
            email="testuser@example.com",
            password="TestPassword123!",
            role="BUYER",
        )
        payload = {
            "username": "testuser",
            "password": "TestPassword123!",
        }
        response = self.client.post(self.login_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_jwt_login_invalid_password(self):
        """Test login rejection when password is wrong."""
        User.objects.create_user(
            username="testuser",
            email="testuser@example.com",
            password="CorrectPassword123!",
            role="BUYER",
        )
        payload = {
            "username": "testuser",
            "password": "WrongPassword!",
        }
        response = self.client.post(self.login_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def setUp(self):
        
        try:
            self.login_url = reverse("login")
        except:
           
            self.login_url = reverse("token_obtain_pair")

        try:
            self.register_url = reverse("register")
        except:
            self.register_url = "/api/v1/auth/register/"