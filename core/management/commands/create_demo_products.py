from django.core.management.base import BaseCommand
from core.models import Product, Store, ProductVariant, ProductColor, ProductImage
import random
import urllib.parse

class Command(BaseCommand):
    help = 'Creates 30 demo products (10 Women, 10 Kids, 10 Men) with variants'

    def handle(self, *args, **options):
        self.stdout.write('Starting demo products creation...')

        # 1. Get or Create Store
        store, _ = Store.objects.get_or_create(
            name='متجر الموضة التجريبي',
            defaults={
                'city': 'بغداد',
                'address': 'المنصور',
                'description': 'متجر تجريبي يحتوي على أحدث صيحات الموضة',
                'category': 'clothing'
            }
        )
        self.stdout.write(f'Using store: {store.name}')

        # Common Colors
        colors_data = [
            {'name': 'أحمر', 'code': '#FF0000'},
            {'name': 'أزرق', 'code': '#0000FF'},
            {'name': 'أسود', 'code': '#000000'},
            {'name': 'أبيض', 'code': '#FFFFFF'},
            {'name': 'أخضر', 'code': '#008000'},
        ]

        # Common Sizes (Symbolic)
        sizes = ['S', 'M', 'L', 'XL']

        # 2. Women's Products Data (10 items)
        women_products = [
            ("فستان صيفي مزهر", "فستان صيفي خفيف بطبعة زهور أنيقة", 45000),
            ("بلوزة حريرية", "بلوزة ناعمة من الحرير الصناعي للمناسبات", 35000),
            ("بنطلون جينز سكيني", "بنطلون جينز ضيق عالي الخصر", 50000),
            ("تنورة ميدي", "تنورة متوسطة الطول بتصميم كلاسيكي", 40000),
            ("جاكيت رسمي", "جاكيت بليزر رسمي للعمل والمناسبات", 75000),
            ("عباية سوداء مطرزة", "عباية خليجية فاخرة مع تطريز يدوي", 120000),
            ("قميص قطني أبيض", "قميص أساسي أبيض مريح للارتداء اليومي", 25000),
            ("فستان سهرة طويل", "فستان سهرة راقي للحفلات", 150000),
            ("بيجامة قطنية", "طقم بيجامة مريح للنوم من القطن الصافي", 30000),
            ("شال شتوي صوف", "شال عريض ودافئ لفصل الشتاء", 15000),
        ]

        # 3. Kids' Products Data (10 items)
        kids_products = [
            ("طقم ولادي قطعتين", "تيشيرت وشورت صيفي للأولاد", 25000),
            ("فستان بنات منفوش", "فستان حفلات للبنات الصغار", 45000),
            ("بدلة رياضة أطفال", "بدلة تدريب مريحة للجنسين", 35000),
            ("تيشيرت أبطال خارقين", "تيشيرت قطن بطبعة شخصيات كرتونية", 15000),
            ("بنطلون جينز أطفال", "جينز متين ومريح للحركة", 30000),
            ("جاكيت شتوي مبطن", "جاكيت مقاوم للماء ومبطن بالفرو", 60000),
            ("أفرول جينز", "سالوبيت جينز عملي للأطفال", 40000),
            ("قميص مدرسي", "قميص أبيض للزي المدرسي", 18000),
            ("بيجامة أطفال ملونة", "بيجامة برسومات لطيفة", 20000),
            ("طقم مواليد جديد", "طقم كامل للمواليد قطن 100%", 50000),
        ]

        # 4. Men's Products Data (10 items) - To complete 30
        men_products = [
            ("قميص رسمي أزرق", "قميص كلاسيكي للعمل والمناسبات", 35000),
            ("بنطلون جينز كحلي", "جينز قصة مستقيمة لون كحلي غامق", 45000),
            ("تيشيرت بولو", "تيشيرت بولو قطن 100% متوفر بعدة ألوان", 20000),
            ("جاكيت جلد", "جاكيت جلد صناعي عالي الجودة", 85000),
            ("بدلة رسمية سوداء", "بدلة كاملة (جاكيت وبنطلون) لون أسود", 150000),
            ("شورت رياضي", "شورت مريح للرياضة والجيم", 15000),
            ("كنزة صوفية", "بلوفر صوف خفيف لفصل الخريف", 30000),
            ("بنطلون قماش بيج", "بنطلون تشينو بيج كاجوال", 35000),
            ("معطف طويل", "معطف شتوي طويل وأنيق", 120000),
            ("قميص كاروهات", "قميص كاجوال كاروهات مريح", 25000),
        ]

        def create_category_products(product_list, category_code, size_type='symbolic'):
            for name, desc, price in product_list:
                # Create Product
                product, created = Product.objects.get_or_create(
                    store=store,
                    name=name,
                    defaults={
                        'description': desc,
                        'base_price': price,
                        'category': category_code,
                        'size_type': size_type,
                        'status': 'ACTIVE',
                        'is_active': True,
                        'fit_type': 'standard'
                    }
                )
                
                if not created:
                    self.stdout.write(f'Skipping existing product: {name}')
                    continue

                self.stdout.write(f'Creating product: {name}')

                # Add Main Image
                encoded_name = urllib.parse.quote(name)
                ProductImage.objects.create(
                    product=product,
                    image_url=f'https://placehold.co/600x800/png?text={encoded_name}',
                    is_main=True
                )

                # Select 3 random colors for this product
                product_colors = random.sample(colors_data, 3)
                
                created_colors = []
                for col in product_colors:
                    p_color, _ = ProductColor.objects.get_or_create(
                        product=product,
                        name=col['name'],
                        defaults={'code': col['code']}
                    )
                    created_colors.append(p_color)

                # Create Variants (3 colors * 4 sizes)
                for p_color in created_colors:
                    for size in sizes:
                        ProductVariant.objects.get_or_create(
                            product=product,
                            color_obj=p_color,
                            size=size,
                            defaults={
                                'stock_qty': random.randint(5, 50),
                                'price_override': None, # Use base price
                                'is_enabled': True
                            }
                        )

        # Execute creation
        self.stdout.write('Creating Women Products...')
        create_category_products(women_products, 'women')

        self.stdout.write('Creating Kids Products...')
        create_category_products(kids_products, 'kids')

        self.stdout.write('Creating Men Products...')
        create_category_products(men_products, 'men')

        self.stdout.write(self.style.SUCCESS('Successfully created 30 demo products with variants.'))
