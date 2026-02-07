from django.test import TestCase, Client, override_settings
from django.urls import reverse
from core.models import User, Store, Product, AttributeColor, ProductVariant, ProductImage
from django.core.files.uploadedfile import SimpleUploadedFile
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

    def test_add_global_color_hex_validation(self):
        s = Store.objects.create(name='S', city='Baghdad', address='A')
        p = Product.objects.create(store=s, name='P', description='D', base_price=1000, category='men', size_type='none', status='DRAFT')
        url = reverse('super_owner_add_product')
        r1 = self.client.post(url, {
            'action': 'add_global_color',
            'pid': str(p.id),
            'color_name': '',
            'color_code': 'abc'
        })
        self.assertEqual(r1.status_code, 302)
        self.assertTrue(AttributeColor.objects.filter(code='#AABBCC').exists())
        r2 = self.client.post(url, {
            'action': 'add_global_color',
            'pid': str(p.id),
            'color_name': '',
            'color_code': 'ZZZZZZ'
        })
        self.assertEqual(r2.status_code, 302)
        self.assertFalse(AttributeColor.objects.filter(code='#ZZZZZZ').exists())

    def test_upload_images_default_color_assignment(self):
        s = Store.objects.create(name='S3', city='Baghdad', address='A')
        p = Product.objects.create(store=s, name='P3', description='D', base_price=1000, category='men', size_type='symbolic', status='DRAFT')
        red = AttributeColor.objects.create(name='Red', code='#FF0000')
        blue = AttributeColor.objects.create(name='Blue', code='#0000FF')
        ProductVariant.objects.create(product=p, color_attr=red, size_attr=None, size='M', stock_qty=0, is_enabled=False)
        ProductVariant.objects.create(product=p, color_attr=blue, size_attr=None, size='L', stock_qty=0, is_enabled=False)
        url = reverse('super_owner_add_product')
        file_content = b'unique-image-bytes-1'
        up = SimpleUploadedFile('img1.jpg', file_content, content_type='image/jpeg')
        r = self.client.post(url, {
            'action': 'upload_images',
            'pid': str(p.id),
            'images': up,
        })
        self.assertEqual(r.status_code, 302)
        imgs = list(ProductImage.objects.filter(product=p))
        self.assertTrue(len(imgs) >= 1)
        self.assertIsNotNone(imgs[0].color_attr)
        self.assertEqual(imgs[0].color_attr.name, 'Red')
        self.assertTrue(imgs[0].image_hash)

    def test_upload_images_multiple_formats_and_product_detail_visibility(self):
        s = Store.objects.create(name='S4', city='Baghdad', address='A')
        p = Product.objects.create(store=s, name='P4', description='D', base_price=1000, category='men', size_type='none', status='ACTIVE', is_active=True)
        url = reverse('super_owner_add_product')
        up_jpg = SimpleUploadedFile('imgA.jpg', b'bytes-jpg', content_type='image/jpeg')
        up_png = SimpleUploadedFile('imgB.png', b'bytes-png', content_type='image/png')
        up_webp = SimpleUploadedFile('imgC.webp', b'bytes-webp', content_type='image/webp')
        r = self.client.post(url, {
            'action': 'upload_images',
            'pid': str(p.id),
            'images': [up_jpg, up_png, up_webp],
        })
        self.assertEqual(r.status_code, 302)
        imgs = list(ProductImage.objects.filter(product=p))
        self.assertTrue(len(imgs) >= 3)
        # Bad request when no files provided
        r2 = self.client.post(url, {
            'action': 'upload_images',
            'pid': str(p.id),
        })
        self.assertEqual(r2.status_code, 400)
        # Now load product detail without cache
        pd_url = reverse('product_detail', args=[p.id]) + '?nocache=1'
        res = self.client.get(pd_url)
        self.assertEqual(res.status_code, 200)
        self.assertIn('default_main_image_url', res.context)
