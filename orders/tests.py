from decimal import Decimal
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from users.models import User
from products.models import Category, Product
from cart.models import Cart, CartItem
from orders.models import Order, OrderItem
from reviews.models import Review


class ECommerceIntegrationTests(APITestCase):

    def setUp(self):
        # 1. Create test category
        self.category = Category.objects.create(
            name="Keyboards",
            slug="keyboards",
            is_active=True,
        )

        # 2. Create Seller user
        self.seller = User.objects.create_user(
            username="test_seller",
            email="seller@test.com",
            password="Password123!",
            role="SELLER",
        )

        # 3. Create Buyer user
        self.buyer = User.objects.create_user(
            username="test_buyer",
            email="buyer@test.com",
            password="Password123!",
            role="BUYER",
        )

        # 4. Create a product owned by the seller
        self.product = Product.objects.create(
            seller=self.seller,
            category=self.category,
            name="Mechanical Keyboard",
            slug="mechanical-keyboard",
            price=Decimal("150.00"),
            stock=5,
            is_active=True,
        )

        self.checkout_url = reverse("order-checkout")
        self.cart_items_url = reverse("cart-add-item")
        self.review_url = reverse("review-list")
        self.seller_product_url = reverse("seller-product-list")
        self.public_product_url = reverse("public-product-list")

    def test_seller_can_create_product_buyer_cannot(self):
        """Test that sellers can create products, but buyers receive 403 Forbidden."""
        product_data = {
            "name": "Gaming Mouse",
            "category": str(self.category.id),
            "price": "59.99",
            "stock": 10,
            "is_active": True,
        }

        # --- Attempt as Buyer (Should Fail) ---
        self.client.force_authenticate(user=self.buyer)
        response = self.client.post(self.seller_product_url, product_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # --- Attempt as Seller (Should Succeed) ---
        self.client.force_authenticate(user=self.seller)
        response = self.client.post(self.seller_product_url, product_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["name"], "Gaming Mouse")

        # Verify directly in PostgreSQL that the product was created and assigned to the seller
        created_product = Product.objects.get(name="Gaming Mouse")
        self.assertEqual(created_product.seller, self.seller)

    def test_cart_management_and_checkout_atomic_flow(self):
        """Test adding items to cart, running atomic checkout, and verifying stock deduction."""
        self.client.force_authenticate(user=self.buyer)

        # 1. Add item to cart
        cart_data = {
            "product_id": str(self.product.id),
            "quantity": 2,
        }
        response = self.client.post(self.cart_items_url, cart_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(len(response.data["items"]), 1)
        self.assertEqual(response.data["total_price"], "300.00")

        # 2. Perform Checkout
        checkout_data = {
            "shipping_address": "123 Test Street, Suite 100",
            "phone_number": "+15550199",
        }
        response = self.client.post(self.checkout_url, checkout_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["status"], "PENDING")
        self.assertEqual(response.data["total_amount"], "300.00")
        self.assertEqual(len(response.data["items"]), 1)

        # 3. Verify stock was securely deducted in PostgreSQL (5 - 2 = 3)
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 3)

        # 4. Verify cart was cleared after successful checkout
        cart = Cart.objects.get(user=self.buyer)
        self.assertEqual(cart.items.count(), 0)

    def test_checkout_fails_on_insufficient_stock(self):
        """Test that checkout fails atomically if requested quantity exceeds stock."""
        self.client.force_authenticate(user=self.buyer)

        # Request more than available stock (Stock is 5)
        cart = Cart.objects.get_or_create(user=self.buyer)[0]
        CartItem.objects.create(cart=cart, product=self.product, quantity=10)

        checkout_data = {
            "shipping_address": "123 Test Street",
            "phone_number": "+15550199",
        }
        response = self.client.post(self.checkout_url, checkout_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("units left in stock", response.data["error"])

        # Verify stock was NOT modified due to atomic rollback
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 5)

    def test_verified_purchase_review_restriction(self):
        """Test that buyers cannot review unpurchased products, but can review purchased ones."""
        self.client.force_authenticate(user=self.buyer)

        review_data = {
            "product": str(self.product.id),
            "rating": 5,
            "comment": "Great keyboard!",
        }

        # 1. Try reviewing without purchasing (Should Fail)
        response = self.client.post(self.review_url, review_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("successfully purchased", str(response.data["product"]))

        # 2. Simulate order purchase
        order = Order.objects.create(
            user=self.buyer,
            total_amount=Decimal("150.00"),
            shipping_address="123 Test St",
            phone_number="555-0199",
            status=Order.Status.DELIVERED,
        )
        OrderItem.objects.create(
            order=order,
            product=self.product,
            seller=self.seller,
            product_name=self.product.name,
            price=self.product.price,
            quantity=1,
        )

        # 3. Retry review after purchase (Should Succeed)
        response = self.client.post(self.review_url, review_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["rating"], 5)

        # 4. Verify review was persisted in PostgreSQL
        self.assertTrue(
            Review.objects.filter(product=self.product, user=self.buyer, rating=5).exists()
        )