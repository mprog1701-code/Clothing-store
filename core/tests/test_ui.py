from django.test import TestCase, Client
from django.contrib.auth import get_user_model

class UITest(TestCase):
    def setUp(self):
        self.client = Client()

    def test_base_has_rtl_and_contrast_rules(self):
        resp = self.client.get('/')
        self.assertEqual(resp.status_code, 200)
        html = resp.content.decode('utf-8')
        self.assertIn('dir="rtl"', html)
        self.assertIn('input, textarea, select { direction: rtl', html)
        self.assertIn('table th, table td { text-align: right', html)
        self.assertIn('color: #111 !important;', html)

    def test_alert_autohide_skips_danger(self):
        resp = self.client.get('/')
        html = resp.content.decode('utf-8')
        self.assertIn(".alert:not(.alert-danger)", html)

    def test_owners_page_has_search_label(self):
        U = get_user_model()
        user = U.objects.create_user(username='super_owner', password='x', role='admin')
        self.client.login(username='super_owner', password='x')
        resp = self.client.get('/dashboard/super-owner/owners/')
        self.assertEqual(resp.status_code, 200)
        html = resp.content.decode('utf-8')
        self.assertIn('label class="form-label"', html)
        self.assertIn('id="owners_search"', html)
