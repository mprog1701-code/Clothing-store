from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.conf import settings
from django.db import transaction
from .models import User, Store, Product, ProductImage, ProductVariant, Address, Order, OrderItem, CartItem


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'phone', 'role', 'city', 'first_name', 'last_name']
        read_only_fields = ['id', 'role']


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)
    full_name = serializers.CharField(write_only=True)
    email = serializers.EmailField(required=True)
    
    class Meta:
        model = User
        fields = ['phone', 'email', 'password', 'password_confirm', 'city', 'full_name']
    
    def validate_phone(self, value):
        # Validate Iraqi mobile number format (starts with 07 and 11 digits)
        if not value.startswith('07') or len(value) != 11:
            raise serializers.ValidationError("رقم الجوال يجب أن يبدأ بـ 07 ويكون 11 رقماً")
        
        # Check if phone already exists
        if User.objects.filter(phone=value).exists():
            raise serializers.ValidationError("رقم الجوال مسجل بالفعل")
        
        return value
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("كلمات المرور غير متطابقة")
        return attrs

    def validate_email(self, value):
        v = (value or '').strip().lower()
        if not v:
            raise serializers.ValidationError("يرجى إدخال البريد الإلكتروني")
        if User.objects.filter(email__iexact=v).exists():
            raise serializers.ValidationError("البريد الإلكتروني مسجل بالفعل")
        return v
    
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        full_name = validated_data.pop('full_name')
        
        # Split full name into first and last name
        name_parts = full_name.strip().split(' ', 1)
        first_name = name_parts[0]
        last_name = name_parts[1] if len(name_parts) > 1 else ''
        
        # Generate username from phone number
        username = f"user_{validated_data['phone'][-6:]}"
        
        # Ensure unique username
        counter = 1
        original_username = username
        while User.objects.filter(username=username).exists():
            username = f"{original_username}_{counter}"
            counter += 1
        
        user = User.objects.create_user(
            username=username,
            email=validated_data['email'],
            password=validated_data['password'],
            phone=validated_data['phone'],
            city=validated_data['city'],
            first_name=first_name,
            last_name=last_name,
            role='customer',
            is_active=False,
        )
        return user


class StoreSerializer(serializers.ModelSerializer):
    owner = UserSerializer(read_only=True)
    
    class Meta:
        model = Store
        fields = ['id', 'owner', 'name', 'city', 'address', 'description', 'is_active', 'created_at']
        read_only_fields = ['id', 'owner', 'created_at']


class ProductImageSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField()
    image_url = serializers.CharField(read_only=True)
    color_name = serializers.SerializerMethodField()
    color_key = serializers.SerializerMethodField()
    color_obj_id = serializers.SerializerMethodField()
    color_attr_id = serializers.SerializerMethodField()
    color_id = serializers.SerializerMethodField()
    variant_id = serializers.SerializerMethodField()
    order = serializers.IntegerField(read_only=True)

    class Meta:
        model = ProductImage
        fields = ['id', 'image', 'image_url', 'is_main', 'url', 'color_name', 'color_key', 'color_obj_id', 'color_attr_id', 'color_id', 'variant_id', 'order']

    def get_url(self, obj):
        try:
            u = obj.get_image_url() or ''
            s = str(u).strip()
            if s and not (s.startswith('http://') or s.startswith('https://')):
                try:
                    req = self.context.get('request')
                    if req:
                        s = req.build_absolute_uri(s)
                except Exception:
                    pass
            return s
        except Exception:
            return ''
    
    def get_color_name(self, obj):
        try:
            if obj.color_attr:
                return obj.color_attr.name
            if obj.color:
                return obj.color.name
        except Exception:
            pass
        return ''
    
    def get_color_key(self, obj):
        try:
            if obj.color_attr_id:
                return f"A{obj.color_attr_id}"
            if obj.color_id:
                return str(obj.color_id)
        except Exception:
            pass
        return ''
    
    def get_color_obj_id(self, obj):
        try:
            return int(obj.color_id) if obj.color_id else None
        except Exception:
            return None
    
    def get_color_attr_id(self, obj):
        try:
            return int(obj.color_attr_id) if obj.color_attr_id else None
        except Exception:
            return None
    
    def get_color_id(self, obj):
        try:
            if obj.color_id:
                return int(obj.color_id)
            if obj.color_attr_id:
                return int(obj.color_attr_id)
        except Exception:
            pass
        return None
    
    def get_variant_id(self, obj):
        try:
            return int(obj.variant_id) if obj.variant_id else None
        except Exception:
            return None


