from django.test import TestCase, override_settings
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from core.models import Store, Product, ProductImage


@override_settings(ALLOWED_HOSTS=['testserver'])
class TestApiProductsImages(TestCase):
    def setUp(self):
        U = get_user_model()
        self.user = U.objects.create_user(username='api_u', password='x', role='customer', phone='07720000000', city='Baghdad')
        self.store = Store.objects.create(owner=self.user, name='SAPI', city='Baghdad', address='A')
        self.prod = Product.objects.create(store=self.store, name='AP', description='D', base_price=1000, category='men', size_type='none', status='ACTIVE', is_active=True)

    def test_product_api_returns_image_url_from_image_url_field(self):
        ProductImage.objects.create(product=self.prod, image_url='https://placehold.co/400x400?text=API', is_main=True, order=0)
        url = reverse('products-detail', args=[self.prod.id])
        r = self.client.get('/api' + url.replace('/dashboard', '')) if not url.startswith('/api/') else self.client.get(url)
        if r.status_code == 404:
            url2 = f"/api/products/{self.prod.id}/"
            r = self.client.get(url2)
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertIn('images', data)
        self.assertTrue(len(data['images']) >= 1)
        self.assertIn('url', data['images'][0])
        self.assertTrue(data['images'][0]['url'].startswith('http'))

    def test_product_api_returns_image_url_from_image_file(self):
        file_content = b'1234567890jpeg'
        up = SimpleUploadedFile('api_img.jpg', file_content, content_type='image/jpeg')
        ProductImage.objects.create(product=self.prod, image=up, is_main=True, order=0)
        url = f"/api/products/{self.prod.id}/"
        r = self.client.get(url)
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertIn('images', data)
        self.assertTrue(len(data['images']) >= 1)
        self.assertIn('url', data['images'][0])
        self.assertTrue(isinstance(data['images'][0]['url'], str))
