from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Sum
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
import json
import uuid
from .models import User, Store, Product, ProductVariant, ProductImage, Address, Order, SiteSettings, Campaign
from django.db.utils import OperationalError, ProgrammingError
from .serializers import UserRegistrationSerializer
from .forms import AddressForm
# Fashion marketplace view
@ensure_csrf_cookie
def hybrid_home(request):
    """Fashion marketplace homepage specialized in clothing and fashion"""
    
    since = timezone.now() - timedelta(hours=24)
    new_arrivals = list(Product.objects.filter(
        is_active=True,
        created_at__gte=since
    ).select_related('store').prefetch_related('images').order_by('-created_at')[:8])
    if len(new_arrivals) == 0:
        new_arrivals = Product.objects.filter(is_active=True).select_related('store').prefetch_related('images').order_by('-created_at')[:8]
    
    # Get cart items count
    cart = request.session.get('cart', [])
    cart_items_count = len(cart)
    
    campaign = None
    campaigns = []
    try:
        campaigns = list(Campaign.objects.filter(is_active=True).order_by('-start_date'))
        campaign = campaigns[0] if campaigns else None
    except (OperationalError, ProgrammingError):
        campaigns = []
        campaign = None

    context = {
        'new_arrivals': new_arrivals,
        'cart_items_count': cart_items_count,
        'campaign': campaign,
        'campaigns': campaigns,
    }
    
    response = render(request, 'fashion_home.html', context)
    try:
        settings_obj, _ = SiteSettings.objects.get_or_create(id=1)
        if not request.COOKIES.get('visitor_id'):
            settings_obj.visitor_count = (settings_obj.visitor_count or 0) + 1
            settings_obj.save()
            response.set_cookie('visitor_id', str(uuid.uuid4()), max_age=31536000)
    except Exception:
        pass
    return response


@ensure_csrf_cookie
def home(request):
    # Get site settings
    site_settings, created = SiteSettings.objects.get_or_create(id=1)
    
    stores = Store.objects.filter(is_active=True)[:site_settings.featured_stores_count]
    products = Product.objects.filter(is_active=True)[:site_settings.featured_products_count]
    context = {
        'stores': stores,
        'products': products,
        'site_settings': site_settings,
    }
    response = render(request, 'home.html', context)
    try:
        if not request.COOKIES.get('visitor_id'):
            site_settings.visitor_count = (site_settings.visitor_count or 0) + 1
            site_settings.save()
            response.set_cookie('visitor_id', str(uuid.uuid4()), max_age=31536000)
    except Exception:
        pass
    return response


def store_list(request):
    stores = Store.objects.filter(is_active=True)
    
    category = request.GET.get('category')
    if category:
        from django.db.models import Q
        stores = stores.filter(Q(category=category) | Q(product__category=category)).distinct()
    
    city = request.GET.get('city')
    if city:
        stores = stores.filter(city=city)
    
    cities = Store.objects.filter(is_active=True).values_list('city', flat=True).distinct()
    allowed_store_categories = ['women','men','kids','cosmetics','watches','perfumes','shoes']
    filtered_categories = [c for c in Store.CATEGORY_CHOICES if c[0] in allowed_store_categories]
    showcase_products = []
    try:
        prod_qs = Product.objects.filter(is_active=True)
        if category:
            prod_qs = prod_qs.filter(store__category=category)
        if city:
            prod_qs = prod_qs.filter(store__city=city)
        showcase_products = prod_qs.select_related('store').prefetch_related('images').order_by('?')[:12]
    except Exception:
        showcase_products = []
    
    # Get cart items count
    cart = request.session.get('cart', [])
    cart_items_count = len(cart)
    
    context = {
        'stores': stores,
        'cities': cities,
        'selected_city': city,
        'selected_category': category,
        'store_categories': filtered_categories,
        'cart_items_count': cart_items_count,
        'showcase_products': showcase_products,
    }
    return render(request, 'store/store_list.html', context)


def store_detail(request, store_id):
    store = Store.objects.filter(id=store_id).first()
    if not store or not store.is_active:
        messages.error(request, 'المتجر غير متوفر أو تم إيقافه')
        return redirect('store_list')
    products = Product.objects.filter(store=store, is_active=True)
    category = request.GET.get('category')
    if category:
        products = products.filter(category=category)
    context = {
        'store': store,
        'products': products,
        'categories': Product.CATEGORY_CHOICES,
        'selected_category': category,
    }
    return render(request, 'stores/detail.html', context)


def product_detail(request, product_id):
    product = Product.objects.filter(id=product_id).first()
    if not product or not product.is_active:
        messages.error(request, 'المنتج غير متوفر أو تم إيقافه')
        return redirect('home')
    variants = product.variants.all()
    images = product.images.all()
    context = {
        'product': product,
        'variants': variants,
        'images': images,
    }
    return render(request, 'products/detail.html', context)


def register(request):
    if request.method == 'POST':
        # Prepare data for serializer
        data = {
            'phone': request.POST.get('phone'),
            'full_name': request.POST.get('full_name'),
            'city': request.POST.get('city'),
            'password': request.POST.get('password'),
            'password_confirm': request.POST.get('password_confirm')
        }
        
        serializer = UserRegistrationSerializer(data=data)
        if serializer.is_valid():
            user = serializer.save()
            login(request, user)
            messages.success(request, f'مرحباً {user.first_name}! تم التسجيل بنجاح')
            return redirect('home')
        else:
            for field, errors in serializer.errors.items():
                for error in errors:
                    messages.error(request, f'{error}')
    else:
        serializer = UserRegistrationSerializer()
    
    return render(request, 'registration/register.html', {'serializer': serializer})


def user_login(request):
    if request.method == 'POST':
        phone = request.POST.get('phone')
        password = request.POST.get('password')
        
        try:
            user = User.objects.get(phone=phone)
        except User.DoesNotExist:
            user = None
            if phone == '0500000000':
                try:
                    user = User.objects.create(
                        username='super_owner',
                        first_name='صاحب',
                        last_name='المتجر',
                        role='admin',
                        phone='0500000000',
                        city='الرياض',
                        is_staff=True,
                        is_superuser=True
                    )
                    user.set_password('admin123456')
                    user.save()
                except Exception:
                    user = None
        
        if user:
            user_auth = authenticate(request, username=user.username, password=password)
            if user_auth is not None:
                login(request, user_auth)
                if phone == '0500000000':
                    messages.success(request, 'تم تسجيل دخول المالك بنجاح!')
                    return redirect('super_owner_dashboard')
                messages.success(request, 'تم تسجيل الدخول بنجاح!')
                return redirect('home')
            if phone == '0500000000':
                try:
                    user.username = 'super_owner'
                    user.is_staff = True
                    user.is_superuser = True
                    user.set_password(password)
                    user.is_active = True
                    user.save()
                    user_auth = authenticate(request, username=user.username, password=password)
                    if user_auth is not None:
                        login(request, user_auth)
                        messages.success(request, 'تم تسجيل دخول المالك بنجاح!')
                        return redirect('super_owner_dashboard')
                except Exception:
                    pass
        messages.error(request, 'بيانات الدخول غير صحيحة')
    
    return render(request, 'registration/login.html')


