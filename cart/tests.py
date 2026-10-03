from decimal import Decimal
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from cart.models import Cart, CartItem
from products.models import Category, Product

User = get_user_model()


class CartTests(APITestCase):
    def setUp(self):
        self.buyer = User.objects.create_user(
            username="buyer_cart", email="bc@test.com", password="Password123!", role="BUYER"
        )
        self.seller = User.objects.create_user(
            username="seller_cart", email="sc@test.com", password="Password123!", role="SELLER"
        )
        self.category = Category.objects.create(name="Monitors", slug="monitors", is_active=True)
        self.product = Product.objects.create(
            seller=self.seller,
            category=self.category,
            name="4K Monitor",
            slug="4k-monitor",
            price=Decimal("400.00"),
            stock=4,
            is_active=True,
        )

        self.cart_url = reverse("cart-detail")
        self.cart_add_url = reverse("cart-add-item")
        self.cart_clear_url = reverse("cart-clear")

    def test_cart_requires_authentication(self):
        """Anonymous access returns 401 Unauthorized."""
        response = self.client.get(self.cart_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_add_item_to_cart_and_increment(self):
        """Adding duplicate product increments item quantity."""
        self.client.force_authenticate(user=self.buyer)

        # 1. Add 1 item
        payload = {"product_id": str(self.product.id), "quantity": 1}
        res1 = self.client.post(self.cart_add_url, payload, format="json")
        self.assertEqual(res1.status_code, status.HTTP_201_CREATED)
        self.assertEqual(len(res1.data["items"]), 1)
        self.assertEqual(res1.data["items"][0]["quantity"], 1)

        # 2. Add 2 more of the same item
        payload2 = {"product_id": str(self.product.id), "quantity": 2}
        res2 = self.client.post(self.cart_add_url, payload2, format="json")
        self.assertEqual(res2.status_code, status.HTTP_201_CREATED)
        self.assertEqual(len(res2.data["items"]), 1)
        self.assertEqual(res2.data["items"][0]["quantity"], 3)

    def test_add_item_exceeding_stock_fails(self):
        """Adding quantity greater than inventory returns 400 Bad Request."""
        self.client.force_authenticate(user=self.buyer)
        payload = {"product_id": str(self.product.id), "quantity": 10}
        response = self.client.post(self.cart_add_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_clear_cart(self):
        """Clearing the cart removes all cart items."""
        self.client.force_authenticate(user=self.buyer)
        cart = Cart.objects.create(user=self.buyer)
        CartItem.objects.create(cart=cart, product=self.product, quantity=2)

        response = self.client.delete(self.cart_clear_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(cart.items.count(), 0)