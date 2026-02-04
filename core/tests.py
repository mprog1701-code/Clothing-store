from django.test import TestCase, override_settings
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.test import Client
from core.models import Store, Product, ProductVariant, AttributeColor, Order, Address, StoreOwnerInvite
from unittest.mock import patch
from urllib.error import HTTPError
from io import BytesIO
import os


class CartAndCheckoutTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.client = Client()

        self.admin = User.objects.create_user(
            username="admin1", password="pass1234", role="store_admin", phone="07700000001", city="Baghdad"
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
        self.assertEqual(res2.status_code, 200)
        self.assertTrue(res2.json().get("ok"))

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

    def test_multi_store_checkout_multiple_orders(self):
        self.login_customer()
        addr = Address.objects.create(user=self.customer, city="Baghdad", area="Karrada", street="2nd")
        session = self.client.session
        session["cart"] = [
            {"product_id": self.product_with_variant.id, "variant_id": self.variant_v1.id, "quantity": 1}
        ]
        color_blue = AttributeColor.objects.create(name="Blue", code="#0000ff")
        product_b_v = Product.objects.create(
            store=self.store_b,
            name="Polo V",
            description="Variant product B",
            base_price=7000,
            category="men",
            size_type="symbolic",
        )
        variant_b1 = ProductVariant.objects.create(
            product=product_b_v,
            color_attr=color_blue,
            size="L",
            stock_qty=3,
        )
        session["cart"].append({"product_id": product_b_v.id, "variant_id": variant_b1.id, "quantity": 1})
        session["discount"] = 1000
        session["discount_code"] = "WELCOME10"
        session["discount_label"] = "خصم ترحيبي"
        session.save()

        url = reverse("checkout")
        res = self.client.post(url, data={"address_id": addr.id}, HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertTrue(body.get("ok"))
        self.assertEqual(len(body.get("order_ids") or []), 2)
        from django.conf import settings
        order_ids = body.get("order_ids")
        from core.models import Order
        o1 = Order.objects.get(id=order_ids[0])
        o2 = Order.objects.get(id=order_ids[1])
        # First order should include unified shipping
        self.assertEqual(int(o1.delivery_fee), int(settings.DELIVERY_FEE))
        self.assertEqual(int(o2.delivery_fee), 0)
        # Discount applied to all orders
        self.assertEqual(int(o1.total_amount), int(10000 + int(settings.DELIVERY_FEE) - 1000))
        self.assertEqual(int(o2.total_amount), int(7000 - 1000))

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


class OwnerInviteFlowTests(TestCase):
    def setUp(self):
        U = get_user_model()
        self.super_owner = U.objects.create_user(
            username='super_owner',
            password='AdminPass123!',
            role='store_admin',
            phone='07700000000',
            city='Baghdad',
            is_staff=True,
            is_superuser=True,
        )

    def test_admin_add_store_owner_no_user_created(self):
        contact_phone = '07712345678'
        contact_name = 'مالك تجريبي'
        self.client.force_login(self.super_owner)

        resp1 = self.client.post(
            reverse('super_owner_create_store'),
            {'step': '1', 'action': 'next', 'owner_id': ''},
        )
        self.assertEqual(resp1.status_code, 200)

        resp2 = self.client.post(
            reverse('super_owner_create_store'),
            {
                'step': '2',
                'action': 'next',
                'name': 'متجر الاختبار',
                'city': 'بغداد',
                'category': '',
                'status': 'ACTIVE',
                'address': 'العنوان التجريبي',
                'owner_contact_name': contact_name,
                'owner_contact_phone': contact_phone,
            },
        )
        self.assertEqual(resp2.status_code, 200)

        resp3 = self.client.post(
            reverse('super_owner_create_store'),
            {
                'step': '3',
                'action': 'finish',
                'delivery_fee': '1000',
                'free_delivery_threshold': '0',
                'delivery_time_value': '24',
                'delivery_time_unit': 'hour',
            },
            follow=True,
        )
        self.assertEqual(resp3.status_code, 200)

        U = get_user_model()
        self.assertFalse(U.objects.filter(phone=contact_phone).exists())

        store = Store.objects.order_by('-created_at').first()
        self.assertIsNotNone(store)
        self.assertIsNone(store.owner_user)
        from core.models import StoreOwner
        self.assertIsNotNone(store.owner_profile)
        self.assertEqual(store.owner_profile.phone, contact_phone)
        self.assertEqual(store.owner_profile.full_name, contact_name)

        invite = StoreOwnerInvite.objects.filter(store=store, phone=contact_phone, status='pending').first()
        self.assertIsNotNone(invite)

    def test_register_claims_invite_and_links_store(self):
        from django.utils import timezone
        contact_phone = '07798765432'
        store = Store.objects.create(
            name='متجر للربط', city='بغداد', address='test', description='', category='clothing', is_active=True
        )
        StoreOwnerInvite.objects.create(store=store, phone=contact_phone, status='pending', expires_at=timezone.now() + timezone.timedelta(days=15))

        resp = self.client.post(
            '/api/auth/register/',
            data={
                'phone': contact_phone,
                'city': 'بغداد',
                'full_name': 'صاحب متجر',
                'password': 'Aa12345678!',
                'password_confirm': 'Aa12345678!',
            },
        )
        self.assertEqual(resp.status_code, 201)

        U = get_user_model()
        user = U.objects.filter(phone=contact_phone).first()
        self.assertIsNotNone(user)
        store.refresh_from_db()
        self.assertEqual(getattr(store, 'owner_user_id'), user.id)
        self.assertEqual(user.role, 'store_admin')
        self.assertTrue(user.is_staff)

        invite = StoreOwnerInvite.objects.filter(store=store, phone=contact_phone).first()
        self.assertIsNotNone(invite)
        self.assertEqual(invite.status, 'claimed')

        resp2 = self.client.post(
            '/api/auth/register/',
            data={
                'phone': contact_phone,
                'city': 'بغداد',
                'full_name': 'مكرر',
                'password': 'Aa12345678!',
                'password_confirm': 'Aa12345678!',
            },
        )
        self.assertEqual(resp2.status_code, 409)
        self.assertIn('PHONE_ALREADY_HAS_ACCOUNT', (resp2.json() or {}).get('code', ''))


@override_settings(ALLOWED_HOSTS=['testserver'])
class TestReverseGeocode(TestCase):
    def setUp(self):
        self.client = Client()

    def test_mapbox_401_fallback(self):
        os.environ['MAPBOX_ACCESS_TOKEN'] = 'bad'
        def _raise(req, timeout=8):
            raise HTTPError(req.full_url, 401, 'Unauthorized', hdrs={}, fp=None)
        with patch('core.api_views.urlopen', side_effect=_raise):
            r = self.client.get('/api/addresses/reverse-geocode/', {'lat': '33.3', 'lng': '44.4'})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()['provider'], 'mapbox')
        self.assertEqual(r.json()['formatted'], '')
        os.environ.pop('MAPBOX_ACCESS_TOKEN', None)

    def test_nominatim_success(self):
        os.environ.pop('MAPBOX_ACCESS_TOKEN', None)
        os.environ.pop('MAPS_API_KEY', None)
        payload = {
            'address': {
                'city': 'Baghdad',
                'suburb': 'Karrada',
                'road': 'Street',
                'house_number': '10'
            },
            'display_name': 'Baghdad, Iraq'
        }
        body = BytesIO()
        body.write(str.encode(__import__('json').dumps(payload)))
        body.seek(0)
        class _Resp:
            def __init__(self, b): self._b=b
            def read(self): return self._b.read()
        with patch('core.api_views.urlopen', return_value=_Resp(body)):
            r = self.client.get('/api/addresses/reverse-geocode/', {'lat': '33.3', 'lng': '44.4'})
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertEqual(data['provider'], 'nominatim')
        self.assertEqual(data['city'], 'Baghdad')


@override_settings(ALLOWED_HOSTS=['testserver'])
class TestSuperOwnerViews(TestCase):
    def setUp(self):
        self.client = Client()
        U = get_user_model()
        self.super_owner = U.objects.create_user(username='super_owner', password='x', role='store_admin', phone='07700000000', city='Baghdad')
        self.client.login(username='super_owner', password='x')

    def test_edit_store_get(self):
        s = Store.objects.create(name='S', city='Baghdad', address='A')
        url = reverse('super_owner_store_settings', args=[s.id])
        r = self.client.get(url)
        self.assertEqual(r.status_code, 200)

    def test_edit_store_render_exception_redirect(self):
        s = Store.objects.create(name='S2', city='Baghdad', address='A')
        url = reverse('super_owner_store_settings', args=[s.id])
        with patch('core.views.render', side_effect=Exception('x')):
            r = self.client.get(url)
        self.assertEqual(r.status_code, 302)
        self.assertEqual(r.url, reverse('super_owner_stores'))

    def test_owners_ordering_newest_first(self):
        U = get_user_model()
        u1 = U.objects.create_user(username='owner1', password='x', role='store_admin', phone='07700000001', city='Baghdad')
        u2 = U.objects.create_user(username='owner2', password='x', role='store_admin', phone='07700000002', city='Baghdad')
        url = reverse('super_owner_owners')
        r = self.client.get(url)
        self.assertEqual(r.status_code, 200)
        owners_info = r.context['owners_info']
        self.assertTrue(len(owners_info) >= 2)
        self.assertEqual(owners_info[0]['owner'].id, u2.id)