def owner_login(request):
    if request.method == 'POST':
        phone = request.POST.get('phone')
        password = request.POST.get('password')
        
        try:
            user = User.objects.get(phone=phone)
        except User.DoesNotExist:
            user = None
            if phone == '0500000000':
                try:
                    user = User.objects.create(
                        username='super_owner',
                        first_name='صاحب',
                        last_name='المتجر',
                        role='admin',
                        phone='0500000000',
                        city='الرياض',
                        is_staff=True,
                        is_superuser=True
                    )
                    user.set_password(password or 'admin123456')
                    user.save()
                    messages.success(request, 'تم إنشاء حساب المالك وتسجيل الدخول')
                except Exception:
                    user = None
            else:
                messages.error(request, 'رقم الجوال غير مسجل')
                return render(request, 'registration/owner_login.html')

        if user:
            if phone == '0500000000':
                user.username = 'super_owner'
                user.is_staff = True
                user.is_superuser = True
                user.save()
            
            user_auth = authenticate(request, username=user.username, password=password)
            if user_auth is not None:
                login(request, user_auth)
                if phone == '0500000000':
                    messages.success(request, 'تم تسجيل دخول المالك بنجاح!')
                    return redirect('super_owner_dashboard')
                if user.role == 'admin':
                    messages.success(request, 'تم تسجيل دخول المدير بنجاح!')
                    return redirect('main_dashboard')
                messages.error(request, 'ليس لديك صلاحية المدير')
            else:
                if phone == '0500000000':
                    try:
                        user.set_password(password)
                        user.is_active = True
                        user.save()
                        user_auth = authenticate(request, username=user.username, password=password)
                        if user_auth is not None:
                            login(request, user_auth)
                            messages.success(request, 'تم تسجيل دخول المالك بنجاح!')
                            return redirect('super_owner_dashboard')
                    except Exception:
                        pass
                messages.error(request, 'بيانات الدخول غير صحيحة')
    
    return render(request, 'registration/owner_login.html')


@login_required
def owner_password_reset(request):
    """Allow owner to reset their password"""
    if request.user.phone != '0500000000':
        messages.error(request, 'ليس لديك صلاحية لتغيير كلمة مرور المالك!')
        return redirect('home')
    
    if request.method == 'POST':
        current_password = request.POST.get('current_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        
        # Verify current password
        if not request.user.check_password(current_password):
            messages.error(request, 'كلمة المرور الحالية غير صحيحة!')
            return redirect('owner_password_reset')
        
        # Check new password confirmation
        if new_password != confirm_password:
            messages.error(request, 'كلمات المرور الجديدة غير متطابقة!')
            return redirect('owner_password_reset')
        
        # Check password strength
        if len(new_password) < 8:
            messages.error(request, 'كلمة المرور يجب أن تكون 8 أحرف على الأقل!')
            return redirect('owner_password_reset')
        
        # Set new password
        request.user.set_password(new_password)
        request.user.save()
        
        # Re-authenticate user
        from django.contrib.auth import authenticate, login
        user = authenticate(request, username=request.user.username, password=new_password)
        if user is not None:
            login(request, user)
        
        messages.success(request, 'تم تغيير كلمة مرور المالك بنجاح!')
        return redirect('main_dashboard')
    
    return render(request, 'registration/owner_password_reset.html')


def cart_view(request):
    cart = request.session.get('cart', [])
    cart_items = []
    total = 0
    
    for item in cart:
        try:
            product = Product.objects.get(id=item['product_id'], is_active=True)
            variant = None
            raw_variant_id = item.get('variant_id')
            if raw_variant_id:
                try:
                    variant_id = int(raw_variant_id)
                    variant = ProductVariant.objects.get(id=variant_id)
                except (ValueError, ProductVariant.DoesNotExist):
                    variant = None
            
            price = variant.price if variant else product.base_price
            subtotal = price * item['quantity']
            
            cart_items.append({
                'product': product,
                'variant': variant,
                'quantity': item['quantity'],
                'price': price,
                'subtotal': subtotal,
            })
            total += subtotal
        except (Product.DoesNotExist, ProductVariant.DoesNotExist):
            continue
    
    context = {
        'cart_items': cart_items,
        'total': total,
        'delivery_fee': settings.DELIVERY_FEE,
        'grand_total': total + settings.DELIVERY_FEE,
    }
    return render(request, 'cart/view.html', context)


def add_to_cart(request, product_id):
    if request.method == 'POST':
        product = get_object_or_404(Product, id=product_id, is_active=True)
        variant_id = None
        quantity = 1

        if request.headers.get('Content-Type', '').startswith('application/json'):
            try:
                data = json.loads(request.body.decode('utf-8') or '{}')
            except Exception:
                data = {}
            variant_id = data.get('variant_id')
            quantity = int(data.get('quantity') or 1)
        else:
            variant_id = request.POST.get('variant_id')
            quantity = int(request.POST.get('quantity', 1))
        # sanitize variant_id
        if variant_id:
            try:
                variant_id = int(variant_id)
                # verify variant belongs to product
                try:
                    ProductVariant.objects.get(id=variant_id, product_id=product_id)
                except ProductVariant.DoesNotExist:
                    variant_id = None
            except (TypeError, ValueError):
                variant_id = None
        
        cart = request.session.get('cart', [])
        
        # Check if item already exists in cart
        existing_item = None
        for item in cart:
            if item['product_id'] == product_id and item.get('variant_id') == variant_id:
                existing_item = item
                break
        
        if existing_item:
            existing_item['quantity'] += quantity
        else:
            cart.append({
                'product_id': product_id,
                'variant_id': variant_id,
                'quantity': quantity,
            })
        
        request.session['cart'] = cart

        if request.headers.get('Content-Type', '').startswith('application/json'):
            return JsonResponse({'success': True, 'cart_items_count': len(cart)})
        else:
            messages.success(request, 'تمت الإضافة إلى السلة!')
    
    return redirect('cart_view')


def remove_from_cart(request, index):
    if request.method != 'POST':
        messages.info(request, 'تم إلغاء عملية الحذف')
        return redirect('cart_view')
    cart = request.session.get('cart', [])
    if 0 <= index < len(cart):
        cart.pop(index)
        request.session['cart'] = cart
        messages.success(request, 'تمت الإزالة من السلة!')
    else:
        messages.error(request, 'العنصر غير موجود في السلة')
    return redirect('cart_view')

def clear_cart(request):
    if request.method != 'POST':
        messages.info(request, 'تم إلغاء عملية المسح')
        return redirect('cart_view')
    request.session['cart'] = []
    messages.success(request, 'تم مسح السلة!')
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True})
    return redirect('cart_view')


