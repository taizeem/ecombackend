from decimal import Decimal
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from products.models import Category, Product

User = get_user_model()


class ProductCatalogTests(APITestCase):
    def setUp(self):
        self.category = Category.objects.create(name="Audio", slug="audio", is_active=True)

        self.seller_1 = User.objects.create_user(
            username="seller_one", email="s1@test.com", password="Password123!", role="SELLER"
        )
        self.seller_2 = User.objects.create_user(
            username="seller_two", email="s2@test.com", password="Password123!", role="SELLER"
        )
        self.buyer = User.objects.create_user(
            username="buyer_one", email="b1@test.com", password="Password123!", role="BUYER"
        )

        self.product_1 = Product.objects.create(
            seller=self.seller_1,
            category=self.category,
            name="Wireless Headphones",
            slug="wireless-headphones",
            price=Decimal("199.99"),
            stock=10,
            is_active=True,
        )

        self.public_products_url = reverse("public-product-list")
        self.seller_products_url = reverse("seller-product-list")

    def test_public_catalog_browsing_without_authentication(self):
        """Public catalog allows unauthenticated access and supports search."""
        response = self.client.get(self.public_products_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)

        # Test Search filter
        search_res = self.client.get(f"{self.public_products_url}?search=Headphones")
        self.assertEqual(search_res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(search_res.data["results"]), 1)

        empty_search = self.client.get(f"{self.public_products_url}?search=NonExistent")
        self.assertEqual(len(empty_search.data["results"]), 0)

    def test_buyer_forbidden_from_creating_products(self):
        """Buyers are rejected with 403 on seller creation endpoint."""
        self.client.force_authenticate(user=self.buyer)
        payload = {
            "name": "Unauthorized Earbuds",
            "category": self.category.id,
            "price": "49.99",
            "stock": 5,
        }
        response = self.client.post(self.seller_products_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_seller_isolation_in_dashboard(self):
        """Sellers can only list and modify their own inventory."""
        # Authenticate as Seller 2
        self.client.force_authenticate(user=self.seller_2)

        # Seller 2 requests their seller inventory; should not see Seller 1's product
        response = self.client.get(self.seller_products_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 0)

        # Seller 2 attempts to edit Seller 1's product directly
        detail_url = reverse("seller-product-detail", kwargs={"pk": self.product_1.id})
        update_res = self.client.patch(detail_url, {"price": "149.99"}, format="json")
        self.assertEqual(update_res.status_code, status.HTTP_404_NOT_FOUND)