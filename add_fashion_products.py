#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'clothing_store.settings')
django.setup()

from core.models import Product, Store, ProductImage
from django.contrib.auth import get_user_model

User = get_user_model()

# Fashion products data
fashion_products = [
    # Women's Fashion
    {
        'store_name': 'بوتيك الأزياء النسائية',
        'category': 'women',
        'products': [
            {
                'name': 'فستان ماكسي أنيق باللون الأزرق',
                'description': 'فستان ماكسي أنيق مصنوع من قماش عالي الجودة، مثالي للمناسبات الخاصة والسهرات',
                'base_price': 450.00,
                'category': 'formal',
                'image_url': 'https://trae-api-sg.mchost.guru/api/ide/v1/text_to_image?prompt=elegant%20blue%20maxi%20dress%20for%20women%20fashion%20photography&image_size=portrait_4_3'
            },
            {
                'name': 'بلوزة نسائية بأكمام منفوخة',
                'description': 'بلوزة أنيقة بأكمام منفوخة، مصنوعة من قماش مريم وناعم، متوفرة بألوان متعددة',
                'base_price': 180.00,
                'category': 'casual',
                'image_url': 'https://trae-api-sg.mchost.guru/api/ide/v1/text_to_image?prompt=women%20blouse%20with%20puffed%20sleeves%20fashion%20photography&image_size=portrait_4_3'
            },
            {
                'name': 'تنورة جينز كلاسيكية',
                'description': 'تنورة جينز كلاسيكية بطول الركبة، مصنوعة من دنيم عالي الجودة، مثالية للإطلالات الكاجوال',
                'base_price': 220.00,
                'category': 'casual',
                'image_url': 'https://trae-api-sg.mchost.guru/api/ide/v1/text_to_image?prompt=classic%20denim%20skirt%20for%20women%20fashion%20photography&image_size=portrait_4_3'
            },
            {
                'name': 'كارديغان نسائي محبوك',
                'description': 'كارديغان نسائي محبوك بأزرار، مصنوع من صوف ناعم ودافئ، مثالي للشتاء',
                'base_price': 280.00,
                'category': 'casual',
                'image_url': 'https://trae-api-sg.mchost.guru/api/ide/v1/text_to_image?prompt=women%20knitted%20cardigan%20fashion%20photography&image_size=portrait_4_3'
            }
        ]
    },
    # Men's Fashion
    {
        'store_name': 'صالة الأزياء الرجالية',
        'category': 'men',
        'products': [
            {
                'name': 'قميص رجالي أكسفورد كلاسيكي',
                'description': 'قميص رجالي أكسفورد كلاسيكي، مصنوع من قطن عالي الجودة، مثالي للمناسبات الرسمية',
                'base_price': 320.00,
                'category': 'formal',
                'image_url': 'https://trae-api-sg.mchost.guru/api/ide/v1/text_to_image?prompt=men%20oxford%20classic%20shirt%20fashion%20photography&image_size=portrait_4_3'
            },
            {
                'name': 'بنطلون جينز رجالي سكيني',
                'description': 'بنطلون جينز رجالي سكيني، مصنوع من دنيم مرن ومريح، تصميم عصري وشبابي',
                'base_price': 250.00,
                'category': 'casual',
                'image_url': 'https://trae-api-sg.mchost.guru/api/ide/v1/text_to_image?prompt=men%20skinny%20jeans%20fashion%20photography&image_size=portrait_4_3'
            },
            {
                'name': 'بليزر رجالي أنيق باللون الرمادي',
                'description': 'بليزر رجالي أنيق باللون الرمادي، مصنوع من قماش عالي الجودة، مثالي للمناسبات الرسمية',
                'base_price': 680.00,
                'category': 'formal',
                'image_url': 'https://trae-api-sg.mchost.guru/api/ide/v1/text_to_image?prompt=elegant%20gray%20men%20blazer%20fashion%20photography&image_size=portrait_4_3'
            },
            {
                'name': 'تيشيرت بولو رجالي كلاسيكي',
                'description': 'تيشيرت بولو رجالي كلاسيكي، مصنوع من قطن ناعم ومريح، متوفر بألوان متعددة',
                'base_price': 150.00,
                'category': 'casual',
                'image_url': 'https://trae-api-sg.mchost.guru/api/ide/v1/text_to_image?prompt=men%20classic%20polo%20shirt%20fashion%20photography&image_size=portrait_4_3'
            }
        ]
    },
    # Kids Fashion
    {
        'store_name': 'عالم أزياء الأطفال',
        'category': 'kids',
        'products': [
            {
                'name': 'فستان أطفال وردي بأزهار',
                'description': 'فستان أطفال وردي بأزهار جميلة، مصنوع من قماش ناعم ومريح، مثالي للبنات الصغيرات',
                'base_price': 120.00,
                'category': 'casual',
                'image_url': 'https://trae-api-sg.mchost.guru/api/ide/v1/text_to_image?prompt=girls%20pink%20floral%20dress%20kids%20fashion%20photography&image_size=portrait_4_3'
            },
            {
                'name': 'طقم رياضي أطفال بألوان زاهية',
                'description': 'طقم رياضي أطفال بألوان زاهية، يتكون من تيشيرت وبنطلون رياضي، مصنوع من قماش مريح ومرن',
                'base_price': 95.00,
                'category': 'sports',
                'image_url': 'https://trae-api-sg.mchost.guru/api/ide/v1/text_to_image?prompt=kids%20bright%20color%20sportswear%20set%20fashion%20photography&image_size=portrait_4_3'
            },
            {
                'name': 'تيشيرت أطفال بشخصيات كرتونية',
                'description': 'تيشيرت أطفال بشخصيات كرتونية محبوبة، مصنوع من قطن ناعم ومريح، متوفر بمقاسات مختلفة',
                'base_price': 45.00,
                'category': 'casual',
                'image_url': 'https://trae-api-sg.mchost.guru/api/ide/v1/text_to_image?prompt=kids%20t-shirt%20with%20cartoon%20characters%20fashion%20photography&image_size=portrait_4_3'
            },
            {
                'name': 'جاكيت أطفال شتوي دافئ',
                'description': 'جاكيت أطفال شتوي دافئ، مصنوع من مواد عازلة ودافئة، مثالي للشتاء والأيام الباردة',
                'base_price': 180.00,
                'category': 'casual',
                'image_url': 'https://trae-api-sg.mchost.guru/api/ide/v1/text_to_image?prompt=kids%20winter%20jacket%20warm%20fashion%20photography&image_size=portrait_4_3'
            }
        ]
    },
    # Perfumes
    {
        'store_name': 'دار العطور الفاخرة',
        'category': 'perfumes',
        'products': [
            {
                'name': 'عطر فاخر للنساء برائحة الياسمين',
                'description': 'عطر فاخر للنساء برائحة الياسمين المنعشة، تركيبة عطرية مميزة تدوم طويلاً',
                'base_price': 450.00,
                'category': 'beauty',
                'image_url': 'https://trae-api-sg.mchost.guru/api/ide/v1/text_to_image?prompt=luxury%20women%20perfume%20jasmine%20scent%20elegant%20bottle%20photography&image_size=portrait_4_3'
            },
            {
                'name': 'عطر رجالي كلاسيكي برائحة الأخشاب',
                'description': 'عطر رجالي كلاسيكي برائحة الأخشاب الشرقية، تركيبة عطرية قوية وجذابة',
                'base_price': 380.00,
                'category': 'beauty',
                'image_url': 'https://trae-api-sg.mchost.guru/api/ide/v1/text_to_image?prompt=classic%20men%20perfume%20woody%20scent%20elegant%20bottle%20photography&image_size=portrait_4_3'
            },
            {
                'name': 'عطر أطفال خفيف برائحة الفواكه',
                'description': 'عطر أطفال خفيف برائحة الفواكه المنعشة، تركيبة لطيفة وآمنة للأطفال',
                'base_price': 120.00,
                'category': 'beauty',
                'image_url': 'https://trae-api-sg.mchost.guru/api/ide/v1/text_to_image?prompt=kids%20light%20perfume%20fruit%20scent%20cute%20bottle%20photography&image_size=portrait_4_3'
            }
        ]
    },
    # Cosmetics (Coming Soon)
    {
        'store_name': 'صالة كوزمتك الأنيق',
        'category': 'cosmetics',
        'products': [
            {
                'name': 'مستحضرات تجميل قريباً',
                'description': 'مجموعة متكاملة من مستحضرات التجميل عالية الجودة قريباً في متجرنا',
                'base_price': 200.00,
                'category': 'beauty',
                'image_url': 'https://trae-api-sg.mchost.guru/api/ide/v1/text_to_image?prompt=cosmetics%20collection%20coming%20soon%20elegant%20makeup%20products%20photography&image_size=portrait_4_3'
            }
        ]
    },
    # Watches (Coming Soon)
    {
        'store_name': 'صالة الساعات الفاخرة',
        'category': 'watches',
        'products': [
            {
                'name': 'ساعات فاخرة قريباً',
                'description': 'مجموعة مميزة من الساعات الفاخرة للرجال والنساء قريباً في متجرنا',
                'base_price': 1500.00,
                'category': 'accessories',
                'image_url': 'https://trae-api-sg.mchost.guru/api/ide/v1/text_to_image?prompt=luxury%20watches%20collection%20coming%20soon%20elegant%20timepieces%20photography&image_size=portrait_4_3'
            }
        ]
    }
]

def create_fashion_products():
    created_count = 0
    
    for store_data in fashion_products:
        # Get or create store
        try:
            store = Store.objects.get(name=store_data['store_name'])
        except Store.DoesNotExist:
            print(f"Store '{store_data['store_name']}' not found. Skipping...")
            continue
        
        # Create products for this store
        for product_data in store_data['products']:
            try:
                # Check if product already exists
                product, created = Product.objects.get_or_create(
                    store=store,
                    name=product_data['name'],
                    defaults={
                        'description': product_data['description'],
                        'base_price': product_data['base_price'],
                        'category': product_data['category'],
                        'is_active': True
                    }
                )
                
                if created:
                    # Create product image
                    ProductImage.objects.create(
                        product=product,
                        image_url=product_data['image_url'],
                        is_main=True
                    )
                    created_count += 1
                    print(f"Created product: {product.name}")
                else:
                    print(f"Product already exists: {product.name}")
                    
            except Exception as e:
                print(f"Error creating product '{product_data['name']}': {e}")
    
    print(f"\nTotal products created: {created_count}")

if __name__ == "__main__":
    create_fashion_products()