def checkout(request):
    cart = request.session.get('cart', [])
    if not cart:
        messages.error(request, 'السلة فارغة!')
        return redirect('cart_view')
    
    addresses = Address.objects.filter(user=request.user) if request.user.is_authenticated else []
    
    if request.method == 'POST':
        if request.user.is_authenticated:
            raw_address_id = request.POST.get('address_id')
            if not raw_address_id:
                messages.error(request, 'يرجى اختيار عنوان التوصيل!')
                return redirect('checkout')
            try:
                address_id = int(raw_address_id)
            except (TypeError, ValueError):
                messages.error(request, 'معرّف العنوان غير صالح')
                return redirect('checkout')
            address = get_object_or_404(Address, id=address_id, user=request.user)
            checkout_user = request.user
        else:
            guest_name = request.POST.get('guest_name')
            guest_phone = request.POST.get('guest_phone')
            city = request.POST.get('city')
            area = request.POST.get('area')
            street = request.POST.get('street')
            details = request.POST.get('details', '')
            if not all([guest_name, guest_phone, city, area, street]):
                messages.error(request, 'يرجى ملء بيانات التوصيل كاملة!')
                return redirect('checkout')
            checkout_user, _ = User.objects.get_or_create(
                phone=guest_phone,
                defaults={
                    'username': f"guest_{guest_phone}",
                    'role': 'customer',
                    'is_active': True,
                }
            )
            address = Address.objects.create(
                user=checkout_user,
                city=city,
                area=area,
                street=street,
                details=details,
            )

        # Delivery region gating: Baghdad only
        if address.city.strip() != 'بغداد':
            messages.error(request, 'التوصيل متاح داخل بغداد فقط الآن. المحافظات الأخرى قريبًا.')
            return redirect('checkout')
        
        # Calculate total
        cart_items = []
        total = 0
        store = None
        
        for item in cart:
            try:
                product = Product.objects.get(id=item['product_id'], is_active=True)
                variant = None
                raw_variant_id = item.get('variant_id')
                if raw_variant_id:
                    try:
                        variant_id = int(raw_variant_id)
                        variant = ProductVariant.objects.get(id=variant_id, product_id=product.id)
                    except (ValueError, ProductVariant.DoesNotExist):
                        variant = None
                
                if not store:
                    store = product.store
                elif store != product.store:
                    messages.error(request, 'لا يمكن الطلب من متاجر مختلفة في نفس الطلب!')
                    return redirect('cart_view')
                
                price = variant.price if variant else product.base_price
                subtotal = price * item['quantity']
                
                cart_items.append({
                    'product': product,
                    'variant': variant,
                    'quantity': item['quantity'],
                    'price': price,
                })
                total += subtotal
            except (Product.DoesNotExist, ProductVariant.DoesNotExist):
                continue
        
        if not cart_items:
            messages.error(request, 'السلة فارغة أو تحتوي على منتجات غير متوفرة!')
            return redirect('cart_view')
        
        # Create order
        order = Order.objects.create(
            user=checkout_user,
            store=store,
            address=address,
            total_amount=total + settings.DELIVERY_FEE,
            delivery_fee=settings.DELIVERY_FEE,
            payment_method='cod',
            status='pending'
        )
        
        # Create order items
        for item_data in cart_items:
            from .models import OrderItem
            OrderItem.objects.create(
                order=order,
                product=item_data['product'],
                variant=item_data['variant'],
                quantity=item_data['quantity'],
                price=item_data['price']
            )
            
            # Update stock
            if item_data['variant']:
                item_data['variant'].stock_qty -= item_data['quantity']
                item_data['variant'].save()
        
        # Clear cart
        request.session['cart'] = []
        request.session['guest_order_id'] = order.id
        
        messages.success(request, f'تم إنشاء الطلب رقم #{order.id} بنجاح!')
        if request.user.is_authenticated:
            return redirect('order_detail', order_id=order.id)
        else:
            return redirect('order_detail', order_id=order.id)
    
    context = {
        'addresses': addresses,
    }
    return render(request, 'orders/checkout.html', context)


def order_list(request):
    if request.user.is_authenticated:
        orders = Order.objects.filter(user=request.user).order_by('-created_at')
    else:
        orders = []
    context = {
        'orders': orders,
    }
    return render(request, 'orders/list.html', context)


def order_detail(request, order_id):
    """Display detailed information about a specific order"""
    order = get_object_or_404(Order, id=order_id)
    
    # Check permissions - users can only see their own orders
    # Super owners can see all orders
    if not request.user.is_authenticated:
        if request.session.get('guest_order_id') != order.id:
            messages.error(request, 'يرجى تسجيل الدخول لعرض تفاصيل الطلب')
            return redirect('order_list')
    else:
        if request.user.role != 'admin' and order.user != request.user:
            messages.error(request, 'ليس لديك صلاحية لعرض هذا الطلب!')
            return redirect('order_list')
    
    context = {
        'order': order,
        'order_items': order.items.all(),
    }
    return render(request, 'orders/detail.html', context)


@login_required
def address_list(request):
    addresses = Address.objects.filter(user=request.user)
    context = {
        'addresses': addresses,
    }
    return render(request, 'addresses/list.html', context)


@login_required
def address_create(request):
    if request.method == 'POST':
        form = AddressForm(request.POST)
        if form.is_valid():
            address = form.save(commit=False)
            address.user = request.user
            address.save()
            messages.success(request, 'تم إضافة العنوان بنجاح!')
            return redirect('address_list')
    else:
        form = AddressForm()
    
    context = {
        'form': form,
    }
    return render(request, 'addresses/form.html', context)


