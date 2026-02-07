from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from core.models import Store, Product, ProductVariant, AttributeColor, ProductImage


class ProductDetailRedesignTests(TestCase):
    def setUp(self):
        U = get_user_model()
        self.user = U.objects.create_user(username='u_pd', password='pass1234', role='customer', phone='07710000000', city='Baghdad')
        self.store1 = Store.objects.create(owner=self.user, name='S1', city='Baghdad', address='A1')
        self.store2 = Store.objects.create(owner=self.user, name='S2', city='Baghdad', address='A2')
        self.prod = Product.objects.create(store=self.store1, name='Jacket', description='Warm jacket', base_price=20000, category='men', size_type='symbolic')
        red = AttributeColor.objects.create(name='Red', code='#ff0000')
        blue = AttributeColor.objects.create(name='Blue', code='#0000ff')
        ProductVariant.objects.create(product=self.prod, color_attr=red, size='M', stock_qty=5)
        ProductVariant.objects.create(product=self.prod, color_attr=blue, size='L', stock_qty=0)
        ProductImage.objects.create(product=self.prod, color_attr=red, image_url='https://placehold.co/600x600?text=Red1', is_main=True, order=1)
        ProductImage.objects.create(product=self.prod, color_attr=red, image_url='https://placehold.co/600x600?text=Red2', order=2)
        ProductImage.objects.create(product=self.prod, color_attr=blue, image_url='https://placehold.co/600x600?text=Blue1', order=1)
        ProductImage.objects.create(product=self.prod, image_url='https://placehold.co/600x600?text=Default', order=99)
        for i in range(12):
            p = Product.objects.create(store=self.store2, name=f'Similar {i}', description='x', base_price=10000+i, category='men', size_type='none', status='ACTIVE')
            ProductImage.objects.create(product=p, image_url='https://placehold.co/300x300?text=Sim', order=1)

    def test_product_detail_queries_and_render(self):
        url = reverse('product_detail', args=[self.prod.id])
        with self.assertNumQueries(14):
            res = self.client.get(url)
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'id="pdMain"')
        self.assertContains(res, 'id="pdThumbs"')
        self.assertContains(res, 'id="images-data"')
        self.assertContains(res, 'id="colors-data"')

    def test_product_detail_updates_after_new_image_with_nocache(self):
        ProductImage.objects.create(product=self.prod, color_attr=None, image_url='https://placehold.co/600x600?text=NewDefault', order=0)
        url = reverse('product_detail', args=[self.prod.id]) + '?nocache=1'
        res = self.client.get(url)
        self.assertEqual(res.status_code, 200)
        self.assertIn('default_main_image_url', res.context)
        self.assertTrue(res.context['default_main_image_url'])
