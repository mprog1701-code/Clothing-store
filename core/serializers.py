from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from .models import User, Store, Product, ProductImage, ProductVariant, Address, Order, OrderItem


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'phone', 'role', 'city', 'first_name', 'last_name']
        read_only_fields = ['id', 'role']


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)
    full_name = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = ['phone', 'password', 'password_confirm', 'city', 'full_name']
    
    def validate_phone(self, value):
        # Validate Saudi phone number format
        if not value.startswith('05') or len(value) != 10:
            raise serializers.ValidationError("رقم الجوال يجب أن يبدأ بـ 05 ويحتوي على 10 أرقام")
        
        # Check if phone already exists
        if User.objects.filter(phone=value).exists():
            raise serializers.ValidationError("رقم الجوال مسجل بالفعل")
        
        return value
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("كلمات المرور غير متطابقة")
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        full_name = validated_data.pop('full_name')
        
        # Split full name into first and last name
        name_parts = full_name.strip().split(' ', 1)
        first_name = name_parts[0]
        last_name = name_parts[1] if len(name_parts) > 1 else ''
        
        # Generate username from phone number
        username = f"user_{validated_data['phone'][-6:]}"  # Use last 6 digits of phone
        
        # Ensure unique username
        counter = 1
        original_username = username
        while User.objects.filter(username=username).exists():
            username = f"{original_username}_{counter}"
            counter += 1
        
        user = User.objects.create_user(
            username=username,
            email='',  # Email is optional now
            password=validated_data['password'],
            phone=validated_data['phone'],
            city=validated_data['city'],
            first_name=first_name,
            last_name=last_name,
            role='customer'
        )
        return user


class StoreSerializer(serializers.ModelSerializer):
    owner = UserSerializer(read_only=True)
    
    class Meta:
        model = Store
        fields = ['id', 'owner', 'name', 'city', 'address', 'description', 'is_active', 'created_at']
        read_only_fields = ['id', 'owner', 'created_at']


class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ['id', 'image', 'is_main']


class ProductVariantSerializer(serializers.ModelSerializer):
    price = serializers.ReadOnlyField()
    
    class Meta:
        model = ProductVariant
        fields = ['id', 'size', 'color', 'stock_qty', 'price_override', 'price']


class ProductSerializer(serializers.ModelSerializer):
    store = StoreSerializer(read_only=True)
    images = ProductImageSerializer(many=True, read_only=True)
    variants = ProductVariantSerializer(many=True, read_only=True)
    main_image = serializers.SerializerMethodField()
    
    class Meta:
        model = Product
        fields = ['id', 'store', 'name', 'description', 'base_price', 'category', 'size_type', 'is_active', 'created_at', 'images', 'variants', 'main_image']
    
    def get_main_image(self, obj):
        main_image = obj.main_image
        if main_image:
            return ProductImageSerializer(main_image).data
        return None


class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = ['id', 'city', 'area', 'street', 'details', 'latitude', 'longitude']


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
        
        # Create order
        order = Order.objects.create(
            user=user,
            store=store,
            address=address,
            delivery_fee=5000,  # 50 SAR
            payment_method='cod',
            status='pending'
        )
        
        # Create order items
        total_amount = 0
        for item_data in items_data:
            product = Product.objects.get(id=item_data['product_id'])
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
            
            # Update stock
            if variant:
                variant.stock_qty -= quantity
                variant.save()
        
        # Update order total
        order.total_amount = total_amount + order.delivery_fee
        order.save()
        
        return order