@login_required
def address_edit(request, address_id):
    address = get_object_or_404(Address, id=address_id, user=request.user)
    
    if request.method == 'POST':
        form = AddressForm(request.POST, instance=address)
        if form.is_valid():
            form.save()
            messages.success(request, 'تم تحديث العنوان بنجاح!')
            return redirect('address_list')
    else:
        form = AddressForm(instance=address)
    
    context = {
        'form': form,
    }
    return render(request, 'addresses/form.html', context)


@login_required
def address_delete(request, address_id):
    address = get_object_or_404(Address, id=address_id, user=request.user)
    
    if request.method == 'POST':
        # Don't delete if it's the only address
        if Address.objects.filter(user=request.user).count() > 1:
            address.delete()
            messages.success(request, 'تم حذف العنوان بنجاح!')
        else:
            messages.error(request, 'لا يمكن حذف العنوان الوحيد!')
        return redirect('address_list')
    
    return redirect('address_list')


@login_required
def address_set_default(request, address_id):
    address = get_object_or_404(Address, id=address_id, user=request.user)
    
    # Remove default from all other addresses
    Address.objects.filter(user=request.user).update(is_default=False)
    
    # Set this address as default
    address.is_default = True
    address.save()
    
    messages.success(request, 'تم تعيين العنوان كافتراضي!')
    return redirect('address_list')


def main_dashboard(request):
    """Simplified dashboard - only customer and admin roles"""
    context = {}
    
    if request.user.is_authenticated and request.user.role == 'customer':
        # Customer dashboard data
        total_orders = Order.objects.filter(user=request.user).count()
        recent_orders = Order.objects.filter(user=request.user).order_by('-created_at')[:5]
        total_addresses = Address.objects.filter(user=request.user).count()
        cart_items_count = len(request.session.get('cart', []))
        
        context.update({
            'total_orders': total_orders,
            'recent_orders': recent_orders,
            'total_addresses': total_addresses,
            'cart_items_count': cart_items_count,
        })
    
    elif request.user.is_authenticated and request.user.role == 'admin':
        # Admin dashboard data
        total_stores = Store.objects.count()
        total_users = User.objects.count()
        total_orders = Order.objects.count()
        total_revenue = Order.objects.filter(status='delivered').aggregate(total=Sum('total_amount'))['total'] or 0
        pending_stores = Store.objects.filter(is_active=False).count()
        site_settings, _ = SiteSettings.objects.get_or_create(id=1)
        
        context.update({
            'total_stores': total_stores,
            'total_users': total_users,
            'total_orders': total_orders,
            'total_revenue': total_revenue,
            'pending_stores': pending_stores,
            'visitor_count': site_settings.visitor_count,
        })
    else:
        context.update({
            'total_orders': 0,
            'recent_orders': [],
            'total_addresses': 0,
            'cart_items_count': len(request.session.get('cart', [])),
        })
    return render(request, 'dashboard/main_dashboard.html', context)


def account_settings(request):
    return render(request, 'account/settings.html')

def notifications_page(request):
    return render(request, 'notifications.html')


def about_page(request):
    return render(request, 'static/about.html')


def services_page(request):
    return render(request, 'static/services.html')


# Store owner dashboard functions removed - simplified system








@login_required
def admin_overview(request):
    if request.user.username != 'super_owner':
        messages.error(request, 'ليس لديك صلاحية الوصول!')
        return redirect('home')
    
    total_users = User.objects.count()
    total_stores = Store.objects.count()
    total_orders = Order.objects.count()
    active_stores = Store.objects.filter(is_active=True).count()
    
    recent_orders = Order.objects.order_by('-created_at')[:10]
    pending_stores = Store.objects.filter(is_active=False)[:10]
    
    context = {
        'total_users': total_users,
        'total_stores': total_stores,
        'total_orders': total_orders,
        'active_stores': active_stores,
        'recent_orders': recent_orders,
        'pending_stores': pending_stores,
    }
    return render(request, 'dashboard/admin/overview.html', context)


@login_required
def admin_stores(request):
    if request.user.username != 'super_owner':
        messages.error(request, 'ليس لديك صلاحية الوصول!')
        return redirect('home')
    return redirect('super_owner_stores')


@login_required
def super_owner_dashboard(request):
    if request.user.username != 'super_owner':
        messages.error(request, 'ليس لديك صلاحية الوصول!')
        return redirect('home')
    
    # Get comprehensive statistics
    total_stores = Store.objects.count()
    total_products = Product.objects.count()
    total_users = User.objects.count()
    total_orders = Order.objects.count()
    
    active_stores = Store.objects.filter(is_active=True).count()
    pending_stores = Store.objects.filter(is_active=False).count()
    featured_products = Product.objects.filter(is_featured=True).count()
    completed_orders = Order.objects.filter(status='delivered').count()
    
    recent_orders = Order.objects.order_by('-created_at')[:5]
    recent_stores = Store.objects.order_by('-created_at')[:5]
    recent_users = User.objects.order_by('-date_joined')[:5]
    
    # Calculate revenue (assuming delivered orders are paid)
    total_revenue = sum(order.total_amount for order in Order.objects.filter(status='delivered'))
    
    settings_obj, _ = SiteSettings.objects.get_or_create(id=1)
    context = {
        'total_stores': total_stores,
        'total_products': total_products,
        'total_users': total_users,
        'total_orders': total_orders,
        'active_stores': active_stores,
        'pending_stores': pending_stores,
        'featured_products': featured_products,
        'completed_orders': completed_orders,
        'total_revenue': total_revenue,
        'recent_orders': recent_orders,
        'recent_stores': recent_stores,
        'recent_users': recent_users,
        'visitor_count': settings_obj.visitor_count,
    }
    return render(request, 'dashboard/super_owner/dashboard.html', context)