class ProductVariantSerializer(serializers.ModelSerializer):
    price = serializers.ReadOnlyField()
    color_name = serializers.SerializerMethodField()
    color_hex = serializers.SerializerMethodField()
    images = ProductImageSerializer(many=True, read_only=True)
    sizes = serializers.SerializerMethodField()
    color_key = serializers.SerializerMethodField()
    color_obj_id = serializers.SerializerMethodField()
    color_attr_id = serializers.SerializerMethodField()
    
    class Meta:
        model = ProductVariant
        fields = ['id', 'size', 'color', 'stock_qty', 'price_override', 'price', 'color_name', 'color_hex', 'images', 'sizes', 'color_key', 'color_obj_id', 'color_attr_id']

    def get_color_name(self, obj):
        try:
            if obj.color_attr:
                return obj.color_attr.name
            if obj.color_obj:
                return obj.color_obj.name
        except Exception:
            pass
        return ''

    def get_color_hex(self, obj):
        try:
            if obj.color_attr and getattr(obj.color_attr, 'code', None):
                return obj.color_attr.code
            if obj.color_obj and getattr(obj.color_obj, 'code', None):
                return obj.color_obj.code
            name = ''
            if obj.color_attr and getattr(obj.color_attr, 'name', None):
                name = str(obj.color_attr.name or '')
            elif obj.color_obj and getattr(obj.color_obj, 'name', None):
                name = str(obj.color_obj.name or '')
            key = name.strip().lower()
            M = {
                'أسود': '#000000',
                'ابيض': '#ffffff',
                'أبيض': '#ffffff',
                'احمر': '#ff0000',
                'أحمر': '#ff3b30',
                'أزرق': '#007aff',
                'ازرق': '#007aff',
                'أخضر': '#34c759',
                'اخضر': '#34c759',
                'رمادي': '#8e8e93',
                'زهري': '#ff2d55',
                'وردي': '#ff2d55',
                'بنفسجي': '#af52de',
                'بني': '#795548',
                'بيج': '#f5f5dc',
                'ذهبي': '#d4af37',
                'فضي': '#c0c0c0',
                'أزرق داكن': '#003366',
                'كحلي': '#003366',
            }
            if key in M:
                return M[key]
        except Exception:
            pass
        return ''

    def get_sizes(self, obj):
        try:
            qs = obj.product.variants.all()
            if obj.color_attr_id:
                qs = qs.filter(color_attr_id=obj.color_attr_id)
            elif obj.color_obj_id:
                qs = qs.filter(color_obj_id=obj.color_obj_id)
            items = []
            for v in qs:
                try:
                    val = v.size_attr.name if v.size_attr else v.size
                    items.append({'value': val, 'in_stock': v.stock_qty > 0})
                except Exception:
                    continue
            return items
        except Exception:
            return []
    
    def get_color_key(self, obj):
        try:
            if obj.color_attr_id:
                return f"A{obj.color_attr_id}"
            if obj.color_obj_id:
                return str(obj.color_obj_id)
        except Exception:
            pass
        return ''
    
    def get_color_obj_id(self, obj):
        try:
            return int(obj.color_obj_id) if obj.color_obj_id else None
        except Exception:
            return None
    
    def get_color_attr_id(self, obj):
        try:
            return int(obj.color_attr_id) if obj.color_attr_id else None
        except Exception:
            return None


class ProductSerializer(serializers.ModelSerializer):
    store = StoreSerializer(read_only=True)
    images = ProductImageSerializer(many=True, read_only=True)
    variants = ProductVariantSerializer(many=True, read_only=True)
    main_image = serializers.SerializerMethodField()
    colors = serializers.SerializerMethodField()
    
    class Meta:
        model = Product
        fields = ['id', 'store', 'name', 'description', 'base_price', 'category', 'size_type', 'is_active', 'created_at', 'images', 'variants', 'main_image', 'colors']
    
    def get_main_image(self, obj):
        main_image = obj.main_image
        if main_image:
            return ProductImageSerializer(main_image).data
        return None
    
    def get_colors(self, obj):
        data = []
        try:
            for c in obj.colors.all():
                data.append({'id': c.id, 'name': c.name, 'code': c.code})
        except Exception:
            pass
        return data


