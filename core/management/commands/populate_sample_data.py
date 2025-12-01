from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from core.models import Store, Product, ProductImage, ProductVariant
import random
from decimal import Decimal

User = get_user_model()

class Command(BaseCommand):
    help = 'Populate database with sample stores, products, and images'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS('Starting to populate sample data...'))
        
        # Create sample users
        self.create_sample_users()
        
        # Create sample stores
        self.create_sample_stores()
        
        # Create sample products
        self.create_sample_products()
        
        self.stdout.write(self.style.SUCCESS('Successfully populated sample data!'))

    def create_sample_users(self):
        """Create sample users with different roles"""
        users_data = [
            {'username': 'admin_store', 'email': 'admin@example.com', 'role': 'admin', 'first_name': 'أحمد', 'last_name': 'الإداري', 'phone': '0500000001'},
            {'username': 'fashion_store', 'email': 'fashion@example.com', 'role': 'store_owner', 'first_name': 'فاطمة', 'last_name': 'أبوالعز', 'phone': '0500000002'},
            {'username': 'sport_store', 'email': 'sport@example.com', 'role': 'store_owner', 'first_name': 'محمد', 'last_name': 'الرياضي', 'phone': '0500000003'},
            {'username': 'luxury_store', 'email': 'luxury@example.com', 'role': 'store_owner', 'first_name': 'سارة', 'last_name': 'الفاخرة', 'phone': '0500000004'},
            {'username': 'customer1', 'email': 'customer1@example.com', 'role': 'customer', 'first_name': 'عبدالله', 'last_name': 'الزبون', 'phone': '0500000005'},
        ]
        
        for user_data in users_data:
            user, created = User.objects.get_or_create(
                username=user_data['username'],
                defaults=user_data
            )
            if created:
                user.set_password('123456')
                user.save()
                self.stdout.write(f'Created user: {user.username}')

    def create_sample_stores(self):
        """Create sample stores with different specializations"""
        stores_data = [
            {
                'owner_username': 'fashion_store',
                'name': 'بوتيك الأزياء الحديثة',
                'city': 'الرياض',
                'address': 'شارع العليا، حي الملك فهد',
                'description': 'متجر متخصص في أحدث صيحات الموضة والأزياء العصرية للنساء والرجال. نقدم تشكيلة واسعة من الملابس ذات الجودة العالية بأسعار منافسة.',
                'is_active': True
            },
            {
                'owner_username': 'sport_store',
                'name': 'رياضة برو سبورت',
                'city': 'جدة',
                'address': 'شارع التحلية، حي الشاطئ',
                'description': 'كل ما تحتاجه من ملابس ومعدات رياضية عالية الجودة. نحمل أفضل الماركات العالمية ونوفر خدمة ممتازة لعملائنا.',
                'is_active': True
            },
            {
                'owner_username': 'luxury_store',
                'name': 'الدار للأزياء الفاخرة',
                'city': 'الدمام',
                'address': 'شارع الأمير محمد بن فهد، حي الفيصلية',
                'description': 'متجر متخصص في الأزياء الفاخرة والماركات العالمية. نقدم تجربة تسوق فاخرة مع منتجات نادرة وخدمة شخصية مميزة.',
                'is_active': True
            },
            {
                'owner_username': 'fashion_store',
                'name': 'أساسيات الموضة',
                'city': 'مكة',
                'address': 'شارع إبراهيم الخليل، حي الزاهر',
                'description': 'متجر يوفر أساسيات الموضة اليومية بأسعار مناسبة. تشكيلة متنوعة من الملابس الكاجوال والرسمية.',
                'is_active': True
            }
        ]
        
        for store_data in stores_data:
            try:
                owner = User.objects.get(username=store_data['owner_username'])
                store, created = Store.objects.get_or_create(
                    name=store_data['name'],
                    defaults={
                        'owner': owner,
                        'city': store_data['city'],
                        'address': store_data['address'],
                        'description': store_data['description'],
                        'is_active': store_data['is_active']
                    }
                )
                if created:
                    self.stdout.write(f'Created store: {store.name}')
            except User.DoesNotExist:
                self.stdout.write(f'User {store_data["owner_username"]} not found')

    def create_sample_products(self):
        """Create sample products with images and variants"""
        products_data = [
            # Fashion Store Products
            {
                'store_name': 'بوتيك الأزياء الحديثة',
                'category': 'women',
                'name': 'فستان سهرة أسود أنيق',
                'description': 'فستان سهرة أسود بتصميم كلاسيكي راقي، مصنوع من أجود أنواع الأقمشة مع تطريزات دقيقة. مثالي للمناسبات الرسمية والسهرات الخاصة.',
                'base_price': Decimal('299.99'),
                'images': [
                    'https://trae-api-sg.mchost.guru/api/ide/v1/text_to_image?prompt=Black+elegant+evening+dress+with+delicate+embroidery%2C+luxury+fabric%2C+classic+design%2C+formal+occasion+wear&image_size=portrait_4_3',
                    'https://trae-api-sg.mchost.guru/api/ide/v1/text_to_image?prompt=Close-up+view+of+black+evening+dress+showing+embroidery+details%2C+high+quality+fabric+texture&image_size=portrait_4_3'
                ],
                'variants': [
                    {'size': 'S', 'color': 'أسود', 'stock': 5, 'price': Decimal('299.99')},
                    {'size': 'M', 'color': 'أسود', 'stock': 8, 'price': Decimal('299.99')},
                    {'size': 'L', 'color': 'أسود', 'stock': 3, 'price': Decimal('299.99')},
                ]
            },
            {
                'store_name': 'بوتيك الأزياء الحديثة',
                'category': 'men',
                'name': 'بدلة رجالية رمادية أنيقة',
                'description': 'بدلة رجالية رمادية بتصميم عصري، مصنوعة من أجود أقمشة الصوف الإيطالي. مثالية للاجتماعات الرسمية والمناسبات الخاصة.',
                'base_price': Decimal('599.99'),
                'images': [
                    'https://trae-api-sg.mchost.guru/api/ide/v1/text_to_image?prompt=Gray+elegant+men+suit%2C+Italian+wool+fabric%2C+modern+design%2C+formal+business+attire&image_size=portrait_4_3',
                    'https://trae-api-sg.mchost.guru/api/ide/v1/text_to_image?prompt=Close-up+view+of+gray+suit+jacket+showing+fabric+texture+and+tailoring+details&image_size=portrait_4_3'
                ],
                'variants': [
                    {'size': 'M', 'color': 'رمادي', 'stock': 4, 'price': Decimal('599.99')},
                    {'size': 'L', 'color': 'رمادي', 'stock': 6, 'price': Decimal('599.99')},
                    {'size': 'XL', 'color': 'رمادي', 'stock': 2, 'price': Decimal('599.99')},
                ]
            },
            # Sport Store Products
            {
                'store_name': 'رياضة برو سبورت',
                'category': 'sports',
                'name': 'طقم رياضي احترافي',
                'description': 'طقم رياضي احترافي يتضمن تيشيرت وبنطال رياضي، مصنوع من أحدث الأقمشة الماصة للعرق. مثالي للتمارين الرياضية والأنشطة البدنية.',
                'base_price': Decimal('149.99'),
                'images': [
                    'https://trae-api-sg.mchost.guru/api/ide/v1/text_to_image?prompt=Professional+sports+outfit%2C+moisture+wicking+fabric%2C+athletic+wear%2C+modern+sportswear+design&image_size=portrait_4_3',
                    'https://trae-api-sg.mchost.guru/api/ide/v1/text_to_image?prompt=Sports+outfit+details+showing+fabric+texture+and+athletic+design&image_size=portrait_4_3'
                ],
                'variants': [
                    {'size': 'S', 'color': 'أزرق', 'stock': 10, 'price': Decimal('149.99')},
                    {'size': 'M', 'color': 'أزرق', 'stock': 15, 'price': Decimal('149.99')},
                    {'size': 'L', 'color': 'أزرق', 'stock': 12, 'price': Decimal('149.99')},
                    {'size': 'XL', 'color': 'أزرق', 'stock': 8, 'price': Decimal('149.99')},
                ]
            },
            # Luxury Store Products
            {
                'store_name': 'الدار للأزياء الفاخرة',
                'category': 'women',
                'name': 'فستان سهرة فاخر باللون الذهبي',
                'description': 'فستان سهرة فاخر باللون الذهبي اللامع، مصنوع من الحرير الطبيعي مع تطريزات يدوية بالخرز والكريستال. قطعة فنية نادرة للمناسبات الخاصة جداً.',
                'base_price': Decimal('1299.99'),
                'images': [
                    'https://trae-api-sg.mchost.guru/api/ide/v1/text_to_image?prompt=Luxury+golden+evening+dress%2C+natural+silk+fabric%2C+hand+embroidery+with+beads+and+crystals%2C+exclusive+design&image_size=portrait_4_3',
                    'https://trae-api-sg.mchost.guru/api/ide/v1/text_to_image?prompt=Close-up+of+luxury+golden+dress+showing+hand+embroidery+details+and+crystal+work&image_size=portrait_4_3'
                ],
                'variants': [
                    {'size': 'S', 'color': 'ذهبي', 'stock': 1, 'price': Decimal('1299.99')},
                    {'size': 'M', 'color': 'ذهبي', 'stock': 2, 'price': Decimal('1299.99')},
                ]
            },
            # Basics Store Products
            {
                'store_name': 'أساسيات الموضة',
                'category': 'men',
                'name': 'تيشيرت قطن أساسي',
                'description': 'تيشيرت قطن أساسي عالي الجودة، مصنوع من 100% قطن مصري. مريح وعملي للاستخدام اليومي، متوفر بعدة ألوان.',
                'base_price': Decimal('49.99'),
                'images': [
                    'https://trae-api-sg.mchost.guru/api/ide/v1/text_to_image?prompt=Basic+cotton+t-shirt%2C+100%25+Egyptian+cotton%2C+comfortable+daily+wear%2C+multiple+colors&image_size=portrait_4_3',
                    'https://trae-api-sg.mchost.guru/api/ide/v1/text_to_image?prompt=Cotton+t-shirt+fabric+texture+showing+quality+and+comfort&image_size=portrait_4_3'
                ],
                'variants': [
                    {'size': 'S', 'color': 'أبيض', 'stock': 20, 'price': Decimal('49.99')},
                    {'size': 'M', 'color': 'أبيض', 'stock': 25, 'price': Decimal('49.99')},
                    {'size': 'L', 'color': 'أبيض', 'stock': 30, 'price': Decimal('49.99')},
                    {'size': 'XL', 'color': 'أبيض', 'stock': 15, 'price': Decimal('49.99')},
                    {'size': 'M', 'color': 'أسود', 'stock': 20, 'price': Decimal('49.99')},
                    {'size': 'L', 'color': 'أسود', 'stock': 25, 'price': Decimal('49.99')},
                ]
            },
        ]
        
        for product_data in products_data:
            try:
                store = Store.objects.get(name=product_data['store_name'])
                product, created = Product.objects.get_or_create(
                    name=product_data['name'],
                    store=store,
                    defaults={
                        'category': product_data['category'],
                        'description': product_data['description'],
                        'base_price': product_data['base_price']
                    }
                )
                
                if created:
                    # Create product images
                    for i, image_url in enumerate(product_data['images']):
                        ProductImage.objects.create(
                            product=product,
                            image_url=image_url,
                            is_main=(i == 0)
                        )
                    
                    # Create product variants
                    for variant_data in product_data['variants']:
                        ProductVariant.objects.create(
                            product=product,
                            size=variant_data['size'],
                            color=variant_data['color'],
                            stock_qty=variant_data['stock'],
                            price_override=variant_data['price']
                        )
                    
                    self.stdout.write(f'Created product: {product.name} with {len(product_data["images"])} images and {len(product_data["variants"])} variants')
            except Store.DoesNotExist:
                self.stdout.write(f'Store {product_data["store_name"]} not found')