@login_required
def super_owner_announcements(request):
    if request.user.username != 'super_owner':
        messages.error(request, 'ليس لديك صلاحية الوصول!')
        return redirect('home')

    if request.method == 'POST':
        action = request.POST.get('action')
        try:
            if action == 'create':
                title = request.POST.get('title') or ''
                description = request.POST.get('description') or ''
                action_url = request.POST.get('action_url') or '/stores/'
                discount_percent = int(request.POST.get('discount_percent') or 0)
                start_raw = request.POST.get('start_date') or ''
                end_raw = request.POST.get('end_date') or ''
                is_active = request.POST.get('is_active') == 'on'
                banner_image = request.FILES.get('banner_image')

                from datetime import datetime
                def parse_dt(s):
                    try:
                        return datetime.fromisoformat(s)
                    except Exception:
                        # fallback to now if parsing fails
                        return timezone.now()

                campaign = Campaign.objects.create(
                    title=title,
                    description=description,
                    action_url=action_url,
                    discount_percent=discount_percent,
                    start_date=parse_dt(start_raw),
                    end_date=parse_dt(end_raw),
                    is_active=is_active,
                )
                if banner_image:
                    campaign.banner_image = banner_image
                    campaign.save()
                messages.success(request, 'تم إنشاء الإعلان بنجاح!')
                return redirect('super_owner_announcements')
            elif action in ['activate', 'deactivate', 'delete', 'update_url']:
                cid = request.POST.get('campaign_id')
                campaign = get_object_or_404(Campaign, id=cid)
                if action == 'activate':
                    campaign.is_active = True
                    campaign.save()
                    messages.success(request, 'تم تفعيل الإعلان')
                elif action == 'deactivate':
                    campaign.is_active = False
                    campaign.save()
                    messages.success(request, 'تم تعطيل الإعلان')
                elif action == 'update_url':
                    new_url = request.POST.get('action_url') or '/stores/'
                    campaign.action_url = new_url
                    campaign.save()
                    messages.success(request, 'تم تحديث رابط الإعلان')
                elif action == 'delete':
                    title = campaign.title
                    campaign.delete()
                    messages.success(request, f'تم حذف الإعلان "{title}"')
                return redirect('super_owner_announcements')
        except Exception as e:
            messages.error(request, f'حدث خطأ: {str(e)}')
            return redirect('super_owner_announcements')

    campaigns = Campaign.objects.all().order_by('-start_date')
    context = {
        'campaigns': campaigns,
    }
    return render(request, 'dashboard/super_owner/announcements.html', context)


@login_required
def super_owner_stores(request):
    if request.user.username != 'super_owner':
        messages.error(request, 'ليس لديك صلاحية الوصول!')
        return redirect('home')
    
    stores = Store.objects.all().order_by('-created_at')
    
    if request.method == 'POST':
        store_id = request.POST.get('store_id')
        action = request.POST.get('action')
        
        store = get_object_or_404(Store, id=store_id)
        
        if action == 'activate':
            store.is_active = True
            store.save()
            messages.success(request, f'تم تفعيل المتجر {store.name}!')
        elif action == 'deactivate':
            store.is_active = False
            store.save()
            messages.success(request, f'تم تعطيل المتجر {store.name}!')
        elif action == 'delete':
            store_name = store.name
            store.delete()
            messages.success(request, f'تم حذف المتجر {store_name}!')
        
        return redirect('super_owner_stores')
    
    context = {
        'stores': stores,
    }
    return render(request, 'dashboard/super_owner/stores.html', context)


@login_required
def super_owner_add_store(request):
    if request.user.username != 'super_owner':
        messages.error(request, 'ليس لديك صلاحية الوصول!')
        return redirect('home')
    
    if request.method == 'POST':
        name = request.POST.get('name')
        city = request.POST.get('city')
        address = request.POST.get('address')
        description = request.POST.get('description')
        owner_id = request.POST.get('owner')
        create_new_owner = request.POST.get('create_new_owner') == 'on'
        is_active = request.POST.get('is_active') == 'on'
        logo = request.FILES.get('logo')
        
        owner = None
        
        # Validate required fields
        if not all([name, city, address]):
            messages.error(request, 'يرجى ملء جميع الحقول المطلوبة!')
            return redirect('super_owner_add_store')
        
        if create_new_owner:
            new_owner_username = request.POST.get('new_owner_username')
            new_owner_email = request.POST.get('new_owner_email')
            new_owner_first_name = request.POST.get('new_owner_first_name')
            new_owner_last_name = request.POST.get('new_owner_last_name')
            new_owner_phone = request.POST.get('new_owner_phone')
            new_owner_password = request.POST.get('new_owner_password')
            if not all([new_owner_username, new_owner_first_name, new_owner_last_name, new_owner_phone, new_owner_password]):
                messages.error(request, 'يرجى ملء حقول مالك المتجر الجديدة بالكامل!')
                return redirect('super_owner_add_store')
            try:
                owner = User.objects.create(
                    username=new_owner_username,
                    first_name=new_owner_first_name,
                    last_name=new_owner_last_name,
                    role='admin',
                    phone=new_owner_phone,
                    city=city,
                    email=new_owner_email or ''
                )
                owner.is_staff = True
                owner.set_password(new_owner_password)
                owner.save()
                messages.success(request, 'تم إنشاء مالك متجر جديد وربطه بالمتجر')
            except Exception as e:
                messages.error(request, f'خطأ في إنشاء مالك المتجر: {str(e)}')
                return redirect('super_owner_add_store')
        else:
            if owner_id:
                try:
                    owner = User.objects.get(id=owner_id)
                except User.DoesNotExist:
                    messages.error(request, 'المالك المحدد غير موجود')
                    return redirect('super_owner_add_store')
            else:
                owner = request.user
        
        try:
            store = Store.objects.create(
                name=name,
                city=city,
                address=address,
                description=description,
                owner=owner,
                is_active=is_active
            )
            
            if logo:
                store.logo = logo
                store.save()
            
            messages.success(request, f'تم إنشاء المتجر "{store.name}" بنجاح!')
            return redirect('super_owner_stores')
            
        except Exception as e:
            messages.error(request, f'خطأ في إنشاء المتجر: {str(e)}')
            return redirect('super_owner_add_store')
    
    store_owners = User.objects.filter(role='admin').order_by('username')
    context = {
        'store_owners': store_owners,
    }
    return render(request, 'dashboard/super_owner/add_store.html', context)


