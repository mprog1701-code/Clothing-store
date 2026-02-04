from django.test import TestCase, Client, override_settings
from django.urls import reverse
from core.models import User, Store
from unittest.mock import patch

@override_settings(ALLOWED_HOSTS=['testserver'])
class TestSuperOwnerViews(TestCase):
    def setUp(self):
        self.client = Client()
        self.super_owner = User.objects.create_user(username='super_owner', password='x', role='store_admin', phone='07700000000', city='Baghdad')
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
        u1 = User.objects.create_user(username='owner1', password='x', role='store_admin', phone='07700000001', city='Baghdad')
        u2 = User.objects.create_user(username='owner2', password='x', role='store_admin', phone='07700000002', city='Baghdad')
        url = reverse('super_owner_owners')
        r = self.client.get(url)
        self.assertEqual(r.status_code, 200)
        owners_info = r.context['owners_info']
        self.assertTrue(len(owners_info) >= 2)
        self.assertEqual(owners_info[0]['owner'].id, u2.id)
