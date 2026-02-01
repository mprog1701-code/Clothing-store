from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from core.models import Store


class UserManagementTests(TestCase):
    def setUp(self):
        U = get_user_model()
        self.client = Client()
        self.super_owner = U.objects.create_user(
            username='super_owner', password='x', role='admin', phone='07700000000', city='Baghdad'
        )
        self.client.login(username='super_owner', password='x')

    def test_demote_owner_and_detach_stores_no_logout(self):
        U = get_user_model()
        owner = U.objects.create_user(
            username='owner_a', password='pass123', role='admin', phone='07700000111', city='Baghdad'
        )
        s1 = Store.objects.create(owner=owner, name='Store A', city='Baghdad', address='addr')
        resp = self.client.post(reverse('super_owner_owners'), {
            'action': 'bulk_delete_selected',
            'selected_ids': [str(owner.id)],
        })
        self.assertEqual(resp.status_code, 302)
        owner.refresh_from_db()
        self.assertEqual(owner.role, 'customer')
        s1.refresh_from_db()
        self.assertIsNone(s1.owner)
        resp2 = self.client.get(reverse('super_owner_owners'))
        self.assertEqual(resp2.status_code, 200)

    def test_allow_duplicate_phone_except_reserved(self):
        U = get_user_model()
        o1 = U.objects.create_user(
            username='owner_b', password='pass123', role='admin', phone='07700000222', city='Baghdad'
        )
        resp = self.client.post(reverse('super_owner_create_owner_json'), {
            'full_name': 'Owner C',
            'phone': '07700000222',
            'email': 'c@example.com',
        })
        self.assertEqual(resp.status_code, 200)
        resp_fail = self.client.post(reverse('super_owner_create_owner_json'), {
            'full_name': 'Another',
            'phone': '07700000000',
            'email': 'a@example.com',
        })
        self.assertEqual(resp_fail.status_code, 409)
        o2 = U.objects.create_user(
            username='owner_d', password='pass123', role='admin', phone='07700000333', city='Baghdad'
        )
        resp2 = self.client.post(reverse('super_owner_owners'), {
            'action': 'update_phone',
            'owner_id': str(o2.id),
            'phone': '07700000000',
        })
        self.assertEqual(resp2.status_code, 302)
        o2.refresh_from_db()
        self.assertEqual(o2.phone, '07700000333')