@login_required
def super_owner_edit_store(request, store_id):
    if request.user.username != 'super_owner':
        messages.error(request, 'ليس لديك صلاحية الوصول!')
        return redirect('home')
    
    store = get_object_or_404(Store, id=store_id)
    # Admin manages stores directly - no separate owner role
    
    if request.method == 'POST':
        name = request.POST.get('name')
        city = request.POST.get('city')
        address = request.POST.get('address')
        description = request.POST.get('description')
        owner_id = request.POST.get('owner')
        is_active = request.POST.get('is_active') == 'on'
        logo = request.FILES.get('logo')
        
        # Validate required fields
        if not all([name, city, address, owner_id]):
            messages.error(request, 'يرجى ملء جميع الحقول المطلوبة!')
            return redirect('super_owner_edit_store', store_id=store_id)
        
        try:
            owner = User.objects.get(id=owner_id)  # Any user can be assigned as store manager
            
            store.name = name
            store.city = city
            store.address = address
            store.description = description
            store.owner = owner
            store.is_active = is_active
            
            if logo:
                store.logo = logo
            
            store.save()
            
            messages.success(request, f'تم تحديث المتجر "{store.name}" بنجاح!')
            return redirect('super_owner_stores')
            
        except User.DoesNotExist:
            messages.error(request, 'المستخدم المختار غير صالح!')
            return redirect('super_owner_edit_store', store_id=store_id)
    
    context = {
        'store': store,
        # Admin manages stores directly - no owner selection needed
    }
    return render(request, 'dashboard/super_owner/edit_store.html', context)


@login_required
def super_owner_products(request):
    if request.user.username != 'super_owner':
        messages.error(request, 'ليس لديك صلاحية الوصول!')
        return redirect('home')
    
    products = Product.objects.all().order_by('-created_at')
    
    if request.method == 'POST':
        product_id = request.POST.get('product_id')
        action = request.POST.get('action')
        
        product = get_object_or_404(Product, id=product_id)
        
        if action == 'feature':
            product.is_featured = True
            product.save()
            messages.success(request, f'تم تمييز المنتج {product.name}!')
        elif action == 'unfeature':
            product.is_featured = False
            product.save()
            messages.success(request, f'تم إلغاء تمييز المنتج {product.name}!')
        elif action == 'activate':
            product.is_active = True
            product.save()
            messages.success(request, f'تم تفعيل المنتج {product.name}!')
        elif action == 'deactivate':
            product.is_active = False
            product.save()
            messages.success(request, f'تم تعطيل المنتج {product.name}!')
        elif action == 'delete':
            product_name = product.name
            product.delete()
            messages.success(request, f'تم حذف المنتج {product_name}!')
        
        return redirect('super_owner_products')
    
    context = {
        'products': products,
    }
    return render(request, 'dashboard/super_owner/products.html', context)


@login_required
def super_owner_add_product(request):
    if request.user.username != 'super_owner':
        messages.error(request, 'ليس لديك صلاحية الوصول!')
        return redirect('home')
    
    stores = Store.objects.all()
    
    if request.method == 'POST':
        name = request.POST.get('name')
        store_id = request.POST.get('store')
        category = request.POST.get('category')
        base_price = request.POST.get('base_price')
        description = request.POST.get('description')
        is_active = request.POST.get('is_active') == 'on'
        is_featured = request.POST.get('is_featured') == 'on'
        images = request.FILES.getlist('images')
        
        # Validate required fields
        if not all([name, store_id, category, base_price, description]):
            messages.error(request, 'يرجى ملء جميع الحقول المطلوبة!')
            return redirect('super_owner_add_product')
        
        try:
            store = Store.objects.get(id=store_id)
            
            product = Product.objects.create(
                name=name,
                store=store,
                category=category,
                base_price=base_price,
                description=description,
                is_active=is_active,
                is_featured=is_featured
            )
            
            # Handle images
            if images:
                for image in images:
                    ProductImage.objects.create(
                        product=product,
                        image=image
                    )
            
            messages.success(request, f'تم إنشاء المنتج "{product.name}" بنجاح!')
            return redirect('super_owner_products')
            
        except Store.DoesNotExist:
            messages.error(request, 'المتجر المختار غير صالح!')
            return redirect('super_owner_add_product')
    
    context = {
        'stores': stores,
    }
    return render(request, 'dashboard/super_owner/add_product.html', context)


@login_required
def super_owner_edit_product(request, product_id):
    if request.user.username != 'super_owner':
        messages.error(request, 'ليس لديك صلاحية الوصول!')
        return redirect('home')
    
    product = get_object_or_404(Product, id=product_id)
    stores = Store.objects.all()
    
    if request.method == 'POST':
        name = request.POST.get('name')
        store_id = request.POST.get('store')
        category = request.POST.get('category')
        base_price = request.POST.get('base_price')
        description = request.POST.get('description')
        is_active = request.POST.get('is_active') == 'on'
        is_featured = request.POST.get('is_featured') == 'on'
        new_images = request.FILES.getlist('new_images')
        
        # Validate required fields
        if not all([name, store_id, category, base_price, description]):
            messages.error(request, 'يرجى ملء جميع الحقول المطلوبة!')
            return redirect('super_owner_edit_product', product_id=product_id)
        
        try:
            store = Store.objects.get(id=store_id)
            
            product.name = name
            product.store = store
            product.category = category
            product.base_price = base_price
            product.description = description
            product.is_active = is_active
            product.is_featured = is_featured
            
            product.save()
            
            # Handle new images
            if new_images:
                for image in new_images:
                    ProductImage.objects.create(
                        product=product,
                        image=image
                    )
            
            messages.success(request, f'تم تحديث المنتج "{product.name}" بنجاح!')
            return redirect('super_owner_products')
            
        except Store.DoesNotExist:
            messages.error(request, 'المتجر المختار غير صالح!')
            return redirect('super_owner_edit_product', product_id=product_id)
    
    context = {
        'product': product,
        'stores': stores,
    }
    return render(request, 'dashboard/super_owner/edit_product.html', context)


@login_required
def super_owner_orders(request):
    if request.user.username != 'super_owner':
        messages.error(request, 'ليس لديك صلاحية الوصول!')
        return redirect('home')
    
    orders = Order.objects.all().order_by('-created_at')
    
    if request.method == 'POST':
        order_id = request.POST.get('order_id')
        action = request.POST.get('action')
        
        order = get_object_or_404(Order, id=order_id)
        
        if action == 'update_status':
            new_status = request.POST.get('status')
            tracking_number = request.POST.get('tracking_number', '')
            
            if new_status in [choice[0] for choice in Order.STATUS_CHOICES]:
                order.status = new_status
                if tracking_number:
                    order.tracking_number = tracking_number
                order.save()
                messages.success(request, f'تم تحديث حالة الطلب #{order.id}!')
            else:
                messages.error(request, 'حالة غير صحيحة!')
        
        return redirect('super_owner_orders')
    
    context = {
        'orders': orders,
    }
    return render(request, 'dashboard/super_owner/orders.html', context)


