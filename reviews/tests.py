from decimal import Decimal
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from orders.models import Order, OrderItem
from products.models import Category, Product
from reviews.models import Review

User = get_user_model()


class ReviewTests(APITestCase):
    def setUp(self):
        self.seller = User.objects.create_user(
            username="rev_seller", email="rs@test.com", password="Password123!", role="SELLER"
        )
        self.buyer = User.objects.create_user(
            username="rev_buyer", email="rb@test.com", password="Password123!", role="BUYER"
        )
        self.other_buyer = User.objects.create_user(
            username="rev_other", email="ro@test.com", password="Password123!", role="BUYER"
        )
        self.category = Category.objects.create(name="Shoes", slug="shoes", is_active=True)
        self.product = Product.objects.create(
            seller=self.seller,
            category=self.category,
            name="Running Shoes",
            slug="running-shoes",
            price=Decimal("120.00"),
            stock=15,
            is_active=True,
        )

        self.reviews_url = reverse("review-list")

    def test_review_rejected_without_verified_purchase(self):
        """Buyers cannot review products they have not purchased."""
        self.client.force_authenticate(user=self.buyer)
        payload = {"product": str(self.product.id), "rating": 5, "comment": "Nice!"}
        response = self.client.post(self.reviews_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_review_accepted_after_verified_purchase(self):
        """Review creation succeeds after an order in a valid status exists."""
        order = Order.objects.create(
            user=self.buyer,
            total_amount=Decimal("120.00"),
            shipping_address="100 Pine St",
            phone_number="555-1234",
            status=Order.Status.DELIVERED,
        )
        OrderItem.objects.create(
            order=order,
            product=self.product,
            seller=self.seller,
            product_name="Running Shoes",
            price=Decimal("120.00"),
            quantity=1,
        )

        self.client.force_authenticate(user=self.buyer)
        payload = {"product": str(self.product.id), "rating": 5, "comment": "Great quality shoes!"}
        response = self.client.post(self.reviews_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Review.objects.filter(user=self.buyer, product=self.product).exists())

    def test_prevent_duplicate_reviews_on_same_product(self):
        """A user cannot submit more than one review for the same product."""
        Review.objects.create(user=self.buyer, product=self.product, rating=4, comment="First review")

        self.client.force_authenticate(user=self.buyer)
        payload = {"product": str(self.product.id), "rating": 5, "comment": "Duplicate attempt"}
        response = self.client.post(self.reviews_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_only_author_can_edit_review(self):
        """Other users cannot modify a review they did not author."""
        review = Review.objects.create(
            user=self.buyer, product=self.product, rating=4, comment="Original review"
        )
        detail_url = reverse("review-detail", kwargs={"pk": review.id})

        # Another authenticated buyer tries to edit it
        self.client.force_authenticate(user=self.other_buyer)
        response = self.client.patch(detail_url, {"rating": 1}, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)