class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = ['id', 'city', 'area', 'street', 'details', 'latitude', 'longitude', 'accuracy_m', 'formatted_address', 'provider', 'provider_place_id']


class OrderItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    variant = ProductVariantSerializer(read_only=True)
    
    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'variant', 'quantity', 'price']


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    store = StoreSerializer(read_only=True)
    address = AddressSerializer(read_only=True)
    
    class Meta:
        model = Order
        fields = ['id', 'user', 'store', 'status', 'total_amount', 'delivery_fee', 'payment_method', 'address', 'created_at', 'updated_at', 'items']
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']


class OrderCreateSerializer(serializers.ModelSerializer):
    items = serializers.ListField(
        child=serializers.DictField(),
        write_only=True
    )
    
    class Meta:
        model = Order
        fields = ['store', 'address', 'items']
    
    def validate_items(self, items):
        if not items:
            raise serializers.ValidationError("الطلب يجب أن يحتوي على عناصر")
        
        for item in items:
            if 'product_id' not in item or 'quantity' not in item:
                raise serializers.ValidationError("كل عنصر يجب أن يحتوي على product_id و quantity")
            
            try:
                quantity = int(item['quantity'])
                if quantity < 1:
                    raise serializers.ValidationError("الكمية يجب أن تكون أكبر من 0")
            except (ValueError, TypeError):
                raise serializers.ValidationError("الكمية يجب أن تكون رقماً")
        
        return items
    
    def create(self, validated_data):
        items_data = validated_data.pop('items')
        user = self.context['request'].user
        store = validated_data['store']
        address = validated_data['address']

        with transaction.atomic():
            order = Order.objects.create(
                user=user,
                store=store,
                address=address,
                total_amount=0,
                delivery_fee=settings.DELIVERY_FEE,
                payment_method='cod',
                status='pending'
            )

            total_amount = 0
            for item_data in items_data:
                product = Product.objects.get(id=item_data['product_id'])
                if product.store_id != store.id:
                    raise serializers.ValidationError("بعض العناصر لا تنتمي إلى المتجر المحدد")

                variant_id = item_data.get('variant_id')
                variant = None

                if variant_id:
                    variant = ProductVariant.objects.get(id=variant_id, product=product)
                    if variant.stock_qty < item_data['quantity']:
                        raise serializers.ValidationError(f"الكمية غير متوفرة للمتغير {variant}")

                price = variant.price if variant else product.base_price
                quantity = item_data['quantity']

                OrderItem.objects.create(
                    order=order,
                    product=product,
                    variant=variant,
                    quantity=quantity,
                    price=price
                )

                total_amount += price * quantity

                if variant:
                    variant.stock_qty -= quantity
                    variant.save(update_fields=['stock_qty'])

            order.total_amount = total_amount + order.delivery_fee
            order.save(update_fields=['total_amount'])
            return order


class CartItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    variant = ProductVariantSerializer(read_only=True)
    product_id = serializers.IntegerField(write_only=True, required=True)
    variant_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    quantity = serializers.IntegerField()
    
    class Meta:
        model = CartItem
        fields = ['id', 'product', 'variant', 'product_id', 'variant_id', 'quantity', 'proposed_price', 'proposal_status', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at', 'proposed_price', 'proposal_status']
    
    def create(self, validated_data):
        user = self.context['request'].user
        product_id = validated_data.pop('product_id')
        variant_id = validated_data.pop('variant_id', None)
        product = Product.objects.get(id=product_id)
        variant = None
        if variant_id:
            variant = ProductVariant.objects.get(id=variant_id, product=product)
        item, _ = CartItem.objects.get_or_create(user=user, product=product, variant=variant, defaults={'quantity': validated_data.get('quantity', 1)})
        if not _:
            item.quantity = validated_data.get('quantity', item.quantity)
            item.save()
        return item
    
    def update(self, instance, validated_data):
        qty = int(validated_data.get('quantity', instance.quantity))
        instance.quantity = qty
        instance.save()
        return instance