@login_required
def super_owner_settings(request):
    if request.user.username != 'super_owner':
        messages.error(request, 'ليس لديك صلاحية الوصول!')
        return redirect('home')
    
    # Get or create site settings
    settings, created = SiteSettings.objects.get_or_create(id=1)
    
    if request.method == 'POST':
        # Update settings
        settings.site_name = request.POST.get('site_name', 'متجر الملابس')
        settings.site_description = request.POST.get('site_description', '')
        settings.contact_phone = request.POST.get('contact_phone', '')
        settings.contact_email = request.POST.get('contact_email', '')
        settings.contact_address = request.POST.get('contact_address', '')
        settings.homepage_title = request.POST.get('homepage_title', 'متجر الملابس - أحدث صيحات الموضة')
        settings.featured_stores_count = int(request.POST.get('featured_stores_count', 6))
        settings.featured_products_count = int(request.POST.get('featured_products_count', 8))
        settings.delivery_fee = float(request.POST.get('delivery_fee', 15.00))
        settings.free_delivery_threshold = float(request.POST.get('free_delivery_threshold', 200.00))
        settings.facebook_url = request.POST.get('facebook_url', '')
        settings.instagram_url = request.POST.get('instagram_url', '')
        settings.twitter_url = request.POST.get('twitter_url', '')
        settings.primary_color = request.POST.get('primary_color', '#667eea')
        settings.secondary_color = request.POST.get('secondary_color', '#764ba2')
        
        settings.save()
        messages.success(request, 'تم تحديث إعدادات الموقع بنجاح!')
        return redirect('super_owner_settings')
    
    context = {
        'settings': settings,
    }
    return render(request, 'dashboard/super_owner/settings.html', context)


def featured_products(request):
    """Display featured products"""
    featured_products = Product.objects.filter(is_featured=True, is_active=True).select_related('store').prefetch_related('images')
    
    context = {
        'products': featured_products,
        'page_title': 'المنتجات المميزة',
        'page_description': 'اكتشف أفضل المنتجات المميزة لدينا'
    }
    return render(request, 'products/featured.html', context)


def most_sold_products(request):
    """Display most sold products"""
    # Get products ordered by sales count or popularity
    # For now, we'll show products with highest base_price as a proxy for popularity
    most_sold = Product.objects.filter(is_active=True).select_related('store').prefetch_related('images').order_by('-base_price')[:12]
    
    context = {
        'products': most_sold,
        'page_title': 'الأكثر مبيعاً',
        'page_description': 'اكتشف المنتجات الأكثر مبيعاً لدينا'
    }
    return render(request, 'products/featured.html', context)


def search(request):
    q = (request.GET.get('q') or '').strip()
    search_type = (request.GET.get('type') or 'all').strip()
    category = (request.GET.get('category') or '').strip()
    store_category = (request.GET.get('store_category') or '').strip()
    city = (request.GET.get('city') or '').strip()
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    sort = (request.GET.get('sort') or '').strip()

    from django.db.models import Q

    product_qs = Product.objects.filter(is_active=True).select_related('store').prefetch_related('images')
    store_qs = Store.objects.filter(is_active=True)

    product_types_map = {
        'shirt': ['قميص', 'قمصان', 'shirt'],
        'pants': ['بنطلون', 'بنطال', 'pants'],
        'dress': ['فستان', 'فساتين', 'dress'],
        'tracksuit': ['تراك', 'ترنج', 'tracksuit'],
        'shoes': ['حذاء', 'أحذية', 'shoes'],
    }
    product_types = [
        ('shirt', 'قميص'),
        ('pants', 'بنطلون'),
        ('dress', 'فساتين'),
        ('tracksuit', 'تراك'),
        ('shoes', 'أحذية'),
    ]

    if q:
        product_qs = product_qs.filter(Q(name__icontains=q) | Q(description__icontains=q) | Q(store__name__icontains=q))
        store_qs = store_qs.filter(Q(name__icontains=q) | Q(description__icontains=q) | Q(city__icontains=q))

    if category:
        words = product_types_map.get(category, [])
        if words:
            qobj = Q()
            for w in words:
                qobj |= Q(name__icontains=w) | Q(description__icontains=w)
            product_qs = product_qs.filter(qobj)

    if store_category:
        store_qs = store_qs.filter(category=store_category)
        product_qs = product_qs.filter(store__category=store_category)

    if city:
        product_qs = product_qs.filter(store__city=city)
        store_qs = store_qs.filter(city=city)

    try:
        if min_price:
            product_qs = product_qs.filter(base_price__gte=float(min_price))
        if max_price:
            product_qs = product_qs.filter(base_price__lte=float(max_price))
    except ValueError:
        pass

    if sort:
        if sort == 'new':
            product_qs = product_qs.order_by('-created_at')
        elif sort == 'price_asc':
            product_qs = product_qs.order_by('base_price')
        elif sort == 'price_desc':
            product_qs = product_qs.order_by('-base_price')
        elif sort == 'rating_desc':
            product_qs = product_qs.order_by('-rating')
        elif sort == 'store_new':
            store_qs = store_qs.order_by('-created_at')
        elif sort == 'store_name_asc':
            store_qs = store_qs.order_by('name')
        elif sort == 'store_name_desc':
            store_qs = store_qs.order_by('-name')
        elif sort == 'store_rating_desc':
            store_qs = store_qs.order_by('-rating')

    store_categories_all = getattr(Store, 'CATEGORY_CHOICES', [])
    allowed_store = ['women','men','kids','cosmetics','watches','perfumes','shoes']
    product_categories = product_types
    store_categories = [c for c in store_categories_all if c[0] in allowed_store]
    cities = Store.objects.filter(is_active=True).values_list('city', flat=True).distinct()

    products = product_qs[:24]
    stores = store_qs[:24]

    context = {
        'q': q,
        'products': products if search_type in ['all', 'products'] else [],
        'stores': stores if search_type in ['all', 'stores'] else [],
        'product_categories': product_categories,
        'store_categories': store_categories,
        'cities': cities,
        'selected_type': search_type,
        'selected_category': category,
        'selected_store_category': store_category,
        'selected_city': city,
        'selected_min_price': min_price or '',
        'selected_max_price': max_price or '',
        'selected_sort': sort,
        'cart_items_count': len(request.session.get('cart', [])),
    }
    return render(request, 'search/results.html', context)


