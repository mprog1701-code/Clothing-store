from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.test import Client
from core.models import Store, Product, ProductVariant, AttributeColor, Order, Address


class CartAndCheckoutTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.client = Client()

        self.admin = User.objects.create_user(
            username="admin1", password="pass1234", role="admin", phone="07700000001", city="Baghdad"
        )
        self.customer = User.objects.create_user(
            username="cust1", password="pass1234", role="customer", phone="07700000002", city="Baghdad"
        )
        self.other_customer = User.objects.create_user(
            username="cust2", password="pass1234", role="customer", phone="07700000003", city="Baghdad"
        )

        self.store_a = Store.objects.create(owner=self.admin, name="Store A", city="Baghdad", address="addr A")
        self.store_b = Store.objects.create(owner=self.admin, name="Store B", city="Baghdad", address="addr B")

        self.product_with_variant = Product.objects.create(
            store=self.store_a,
            name="Shirt V",
            description="Variant product",
            base_price=10000,
            category="men",
            size_type="symbolic",
        )
        color_red = AttributeColor.objects.create(name="Red", code="#ff0000")
        self.variant_v1 = ProductVariant.objects.create(
            product=self.product_with_variant,
            color_attr=color_red,
            size="M",
            stock_qty=1,
        )

        self.product_a = Product.objects.create(
            store=self.store_a,
            name="Plain Tee",
            description="Basic tee",
            base_price=5000,
            category="men",
            size_type="none",
        )

        self.product_b = Product.objects.create(
            store=self.store_b,
            name="Cap",
            description="Basic cap",
            base_price=3000,
            category="men",
            size_type="none",
        )

    def login_customer(self):
        self.client.login(username="cust1", password="pass1234")

    def test_add_to_cart_variant_required(self):
        self.login_customer()
        url = reverse("cart_items_json")
        payload = {"productId": self.product_with_variant.id, "quantity": 1}
        res = self.client.post(url, data=payload, content_type="application/json", HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json().get("code"), "VARIANT_REQUIRED")

    def test_multi_store_rejection(self):
        self.login_customer()
        url = reverse("cart_items_json")
        res1 = self.client.post(
            url,
            data={"productId": self.product_a.id, "quantity": 1},
            content_type="application/json",
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(res1.status_code, 200)
        self.assertTrue(res1.json().get("ok"))

        res2 = self.client.post(
            url,
            data={"productId": self.product_b.id, "quantity": 1},
            content_type="application/json",
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(res2.status_code, 409)
        self.assertEqual(res2.json().get("code"), "MULTI_STORE_NOT_ALLOWED")

    def test_checkout_stock_failed(self):
        self.login_customer()
        addr = Address.objects.create(user=self.customer, city="Baghdad", area="Karrada", street="1st")
        session = self.client.session
        session["cart"] = [
            {"product_id": self.product_with_variant.id, "variant_id": self.variant_v1.id, "quantity": 2}
        ]
        session["cart_store_id"] = self.store_a.id
        session.save()

        url = reverse("checkout")
        res = self.client.post(
            url,
            data={"address_id": addr.id},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(res.status_code, 409)
        self.assertEqual(res.json().get("code"), "CHECKOUT_STOCK_FAILED")

    def test_idor_prevention_order_detail(self):
        User = get_user_model()
        self.client.login(username="cust2", password="pass1234")
        order = Order.objects.create(
            user=self.customer,
            store=self.store_a,
            total_amount=15000,
            delivery_fee=1000,
        )
        url = reverse("order_detail", args=[order.id])
        res = self.client.get(url)
        self.assertEqual(res.status_code, 302)