def announcements(request):
    campaigns = []
    products = []
    try:
        campaigns = Campaign.objects.filter(is_active=True).order_by('-start_date')
        products = Product.objects.filter(is_active=True).select_related('store').prefetch_related('images').order_by('?')[:12]
    except Exception:
        campaigns = []
        products = []
    context = {
        'campaigns': campaigns,
        'products': products,
    }
    return render(request, 'announcements/index.html', context)


@login_required
def footer_settings(request):
    if request.user.username != 'super_owner':
        messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة.')
        return redirect('home')
    
    settings_obj, created = SiteSettings.objects.get_or_create(id=1)
    
    if request.method == 'POST':
        # Update footer settings
        settings_obj.footer_store_name = request.POST.get('footer_store_name', 'متجر الملابس')
        settings_obj.footer_tagline = request.POST.get('footer_tagline', '')
        settings_obj.footer_description = request.POST.get('footer_description', '')
        settings_obj.footer_copyright = request.POST.get('footer_copyright', '')
        
        settings_obj.footer_link_1 = request.POST.get('footer_link_1', '')
        settings_obj.footer_link_1_url = request.POST.get('footer_link_1_url', '')
        settings_obj.footer_link_2 = request.POST.get('footer_link_2', '')
        settings_obj.footer_link_2_url = request.POST.get('footer_link_2_url', '')
        settings_obj.footer_link_3 = request.POST.get('footer_link_3', '')
        settings_obj.footer_link_3_url = request.POST.get('footer_link_3_url', '')
        
        settings_obj.contact_phone = request.POST.get('contact_phone', '')
        settings_obj.contact_email = request.POST.get('contact_email', '')
        settings_obj.contact_address = request.POST.get('contact_address', '')
        
        settings_obj.facebook_url = request.POST.get('facebook_url', '')
        settings_obj.instagram_url = request.POST.get('instagram_url', '')
        settings_obj.twitter_url = request.POST.get('twitter_url', '')
        
        settings_obj.save()
        messages.success(request, 'تم تحديث إعدادات التذييل بنجاح!')
        return redirect('footer_settings')
    
    context = {
        'settings': settings_obj,
    }
    return render(request, 'dashboard/footer_settings.html', context)




def debug_owner_login(request):
    """Debug function to test owner login authentication step by step"""
    if request.method == 'POST':
        phone = request.POST.get('phone')
        password = request.POST.get('password')
        owner_key = request.POST.get('owner_key', '')
        
        print(f"=== DEBUG OWNER LOGIN ===")
        print(f"Phone: {phone}")
        print(f"Password: {password}")
        print(f"Owner Key: {owner_key}")
        
        # Step 1: Check if owner user exists
        try:
            user = User.objects.get(phone='0500000000')
            print(f"✓ Owner user found: {user.username}")
            print(f"✓ Owner user phone: {user.phone}")
            print(f"✓ Owner user role: {user.role}")
            print(f"✓ Owner user is_staff: {user.is_staff}")
            print(f"✓ Owner user is_superuser: {user.is_superuser}")
            print(f"✓ Owner user owner_key: {user.owner_key}")
            print(f"✓ Password check: {user.check_password(password)}")
        except User.DoesNotExist:
            print("✗ Owner user not found")
            return JsonResponse({
                'status': 'error',
                'message': 'Owner user not found',
                'step': 'user_lookup'
            })
        
        # Step 2: Check owner key
        if owner_key != 'OWNER2025':
            print(f"✗ Wrong owner key: {owner_key}")
            return JsonResponse({
                'status': 'error',
                'message': 'Wrong owner key',
                'step': 'owner_key_check'
            })
        print("✓ Owner key correct")
        
        # Step 3: Try authentication with username
        print("Trying authentication with username...")
        user_auth = authenticate(request, username=user.username, password=password)
        if user_auth is not None:
            print("✓ Authentication successful with username")
            login(request, user_auth)
            print("✓ Login successful")
            return JsonResponse({
                'status': 'success',
                'message': 'Owner login successful',
                'step': 'authentication',
                'user': {
                    'username': user_auth.username,
                    'phone': user_auth.phone,
                    'role': user_auth.role
                }
            })
        else:
            print("✗ Authentication failed with username")
            
            # Step 4: Try authentication with phone
            print("Trying authentication with phone...")
            user_auth = authenticate(request, username=phone, password=password)
            if user_auth is not None:
                print("✓ Authentication successful with phone")
                login(request, user_auth)
                print("✓ Login successful")
                return JsonResponse({
                    'status': 'success',
                    'message': 'Owner login successful with phone',
                    'step': 'phone_authentication',
                    'user': {
                        'username': user_auth.username,
                        'phone': user_auth.phone,
                        'role': user_auth.role
                    }
                })
            else:
                print("✗ Authentication failed with phone too")
                return JsonResponse({
                    'status': 'error',
                    'message': 'Authentication failed - wrong password',
                    'step': 'authentication_failed'
                })
    
    # For GET requests, show debug form
    return render(request, 'debug/owner_login_debug.html')
@login_required
def store_products(request):
    if request.user.username != 'super_owner':
        messages.error(request, 'ليس لديك صلاحية الوصول!')
        return redirect('home')
    store = Store.objects.filter(owner=request.user).first()
    if not store:
        messages.error(request, 'لا يوجد متجر مرتبط بحسابك.')
        return redirect('home')
    products = Product.objects.filter(store=store).order_by('-created_at')
    context = {
        'store': store,
        'products': products,
    }
    return render(request, 'dashboard/store/products.html', context)


@login_required
def store_orders(request):
    if request.user.username != 'super_owner':
        messages.error(request, 'ليس لديك صلاحية الوصول!')
        return redirect('home')
    store = Store.objects.filter(owner=request.user).first()
    if not store:
        messages.error(request, 'لا يوجد متجر مرتبط بحسابك.')
        return redirect('home')
    orders = Order.objects.filter(store=store).order_by('-created_at')
    if request.method == 'POST':
        order_id = request.POST.get('order_id')
        status = request.POST.get('status')
        order = get_object_or_404(Order, id=order_id, store=store)
        valid_statuses = [choice[0] for choice in Order.STATUS_CHOICES]
        if status in valid_statuses:
            order.status = status
            order.save()
            messages.success(request, f'تم تحديث حالة الطلب #{order.id}!')
        else:
            messages.error(request, 'حالة غير صحيحة!')
        return redirect('store_orders')
    context = {
        'store': store,
        'orders': orders,
    }
    return render(request, 'dashboard/store/orders.html', context)

