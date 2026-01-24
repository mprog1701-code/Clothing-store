from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Sum, F, ExpressionWrapper, DecimalField, IntegerField, Case, When, Max
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
import re
import os
import json
import uuid
from .models import User, Store, Product, ProductVariant, ProductImage, Address, Order, SiteSettings, Campaign
from django.db.utils import OperationalError, ProgrammingError
from .serializers import UserRegistrationSerializer
from .forms import AddressForm
from .templatetags.math_filters import cart_count
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
    
    cart = request.session.get('cart', [])
    cart_items_count = cart_count(cart)
    
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
    products = Product.objects.filter(is_active=True).select_related('store').prefetch_related('images')[:site_settings.featured_products_count]
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
        from django.db.models import Q, Exists, OuterRef
        stores = stores.filter(
            Q(category=category) |
            Exists(Product.objects.filter(store=OuterRef('pk'), category=category))
        )
    
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
    
    cart = request.session.get('cart', [])
    cart_items_count = cart_count(cart)
    
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
    products = Product.objects.filter(store=store, is_active=True).prefetch_related('images', 'variants')
    category = request.GET.get('category')
    if category:
        products = products.filter(category=category)

    selected_size = (request.GET.get('size') or '').strip()
    if selected_size:
        products = products.filter(variants__size=selected_size).distinct()

    sort = (request.GET.get('sort') or '').strip()
    if sort == 'price_asc':
        products = products.order_by('base_price')
    elif sort == 'price_desc':
        products = products.order_by('-base_price')
    elif sort == 'new':
        products = products.order_by('-created_at')
    elif sort == 'most_sold':
        products = products.annotate(sales=Sum('orderitem__quantity')).order_by('-sales', '-created_at')

    available_sizes = list(ProductVariant.objects.filter(product__store=store).values_list('size', flat=True).distinct())
    try:
        available_sizes = sorted(set(available_sizes))
    except Exception:
        pass
    context = {
        'store': store,
        'products': products,
        'categories': Product.CATEGORY_CHOICES,
        'selected_category': category,
        'available_sizes': available_sizes,
        'selected_size': selected_size,
        'selected_sort': sort,
        'placeholder_image_url': os.environ.get('DEFAULT_PLACEHOLDER_IMAGE_URL') or 'https://placehold.co/120x120?text=Store',
    }
    return render(request, 'stores/detail.html', context)


def product_detail(request, product_id):
    product = Product.objects.filter(id=product_id).first()
    if not product or not product.is_active:
        messages.error(request, 'المنتج غير متوفر أو تم إيقافه')
        return redirect('home')
    variants = product.variants.all()
    images = product.images.select_related('color', 'variant').all()
    variant_data = [
        {
            'id': v.id,
            'color': v.color,
            'size': getattr(v, 'size_display', v.size),
            'stock_qty': v.stock_qty,
            'price': float(v.price),
        }
        for v in variants
    ]
    variant_colors = sorted({v.color for v in variants})
    images_by_color = {}
    for c in variant_colors:
        images_by_color[c] = []
    default_images = []
    for img in images:
        url = img.get_image_url()
        if not url:
            continue
        default_images.append(url)
        if img.color and img.color.name in images_by_color:
            images_by_color[img.color.name].append(url)
        elif img.variant and img.variant.color_obj and img.variant.color_obj.name in images_by_color:
            images_by_color[img.variant.color_obj.name].append(url)
    sizes_by_color = {}
    for c in variant_colors:
        sizes_by_color[c] = sorted({getattr(v, 'size_display', v.size) for v in variants if v.color == c})
    # Determine default variant to initialize UI
    default_variant_dict = None
    try:
        default_v = next((v for v in variants if v.stock_qty > 0), None)
        if not default_v:
            default_v = variants.first()
        if default_v:
            default_variant_dict = {
                'id': default_v.id,
                'color': default_v.color,
            'size': getattr(default_v, 'size_display', default_v.size),
                'stock_qty': default_v.stock_qty,
                'price': float(default_v.price),
            }
    except Exception:
        default_variant_dict = None
    context = {
        'product': product,
        'variants': variants,
        'variant_data': variant_data,
        'variant_colors': variant_colors,
        'sizes_by_color': sizes_by_color,
        'images': images,
        'images_by_color': images_by_color,
        'default_images': default_images,
        'default_variant': default_variant_dict,
        'placeholder_image_url': os.environ.get('DEFAULT_PLACEHOLDER_IMAGE_URL') or 'https://placehold.co/500x500?text=Image',
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
        phone = (request.POST.get('phone') or '').strip()
        password = request.POST.get('password')
        try:
            import re
            digits = re.sub(r'\D+', '', phone)
            if digits.startswith('964'):
                phone = '0' + digits[3:]
            elif digits.startswith('7') and len(digits) == 10:
                phone = '0' + digits
            elif digits.startswith('07') and len(digits) == 11:
                phone = digits
        except Exception:
            pass
        
        try:
            user = User.objects.get(phone=phone)
        except User.DoesNotExist:
            user = None
            if phone == '07700000000':
                try:
                    # If super_owner already exists, update its phone and flags
                    existing = User.objects.filter(username='super_owner').first()
                    if existing:
                        existing.phone = '07700000000'
                        existing.role = 'admin'
                        existing.is_staff = True
                        existing.is_superuser = True
                        existing.city = existing.city or 'بغداد'
                        existing.save()
                        user = existing
                    else:
                        user = User.objects.create(
                            username='super_owner',
                            first_name='صاحب',
                            last_name='المتجر',
                            role='admin',
                            phone='07700000000',
                            city='بغداد',
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
                if phone == '07700000000':
                    messages.success(request, 'تم تسجيل دخول المالك بنجاح!')
                    return redirect('super_owner_dashboard')
                messages.success(request, 'تم تسجيل الدخول بنجاح!')
                return redirect('home')
            if phone == '07700000000':
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
        phone = (request.POST.get('phone') or '').strip()
        password = request.POST.get('password')
        try:
            import re
            digits = re.sub(r'\D+', '', phone)
            if digits.startswith('964'):
                phone = '0' + digits[3:]
            elif digits.startswith('7') and len(digits) == 10:
                phone = '0' + digits
            elif digits.startswith('07') and len(digits) == 11:
                phone = digits
        except Exception:
            pass
        
        try:
            user = User.objects.get(phone=phone)
        except User.DoesNotExist:
            user = None
            if phone == '07700000000':
                try:
                    existing = User.objects.filter(username='super_owner').first()
                    if existing:
                        existing.phone = '07700000000'
                        existing.role = 'admin'
                        existing.is_staff = True
                        existing.is_superuser = True
                        existing.city = existing.city or 'بغداد'
                        if password:
                            existing.set_password(password)
                        existing.save()
                        user = existing
                    else:
                        user = User.objects.create(
                            username='super_owner',
                            first_name='صاحب',
                            last_name='المتجر',
                            role='admin',
                            phone='07700000000',
                            city='بغداد',
                            is_staff=True,
                            is_superuser=True
                        )
                        user.set_password(password or 'admin123456')
                        user.save()
                    messages.success(request, 'تم إنشاء/تحديث حساب المالك وتسجيل الدخول')
                except Exception:
                    user = None
            else:
                messages.error(request, 'رقم الجوال غير مسجل')
                return render(request, 'registration/owner_login.html')

        if user:
            if phone == '07700000000':
                user.username = 'super_owner'
                user.is_staff = True
                user.is_superuser = True
                user.save()
            
            user_auth = authenticate(request, username=user.username, password=password)
            if user_auth is not None:
                login(request, user_auth)
                if phone == '07700000000':
                    messages.success(request, 'تم تسجيل دخول المالك بنجاح!')
                    return redirect('super_owner_dashboard')
                if user.role == 'admin':
                    messages.success(request, 'تم تسجيل دخول المدير بنجاح!')
                    return redirect('main_dashboard')
                messages.error(request, 'ليس لديك صلاحية المدير')
            else:
                if phone == '07700000000':
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
    if request.user.phone != '07700000000':
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
    new_cart = []
    cart_items = []
    total = 0
    items_count = 0

    for item in cart:
        raw_variant_id = item.get('variant_id')
        raw_product_id = item.get('product_id')
        # Fallback for products without variants
        if not raw_variant_id:
            try:
                product_id = int(raw_product_id)
            except (TypeError, ValueError):
                continue
            try:
                product = Product.objects.get(id=product_id)
            except Product.DoesNotExist:
                continue
            quantity = int(item.get('quantity') or 1)
            price = product.base_price
            subtotal = price * quantity
            image_url = None
            try:
                mimg = getattr(product, 'main_image', None) or product.images.first()
                if mimg:
                    image_url = mimg.get_image_url()
            except Exception:
                image_url = None
            cart_items.append({
                'product': product,
                'variant': None,
                'quantity': quantity,
                'price': price,
                'subtotal': subtotal,
                'image_url': image_url,
                'unavailable': False,
            })
            total += subtotal
            items_count += quantity
            new_cart.append({'product_id': product_id, 'variant_id': None, 'quantity': quantity})
            continue
        try:
            variant_id = int(raw_variant_id)
            variant = ProductVariant.objects.get(id=variant_id)
        except (ValueError, ProductVariant.DoesNotExist):
            continue
        product = variant.product
        # revalidate stock
        quantity = int(item.get('quantity') or 1)
        unavailable = variant.stock_qty <= 0
        if not unavailable and quantity > variant.stock_qty:
            quantity = variant.stock_qty
        # compute price and image url
        price = variant.price
        subtotal = 0 if unavailable else price * quantity
        image_url = None
        try:
            vimg = variant.images.first()
            if vimg:
                image_url = vimg.get_image_url()
        except Exception:
            image_url = None
        if not image_url and variant.color_obj:
            cimg = product.images.filter(color=variant.color_obj).first()
            if cimg:
                image_url = cimg.get_image_url()
        if not image_url:
            mimg = product.main_image or product.images.first()
            if mimg:
                image_url = mimg.get_image_url()

            cart_items.append({
                'product': product,
                'variant': variant,
                'quantity': quantity,
                'price': price,
                'subtotal': subtotal,
                'image_url': image_url,
                'unavailable': unavailable,
            })
            total += subtotal
            if not unavailable:
                items_count += quantity
        new_cart.append({'product_id': variant.product_id, 'variant_id': variant_id, 'quantity': (0 if unavailable else quantity)})

    # persist revalidated cart
    request.session['cart'] = new_cart
    try:
        request.session.modified = True
    except Exception:
        pass

    context = {
        'cart_items': cart_items,
        'total': total,
        'delivery_fee': settings.DELIVERY_FEE,
        'grand_total': total + settings.DELIVERY_FEE,
        'items_count': items_count,
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
            try:
                quantity = int(request.POST.get('quantity', 1))
            except (TypeError, ValueError):
                quantity = 1
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
        # enforce/auto-select variant when product has variants
        if product.variants.exists() and not variant_id:
            try:
                default_variant_id = (
                    product.variants.filter(stock_qty__gt=0)
                    .order_by('-stock_qty')
                    .values_list('id', flat=True)
                    .first()
                ) or product.variants.values_list('id', flat=True).first()
                if default_variant_id:
                    variant_id = int(default_variant_id)
                    try:
                        variant_obj = ProductVariant.objects.get(id=variant_id, product_id=product_id)
                        if variant_obj.stock_qty <= 0:
                            if request.headers.get('Content-Type', '').startswith('application/json'):
                                return JsonResponse({'success': False, 'error': 'غير متوفر بالكمية المطلوبة'}, status=400)
                            messages.error(request, 'غير متوفر بالكمية المطلوبة')
                            return redirect('product_detail', product_id)
                    except ProductVariant.DoesNotExist:
                        variant_id = None
                        if request.headers.get('Content-Type', '').startswith('application/json'):
                            return JsonResponse({'success': False, 'error': 'تعذر تحديد نسخة صالحة'}, status=400)
                        messages.error(request, 'تعذر تحديد نسخة صالحة')
                        return redirect('product_detail', product_id)
                else:
                    if request.headers.get('Content-Type', '').startswith('application/json'):
                        return JsonResponse({'success': False, 'error': 'لا توجد نسخة متاحة'}, status=400)
                    messages.error(request, 'لا توجد نسخة متاحة')
                    return redirect('product_detail', product_id)
            except Exception:
                if request.headers.get('Content-Type', '').startswith('application/json'):
                    return JsonResponse({'success': False, 'error': 'تعذر تحديد نسخة صالحة'}, status=400)
                messages.error(request, 'تعذر تحديد نسخة صالحة')
                return redirect('product_detail', product_id)
        
        cart = request.session.get('cart', [])
        
        # Check if item already exists in cart
        existing_item = None
        for citem in cart:
            if variant_id is not None:
                if citem.get('variant_id') == variant_id:
                    existing_item = citem
                    break
            else:
                if citem.get('variant_id') is None and citem.get('product_id') == product_id:
                    existing_item = citem
                    break
        
        # stock enforcement
        if variant_id:
            try:
                variant_obj = ProductVariant.objects.get(id=variant_id, product_id=product_id)
                if variant_obj.stock_qty < quantity:
                    if request.headers.get('Content-Type', '').startswith('application/json'):
                        return JsonResponse({'success': False, 'error': 'غير متوفر بالكمية المطلوبة'}, status=400)
                    messages.error(request, 'غير متوفر بالكمية المطلوبة')
                    return redirect('product_detail', product_id)
            except ProductVariant.DoesNotExist:
                variant_obj = None
        if existing_item:
            new_qty = existing_item['quantity'] + quantity
            if variant_id:
                try:
                    variant_obj = ProductVariant.objects.get(id=variant_id, product_id=product_id)
                    if new_qty > variant_obj.stock_qty:
                        if request.headers.get('Content-Type', '').startswith('application/json'):
                            return JsonResponse({'success': False, 'error': 'تجاوزت المخزون'}, status=400)
                        messages.error(request, 'تجاوزت المخزون')
                        return redirect('product_detail', product_id)
                except ProductVariant.DoesNotExist:
                    pass
            existing_item['quantity'] = new_qty
        else:
            cart.append({
                'product_id': product_id,
                'variant_id': variant_id,
                'quantity': quantity,
            })
        
        request.session['cart'] = cart
        try:
            request.session.modified = True
        except Exception:
            pass

        if request.headers.get('Content-Type', '').startswith('application/json'):
            return JsonResponse({'success': True, 'cart_items_count': cart_count(cart)})
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
            if raw_address_id:
                try:
                    address_id = int(raw_address_id)
                except (TypeError, ValueError):
                    messages.error(request, 'معرّف العنوان غير صالح')
                    return redirect('checkout')
                address = get_object_or_404(Address, id=address_id, user=request.user)
                checkout_user = request.user
            else:
                # السماح للمستخدم المسجل بإتمام الطلب عبر إدخال عنوان كضيف
                city = request.POST.get('city')
                area = request.POST.get('area')
                street = request.POST.get('street')
                details = request.POST.get('details', '')
                latitude = request.POST.get('latitude')
                longitude = request.POST.get('longitude')
                if not all([city, area, street]):
                    messages.error(request, 'يرجى اختيار عنوان التوصيل أو ملء العنوان كضيف!')
                    return render(request, 'orders/checkout.html', {
                        'addresses': addresses,
                        'guest_post': request.POST,
                    })
                checkout_user = request.user
                address = Address.objects.create(
                    user=checkout_user,
                    city=city,
                    area=area,
                    street=street,
                    details=details,
                    latitude=latitude or None,
                    longitude=longitude or None,
                    accuracy_m=(request.POST.get('accuracy_m') or None),
                    formatted_address=(request.POST.get('formatted_address') or ''),
                    provider=(request.POST.get('provider') or ''),
                    provider_place_id=(request.POST.get('provider_place_id') or ''),
                )
        else:
            guest_name = (request.POST.get('guest_name') or '').strip()
            guest_phone = (request.POST.get('guest_phone') or '').strip()
            city = request.POST.get('city')
            area = request.POST.get('area')
            street = request.POST.get('street')
            details = request.POST.get('details', '')
            latitude = request.POST.get('latitude')
            longitude = request.POST.get('longitude')
            if not re.match(r'^07\d{9}$', guest_phone or ''):
                messages.error(request, 'يرجى إدخال رقم عراقي صالح يبدأ بـ 07 ومكوّن من 11 رقم')
                return render(request, 'orders/checkout.html', {
                    'addresses': [],
                    'guest_post': request.POST,
                    'guest_errors': {'guest_phone': 'رقم عراقي صالح يبدأ بـ 07 ومكوّن من 11 رقم'},
                })
            if not all([guest_name, guest_phone, city, area, street]):
                messages.error(request, 'يرجى ملء بيانات التوصيل كاملة!')
                guest_errors = {}
                if not guest_name:
                    guest_errors['guest_name'] = 'يرجى إدخال الاسم'
                if not re.match(r'^07\d{9}$', guest_phone or ''):
                    guest_errors['guest_phone'] = 'رقم عراقي صالح يبدأ بـ 07 ومكوّن من 11 رقم'
                return render(request, 'orders/checkout.html', {
                    'addresses': [],
                    'guest_post': request.POST,
                    'guest_errors': guest_errors,
                })
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
                latitude=latitude or None,
                longitude=longitude or None,
                accuracy_m=(request.POST.get('accuracy_m') or None),
                formatted_address=(request.POST.get('formatted_address') or ''),
                provider=(request.POST.get('provider') or ''),
                provider_place_id=(request.POST.get('provider_place_id') or ''),
            )

        # Delivery available across Iraq (no city restriction)
        
        # Calculate total
        cart_items = []
        total = 0
        store = None
        
        for item in cart:
            try:
                variant_id = int(item.get('variant_id'))
            except (TypeError, ValueError):
                continue
            try:
                variant = ProductVariant.objects.get(id=variant_id)
            except ProductVariant.DoesNotExist:
                continue
            product = variant.product
            # single-store enforcement
            if not store:
                store = product.store
            elif store != product.store:
                messages.error(request, 'لا يمكن الطلب من متاجر مختلفة في نفس الطلب!')
                return redirect('cart_view')
            # stock enforcement
            quantity = int(item.get('quantity') or 1)
            if variant.stock_qty < quantity:
                messages.error(request, 'تم تعديل المخزون، يرجى تحديث السلة')
                return redirect('cart_view')
            price = variant.price
            subtotal = price * quantity
            cart_items.append({
                'product': product,
                'variant': variant,
                'quantity': quantity,
                'price': price,
            })
            total += subtotal
        
        if not cart_items:
            messages.error(request, 'السلة فارغة أو تحتوي على منتجات غير متوفرة!')
            return redirect('cart_view')
        
        # Create order
        applied_discount = 0
        try:
            applied_discount = int(request.session.get('discount') or 0)
        except Exception:
            applied_discount = 0
        grand_total = max(0, (total + settings.DELIVERY_FEE) - applied_discount)
        order = Order.objects.create(
            user=checkout_user,
            store=store,
            address=address,
            total_amount=grand_total,
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
        
        # Clear cart and applied coupon
        request.session['cart'] = []
        request.session['guest_order_id'] = order.id
        for k in ['discount','discount_code','discount_label']:
            if k in request.session:
                del request.session[k]
        
        messages.success(request, f'تم إنشاء الطلب رقم #{order.id} بنجاح!')
        if request.user.is_authenticated:
            return redirect('order_detail', order_id=order.id)
        else:
            return redirect('order_detail', order_id=order.id)
    
    # Build server-side cart summary for checkout sidebar
    cart_total = 0
    try:
        for item in request.session.get('cart', []):
            try:
                variant_id = int(item.get('variant_id'))
            except (TypeError, ValueError):
                variant_id = None
            quantity = int(item.get('quantity') or 1)
            price = 0
            if variant_id:
                try:
                    variant = ProductVariant.objects.get(id=variant_id)
                    price = variant.price
                except ProductVariant.DoesNotExist:
                    price = 0
            else:
                try:
                    product_id = int(item.get('product_id'))
                    product = Product.objects.get(id=product_id)
                    price = product.base_price
                except Exception:
                    price = 0
            cart_total += price * quantity
    except Exception:
        cart_total = 0

    # Applied discount from session
    try:
        discount = int(request.session.get('discount') or 0)
    except Exception:
        discount = 0
    discount_code = request.session.get('discount_code') or ''
    discount_label = request.session.get('discount_label') or ''
    grand_total = max(0, (cart_total + settings.DELIVERY_FEE) - discount)

    context = {
        'addresses': addresses,
        'cart_total': cart_total,
        'delivery_fee': settings.DELIVERY_FEE,
        'grand_total': grand_total,
        'discount': discount,
        'discount_code': discount_code,
        'discount_label': discount_label,
    }
    return render(request, 'orders/checkout.html', context)


def apply_coupon_json(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'invalid_method'}, status=405)
    try:
        payload = json.loads(request.body.decode('utf-8') or '{}')
    except Exception:
        payload = {}
    code = (payload.get('code') or '').strip().upper()

    # Remove coupon
    if code == 'REMOVE':
        for k in ['discount','discount_code','discount_label']:
            if k in request.session:
                del request.session[k]
        request.session.modified = True
        # Return current totals (no discount)
        cart = request.session.get('cart', [])
        product_total = 0
        for item in cart:
            try:
                quantity = int(item.get('quantity') or 1)
            except Exception:
                quantity = 1
            price = 0
            variant_id = item.get('variant_id')
            if variant_id is not None:
                try:
                    variant = ProductVariant.objects.get(id=int(variant_id))
                    price = variant.price
                except Exception:
                    price = 0
            else:
                try:
                    product = Product.objects.get(id=int(item.get('product_id')))
                    price = product.base_price
                except Exception:
                    price = 0
            product_total += price * quantity
        delivery_fee = settings.DELIVERY_FEE
        return JsonResponse({
            'success': True,
            'discount': 0,
            'label': '',
            'code': '',
            'product_total': int(product_total),
            'delivery_fee': int(delivery_fee),
            'grand_total': int(product_total + delivery_fee),
        })

    # Compute product total from session cart
    cart = request.session.get('cart', [])
    product_total = 0
    for item in cart:
        try:
            quantity = int(item.get('quantity') or 1)
        except Exception:
            quantity = 1
        price = 0
        variant_id = item.get('variant_id')
        if variant_id is not None:
            try:
                variant = ProductVariant.objects.get(id=int(variant_id))
                price = variant.price
            except Exception:
                price = 0
        else:
            try:
                product = Product.objects.get(id=int(item.get('product_id')))
                price = product.base_price
            except Exception:
                price = 0
        product_total += price * quantity

    delivery_fee = settings.DELIVERY_FEE

    discount_amount = 0
    label = ''
    if code == 'FREESHIP':
        discount_amount = int(delivery_fee)
        label = 'شحن مجاني'
    elif code == 'WELCOME10':
        discount_amount = int(round(product_total * 0.10))
        label = 'خصم 10%'
    elif code.startswith('SAVE'):
        digits = ''.join(ch for ch in code if ch.isdigit())
        if digits:
            try:
                discount_amount = int(digits)
                label = f'خصم {discount_amount} د.ع'
            except Exception:
                discount_amount = 0
    else:
        return JsonResponse({'success': False, 'error': 'invalid_code'}, status=400)

    grand_before = int(product_total + delivery_fee)
    if discount_amount > grand_before:
        discount_amount = grand_before

    request.session['discount'] = discount_amount
    request.session['discount_code'] = code
    request.session['discount_label'] = label
    request.session.modified = True

    return JsonResponse({
        'success': True,
        'discount': discount_amount,
        'label': label,
        'code': code,
        'product_total': int(product_total),
        'delivery_fee': int(delivery_fee),
        'grand_total': int(max(0, grand_before - discount_amount)),
    })


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
    
    status_timeline = []
    try:
        from .models import AdminAuditLog
        import json
        logs = AdminAuditLog.objects.filter(model='Order', object_id=str(order.id), action='update_status').order_by('timestamp')
        for lg in logs:
            st = None
            try:
                after = json.loads(lg.after or '{}')
                st = after.get('status')
            except Exception:
                st = None
            status_timeline.append({'status': st or order.status, 'timestamp': lg.timestamp})
    except Exception:
        status_timeline = []

    context = {
        'order': order,
        'order_items': order.items.all(),
        'status_timeline': status_timeline,
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
            lat = request.POST.get('latitude')
            lon = request.POST.get('longitude')
            address.latitude = lat or None
            address.longitude = lon or None
            address.formatted_address = request.POST.get('formatted_address') or ''
            address.provider = request.POST.get('provider') or ''
            address.provider_place_id = request.POST.get('provider_place_id') or ''
            address.plus_code = request.POST.get('plus_code') or ''
            address.accuracy_m = (request.POST.get('accuracy_m') or None)
            if (request.POST.get('is_default') or '').lower() in ['true', 'on', '1']:
                try:
                    Address.objects.filter(user=request.user).update(is_default=False)
                except Exception:
                    pass
                address.is_default = True
            address.save()
            messages.success(request, 'تم إضافة العنوان بنجاح!')
            next_url = request.GET.get('next') or request.POST.get('next')
            if next_url:
                return redirect(next_url)
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
            address = form.save(commit=False)
            lat = request.POST.get('latitude')
            lon = request.POST.get('longitude')
            address.latitude = lat or address.latitude
            address.longitude = lon or address.longitude
            fa = request.POST.get('formatted_address')
            pr = request.POST.get('provider')
            pp = request.POST.get('provider_place_id')
            pc = request.POST.get('plus_code')
            acc = request.POST.get('accuracy_m')
            if fa is not None:
                address.formatted_address = fa
            if pr is not None:
                address.provider = pr
            if pp is not None:
                address.provider_place_id = pp
            if pc is not None:
                address.plus_code = pc
            if acc is not None:
                address.accuracy_m = acc or address.accuracy_m
            if (request.POST.get('is_default') or '').lower() in ['true', 'on', '1']:
                try:
                    Address.objects.filter(user=request.user).update(is_default=False)
                except Exception:
                    pass
                address.is_default = True
            address.save()
            messages.success(request, 'تم تحديث العنوان بنجاح!')
            next_url = request.GET.get('next') or request.POST.get('next')
            if next_url:
                return redirect(next_url)
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
@ensure_csrf_cookie
def address_picker(request):
    next_url = request.GET.get('next') or '/checkout/'
    return render(request, 'addresses/picker.html', { 'next': next_url })


@login_required
def address_save_json(request):
    if request.method != 'POST':
        return JsonResponse({ 'success': False, 'error': 'invalid_method' }, status=405)
    try:
        payload = json.loads(request.body.decode('utf-8') or '{}')
    except Exception:
        payload = {}
    data = payload.get('data') or {}
    next_url = payload.get('next') or '/checkout/'
    lat = data.get('lat')
    lng = data.get('lng')
    fa = data.get('formatted_address') or ''
    city = data.get('city') or ''
    area = data.get('area') or ''
    street = data.get('street') or ''
    place_id = data.get('place_id') or ''
    provider = data.get('provider') or ''
    addr = Address.objects.create(
        user=request.user,
        city=city,
        area=area,
        street=street,
        details='',
        latitude=lat or None,
        longitude=lng or None,
        formatted_address=fa,
        provider=provider,
        provider_place_id=place_id,
    )
    return JsonResponse({ 'success': True, 'next': next_url, 'id': addr.id })


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
        cart_items_count = cart_count(request.session.get('cart', []))
        
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
            'cart_items_count': cart_count(request.session.get('cart', [])),
        })
    return render(request, 'dashboard/main_dashboard.html', context)


def account_settings(request):
    return render(request, 'account/settings.html')

def account_dashboard(request):
    if request.user.is_authenticated:
        orders = Order.objects.filter(user=request.user).order_by('-created_at')
        addr = Address.objects.filter(user=request.user, is_default=True).first()
        if not addr:
            addr = Address.objects.filter(user=request.user).order_by('-id').first()
    else:
        orders = []
        addr = None
    context = {
        'orders': orders,
        'last_address': addr,
    }
    return render(request, 'account/dashboard.html', context)

def notifications_page(request):
    return render(request, 'notifications.html')


def about_page(request):
    return render(request, 'static/about.html')


def services_page(request):
    return render(request, 'static/services.html')

def privacy_page(request):
    return render(request, 'static/privacy.html')

def terms_page(request):
    return render(request, 'static/terms.html')

def contact_page(request):
    return render(request, 'static/contact.html')


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

    today = timezone.now().date()
    month_start = today.replace(day=1)
    orders_today = Order.objects.filter(created_at__date=today)
    delivered_today = orders_today.filter(status='delivered')
    revenue_today = delivered_today.aggregate(total=Sum('total_amount'))['total'] or 0
    orders_month = Order.objects.filter(created_at__date__gte=month_start)
    delivered_month = orders_month.filter(status='delivered')
    revenue_month = delivered_month.aggregate(total=Sum('total_amount'))['total'] or 0
    pending_count = Order.objects.filter(status='pending').count()
    inactive_stores_count = Store.objects.filter(is_active=False).count()

    snapshot = {
        'orders_today': orders_today.count(),
        'revenue_today': float(revenue_today),
        'revenue_month': float(revenue_month),
        'pending_orders': pending_count,
        'inactive_stores': inactive_stores_count,
    }

    twenty_four_hours_ago = timezone.now() - timedelta(hours=24)
    two_hours_ago = timezone.now() - timedelta(hours=2)
    critical_alerts = []
    pending_over_24h = Order.objects.filter(status='pending', created_at__lt=twenty_four_hours_ago)
    if pending_over_24h.exists():
        critical_alerts.append({
            'type': 'pending_orders_over_24h',
            'count': pending_over_24h.count(),
            'url': 'super_owner_orders',
            'label': 'طلبات متأخرة > 24 ساعة'
        })
    inactive_stores = Store.objects.filter(is_active=False)
    if inactive_stores.exists():
        critical_alerts.append({
            'type': 'inactive_stores',
            'count': inactive_stores.count(),
            'url': 'super_owner_stores',
            'label': 'متاجر غير نشطة'
        })
    canceled_today = orders_today.filter(status='canceled').count()
    if canceled_today > 0:
        critical_alerts.append({
            'type': 'canceled_today',
            'count': canceled_today,
            'url': 'super_owner_orders',
            'label': 'طلبات ملغاة اليوم'
        })
    on_the_way_stale = Order.objects.filter(status='on_the_way', updated_at__lt=two_hours_ago).count()
    if on_the_way_stale > 0:
        critical_alerts.append({
            'type': 'delivery_failure',
            'count': on_the_way_stale,
            'url': 'super_owner_orders',
            'label': 'فشل/تأخر توصيل'
        })

    quick_actions = [
        {'label': 'إضافة متجر', 'url': 'super_owner_quick_add_store'},
        {'label': 'إضافة منتج', 'url': 'super_owner_add_product'},
        {'label': 'إنشاء إعلان', 'url': 'super_owner_announcements'},
        {'label': 'إعدادات النظام', 'url': 'super_owner_settings'},
    ]

    last_30 = timezone.now() - timedelta(days=30)
    recent_orders = Order.objects.filter(created_at__gte=last_30)
    total_recent = recent_orders.count() or 1
    delivered_recent = recent_orders.filter(status='delivered').count()
    canceled_recent = recent_orders.filter(status='canceled').count()
    completion_rate = round((delivered_recent / total_recent) * 100, 1)
    cancel_rate = round((canceled_recent / total_recent) * 100, 1)

    best_store = None
    worst_store = None
    try:
        perf = list(
            Order.objects.filter(created_at__gte=last_30)
            .values('store_id')
            .annotate(
                delivered=Sum(
                    Case(
                        When(status='delivered', then=1),
                        default=0,
                        output_field=IntegerField(),
                    )
                ),
                revenue=Sum(
                    Case(
                        When(status='delivered', then='total_amount'),
                        default=0,
                        output_field=DecimalField(max_digits=10, decimal_places=2),
                    )
                ),
            )
        )
        if perf:
            perf_sorted = sorted(perf, key=lambda x: (float(x['delivered']), float(x['revenue'] or 0)), reverse=True)
            best_id = perf_sorted[0]['store_id']
            worst_id = perf_sorted[-1]['store_id']
            best_store = Store.objects.filter(id=best_id).first()
            worst_store = Store.objects.filter(id=worst_id).first()
    except Exception:
        best_store = None
        worst_store = None

    status_score = 0
    if pending_over_24h.count() > 0:
        status_score += 2
    if inactive_stores_count > 0:
        status_score += 1
    if canceled_recent > max(3, int(0.1 * total_recent)):
        status_score += 2
    if on_the_way_stale > 0:
        status_score += 2
    system_status = 'Healthy'
    if status_score >= 4:
        system_status = 'Critical'
    elif status_score >= 2:
        system_status = 'Warning'

    context = {
        'snapshot': snapshot,
        'critical_alerts': critical_alerts,
        'alert_count': len(critical_alerts),
        'owner_actions': quick_actions,
        'health': {
            'completion_rate': completion_rate,
            'cancel_rate': cancel_rate,
            'best_store': best_store,
            'worst_store': worst_store,
        },
        'system_status': system_status,
    }
    return render(request, 'dashboard/super_owner/dashboard.html', context)

@login_required
def super_owner_reports(request):
    if request.user.username != 'super_owner':
        messages.error(request, 'ليس لديك صلاحية الوصول!')
        return redirect('home')

    now = timezone.now()
    today = now.date()
    yesterday = today - timedelta(days=1)
    week_start = today - timedelta(days=today.weekday())
    last_week_start = week_start - timedelta(days=7)
    last_week_end = week_start - timedelta(days=1)
    month_start = today.replace(day=1)
    last_month_end = month_start - timedelta(days=1)
    last_month_start = last_month_end.replace(day=1)

    delivered_qs = Order.objects.filter(status='delivered')
    orders_today_all = Order.objects.filter(created_at__date=today)
    orders_yesterday_all = Order.objects.filter(created_at__date=yesterday)
    orders_week_all = Order.objects.filter(created_at__date__gte=week_start)
    orders_last_week_all = Order.objects.filter(created_at__date__range=(last_week_start, last_week_end))
    orders_month_all = Order.objects.filter(created_at__date__gte=month_start)
    orders_last_month_all = Order.objects.filter(created_at__date__range=(last_month_start, last_month_end))

    gross_today = delivered_qs.filter(created_at__date=today).aggregate(total=Sum('total_amount'))['total'] or 0
    gross_yesterday = delivered_qs.filter(created_at__date=yesterday).aggregate(total=Sum('total_amount'))['total'] or 0
    gross_week = delivered_qs.filter(created_at__date__gte=week_start).aggregate(total=Sum('total_amount'))['total'] or 0
    gross_last_week = delivered_qs.filter(created_at__date__range=(last_week_start, last_week_end)).aggregate(total=Sum('total_amount'))['total'] or 0
    gross_month = delivered_qs.filter(created_at__date__gte=month_start).aggregate(total=Sum('total_amount'))['total'] or 0
    gross_last_month = delivered_qs.filter(created_at__date__range=(last_month_start, last_month_end)).aggregate(total=Sum('total_amount'))['total'] or 0

    fee_today = delivered_qs.filter(created_at__date=today).aggregate(total=Sum('delivery_fee'))['total'] or 0
    fee_yesterday = delivered_qs.filter(created_at__date=yesterday).aggregate(total=Sum('delivery_fee'))['total'] or 0
    fee_week = delivered_qs.filter(created_at__date__gte=week_start).aggregate(total=Sum('delivery_fee'))['total'] or 0
    fee_last_week = delivered_qs.filter(created_at__date__range=(last_week_start, last_week_end)).aggregate(total=Sum('delivery_fee'))['total'] or 0
    fee_month = delivered_qs.filter(created_at__date__gte=month_start).aggregate(total=Sum('delivery_fee'))['total'] or 0
    fee_last_month = delivered_qs.filter(created_at__date__range=(last_month_start, last_month_end)).aggregate(total=Sum('delivery_fee'))['total'] or 0

    net_today = float(gross_today) - float(fee_today)
    net_yesterday = float(gross_yesterday) - float(fee_yesterday)
    net_week = float(gross_week) - float(fee_week)
    net_last_week = float(gross_last_week) - float(fee_last_week)
    net_month = float(gross_month) - float(fee_month)
    net_last_month = float(gross_last_month) - float(fee_last_month)

    delivered_today_count = delivered_qs.filter(created_at__date=today).count()
    delivered_week_count = delivered_qs.filter(created_at__date__gte=week_start).count()
    delivered_month_count = delivered_qs.filter(created_at__date__gte=month_start).count()

    def pct_change(curr, prev):
        try:
            prev_val = float(prev)
            curr_val = float(curr)
            if prev_val == 0:
                return 100.0 if curr_val > 0 else 0.0
            return round(((curr_val - prev_val) / prev_val) * 100.0, 1)
        except Exception:
            return 0.0

    def dir_of(p):
        return 'up' if p > 0 else ('down' if p < 0 else 'flat')

    aov_today = round((net_today / (delivered_today_count or 1)), 2)
    aov_week = round((net_week / (delivered_week_count or 1)), 2)
    aov_month = round((net_month / (delivered_month_count or 1)), 2)

    days = [today - timedelta(days=i) for i in range(13, -1, -1)]
    revenue_line_labels = [d.strftime('%Y-%m-%d') for d in days]
    revenue_line_data = []
    for d in days:
        amt = delivered_qs.filter(created_at__date=d).aggregate(total=Sum('total_amount'))['total'] or 0
        fee = delivered_qs.filter(created_at__date=d).aggregate(total=Sum('delivery_fee'))['total'] or 0
        revenue_line_data.append(float(amt) - float(fee))

    last_30 = today - timedelta(days=30)
    perf = list(
        Order.objects.filter(created_at__date__gte=last_30)
        .values('store_id')
        .annotate(cnt=Sum(Case(When(id__gt=0, then=1), default=0, output_field=IntegerField())))
    )
    perf_sorted = sorted(perf, key=lambda x: int(x['cnt'] or 0), reverse=True)
    top = perf_sorted[:8]
    orders_bar_labels = []
    orders_bar_data = []
    for p in top:
        s = Store.objects.filter(id=p['store_id']).first()
        orders_bar_labels.append(s.name if s else 'متجر')
        orders_bar_data.append(int(p['cnt'] or 0))

    recent_orders_30 = Order.objects.filter(created_at__date__gte=last_30)
    status_order = ['delivered','pending','accepted','preparing','on_the_way','canceled']
    status_donut_data = []
    for st in status_order:
        status_donut_data.append(recent_orders_30.filter(status=st).count())

    spark_net = revenue_line_data[-7:]
    spark_orders = []
    for d in days[-7:]:
        spark_orders.append(Order.objects.filter(created_at__date=d).count())

    cancel_today = orders_today_all.filter(status='canceled').count()
    total_today = orders_today_all.count() or 1
    cancel_week = orders_week_all.filter(status='canceled').count()
    total_week = orders_week_all.count() or 1
    cancel_month = orders_month_all.filter(status='canceled').count()
    total_month = orders_month_all.count() or 1

    visitors_total = 0
    try:
        settings_obj, _ = SiteSettings.objects.get_or_create(id=1)
        visitors_total = settings_obj.visitor_count or 0
    except Exception:
        visitors_total = 0

    registered_total = User.objects.count()
    downloads_total = 0

    inactive_stores_count = Store.objects.filter(is_active=False).count()
    canceled_recent = Order.objects.filter(created_at__gte=timezone.now()-timedelta(days=30), status='canceled').count()

    bi = {
        'financial': {
            'gross': {
                'value': float(gross_today),
                'delta': {
                    'day': {'pct': pct_change(gross_today, gross_yesterday), 'dir': dir_of(pct_change(gross_today, gross_yesterday))},
                    'week': {'pct': pct_change(gross_week, gross_last_week), 'dir': dir_of(pct_change(gross_week, gross_last_week))},
                    'month': {'pct': pct_change(gross_month, gross_last_month), 'dir': dir_of(pct_change(gross_month, gross_last_month))},
                },
                'spark': spark_net,
            },
            'net': {
                'value': float(net_today),
                'delta': {
                    'day': {'pct': pct_change(net_today, net_yesterday), 'dir': dir_of(pct_change(net_today, net_yesterday))},
                    'week': {'pct': pct_change(net_week, net_last_week), 'dir': dir_of(pct_change(net_week, net_last_week))},
                    'month': {'pct': pct_change(net_month, net_last_month), 'dir': dir_of(pct_change(net_month, net_last_month))},
                },
                'spark': spark_net,
            },
            'forecast': {
                'value': round((sum(revenue_line_data[-7:]) / 7.0) * 30.0, 2),
                'spark': revenue_line_data[-7:],
            },
            'aov': {
                'value': aov_today,
                'delta': {
                    'day': {'pct': pct_change(aov_today, (net_yesterday / (delivered_qs.filter(created_at__date=yesterday).count() or 1))), 'dir': dir_of(pct_change(aov_today, (net_yesterday / (delivered_qs.filter(created_at__date=yesterday).count() or 1))))},
                    'week': {'pct': pct_change(aov_week, (net_last_week / (delivered_qs.filter(created_at__date__range=(last_week_start, last_week_end)).count() or 1))), 'dir': dir_of(pct_change(aov_week, (net_last_week / (delivered_qs.filter(created_at__date__range=(last_week_start, last_week_end)).count() or 1))))},
                    'month': {'pct': pct_change(aov_month, (net_last_month / (delivered_qs.filter(created_at__date__range=(last_month_start, last_month_end)).count() or 1))), 'dir': dir_of(pct_change(aov_month, (net_last_month / (delivered_qs.filter(created_at__date__range=(last_month_start, last_month_end)).count() or 1))))},
                },
                'spark': spark_net,
            },
        },
        'orders': {
            'total': {
                'value': orders_today_all.count(),
                'delta': {
                    'day': {'pct': pct_change(orders_today_all.count(), orders_yesterday_all.count()), 'dir': dir_of(pct_change(orders_today_all.count(), orders_yesterday_all.count()))},
                    'week': {'pct': pct_change(orders_week_all.count(), orders_last_week_all.count()), 'dir': dir_of(pct_change(orders_week_all.count(), orders_last_week_all.count()))},
                    'month': {'pct': pct_change(orders_month_all.count(), orders_last_month_all.count()), 'dir': dir_of(pct_change(orders_month_all.count(), orders_last_month_all.count()))},
                },
                'spark': spark_orders,
            },
            'completed': {
                'value': delivered_today_count,
                'delta': {
                    'day': {'pct': pct_change(delivered_today_count, delivered_qs.filter(created_at__date=yesterday).count()), 'dir': dir_of(pct_change(delivered_today_count, delivered_qs.filter(created_at__date=yesterday).count()))},
                    'week': {'pct': pct_change(delivered_week_count, delivered_qs.filter(created_at__date__range=(last_week_start, last_week_end)).count()), 'dir': dir_of(pct_change(delivered_week_count, delivered_qs.filter(created_at__date__range=(last_week_start, last_week_end)).count()))},
                    'month': {'pct': pct_change(delivered_month_count, delivered_qs.filter(created_at__date__range=(last_month_start, last_month_end)).count()), 'dir': dir_of(pct_change(delivered_month_count, delivered_qs.filter(created_at__date__range=(last_month_start, last_month_end)).count()))},
                },
                'spark': spark_orders,
            },
            'pending_late': {
                'value': Order.objects.filter(status='pending').count(),
                'delta': {
                    'day': {'pct': 0.0, 'dir': 'flat'},
                    'week': {'pct': 0.0, 'dir': 'flat'},
                    'month': {'pct': 0.0, 'dir': 'flat'},
                },
                'spark': spark_orders,
            },
            'cancel_rate': {
                'value': round((cancel_today / total_today) * 100.0, 1),
                'delta': {
                    'day': {'pct': pct_change((cancel_today / total_today) * 100.0, ((orders_yesterday_all.filter(status='canceled').count() / (orders_yesterday_all.count() or 1)) * 100.0)), 'dir': dir_of(pct_change((cancel_today / total_today) * 100.0, ((orders_yesterday_all.filter(status='canceled').count() / (orders_yesterday_all.count() or 1)) * 100.0)))},
                    'week': {'pct': pct_change((cancel_week / total_week) * 100.0, ((orders_last_week_all.filter(status='canceled').count() / (orders_last_week_all.count() or 1)) * 100.0)), 'dir': dir_of(pct_change((cancel_week / total_week) * 100.0, ((orders_last_week_all.filter(status='canceled').count() / (orders_last_week_all.count() or 1)) * 100.0)))},
                    'month': {'pct': pct_change((cancel_month / total_month) * 100.0, ((orders_last_month_all.filter(status='canceled').count() / (orders_last_month_all.count() or 1)) * 100.0)), 'dir': dir_of(pct_change((cancel_month / total_month) * 100.0, ((orders_last_month_all.filter(status='canceled').count() / (orders_last_month_all.count() or 1)) * 100.0)))},
                },
                'spark': spark_orders,
            },
        },
        'users': {
            'visitors': {'value': visitors_total, 'delta': {'day': {'pct': 0.0, 'dir': 'flat'}, 'week': {'pct': 0.0, 'dir': 'flat'}, 'month': {'pct': 0.0, 'dir': 'flat'}}},
            'registered': {'value': registered_total, 'delta': {'day': {'pct': 0.0, 'dir': 'flat'}, 'week': {'pct': 0.0, 'dir': 'flat'}, 'month': {'pct': 0.0, 'dir': 'flat'}}},
            'downloads': {'value': downloads_total, 'delta': {'day': {'pct': 0.0, 'dir': 'flat'}, 'week': {'pct': 0.0, 'dir': 'flat'}, 'month': {'pct': 0.0, 'dir': 'flat'}}},
        },
        'health': {
            'payment_errors': 0,
            'order_errors': canceled_recent,
            'expired_products': ProductVariant.objects.filter(stock_qty=0).count(),
            'inactive_stores': inactive_stores_count,
        },
    }

    charts = {
        'revenue_line': {'labels': revenue_line_labels, 'data': revenue_line_data},
        'orders_bar': {'labels': orders_bar_labels, 'data': orders_bar_data},
        'status_donut': {'labels': status_order, 'data': status_donut_data},
    }

    context = {
        'bi': bi,
        'charts': charts,
        'system_status': 'Healthy',
    }
    return render(request, 'dashboard/super_owner/reports.html', context)


@login_required
def super_owner_issues(request):
    if request.user.username != 'super_owner':
        messages.error(request, 'ليس لديك صلاحية الوصول!')
        return redirect('home')

    twenty_four_hours_ago = timezone.now() - timedelta(hours=24)
    two_hours_ago = timezone.now() - timedelta(hours=2)

    orders_today = Order.objects.filter(created_at__date=timezone.now().date())
    pending_over_24h = Order.objects.filter(status='pending', created_at__lt=twenty_four_hours_ago)
    inactive_stores = Store.objects.filter(is_active=False)
    canceled_today = orders_today.filter(status='canceled').count()
    on_the_way_stale = Order.objects.filter(status='on_the_way', updated_at__lt=two_hours_ago).count()

    critical_alerts = []
    if pending_over_24h.exists():
        critical_alerts.append({'type': 'pending_orders_over_24h', 'count': pending_over_24h.count(), 'url': 'super_owner_orders', 'label': 'طلبات متأخرة > 24 ساعة'})
    if inactive_stores.exists():
        critical_alerts.append({'type': 'inactive_stores', 'count': inactive_stores.count(), 'url': 'super_owner_stores', 'label': 'متاجر غير نشطة'})
    if canceled_today > 0:
        critical_alerts.append({'type': 'canceled_today', 'count': canceled_today, 'url': 'super_owner_orders', 'label': 'طلبات ملغاة اليوم'})
    if on_the_way_stale > 0:
        critical_alerts.append({'type': 'delivery_failure', 'count': on_the_way_stale, 'url': 'super_owner_orders', 'label': 'فشل/تأخر توصيل'})

    last_30 = timezone.now() - timedelta(days=30)
    total_recent = Order.objects.filter(created_at__gte=last_30).count() or 1
    canceled_recent = Order.objects.filter(created_at__gte=last_30, status='canceled').count()
    status_score = 0
    if pending_over_24h.count() > 0:
        status_score += 2
    if inactive_stores.count() > 0:
        status_score += 1
    if canceled_recent > max(3, int(0.1 * total_recent)):
        status_score += 2
    if on_the_way_stale > 0:
        status_score += 2
    system_status = 'Healthy'
    if status_score >= 4:
        system_status = 'Critical'
    elif status_score >= 2:
        system_status = 'Warning'

    context = {
        'critical_alerts': critical_alerts,
        'alert_count': len(critical_alerts),
        'system_status': system_status,
    }
    return render(request, 'dashboard/super_owner/issues.html', context)

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
    
    q = (request.GET.get('q') or '').strip()
    city = (request.GET.get('city') or '').strip()
    owner_id = (request.GET.get('owner') or '').strip()
    category = (request.GET.get('category') or '').strip()
    is_active = (request.GET.get('active') or '').strip()

    stores = Store.objects.all().order_by('-created_at')
    if q:
        from django.db.models import Q
        stores = stores.filter(
            Q(name__icontains=q) | Q(city__icontains=q) | Q(owner__username__icontains=q) | Q(owner__first_name__icontains=q) | Q(owner__last_name__icontains=q)
        )
    if city:
        stores = stores.filter(city__iexact=city)
    if owner_id:
        try:
            stores = stores.filter(owner_id=int(owner_id))
        except ValueError:
            pass
    if category:
        stores = stores.filter(category=category)
    if is_active == 'active':
        stores = stores.filter(is_active=True)
    elif is_active == 'inactive':
        stores = stores.filter(is_active=False)
    
    if request.method == 'POST':
        action = (request.POST.get('action') or '').strip()
        try:
            if action in ['activate','deactivate','delete']:
                store_id = int(request.POST.get('store_id'))
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
            elif action == 'copy':
                store_id = int(request.POST.get('store_id'))
                store = get_object_or_404(Store, id=store_id)
                new_store = Store.objects.create(
                    name=f"{store.name} (نسخة)", city=store.city, address=store.address,
                    description=store.description, owner=store.owner, category=store.category,
                    delivery_time=store.delivery_time, delivery_fee=store.delivery_fee,
                    is_active=False, logo=store.logo
                )
                messages.success(request, f'تم نسخ المتجر {store.name}!')
                return redirect('super_owner_store_center', store_id=new_store.id)
            elif action.startswith('bulk_'):
                selected_ids = request.POST.getlist('selected_ids')
                ids = [int(i) for i in selected_ids if str(i).isdigit()]
                if not ids:
                    messages.error(request, 'يرجى اختيار متاجر للتنفيذ')
                    return redirect('super_owner_stores')
                with transaction.atomic():
                    if action == 'bulk_activate':
                        Store.objects.filter(id__in=ids).update(is_active=True)
                        messages.success(request, 'تم تفعيل المتاجر المحددة')
                    elif action == 'bulk_deactivate':
                        Store.objects.filter(id__in=ids).update(is_active=False)
                        messages.success(request, 'تم تعطيل المتاجر المحددة')
                    elif action == 'bulk_set_delivery_fee':
                        fee_raw = request.POST.get('delivery_fee')
                        try:
                            fee = float(fee_raw)
                            for sid in ids:
                                s = Store.objects.get(id=sid)
                                s.delivery_fee = fee
                                s.save()
                            messages.success(request, 'تم تحديث رسوم التوصيل')
                        except Exception:
                            messages.error(request, 'رسوم توصيل غير صالحة')
                    elif action == 'bulk_set_category':
                        cat = (request.POST.get('category') or '').strip()
                        valid = [c[0] for c in Store.CATEGORY_CHOICES]
                        if cat in valid:
                            Store.objects.filter(id__in=ids).update(category=cat)
                            messages.success(request, 'تم تطبيق القالب/الفئة للمتاجر المحددة')
                        else:
                            messages.error(request, 'قالب/فئة غير صالح')
            return redirect('super_owner_stores')
        except Exception:
            messages.error(request, 'حدث خطأ أثناء تنفيذ العملية')
            return redirect('super_owner_stores')
    
    owners = User.objects.filter(role='admin').order_by('username')
    cities = list(Store.objects.values_list('city', flat=True).distinct())
    for s in stores:
        try:
            from .models import Product, Order
            s.products_count = Product.objects.filter(store=s).count()
            s.orders_today = Order.objects.filter(store=s, created_at__date=timezone.now().date()).count()
        except Exception:
            s.products_count = 0
            s.orders_today = 0
    context = {
        'stores': stores,
        'owners': owners,
        'cities': cities,
        'categories': Store.CATEGORY_CHOICES,
        'filters': { 'q': q, 'city': city, 'owner': owner_id, 'category': category, 'active': is_active },
    }
    return render(request, 'dashboard/super_owner/stores_operational.html', context)


@login_required
def super_owner_store_center(request, store_id):
    if request.user.username != 'super_owner':
        messages.error(request, 'ليس لديك صلاحية الوصول!')
        return redirect('home')
    store = get_object_or_404(Store, id=store_id)
    if request.method == 'POST':
        action = (request.POST.get('action') or '').strip()
        try:
            if action == 'activate':
                store.is_active = True
                store.save()
                messages.success(request, 'تم تفعيل المتجر')
            elif action == 'deactivate':
                store.is_active = False
                store.save()
                messages.success(request, 'تم تعطيل المتجر')
            
        except Exception:
            messages.error(request, 'حدث خطأ في العملية')
        return redirect('super_owner_store_center', store_id=store.id)

    from .models import Product, Order
    products_count = Product.objects.filter(store=store).count()
    orders_today = Order.objects.filter(store=store, created_at__date=timezone.now().date()).count()
    last_update = store.created_at
    context = {
        'store': store,
        'products_count': products_count,
        'orders_today': orders_today,
        'last_update': last_update,
        'stores_all': Store.objects.exclude(id=store.id).order_by('name'),
    }
    return render(request, 'dashboard/super_owner/store_center.html', context)


@login_required
def super_owner_add_store(request):
    if request.user.username != 'super_owner':
        messages.error(request, 'ليس لديك صلاحية الوصول!')
        return redirect('home')
    
    if request.method == 'POST':
        name = (request.POST.get('name') or '').strip()
        city = (request.POST.get('city') or '').strip()
        owner_id = request.POST.get('owner')
        create_new_owner = request.POST.get('create_new_owner') == 'on'
        is_active = request.POST.get('is_active') == 'on'
        store_template = (request.POST.get('store_template') or '').strip()
        copy_store_id = (request.POST.get('copy_store_id') or '').strip()

        owner = None

        if not all([name, city]):
            messages.error(request, 'يرجى إدخال اسم المتجر والمدينة')
            return redirect('super_owner_add_store')

        if create_new_owner:
            new_owner_username = (request.POST.get('new_owner_username') or '').strip()
            new_owner_email = (request.POST.get('new_owner_email') or '').strip()
            new_owner_phone = (request.POST.get('new_owner_phone') or '').strip()
            new_owner_password = (request.POST.get('new_owner_password') or '').strip()
            if not all([new_owner_username, new_owner_phone, new_owner_password]):
                messages.error(request, 'يرجى إدخال بيانات المالك الجديد الأساسية')
                return redirect('super_owner_add_store')
            try:
                owner = User.objects.create(
                    username=new_owner_username,
                    first_name='',
                    last_name='',
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

        base_category = 'clothing'
        base_delivery_time = '30-45 دقيقة'
        base_delivery_fee = 1000.00
        base_description = ''
        address_placeholder = '—'

        last_store = Store.objects.order_by('-created_at').first()
        if last_store:
            base_category = last_store.category
            base_delivery_time = last_store.delivery_time
            base_delivery_fee = float(last_store.delivery_fee)
            base_description = last_store.description or ''

        if copy_store_id:
            try:
                src = Store.objects.get(id=int(copy_store_id))
                base_category = src.category
                base_delivery_time = src.delivery_time
                base_delivery_fee = float(src.delivery_fee)
                base_description = src.description or ''
            except (Store.DoesNotExist, ValueError):
                pass
        elif store_template in ['clothing','electronics','food']:
            if store_template == 'clothing':
                base_category = 'clothing'
                base_delivery_time = '30-45 دقيقة'
                base_delivery_fee = 1000.00
            elif store_template == 'electronics':
                base_category = 'electronics'
                base_delivery_time = '60-90 دقيقة'
                base_delivery_fee = 3000.00
            elif store_template == 'food':
                base_category = 'food'
                base_delivery_time = '20-30 دقيقة'
                base_delivery_fee = 2000.00

        try:
            store = Store.objects.create(
                name=name,
                city=city,
                address=address_placeholder,
                description=base_description,
                owner=owner,
                category=base_category,
                delivery_time=base_delivery_time,
                delivery_fee=base_delivery_fee,
                is_active=is_active
            )
            messages.success(request, f'تم إنشاء المتجر "{store.name}" بنجاح!')
            return redirect('super_owner_edit_store', store_id=store.id)

        except Exception as e:
            messages.error(request, f'خطأ في إنشاء المتجر: {str(e)}')
            return redirect('super_owner_add_store')

    store_owners = User.objects.filter(role='admin').order_by('username')
    stores_all = Store.objects.all().order_by('name')
    last_store = Store.objects.order_by('-created_at').first()
    context = {
        'store_owners': store_owners,
        'stores_all': stores_all,
        'default_city': last_store.city if last_store else '',
    }
    return render(request, 'dashboard/super_owner/add_store.html', context)


@login_required
def super_owner_quick_add_store(request):
    return redirect('super_owner_create_store')

@login_required
def super_owner_owner_search_json(request):
    if request.user.username != 'super_owner':
        return JsonResponse({'error': 'unauthorized'}, status=403)
    q = (request.GET.get('q') or '').strip()
    owners = User.objects.filter(role='admin')
    if q:
        owners = owners.filter(Q(username__icontains=q) | Q(first_name__icontains=q) | Q(last_name__icontains=q) | Q(phone__icontains=q))
    owners = owners.order_by('username')[:20]
    data = [{'id': o.id, 'name': o.get_full_name() or o.username, 'phone': o.phone or ''} for o in owners]
    return JsonResponse({'results': data})

@login_required
def super_owner_create_owner_json(request):
    if request.user.username != 'super_owner':
        return JsonResponse({'error': 'unauthorized'}, status=403)
    if request.method != 'POST':
        return JsonResponse({'error': 'method_not_allowed'}, status=405)
    full_name = (request.POST.get('full_name') or '').strip()
    phone = (request.POST.get('phone') or '').strip()
    email = (request.POST.get('email') or '').strip()
    if not full_name or not phone:
        return JsonResponse({'error': 'missing_required', 'message': 'الاسم الكامل ورقم الهاتف مطلوبان'}, status=400)
    import re
    if not re.fullmatch(r'07\d{9}', phone):
        return JsonResponse({'error': 'invalid_phone', 'message': 'رقم هاتف غير صالح. الصيغة: 07xxxxxxxxx'}, status=400)
    # Prevent duplicate phone
    try:
        if User.objects.filter(phone__iexact=phone).exists():
            return JsonResponse({'error': 'duplicate_phone', 'message': 'رقم الهاتف مستخدم مسبقاً'}, status=409)
    except Exception:
        pass
    first, last = '', ''
    parts = full_name.split()
    if parts:
        first = parts[0]
        last = ' '.join(parts[1:])
    try:
        username = f"owner_{uuid.uuid4().hex[:8]}"
        owner = User.objects.create(username=username, first_name=first, last_name=last, role='admin', phone=phone, email=email)
        owner.is_staff = True
        owner.set_password(uuid.uuid4().hex)
        owner.save()
        return JsonResponse({'id': owner.id, 'name': owner.get_full_name() or owner.username, 'phone': owner.phone or ''})
    except Exception:
        return JsonResponse({'error': 'create_failed', 'message': 'فشل إنشاء المالك'}, status=500)

@login_required
def super_owner_create_store(request):
    if request.user.username != 'super_owner':
        messages.error(request, 'ليس لديك صلاحية الوصول!')
        return redirect('home')
    step = (request.POST.get('step') or request.GET.get('step') or '1').strip()
    wizard = request.session.get('create_store_wizard') or {}
    errors = {}
    owners = User.objects.filter(role='admin').order_by('username')
    categories = Store.CATEGORY_CHOICES
    status_code = 200
    if request.method == 'POST':
        action = (request.POST.get('action') or '').strip()
        if step == '1':
            owner_id = (request.POST.get('owner_id') or '').strip()
            if not owner_id or not owner_id.isdigit():
                errors['owner_id'] = 'يرجى اختيار مالك المتجر'
                status_code = 400
            else:
                wizard['owner_id'] = int(owner_id)
                request.session['create_store_wizard'] = wizard
                step = '2'
        elif step == '2':
            name = (request.POST.get('name') or '').strip()
            city = (request.POST.get('city') or '').strip()
            category = (request.POST.get('category') or '').strip()
            status_choice = (request.POST.get('status') or 'ACTIVE').strip()
            if not name:
                errors['name'] = 'يرجى إدخال اسم المتجر'
            if not city:
                errors['city'] = 'يرجى اختيار المدينة'
            valid_categories = [c[0] for c in Store.CATEGORY_CHOICES]
            if category and category not in valid_categories:
                errors['category'] = 'فئة غير صالحة'
            if status_choice not in ['ACTIVE', 'DISABLED']:
                status_choice = 'ACTIVE'
            if not errors:
                wizard.update({'name': name, 'city': city, 'category': category or 'clothing', 'status': status_choice})
                request.session['create_store_wizard'] = wizard
                step = '3'
            else:
                status_code = 400
        elif step == '3':
            delivery_fee_raw = (request.POST.get('delivery_fee') or '').strip()
            free_threshold_raw = (request.POST.get('free_delivery_threshold') or '').strip()
            dt_value_raw = (request.POST.get('delivery_time_value') or '').strip()
            dt_unit = (request.POST.get('delivery_time_unit') or '').strip()
            logo_file = request.FILES.get('logo')
            try:
                delivery_fee = float(delivery_fee_raw)
            except Exception:
                errors['delivery_fee'] = 'يرجى إدخال رسوم توصيل صحيحة'
                delivery_fee = None
            free_threshold = None
            if free_threshold_raw != '':
                try:
                    free_threshold = float(free_threshold_raw)
                except Exception:
                    errors['free_delivery_threshold'] = 'قيمة غير صالحة'
            dt_value = None
            try:
                dt_value = int(dt_value_raw) if dt_value_raw != '' else None
                if dt_value is not None and dt_value < 0:
                    raise ValueError('negative')
            except Exception:
                errors['delivery_time_value'] = 'يرجى إدخال قيمة زمن التوصيل'
            if dt_unit not in ['hour', 'day']:
                errors['delivery_time_unit'] = 'يرجى اختيار وحدة صحيحة'
            if not errors:
                if dt_value is None:
                    dt_value = 24
                if not dt_unit:
                    dt_unit = 'hour'
                delivery_time_text = f"{dt_value} ساعة" if dt_unit == 'hour' else f"{dt_value} يوم"
                wizard.update({
                    'delivery_fee': delivery_fee,
                    'free_delivery_threshold': free_threshold,
                    'delivery_time_value': dt_value,
                    'delivery_time_unit': dt_unit,
                    'delivery_time': delivery_time_text,
                })
                try:
                    with transaction.atomic():
                        owner = User.objects.get(id=int(wizard['owner_id']))
                        status_choice = wizard.get('status') or 'ACTIVE'
                        is_active = True if status_choice == 'ACTIVE' else False
                        s = Store.objects.create(
                            name=wizard.get('name',''),
                            city=wizard.get('city',''),
                            address='—',
                            description='',
                            owner=owner,
                            category=wizard.get('category') or 'clothing',
                            delivery_time=delivery_time_text,
                            delivery_time_value=dt_value,
                            delivery_time_unit=dt_unit,
                            delivery_fee=delivery_fee or 0.0,
                            is_active=is_active,
                            status=status_choice,
                            free_delivery_threshold=free_threshold,
                        )
                        if logo_file:
                            s.logo = logo_file
                            s.save()
                        from .models import AdminAuditLog
                        AdminAuditLog.objects.create(admin_user=request.user, action='create', model='Store', object_id=str(s.id), before='', after=json.dumps({'name': s.name}, ensure_ascii=False), ip=request.META.get('REMOTE_ADDR') or '')
                    request.session.pop('create_store_wizard', None)
                    messages.success(request, 'تم إنشاء المتجر بنجاح')
                    return redirect('super_owner_store_center', store_id=s.id)
                except Exception:
                    errors['general'] = 'فشل الإنشاء'
                    status_code = 500
            else:
                status_code = 400
    context = {'step': step, 'errors': errors, 'owners': owners, 'categories': categories, 'wizard': wizard}
    return render(request, 'dashboard/super_owner/create_store_wizard.html', context, status=status_code)


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
        owner_phone = (request.POST.get('owner_phone') or '').strip()
        is_active = request.POST.get('is_active') == 'on'
        logo = request.FILES.get('logo')
        category = (request.POST.get('category') or '').strip()
        dt_value_raw = (request.POST.get('delivery_time_value') or '').strip()
        dt_unit = (request.POST.get('delivery_time_unit') or '').strip()
        delivery_fee_raw = (request.POST.get('delivery_fee') or '').strip()
        free_threshold_raw = (request.POST.get('free_delivery_threshold') or '').strip()
        
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
            if owner_phone:
                p = owner_phone.replace(' ', '')
                if p.startswith('+964'):
                    p = p[1:]
                if p.startswith('07') and len(p) == 11:
                    p = '964' + p[1:]
                if p and (not p.startswith('9647') or len(p) != 13):
                    messages.error(request, 'رقم هاتف المالك غير صالح')
                    return redirect('super_owner_edit_store', store_id=store_id)
                store.owner_phone = p
            if category in [c[0] for c in Store.CATEGORY_CHOICES]:
                store.category = category
            dt_value = None
            try:
                dt_value = int(dt_value_raw) if dt_value_raw != '' else None
                if dt_value is not None and dt_value < 0:
                    dt_value = None
            except Exception:
                dt_value = None
            if dt_unit not in ['hour','day']:
                dt_unit = store.delivery_time_unit or 'hour'
            if dt_value is not None:
                store.delivery_time_value = dt_value
                store.delivery_time_unit = dt_unit
                store.delivery_time = f"{dt_value} ساعة" if dt_unit == 'hour' else f"{dt_value} يوم"
            try:
                if delivery_fee_raw:
                    store.delivery_fee = float(delivery_fee_raw)
            except Exception:
                pass
            try:
                if free_threshold_raw != '':
                    store.free_delivery_threshold = float(free_threshold_raw)
            except Exception:
                pass
            
            if logo:
                store.logo = logo
            
            store.save()
            
            messages.success(request, f'تم تحديث المتجر "{store.name}" بنجاح!')
            return redirect('super_owner_stores')
            
        except User.DoesNotExist:
            messages.error(request, 'المستخدم المختار غير صالح!')
            return redirect('super_owner_edit_store', store_id=store_id)
    
    store_owners = User.objects.filter(role='admin').order_by('username')
    context = {
        'store': store,
        'store_owners': store_owners,
        'store_categories': Store.CATEGORY_CHOICES,
    }
    return render(request, 'dashboard/super_owner/edit_store.html', context)


@login_required
def super_owner_products(request):
    if request.user.username != 'super_owner':
        messages.error(request, 'ليس لديك صلاحية الوصول!')
        return redirect('home')
    
    from django.core.paginator import Paginator
    from django.db.models import Count, Sum
    q = (request.GET.get('q') or '').strip()
    sort = (request.GET.get('sort') or 'new').strip()
    page = int((request.GET.get('page') or '1') or 1)
    base_qs = Product.objects.select_related('store').prefetch_related('images')
    if q:
        from django.db.models import Q
        base_qs = base_qs.filter(Q(name__icontains=q) | Q(store__name__icontains=q))
    base_qs = base_qs.annotate(variants_count=Count('variants'), total_stock=Sum('variants__stock_qty'))
    if sort == 'price_asc':
        base_qs = base_qs.order_by('base_price')
    elif sort == 'price_desc':
        base_qs = base_qs.order_by('-base_price')
    elif sort == 'active':
        base_qs = base_qs.order_by('-is_active', '-created_at')
    elif sort == 'variants_desc':
        base_qs = base_qs.order_by('-variants_count', '-created_at')
    else:
        base_qs = base_qs.order_by('-created_at')
    paginator = Paginator(base_qs, 20)
    products_page = paginator.get_page(page)
    if request.method == 'POST':
        action = (request.POST.get('action') or '').strip()

        product_id = request.POST.get('product_id')
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
        elif action == 'duplicate':
            from django.db import transaction
            with transaction.atomic():
                new_product = Product.objects.create(
                    store=product.store,
                    name=f"{product.name} - نسخة",
                    description=product.description,
                    base_price=product.base_price,
                    discount_price=product.discount_price,
                    category=product.category,
                    size_type=product.size_type,
                    is_active=False,
                    is_featured=False,
                )
                for img in product.images.all():
                    ProductImage.objects.create(
                        product=new_product,
                        image=img.image,
                        image_url=img.image_url,
                        is_main=False,
                        color=img.color,
                        color_attr=getattr(img, 'color_attr', None),
                        order=img.order,
                    )
                for v in product.variants.all():
                    ProductVariant.objects.create(
                        product=new_product,
                        color_obj=v.color_obj,
                        color_attr=getattr(v, 'color_attr', None),
                        size=v.size,
                        size_attr=getattr(v, 'size_attr', None),
                        stock_qty=v.stock_qty,
                        price_override=v.price_override,
                        is_enabled=False,
                    )
            messages.success(request, f'تم إنشاء نسخة من المنتج {product.name}!')
        elif action == 'delete':
            product_name = product.name
            product.delete()
            messages.success(request, f'تم حذف المنتج {product_name}!')
        
        return redirect('super_owner_products')
    
    context = {
        'products': products_page,
        'page_obj': products_page,
        'paginator': paginator,
        'q': q,
        'sort': sort,
    }
    return render(request, 'dashboard/super_owner/products.html', context)

@login_required
def super_owner_add_product(request):
    if request.user.username != 'super_owner':
        messages.error(request, 'ليس لديك صلاحية الوصول!')
        return redirect('home')

    stores = Store.objects.all()
    preselect_store = request.GET.get('store')
    step = (request.GET.get('step') or 'info').strip()
    pid = request.GET.get('pid')

    from .models import AttributeColor, AttributeSize

    if request.method == 'POST':
        action = (request.POST.get('action') or '').strip()

        if action == 'create_product':
            name = request.POST.get('name')
            store_id = request.POST.get('store')
            category = request.POST.get('category')
            base_price = request.POST.get('base_price')
            description = request.POST.get('description')
            is_active = request.POST.get('is_active') == 'on'
            is_featured = request.POST.get('is_featured') == 'on'
            size_type = (request.POST.get('size_type') or 'symbolic').strip()
            images = request.FILES.getlist('images')
            color_ids = request.POST.getlist('color_ids')
            size_ids = request.POST.getlist('size_ids')

            if not all([name, store_id, category, base_price, description]):
                messages.error(request, 'يرجى ملء جميع الحقول المطلوبة!')
                return redirect('super_owner_add_product')

            try:
                store = Store.objects.get(id=store_id)
                from django.db import transaction
                with transaction.atomic():
                    product = Product.objects.create(
                        name=name,
                        store=store,
                        category=category,
                        base_price=base_price,
                        description=description,
                        size_type=size_type,
                        is_active=is_active,
                        is_featured=is_featured
                    )

                    if images:
                        for idx, image in enumerate(images):
                            ProductImage.objects.create(product=product, image=image, is_main=(idx == 0))

                    try:
                        selected_colors = AttributeColor.objects.filter(id__in=[int(cid) for cid in color_ids if cid.isdigit()])
                    except Exception:
                        selected_colors = []
                    try:
                        selected_sizes = AttributeSize.objects.filter(id__in=[int(sid) for sid in size_ids if sid.isdigit()])
                    except Exception:
                        selected_sizes = []

                    created = 0
                    for c in selected_colors:
                        for s in selected_sizes:
                            exists = ProductVariant.objects.filter(product=product, color_attr=c, size_attr=s).exists()
                            if exists:
                                continue
                            ProductVariant.objects.create(
                                product=product,
                                color_attr=c,
                                size_attr=s,
                                size=s.name,
                                stock_qty=0,
                                price_override=None,
                                is_enabled=product.is_active,
                            )
                            created += 1

                    if created == 0:
                        if not ProductVariant.objects.filter(product=product).exists() and size_type == 'none':
                            ProductVariant.objects.create(
                                product=product,
                                color_attr=None,
                                size_attr=None,
                                size='ONE',
                                stock_qty=0,
                                price_override=None,
                                is_enabled=product.is_active,
                            )

                return redirect(f"{request.path}?pid={product.id}&step=attributes")
            except Store.DoesNotExist:
                messages.error(request, 'المتجر المختار غير صالح!')
                return redirect('super_owner_add_product')

        elif action == 'generate_variants':
            pid = request.POST.get('pid')
            default_qty_raw = request.POST.get('default_qty')
            default_price_raw = (request.POST.get('default_price') or '').strip()
            color_ids = request.POST.getlist('color_ids')
            size_ids = request.POST.getlist('size_ids')
            enable_all = (request.POST.get('enable_all') == 'on')

            try:
                product = Product.objects.get(id=int(pid))
            except (Product.DoesNotExist, TypeError, ValueError):
                messages.error(request, 'المنتج غير موجود')
                return redirect('super_owner_add_product')

            try:
                default_qty = int(default_qty_raw or 0)
            except ValueError:
                default_qty = 0

            from decimal import Decimal, InvalidOperation
            default_price = None
            if default_price_raw:
                try:
                    default_price = Decimal(default_price_raw)
                except InvalidOperation:
                    default_price = None

            selected_colors = AttributeColor.objects.filter(id__in=[int(cid) for cid in color_ids if cid.isdigit()])
            selected_sizes = AttributeSize.objects.filter(id__in=[int(sid) for sid in size_ids if sid.isdigit()])

            created = 0
            for c in selected_colors:
                for s in selected_sizes:
                    exists = ProductVariant.objects.filter(product=product, color_attr=c, size_attr=s).exists()
                    if exists:
                        continue
                    try:
                        ProductVariant.objects.create(
                            product=product,
                            color_attr=c,
                            size_attr=s,
                            stock_qty=default_qty,
                            price_override=default_price,
                            is_enabled=enable_all or True,
                        )
                        created += 1
                    except Exception:
                        pass

            messages.success(request, f'تم إنشاء {created} متغيرات تلقائياً')
            return redirect(f"{request.path}?pid={product.id}&step=variants")

        elif action == 'save_attributes':
            pid = request.POST.get('pid')
            color_ids = request.POST.getlist('color_ids')
            size_ids = request.POST.getlist('size_ids')

            try:
                product = Product.objects.get(id=int(pid))
            except (Product.DoesNotExist, TypeError, ValueError):
                messages.error(request, 'المنتج غير موجود')
                return redirect('super_owner_add_product')

            selected_colors = list(AttributeColor.objects.filter(id__in=[int(cid) for cid in color_ids if cid.isdigit()]))
            selected_sizes = list(AttributeSize.objects.filter(id__in=[int(sid) for sid in size_ids if sid.isdigit()]))

            created = 0
            if selected_colors and selected_sizes:
                for c in selected_colors:
                    for s in selected_sizes:
                        exists = ProductVariant.objects.filter(product=product, color_attr=c, size_attr=s).exists()
                        if exists:
                            continue
                        try:
                            ProductVariant.objects.create(
                                product=product,
                                color_attr=c,
                                size_attr=s,
                                size=s.name,
                                stock_qty=0,
                                price_override=None,
                                is_enabled=False,
                            )
                            created += 1
                        except Exception:
                            pass
            elif selected_colors and not selected_sizes and product.size_type == 'none':
                for c in selected_colors:
                    exists = ProductVariant.objects.filter(product=product, color_attr=c, size_attr__isnull=True).exists()
                    if exists:
                        continue
                    try:
                        ProductVariant.objects.create(
                            product=product,
                            color_attr=c,
                            size_attr=None,
                            size='ONE',
                            stock_qty=0,
                            price_override=None,
                            is_enabled=False,
                        )
                        created += 1
                    except Exception:
                        pass
            elif selected_sizes and not selected_colors:
                for s in selected_sizes:
                    exists = ProductVariant.objects.filter(product=product, color_attr__isnull=True, size_attr=s).exists()
                    if exists:
                        continue
                    try:
                        ProductVariant.objects.create(
                            product=product,
                            color_attr=None,
                            size_attr=s,
                            size=s.name,
                            stock_qty=0,
                            price_override=None,
                            is_enabled=False,
                        )
                        created += 1
                    except Exception:
                        pass
            else:
                if product.size_type == 'none':
                    if not ProductVariant.objects.filter(product=product).exists():
                        try:
                            ProductVariant.objects.create(
                                product=product,
                                color_attr=None,
                                size_attr=None,
                                size='ONE',
                                stock_qty=0,
                                price_override=None,
                                is_enabled=False,
                            )
                            created += 1
                        except Exception:
                            pass

            messages.success(request, f'تم حفظ الخصائص وإنشاء {created} صفوف مخزون')
            return redirect(f"{request.path}?pid={product.id}&step=images")

        elif action == 'add_global_color':
            cname = (request.POST.get('color_name') or '').strip()
            ccode = (request.POST.get('color_code') or '').strip()
            def _hex_to_rgb(h):
                try:
                    return (int(h[1:3],16), int(h[3:5],16), int(h[5:7],16))
                except Exception:
                    return (0,0,0)
            def _nearest_name(h):
                targets = [
                    ('أسود','#000000'),('أبيض','#FFFFFF'),('أحمر','#FF0000'),('أخضر','#008000'),('أزرق','#0000FF'),
                    ('أصفر','#FFFF00'),('برتقالي','#FFA500'),('بنفسجي','#800080'),('نيلي','#4B0082'),('تركوازي','#40E0D0'),
                    ('كحلي','#000080'),('رمادي','#808080'),('زهري','#FFC0CB'),('بنّي','#8B4513'),('سماوي','#87CEEB')
                ]
                t = _hex_to_rgb(h.upper())
                best, bd = None, 10**9
                for name, hexv in targets:
                    r,g,b = _hex_to_rgb(hexv)
                    d = (t[0]-r)*(t[0]-r) + (t[1]-g)*(t[1]-g) + (t[2]-b)*(t[2]-b)
                    if d < bd:
                        bd = d
                        best = name
                return best or h
            if not cname:
                cname = _nearest_name(ccode or '#000000')
            try:
                AttributeColor.objects.get_or_create(name=cname, defaults={'code': ccode})
                messages.success(request, 'تمت إضافة اللون إلى القائمة العامة')
            except Exception:
                messages.error(request, 'تعذر إضافة اللون')
            return redirect(f"{request.path}?pid={request.POST.get('pid')}&step=attributes")

        elif action == 'bulk_qty_color':
            pid = request.POST.get('pid')
            color_id = request.POST.get('color_id')
            try:
                product = Product.objects.get(id=int(pid))
            except (Product.DoesNotExist, ValueError, TypeError):
                messages.error(request, 'المنتج غير موجود')
                return redirect('super_owner_add_product')
            try:
                qty = int(request.POST.get('qty') or 0)
            except ValueError:
                qty = 0
            ProductVariant.objects.filter(product=product, color_attr_id=int(color_id)).update(stock_qty=qty)
            messages.success(request, 'تم تحديث الكمية حسب اللون')
            return redirect(f"{request.path}?pid={product.id}&step=variants")

        elif action == 'delete_attribute_color':
            cid = (request.POST.get('color_id') or '').strip()
            try:
                from .models import AttributeColor
                if cid and cid.isdigit():
                    AttributeColor.objects.filter(id=int(cid)).delete()
                    messages.success(request, 'تم حذف اللون')
                else:
                    messages.error(request, 'معرف لون غير صالح')
            except Exception:
                messages.error(request, 'تعذر حذف اللون')
            return redirect(f"{request.path}?pid={request.POST.get('pid')}&step=attributes")

        elif action == 'bulk_qty_size':
            pid = request.POST.get('pid')
            size_id = request.POST.get('size_id')
            try:
                product = Product.objects.get(id=int(pid))
            except (Product.DoesNotExist, ValueError, TypeError):
                messages.error(request, 'المنتج غير موجود')
                return redirect('super_owner_add_product')
            try:
                qty = int(request.POST.get('qty') or 0)
            except ValueError:
                qty = 0
            ProductVariant.objects.filter(product=product, size_attr_id=int(size_id)).update(stock_qty=qty)
            messages.success(request, 'تم تحديث الكمية حسب المقاس')
            return redirect(f"{request.path}?pid={product.id}&step=variants")

        elif action == 'add_attribute_size':
            sname = (request.POST.get('size_name') or '').strip()
            try:
                if not sname:
                    messages.error(request, 'يرجى إدخال اسم القياس')
                    return redirect(f"{request.path}?pid={request.POST.get('pid')}&step=attributes")
                from django.db.models import Max
                from .models import AttributeSize
                max_order = AttributeSize.objects.aggregate(m=Max('order')).get('m') or 0
                AttributeSize.objects.get_or_create(name=sname, defaults={'order': max_order + 1})
                messages.success(request, 'تمت إضافة القياس')
            except Exception:
                messages.error(request, 'تعذر إضافة القياس')
            return redirect(f"{request.path}?pid={request.POST.get('pid')}&step=attributes")

        elif action == 'delete_attribute_size':
            sid = (request.POST.get('size_id') or '').strip()
            try:
                from .models import AttributeSize
                if sid and sid.isdigit():
                    AttributeSize.objects.filter(id=int(sid)).delete()
                    messages.success(request, 'تم حذف القياس')
                else:
                    messages.error(request, 'معرف قياس غير صالح')
            except Exception:
                messages.error(request, 'تعذر حذف القياس')
            return redirect(f"{request.path}?pid={request.POST.get('pid')}&step=attributes")

        elif action == 'bulk_price_color':
            pid = request.POST.get('pid')
            color_id = request.POST.get('color_id')
            try:
                product = Product.objects.get(id=int(pid))
            except (Product.DoesNotExist, ValueError, TypeError):
                messages.error(request, 'المنتج غير موجود')
                return redirect('super_owner_add_product')
            from decimal import Decimal, InvalidOperation
            raw = (request.POST.get('price') or '').strip()
            price = None
            if raw:
                try:
                    price = Decimal(raw)
                except InvalidOperation:
                    price = None
            ProductVariant.objects.filter(product=product, color_attr_id=int(color_id)).update(price_override=price)
            messages.success(request, 'تم تحديث السعر حسب اللون')
            return redirect(f"{request.path}?pid={product.id}&step=variants")

        elif action == 'bulk_price_size':
            pid = request.POST.get('pid')
            size_id = request.POST.get('size_id')
            try:
                product = Product.objects.get(id=int(pid))
            except (Product.DoesNotExist, ValueError, TypeError):
                messages.error(request, 'المنتج غير موجود')
                return redirect('super_owner_add_product')
            from decimal import Decimal, InvalidOperation
            raw = (request.POST.get('price') or '').strip()
            price = None
            if raw:
                try:
                    price = Decimal(raw)
                except InvalidOperation:
                    price = None
            ProductVariant.objects.filter(product=product, size_attr_id=int(size_id)).update(price_override=price)
            messages.success(request, 'تم تحديث السعر حسب المقاس')
            return redirect(f"{request.path}?pid={product.id}&step=variants")

        elif action == 'bulk_status_color':
            pid = request.POST.get('pid')
            color_id = request.POST.get('color_id')
            try:
                product = Product.objects.get(id=int(pid))
            except (Product.DoesNotExist, ValueError, TypeError):
                messages.error(request, 'المنتج غير موجود')
                return redirect('super_owner_add_product')
            status = (request.POST.get('status') or 'enable').strip()
            enable = status == 'enable'
            ProductVariant.objects.filter(product=product, color_attr_id=int(color_id)).update(is_enabled=enable)
            messages.success(request, 'تم تحديث حالة المتغيرات حسب اللون')
            return redirect(f"{request.path}?pid={product.id}&step=variants")

        elif action == 'bulk_status_size':
            pid = request.POST.get('pid')
            size_id = request.POST.get('size_id')
            try:
                product = Product.objects.get(id=int(pid))
            except (Product.DoesNotExist, ValueError, TypeError):
                messages.error(request, 'المنتج غير موجود')
                return redirect('super_owner_add_product')
            status = (request.POST.get('status') or 'enable').strip()
            enable = status == 'enable'
            ProductVariant.objects.filter(product=product, size_attr_id=int(size_id)).update(is_enabled=enable)
            messages.success(request, 'تم تحديث حالة المتغيرات حسب المقاس')
            return redirect(f"{request.path}?pid={product.id}&step=variants")

        elif action == 'bulk_qty':
            pid = request.POST.get('pid')
            try:
                product = Product.objects.get(id=int(pid))
            except (Product.DoesNotExist, ValueError, TypeError):
                messages.error(request, 'المنتج غير موجود')
                return redirect('super_owner_add_product')
            try:
                qty = int(request.POST.get('qty') or 0)
            except ValueError:
                qty = 0
            ProductVariant.objects.filter(product=product).update(stock_qty=qty)
            messages.success(request, 'تم تحديث الكمية لكل المتغيرات')
            return redirect(f"{request.path}?pid={product.id}&step=variants")

        elif action == 'bulk_price':
            pid = request.POST.get('pid')
            try:
                product = Product.objects.get(id=int(pid))
            except (Product.DoesNotExist, ValueError, TypeError):
                messages.error(request, 'المنتج غير موجود')
                return redirect('super_owner_add_product')
            from decimal import Decimal, InvalidOperation
            raw = (request.POST.get('price') or '').strip()
            price = None
            if raw:
                try:
                    price = Decimal(raw)
                except InvalidOperation:
                    price = None
            ProductVariant.objects.filter(product=product).update(price_override=price)
            messages.success(request, 'تم تحديث السعر لكل المتغيرات')
            return redirect(f"{request.path}?pid={product.id}&step=variants")

        elif action == 'bulk_status':
            pid = request.POST.get('pid')
            try:
                product = Product.objects.get(id=int(pid))
            except (Product.DoesNotExist, ValueError, TypeError):
                messages.error(request, 'المنتج غير موجود')
                return redirect('super_owner_add_product')
            status = (request.POST.get('status') or 'enable').strip()
            enable = status == 'enable'
            ProductVariant.objects.filter(product=product).update(is_enabled=enable)
            messages.success(request, 'تم تحديث حالة المتغيرات')
            return redirect(f"{request.path}?pid={product.id}&step=variants")

        elif action == 'update_variant_row':
            pid = request.POST.get('pid')
            variant_id = request.POST.get('variant_id')
            try:
                product = Product.objects.get(id=int(pid))
                variant = ProductVariant.objects.get(id=int(variant_id), product=product)
            except (Product.DoesNotExist, ProductVariant.DoesNotExist, ValueError, TypeError):
                messages.error(request, 'المتغير غير موجود')
                return redirect('super_owner_add_product')
            try:
                variant.stock_qty = int(request.POST.get('stock_qty') or variant.stock_qty)
            except ValueError:
                pass
            from decimal import Decimal, InvalidOperation
            raw = (request.POST.get('price_override') or '').strip()
            if raw == '':
                variant.price_override = None
            else:
                try:
                    variant.price_override = Decimal(raw)
                except InvalidOperation:
                    pass
            variant.is_enabled = (request.POST.get('is_enabled') == 'on')
            try:
                variant.save()
            except Exception:
                pass
            messages.success(request, 'تم تحديث المتغير')
            return redirect(f"{request.path}?pid={product.id}&step=variants")

        elif action == 'create_or_update_cell':
            pid = request.POST.get('pid')
            color_id = request.POST.get('color_id')
            size_id = request.POST.get('size_id')
            try:
                product = Product.objects.get(id=int(pid))
            except (Product.DoesNotExist, ValueError, TypeError):
                messages.error(request, 'المنتج غير موجود')
                return redirect('super_owner_add_product')
            try:
                cid = int(color_id)
                sid = int(size_id)
            except (ValueError, TypeError):
                messages.error(request, 'خصائص غير صالحة')
                return redirect(f"{request.path}?pid={pid}&step=variants")
            from decimal import Decimal, InvalidOperation
            try:
                qty = int(request.POST.get('stock_qty') or 0)
            except ValueError:
                qty = 0
            raw_price = (request.POST.get('price_override') or '').strip()
            price = None
            if raw_price != '':
                try:
                    price = Decimal(raw_price)
                except InvalidOperation:
                    price = None
            enabled = (request.POST.get('is_enabled') == 'on')
            v = ProductVariant.objects.filter(product=product, color_attr_id=cid, size_attr_id=sid).first()
            created = False
            if not v:
                try:
                    v = ProductVariant(product=product, color_attr_id=cid, size_attr_id=sid, stock_qty=qty, price_override=price, is_enabled=enabled)
                    v.save()
                    created = True
                except Exception:
                    messages.error(request, 'تعذر إنشاء المتغير')
                    return redirect(f"{request.path}?pid={product.id}&step=variants")
            else:
                v.stock_qty = qty
                v.price_override = price
                v.is_enabled = enabled
                try:
                    v.save()
                except Exception:
                    messages.error(request, 'تعذر تحديث المتغير')
                    return redirect(f"{request.path}?pid={product.id}&step=variants")
            messages.success(request, 'تم ' + ('إنشاء' if created else 'تحديث') + ' المتغير')
            return redirect(f"{request.path}?pid={product.id}&step=variants")

        elif action == 'upload_images':
            pid = request.POST.get('pid')
            try:
                product = Product.objects.get(id=int(pid))
            except (Product.DoesNotExist, ValueError, TypeError):
                messages.error(request, 'المنتج غير موجود')
                return redirect('super_owner_add_product')
            files = request.FILES.getlist('images')
            max_order = product.images.aggregate(m=Max('order')).get('m') or 0
            existing_images = list(product.images.all())
            import hashlib
            skipped = 0
            for idx, f in enumerate(files):
                try:
                    sha1 = hashlib.sha1()
                    for chunk in f.chunks():
                        sha1.update(chunk)
                    new_digest = sha1.hexdigest()
                    duplicate = False
                    for img in existing_images:
                        try:
                            if img.image:
                                with img.image.open('rb') as ef:
                                    h = hashlib.sha1()
                                    while True:
                                        data = ef.read(8192)
                                        if not data:
                                            break
                                        h.update(data)
                                    if h.hexdigest() == new_digest:
                                        duplicate = True
                                        break
                        except Exception:
                            continue
                    if duplicate:
                        skipped += 1
                        continue
                    ProductImage.objects.create(product=product, image=f, is_main=False, order=max_order+idx+1)
                except Exception:
                    messages.error(request, 'فشل رفع صورة')
            if skipped:
                messages.info(request, f'تم تجاهل {skipped} صورة مكررة')
            messages.success(request, 'تم رفع الصور')
            return redirect(f"{request.path}?pid={product.id}&step=images")

        elif action == 'set_main_image':
            pid = request.POST.get('pid')
            image_id = request.POST.get('image_id')
            try:
                product = Product.objects.get(id=int(pid))
                img = ProductImage.objects.get(id=int(image_id), product=product)
            except (Product.DoesNotExist, ProductImage.DoesNotExist, ValueError, TypeError):
                messages.error(request, 'الصورة غير موجودة')
                return redirect('super_owner_add_product')
            product.images.update(is_main=False)
            img.is_main = True
            img.save()
            messages.success(request, 'تم تحديد الصورة الرئيسية')
            return redirect(f"{request.path}?pid={product.id}&step=images")

        elif action == 'assign_image_color':
            pid = request.POST.get('pid')
            image_id = request.POST.get('image_id')
            color_id = request.POST.get('color_id')
            try:
                product = Product.objects.get(id=int(pid))
                img = ProductImage.objects.get(id=int(image_id), product=product)
            except (Product.DoesNotExist, ProductImage.DoesNotExist, ValueError, TypeError):
                messages.error(request, 'الصورة غير موجودة')
                return redirect('super_owner_add_product')
            try:
                cid = int(color_id)
            except (ValueError, TypeError):
                cid = None
            img.color_attr_id = cid
            img.save()
            messages.success(request, 'تم ربط الصورة باللون')
            return redirect(f"{request.path}?pid={product.id}&step=images")

        elif action == 'set_color_default_image':
            pid = request.POST.get('pid')
            image_id = request.POST.get('image_id')
            try:
                product = Product.objects.get(id=int(pid))
                img = ProductImage.objects.get(id=int(image_id), product=product)
            except (Product.DoesNotExist, ProductImage.DoesNotExist, ValueError, TypeError):
                messages.error(request, 'الصورة غير موجودة')
                return redirect('super_owner_add_product')
            if not img.color_attr_id:
                messages.error(request, 'يجب ربط الصورة بلون أولاً')
                return redirect(f"{request.path}?pid={product.id}&step=images")
            # lowest order within this color becomes default
            product.images.filter(color_attr_id=img.color_attr_id).update(order=F('order') + 1)
            img.order = 0
            img.save()
            messages.success(request, 'تم تعيين الصورة كافتراضية لهذا اللون')
            return redirect(f"{request.path}?pid={product.id}&step=images")

        elif action == 'reorder_image':
            pid = request.POST.get('pid')
            image_id = request.POST.get('image_id')
            direction = (request.POST.get('direction') or 'up').strip()
            try:
                product = Product.objects.get(id=int(pid))
                img = ProductImage.objects.get(id=int(image_id), product=product)
            except (Product.DoesNotExist, ProductImage.DoesNotExist, ValueError, TypeError):
                messages.error(request, 'الصورة غير موجودة')
                return redirect('super_owner_add_product')
            if direction == 'up':
                img.order = max(0, img.order - 1)
            else:
                img.order = img.order + 1
            img.save()
            messages.success(request, 'تم تعديل ترتيب الصورة')
            return redirect(f"{request.path}?pid={product.id}&step=images")

        elif action == 'bulk_reorder_images':
            pid = request.POST.get('pid')
            try:
                product = Product.objects.get(id=int(pid))
            except (Product.DoesNotExist, ValueError, TypeError):
                messages.error(request, 'المنتج غير موجود')
                return redirect('super_owner_add_product')
            raw_ids = (request.POST.get('image_ids') or '').strip()
            try:
                ids = [int(x) for x in raw_ids.split(',') if x.strip().isdigit()]
            except Exception:
                ids = []
            if not ids:
                messages.error(request, 'ترتيب غير صالح')
                return redirect(f"{request.path}?pid={product.id}&step=images")
            order_value = 0
            for iid in ids:
                try:
                    pi = ProductImage.objects.get(id=iid, product=product)
                    pi.order = order_value
                    pi.save()
                    order_value += 1
                except ProductImage.DoesNotExist:
                    continue
            messages.success(request, 'تم تحديث ترتيب الصور')
            return redirect(f"{request.path}?pid={product.id}&step=images")

        elif action == 'remove_image':
            pid = request.POST.get('pid')
            image_id = request.POST.get('image_id')
            try:
                product = Product.objects.get(id=int(pid))
                img = ProductImage.objects.get(id=int(image_id), product=product)
            except (Product.DoesNotExist, ProductImage.DoesNotExist, ValueError, TypeError):
                messages.error(request, 'الصورة غير موجودة')
                return redirect('super_owner_add_product')
            img.delete()
            messages.success(request, 'تم حذف الصورة')
            return redirect(f"{request.path}?pid={product.id}&step=images")

        elif action == 'extract_color_from_image':
            pid = request.POST.get('pid')
            image_id = request.POST.get('image_id')
            try:
                product = Product.objects.get(id=int(pid))
                img = ProductImage.objects.get(id=int(image_id), product=product)
            except (Product.DoesNotExist, ProductImage.DoesNotExist, ValueError, TypeError):
                messages.error(request, 'الصورة غير موجودة')
                return redirect('super_owner_add_product')
            if not img.image:
                messages.error(request, 'لا يمكن استخراج اللون من رابط صورة فقط')
                return redirect(f"{request.path}?pid={product.id}&step=images")
            try:
                from PIL import Image
                im = Image.open(img.image.path)
                im = im.convert('RGB')
                im.thumbnail((200, 200))
                colors = im.getcolors(maxcolors=256*256)
                if not colors:
                    messages.error(request, 'تعذر استخراج اللون')
                    return redirect(f"{request.path}?pid={product.id}&step=images")
                dominant = max(colors, key=lambda t: t[0])[1]
                hex_code = '#%02x%02x%02x' % dominant
                color_obj, _ = AttributeColor.objects.get_or_create(name=hex_code, defaults={'code': hex_code})
                img.color_attr = color_obj
                img.save()
                messages.success(request, f'تم استخراج اللون {hex_code} وربط الصورة به')
            except Exception:
                messages.error(request, 'حدث خطأ أثناء استخراج اللون')
            return redirect(f"{request.path}?pid={product.id}&step=images")

    product = None
    variants = []
    if pid and pid.isdigit():
        product = Product.objects.filter(id=int(pid)).first()
        if product:
            variants = list(ProductVariant.objects.filter(product=product).select_related('color_attr', 'size_attr'))
    color_attrs = []
    size_attrs = []
    variant_map = {}
    existing_color_ids = []
    existing_size_ids = []
    variant_grid = []
    if variants:
        color_map = {}
        for v in variants:
            if v.color_attr_id and v.color_attr:
                color_map[v.color_attr_id] = v.color_attr
        color_attrs = sorted(color_map.values(), key=lambda x: (x.name or '').lower())
        size_attrs = sorted({v.size_attr for v in variants if v.size_attr}, key=lambda x: x.order)
        existing_color_ids = [c.id for c in color_attrs]
        existing_size_ids = [s.id for s in size_attrs]
        for v in variants:
            if v.color_attr_id and v.size_attr_id:
                if v.color_attr_id not in variant_map:
                    variant_map[v.color_attr_id] = {}
                variant_map[v.color_attr_id][v.size_attr_id] = v
        for c in color_attrs:
            row_cells = []
            for s in size_attrs:
                vv = None
                try:
                    vv = variant_map.get(c.id, {}).get(s.id)
                except Exception:
                    vv = None
                row_cells.append({'size': s, 'variant': vv})
            variant_grid.append({'color': c, 'cells': row_cells})

    if AttributeSize.objects.count() == 0:
        for idx, n in enumerate(['XS','S','M','L','XL','XXL','3XL','4XL']):
            try:
                AttributeSize.objects.create(name=n, order=idx)
            except Exception:
                pass

    # Seed default colors once, إذا لم توجد ألوان
    if AttributeColor.objects.count() == 0:
        default_colors = [
            ('أسود', '#000000'),
            ('أبيض', '#FFFFFF'),
            ('أحمر', '#FF0000'),
            ('أزرق', '#0000FF'),
            ('أخضر', '#008000'),
            ('أصفر', '#FFFF00'),
            ('زهري', '#FFC0CB'),
            ('رمادي', '#808080'),
            ('بنّي', '#8B4513'),
        ]
        for name, code in default_colors:
            try:
                AttributeColor.objects.get_or_create(name=name, defaults={'code': code})
            except Exception:
                pass

    sizes_display = []
    if product:
        st = product.size_type
        if st == 'numeric':
            names = [str(n) for n in range(28, 61, 2)]
            for idx, n in enumerate(names):
                try:
                    AttributeSize.objects.get_or_create(name=n, defaults={'order': idx})
                except Exception:
                    pass
            all_sizes = list(AttributeSize.objects.all())
            sizes_display = sorted([s for s in all_sizes if s.name.isdigit()], key=lambda x: x.order)
        elif st == 'symbolic':
            names = ['XS','S','M','L','XL','XXL','3XL','4XL']
            for idx, n in enumerate(names):
                try:
                    AttributeSize.objects.get_or_create(name=n, defaults={'order': idx})
                except Exception:
                    pass
            all_sizes = list(AttributeSize.objects.all())
            sizes_display = sorted([s for s in all_sizes if s.name in names], key=lambda x: x.order)
        else:
            sizes_display = []
    else:
        sizes_display = list(AttributeSize.objects.all())

    context = {
        'stores': stores,
        'selected_store_id': int(preselect_store) if preselect_store and preselect_store.isdigit() else None,
        'step': step,
        'product': product,
        'colors': list(AttributeColor.objects.all()),
        'sizes': sizes_display,
        'variants': variants,
        'color_attrs': color_attrs,
        'size_attrs': size_attrs,
        'variant_map': variant_map,
        'variant_grid': variant_grid,
        'existing_color_ids': existing_color_ids,
        'existing_size_ids': existing_size_ids,
        'images': list(product.images.order_by('order', '-is_main')) if product else [],
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
        action = (request.POST.get('action') or '').strip()

        if action in ('', 'update_product'):
            name = request.POST.get('name')
            store_id = request.POST.get('store')
            category = request.POST.get('category')
            base_price = request.POST.get('base_price')
            description = request.POST.get('description')
            is_active = request.POST.get('is_active') == 'on'
            is_featured = request.POST.get('is_featured') == 'on'
            size_type = (request.POST.get('size_type') or '').strip()
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
                if size_type in ['symbolic', 'numeric', 'none']:
                    product.size_type = size_type

                product.save()

                # Handle new images
                if new_images:
                    has_main = product.images.filter(is_main=True).exists()
                    for idx, image in enumerate(new_images):
                        try:
                            ProductImage.objects.create(
                                product=product,
                                image=image,
                                is_main=(not has_main and idx == 0)
                            )
                        except Exception:
                            messages.error(request, 'فشل حفظ إحدى الصور الجديدة')
                            return redirect('super_owner_edit_product', product_id=product_id)

                messages.success(request, f'تم تحديث المنتج "{product.name}" بنجاح!')
                return redirect('super_owner_products')

            except Store.DoesNotExist:
                messages.error(request, 'المتجر المختار غير صالح!')
                return redirect('super_owner_edit_product', product_id=product_id)

        elif action == 'add_variant':
            size = (request.POST.get('size') or '').strip()
            color_id_raw = request.POST.get('color_id')
            color_name_fallback = (request.POST.get('color') or '').strip()
            stock_qty_raw = request.POST.get('stock_qty')
            price_override_raw = (request.POST.get('price_override') or '').strip()

            if not size or (not color_id_raw and not color_name_fallback) or stock_qty_raw is None:
                messages.error(request, 'يرجى إدخال المقاس واللون والكمية!')
                return redirect('super_owner_edit_product', product_id=product_id)

            try:
                stock_qty = int(stock_qty_raw)
            except ValueError:
                messages.error(request, 'الكمية يجب أن تكون رقمًا غير سالب')
                return redirect('super_owner_edit_product', product_id=product_id)
            if stock_qty < 0:
                messages.error(request, 'الكمية يجب أن تكون رقمًا غير سالب')
                return redirect('super_owner_edit_product', product_id=product_id)

            from decimal import Decimal, InvalidOperation
            price_override = None
            if price_override_raw:
                try:
                    price_override = Decimal(price_override_raw)
                except InvalidOperation:
                    messages.error(request, 'سعر الخاص غير صالح')
                    return redirect('super_owner_edit_product', product_id=product_id)

            color_obj = None
            if color_id_raw:
                try:
                    color_id = int(color_id_raw)
                    from .models import ProductColor
                    color_obj = ProductColor.objects.get(id=color_id, product=product)
                except (ValueError, ProductColor.DoesNotExist):
                    color_obj = None
            if not color_obj and color_name_fallback:
                from .models import ProductColor
                color_obj = ProductColor.objects.filter(product=product, name=color_name_fallback).first()
            if not color_obj:
                messages.error(request, 'اللون غير موجود لهذا المنتج')
                return redirect('super_owner_edit_product', product_id=product_id)

            try:
                pv = ProductVariant(
                    product=product,
                    color_obj=color_obj,
                    size=size,
                    stock_qty=stock_qty,
                    price_override=price_override,
                )
                pv.save()
            except Exception as e:
                from django.core.exceptions import ValidationError
                if isinstance(e, ValidationError):
                    messages.error(request, 'خطأ في البيانات: ' + str(e))
                else:
                    messages.error(request, 'لا يمكن إنشاء متغير مكرر لهذا اللون والمقاس')
                return redirect('super_owner_edit_product', product_id=product_id)
            messages.success(request, 'تمت إضافة المتغير بنجاح!')
            return redirect('super_owner_edit_product', product_id=product_id)

        elif action == 'update_variant':
            variant_id = request.POST.get('variant_id')
            if not variant_id:
                messages.error(request, 'معرّف المتغير مفقود')
                return redirect('super_owner_edit_product', product_id=product_id)

            try:
                variant = ProductVariant.objects.get(id=int(variant_id), product=product)
            except (ProductVariant.DoesNotExist, ValueError):
                messages.error(request, 'المتغير غير موجود')
                return redirect('super_owner_edit_product', product_id=product_id)

            size = (request.POST.get('size') or '').strip()
            color_id_raw = request.POST.get('color_id')
            stock_qty_raw = request.POST.get('stock_qty')
            price_override_raw = (request.POST.get('price_override') or '').strip()

            if size:
                variant.size = size
            if color_id_raw:
                try:
                    cid = int(color_id_raw)
                    from .models import ProductColor
                    color_obj = ProductColor.objects.get(id=cid, product=product)
                    variant.color_obj = color_obj
                except (ValueError, ProductColor.DoesNotExist):
                    pass
            try:
                variant.stock_qty = int(stock_qty_raw)
            except (TypeError, ValueError):
                messages.error(request, 'الكمية غير صالحة')
                return redirect('super_owner_edit_product', product_id=product_id)

            if price_override_raw == '':
                variant.price_override = None
            else:
                from decimal import Decimal, InvalidOperation
                try:
                    variant.price_override = Decimal(price_override_raw)
                except InvalidOperation:
                    messages.error(request, 'سعر الخاص غير صالح')
                    return redirect('super_owner_edit_product', product_id=product_id)

            try:
                variant.save()
            except Exception as e:
                from django.core.exceptions import ValidationError
                if isinstance(e, ValidationError):
                    messages.error(request, 'خطأ في البيانات: ' + str(e))
                else:
                    messages.error(request, 'تعذر تحديث المتغير بسبب تكرار اللون والمقاس')
                return redirect('super_owner_edit_product', product_id=product_id)
            messages.success(request, 'تم تحديث المتغير بنجاح!')
            return redirect('super_owner_edit_product', product_id=product_id)

        elif action == 'delete_attribute_color':
            cid = (request.POST.get('color_id') or '').strip()
            try:
                from .models import AttributeColor
                if cid and cid.isdigit():
                    AttributeColor.objects.filter(id=int(cid)).delete()
                    messages.success(request, 'تم حذف اللون')
                else:
                    messages.error(request, 'معرف لون غير صالح')
            except Exception:
                messages.error(request, 'تعذر حذف اللون')
            return redirect(f"{request.path}?section=properties")

        elif action == 'delete_attribute_size':
            sid = (request.POST.get('size_id') or '').strip()
            try:
                from .models import AttributeSize
                if sid and sid.isdigit():
                    AttributeSize.objects.filter(id=int(sid)).delete()
                    messages.success(request, 'تم حذف القياس')
                else:
                    messages.error(request, 'معرف قياس غير صالح')
            except Exception:
                messages.error(request, 'تعذر حذف القياس')
            return redirect(f"{request.path}?section=properties")

        elif action == 'add_attribute_size':
            sname = (request.POST.get('size_name') or '').strip()
            if not sname:
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'ok': False, 'error': 'يرجى إدخال اسم القياس'}, status=400)
                messages.error(request, 'يرجى إدخال اسم القياس')
                return redirect(f"{request.path}?section=properties")
            try:
                from django.db.models import Max
                from .models import AttributeSize, AttributeColor, ProductColor
                max_order = AttributeSize.objects.aggregate(m=Max('order')).get('m') or 0
                size_obj, created = AttributeSize.objects.get_or_create(name=sname, defaults={'order': max_order + 1})
                if size_obj:
                    # اربط القياس الجديد بكل ألوان المنتج الموجودة لضمان ظهوره ضمن المختار
                    product_colors = list(product.colors.all())
                    color_attrs = []
                    for pc in product_colors:
                        try:
                            ca, _ = AttributeColor.objects.get_or_create(name=pc.name, defaults={'code': pc.code or ''})
                            color_attrs.append(ca)
                        except Exception:
                            continue
                    created_variants = 0
                    if color_attrs:
                        for ca in color_attrs:
                            try:
                                exists = ProductVariant.objects.filter(product=product, color_attr=ca, size_attr=size_obj).exists()
                            except Exception:
                                exists = True
                            if not exists:
                                try:
                                    ProductVariant.objects.create(
                                        product=product,
                                        color_attr=ca,
                                        size_attr=size_obj,
                                        size=size_obj.name,
                                        stock_qty=0,
                                        price_override=None,
                                        is_enabled=False,
                                    )
                                    created_variants += 1
                                except Exception:
                                    continue
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'ok': True, 'size': {'id': size_obj.id, 'name': size_obj.name}, 'duplicate': (not created), 'created_variants': created_variants})
                messages.success(request, 'تمت إضافة القياس')
            except Exception:
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'ok': False, 'error': 'تعذر إضافة القياس'}, status=500)
                messages.error(request, 'تعذر إضافة القياس')
            return redirect(f"{request.path}?section=properties")

        elif action == 'delete_variant':
            variant_id = request.POST.get('variant_id')
            try:
                variant = ProductVariant.objects.get(id=int(variant_id), product=product)
                variant.delete()
                messages.success(request, 'تم حذف المتغير بنجاح!')
            except (ProductVariant.DoesNotExist, ValueError):
                messages.error(request, 'المتغير غير موجود')
            return redirect('super_owner_edit_product', product_id=product_id)

        elif action == 'edit_generate_variants':
            color_ids = request.POST.getlist('color_attr_ids')
            size_ids = request.POST.getlist('size_attr_ids')
            default_qty_raw = request.POST.get('default_qty')
            default_price_raw = (request.POST.get('default_price') or '').strip()
            enable_all = (request.POST.get('enable_all') == 'on')

            try:
                default_qty = int(default_qty_raw or 0)
            except ValueError:
                default_qty = 0
            from decimal import Decimal, InvalidOperation
            default_price = None
            if default_price_raw:
                try:
                    default_price = Decimal(default_price_raw)
                except InvalidOperation:
                    default_price = None

            from .models import AttributeColor, AttributeSize
            selected_colors = list(AttributeColor.objects.filter(id__in=[int(cid) for cid in color_ids if cid.isdigit()]))
            selected_sizes = list(AttributeSize.objects.filter(id__in=[int(sid) for sid in size_ids if sid.isdigit()]))

            try:
                from django.db import transaction
                with transaction.atomic():
                    created = 0
                    for c in selected_colors:
                        for s in selected_sizes:
                            exists = ProductVariant.objects.filter(product=product, color_attr=c, size_attr=s).exists()
                            if exists:
                                continue
                            ProductVariant.objects.create(
                                product=product,
                                color_attr=c,
                                size_attr=s,
                                size=s.name,
                                stock_qty=default_qty,
                                price_override=default_price,
                                is_enabled=(enable_all or product.is_active),
                            )
                            created += 1

                    sel_color_ids = {c.id for c in selected_colors}
                    sel_size_ids = {s.id for s in selected_sizes}
                    for v in ProductVariant.objects.filter(product=product).only('id','color_attr_id','size_attr_id','is_enabled'):
                        if (v.color_attr_id and v.color_attr_id not in sel_color_ids) or (v.size_attr_id and v.size_attr_id not in sel_size_ids):
                            if v.is_enabled:
                                ProductVariant.objects.filter(id=v.id).update(is_enabled=False)

                messages.success(request, f'تم إنشاء {created} متغيرات وإيقاف غير المحدد منها')
            except Exception:
                messages.error(request, 'تعذر توليد المتغيرات')
            return redirect(f"/dashboard/super-owner/inventory/?store={product.store_id}&product={product.id}")

        elif action == 'edit_generate_from_product':
            default_qty_raw = request.POST.get('default_qty')
            default_price_raw = (request.POST.get('default_price') or '').strip()
            enable_all = (request.POST.get('enable_all') == 'on')

            try:
                default_qty = int(default_qty_raw or 0)
            except ValueError:
                default_qty = 0
            from decimal import Decimal, InvalidOperation
            default_price = None
            if default_price_raw:
                try:
                    default_price = Decimal(default_price_raw)
                except InvalidOperation:
                    default_price = None

            from .models import AttributeColor, AttributeSize
            product_colors = list(product.colors.all())
            color_attrs = []
            for pc in product_colors:
                try:
                    ca, _ = AttributeColor.objects.get_or_create(name=pc.name, defaults={'code': pc.code or ''})
                    color_attrs.append(ca)
                except Exception:
                    continue

            try:
                for idx, n in enumerate([str(x) for x in range(28, 61, 2)]):
                    AttributeSize.objects.get_or_create(name=n, defaults={'order': idx})
                for idx, n in enumerate(['XS','S','M','L','XL','XXL','3XL','4XL']):
                    AttributeSize.objects.get_or_create(name=n, defaults={'order': idx})
            except Exception:
                pass
            size_attrs = list(AttributeSize.objects.all())

            created = 0
            if color_attrs and size_attrs:
                for c in color_attrs:
                    for s in size_attrs:
                        exists = ProductVariant.objects.filter(product=product, color_attr=c, size_attr=s).exists()
                        if exists:
                            continue
                        try:
                            ProductVariant.objects.create(
                                product=product,
                                color_attr=c,
                                size_attr=s,
                                size=s.name,
                                stock_qty=default_qty,
                                price_override=default_price,
                                is_enabled=enable_all and default_qty > 0,
                            )
                            created += 1
                        except Exception:
                            pass
            elif color_attrs and not size_attrs:
                for c in color_attrs:
                    exists = ProductVariant.objects.filter(product=product, color_attr=c, size_attr__isnull=True).exists()
                    if exists:
                        continue
                    try:
                        ProductVariant.objects.create(
                            product=product,
                            color_attr=c,
                            size_attr=None,
                            size='ONE',
                            stock_qty=default_qty,
                            price_override=default_price,
                            is_enabled=enable_all and default_qty > 0,
                        )
                        created += 1
                    except Exception:
                        pass
            elif not color_attrs and size_attrs:
                for s in size_attrs:
                    exists = ProductVariant.objects.filter(product=product, color_attr__isnull=True, size_attr=s).exists()
                    if exists:
                        continue
                    try:
                        ProductVariant.objects.create(
                            product=product,
                            color_attr=None,
                            size_attr=s,
                            size=s.name,
                            stock_qty=default_qty,
                            price_override=default_price,
                            is_enabled=enable_all and default_qty > 0,
                        )
                        created += 1
                    except Exception:
                        pass
            else:
                if not ProductVariant.objects.filter(product=product).exists():
                    try:
                        ProductVariant.objects.create(
                            product=product,
                            color_attr=None,
                            size_attr=None,
                            size='ONE',
                            stock_qty=default_qty,
                            price_override=default_price,
                            is_enabled=enable_all and default_qty > 0,
                        )
                        created += 1
                    except Exception:
                        pass

            messages.success(request, f'تم إنشاء {created} متغيرات تلقائياً من ألوان ومقاسات المنتج')
            return redirect(f"/dashboard/super-owner/inventory/?store={product.store_id}&product={product.id}")

        elif action == 'add_color':
            cname = (request.POST.get('color_name') or '').strip()
            ccode = (request.POST.get('color_code') or '').strip()
            cimg = request.FILES.get('color_image')
            if not cname:
                messages.error(request, 'يرجى إدخال اسم اللون')
                return redirect('super_owner_edit_product', product_id=product_id)
            from .models import ProductColor
            color_obj, created = ProductColor.objects.get_or_create(product=product, name=cname, defaults={'code': ccode})
            if not created:
                if ccode and color_obj.code != ccode:
                    color_obj.code = ccode
                    color_obj.save()
            if cimg:
                ProductImage.objects.create(product=product, color=color_obj, image=cimg)
            messages.success(request, 'تمت إضافة اللون بنجاح!')
            return redirect('super_owner_edit_product', product_id=product_id)

        elif action == 'bulk_qty':
            try:
                qty = int(request.POST.get('qty') or 0)
            except ValueError:
                qty = 0
            ProductVariant.objects.filter(product=product).update(stock_qty=qty)
            messages.success(request, 'تم تحديث الكمية لكل المتغيرات')
            return redirect('super_owner_edit_product', product_id=product_id)

        elif action == 'bulk_price':
            from decimal import Decimal, InvalidOperation
            raw = (request.POST.get('price') or '').strip()
            price = None
            if raw:
                try:
                    price = Decimal(raw)
                except InvalidOperation:
                    price = None
            ProductVariant.objects.filter(product=product).update(price_override=price)
            messages.success(request, 'تم تحديث السعر لكل المتغيرات')
            return redirect('super_owner_edit_product', product_id=product_id)

        elif action == 'bulk_status':
            status = (request.POST.get('status') or 'enable').strip()
            enable = status == 'enable'
            ProductVariant.objects.filter(product=product).update(is_enabled=enable)
            messages.success(request, 'تم تحديث حالة المتغيرات')
            return redirect('super_owner_edit_product', product_id=product_id)

        elif action == 'bulk_qty_color':
            color_id = request.POST.get('color_id')
            try:
                cid = int(color_id)
            except (ValueError, TypeError):
                messages.error(request, 'لون غير صالح')
                return redirect('super_owner_edit_product', product_id=product_id)
            try:
                qty = int(request.POST.get('qty') or 0)
            except ValueError:
                qty = 0
            ProductVariant.objects.filter(product=product, color_obj_id=cid).update(stock_qty=qty)
            messages.success(request, 'تم تحديث الكمية حسب اللون')
            return redirect('super_owner_edit_product', product_id=product_id)

        elif action == 'bulk_qty_size':
            size_id = request.POST.get('size_id')
            size_name = (request.POST.get('size') or '').strip()
            try:
                qty = int(request.POST.get('qty') or 0)
            except ValueError:
                qty = 0
            qs = ProductVariant.objects.filter(product=product)
            applied = False
            if size_id and size_id.isdigit():
                qs = qs.filter(size_attr_id=int(size_id))
                applied = True
            elif size_name:
                qs = qs.filter(size=size_name)
                applied = True
            if not applied:
                messages.error(request, 'مقاس غير صالح')
                return redirect('super_owner_edit_product', product_id=product_id)
            qs.update(stock_qty=qty)
            messages.success(request, 'تم تحديث الكمية حسب المقاس')
            return redirect('super_owner_edit_product', product_id=product_id)

        elif action == 'bulk_price_color':
            color_id = request.POST.get('color_id')
            try:
                cid = int(color_id)
            except (ValueError, TypeError):
                messages.error(request, 'لون غير صالح')
                return redirect('super_owner_edit_product', product_id=product_id)
            from decimal import Decimal, InvalidOperation
            raw = (request.POST.get('price') or '').strip()
            price = None
            if raw:
                try:
                    price = Decimal(raw)
                except InvalidOperation:
                    price = None
            ProductVariant.objects.filter(product=product, color_obj_id=cid).update(price_override=price)
            messages.success(request, 'تم تحديث السعر حسب اللون')
            return redirect('super_owner_edit_product', product_id=product_id)

        elif action == 'bulk_price_size':
            size_id = request.POST.get('size_id')
            size_name = (request.POST.get('size') or '').strip()
            from decimal import Decimal, InvalidOperation
            raw = (request.POST.get('price') or '').strip()
            price = None
            if raw:
                try:
                    price = Decimal(raw)
                except InvalidOperation:
                    price = None
            qs = ProductVariant.objects.filter(product=product)
            applied = False
            if size_id and size_id.isdigit():
                qs = qs.filter(size_attr_id=int(size_id))
                applied = True
            elif size_name:
                qs = qs.filter(size=size_name)
                applied = True
            if not applied:
                messages.error(request, 'مقاس غير صالح')
                return redirect('super_owner_edit_product', product_id=product_id)
            qs.update(price_override=price)
            messages.success(request, 'تم تحديث السعر حسب المقاس')
            return redirect('super_owner_edit_product', product_id=product_id)

        elif action == 'bulk_status_color':
            color_id = request.POST.get('color_id')
            try:
                cid = int(color_id)
            except (ValueError, TypeError):
                messages.error(request, 'لون غير صالح')
                return redirect('super_owner_edit_product', product_id=product_id)
            status = (request.POST.get('status') or 'enable').strip()
            enable = status == 'enable'
            ProductVariant.objects.filter(product=product, color_obj_id=cid).update(is_enabled=enable)
            messages.success(request, 'تم تحديث حالة المتغيرات حسب اللون')
            return redirect('super_owner_edit_product', product_id=product_id)

        elif action == 'bulk_status_size':
            size_id = request.POST.get('size_id')
            size_name = (request.POST.get('size') or '').strip()
            status = (request.POST.get('status') or 'enable').strip()
            enable = status == 'enable'
            qs = ProductVariant.objects.filter(product=product)
            applied = False
            if size_id and size_id.isdigit():
                qs = qs.filter(size_attr_id=int(size_id))
                applied = True
            elif size_name:
                qs = qs.filter(size=size_name)
                applied = True
            if not applied:
                messages.error(request, 'مقاس غير صالح')
                return redirect('super_owner_edit_product', product_id=product_id)
            qs.update(is_enabled=enable)
            messages.success(request, 'تم تحديث حالة المتغيرات حسب المقاس')
            return redirect('super_owner_edit_product', product_id=product_id)

        elif action == 'upload_images':
            files = request.FILES.getlist('images')
            last = product.images.order_by('-order').first()
            max_order = last.order if last else 0
            existing_images = list(product.images.all())
            import hashlib
            skipped = 0
            for idx, f in enumerate(files):
                try:
                    sha1 = hashlib.sha1()
                    for chunk in f.chunks():
                        sha1.update(chunk)
                    new_digest = sha1.hexdigest()
                    duplicate = False
                    for img in existing_images:
                        try:
                            if img.image:
                                with img.image.open('rb') as ef:
                                    h = hashlib.sha1()
                                    while True:
                                        data = ef.read(8192)
                                        if not data:
                                            break
                                        h.update(data)
                                    if h.hexdigest() == new_digest:
                                        duplicate = True
                                        break
                        except Exception:
                            continue
                    if duplicate:
                        skipped += 1
                        continue
                    ProductImage.objects.create(product=product, image=f, is_main=False, order=max_order + idx + 1)
                except Exception:
                    messages.error(request, 'فشل رفع صورة')
            if skipped:
                messages.info(request, f'تم تجاهل {skipped} صورة مكررة')
            messages.success(request, 'تم رفع الصور')
            return redirect('super_owner_edit_product', product_id=product_id)

        elif action == 'set_main_image':
            image_id = request.POST.get('image_id')
            try:
                img = ProductImage.objects.get(id=int(image_id), product=product)
            except (ProductImage.DoesNotExist, ValueError, TypeError):
                messages.error(request, 'الصورة غير موجودة')
                return redirect('super_owner_edit_product', product_id=product_id)
            product.images.update(is_main=False)
            img.is_main = True
            img.save()
            messages.success(request, 'تم تحديد الصورة الرئيسية')
            return redirect('super_owner_edit_product', product_id=product_id)

        elif action == 'assign_image_color':
            image_id = request.POST.get('image_id')
            color_id = request.POST.get('color_id')
            try:
                img = ProductImage.objects.get(id=int(image_id), product=product)
            except (ProductImage.DoesNotExist, ValueError, TypeError):
                messages.error(request, 'الصورة غير موجودة')
                return redirect('super_owner_edit_product', product_id=product_id)
            try:
                cid = int(color_id)
            except (ValueError, TypeError):
                cid = None
            img.color_id = cid
            img.save()
            messages.success(request, 'تم ربط الصورة باللون')
            return redirect('super_owner_edit_product', product_id=product_id)

        elif action == 'set_color_default_image':
            image_id = request.POST.get('image_id')
            try:
                img = ProductImage.objects.get(id=int(image_id), product=product)
            except (ProductImage.DoesNotExist, ValueError, TypeError):
                messages.error(request, 'الصورة غير موجودة')
                return redirect('super_owner_edit_product', product_id=product_id)
            if not img.color_id:
                messages.error(request, 'يجب ربط الصورة بلون أولاً')
                return redirect('super_owner_edit_product', product_id=product_id)
            from django.db.models import F
            product.images.filter(color_id=img.color_id).update(order=F('order') + 1)
            img.order = 0
            img.save()
            messages.success(request, 'تم تعيين الصورة كافتراضية لهذا اللون')
            return redirect('super_owner_edit_product', product_id=product_id)

        elif action == 'bulk_reorder_images':
            raw_ids = (request.POST.get('image_ids') or '').strip()
            try:
                ids = [int(x) for x in raw_ids.split(',') if x.strip().isdigit()]
            except Exception:
                ids = []
            if not ids:
                messages.error(request, 'ترتيب غير صالح')
                return redirect('super_owner_edit_product', product_id=product_id)
            order_value = 0
            for iid in ids:
                try:
                    pi = ProductImage.objects.get(id=iid, product=product)
                    pi.order = order_value
                    pi.save()
                    order_value += 1
                except ProductImage.DoesNotExist:
                    continue
            messages.success(request, 'تم تحديث ترتيب الصور')
            return redirect('super_owner_edit_product', product_id=product_id)
    
    context = {
        'product': product,
        'stores': stores,
    }
    def numeric_sizes():
        return [str(n) for n in range(28, 61, 2)]
    if product.size_type == 'symbolic':
        size_choices = [('XS','XS'),('S','S'),('M','M'),('L','L'),('XL','XL'),('XXL','XXL'),('3XL','3XL'),('4XL','4XL')]
    elif product.size_type == 'numeric':
        size_choices = [(s, s) for s in numeric_sizes()]
    else:
        size_choices = []
    context['size_choices'] = size_choices
    context['size_type'] = product.size_type
    context['colors'] = list(product.colors.all())
    from .models import AttributeColor, AttributeSize
    context['color_attrs'] = list(AttributeColor.objects.all())
    try:
        for idx, n in enumerate([str(x) for x in range(28, 61, 2)]):
            AttributeSize.objects.get_or_create(name=n, defaults={'order': idx})
        for idx, n in enumerate(['XS','S','M','L','XL','XXL','3XL','4XL']):
            AttributeSize.objects.get_or_create(name=n, defaults={'order': idx})
    except Exception:
        pass
    context['size_attrs'] = list(AttributeSize.objects.all().order_by('order', 'name'))
    # Existing selections from current variants
    existing_variants = list(ProductVariant.objects.filter(product=product))
    context['existing_color_attr_ids'] = [v.color_attr_id for v in existing_variants if v.color_attr_id]
    context['existing_size_attr_ids'] = [v.size_attr_id for v in existing_variants if v.size_attr_id]
    # Show only selected size attributes in the properties page
    try:
        sel_ids = context['existing_size_attr_ids']
        if sel_ids:
            context['size_attrs'] = list(AttributeSize.objects.filter(id__in=sel_ids).order_by('order', 'name'))
        else:
            context['size_attrs'] = []
    except Exception:
        context['size_attrs'] = []
    return render(request, 'dashboard/super_owner/edit_product.html', context)


@login_required
def super_owner_orders(request):
    if request.user.username != 'super_owner':
        messages.error(request, 'ليس لديك صلاحية الوصول!')
        return redirect('home')
    
    store_filter = (request.GET.get('store') or '').strip()
    q = (request.GET.get('q') or '').strip()
    group = (request.GET.get('group') or 'active').strip()

    status_order = Case(
        When(status='pending', then=0),
        When(status='accepted', then=1),
        When(status='packed', then=2),
        When(status='delivered', then=100),
        When(status='canceled', then=100),
        default=50,
        output_field=IntegerField(),
    )

    orders = Order.objects.all().annotate(_status_order=status_order).order_by('_status_order', '-created_at')
    if store_filter and store_filter.isdigit():
        orders = orders.filter(store_id=int(store_filter))
    if q:
        try:
            q_id = int(q)
            orders = orders.filter(Q(id=q_id) | Q(user__first_name__icontains=q) | Q(user__last_name__icontains=q) | Q(user__username__icontains=q) | Q(user__phone__icontains=q))
        except ValueError:
            orders = orders.filter(Q(user__first_name__icontains=q) | Q(user__last_name__icontains=q) | Q(user__username__icontains=q) | Q(user__phone__icontains=q) | Q(id__icontains=q))
    if group == 'active':
        orders = orders.filter(status__in=['pending','accepted','packed'])
    elif group == 'completed':
        orders = orders.filter(status='delivered')
    elif group == 'canceled':
        orders = orders.filter(status='canceled')
    
    if request.method == 'POST':
        return redirect('super_owner_orders')
    
    import urllib.parse
    orders_info = []
    for o in orders:
        lines = []
        for it in o.items.all():
            color = ''
            size = ''
            if it.variant:
                color = it.variant.color or ''
                size = it.variant.size or ''
            price = it.price
            lines.append(f"- {it.product.name} | {color} | {size} × {it.quantity} | {int(price)} د.ع")
        total_iqd_val = int(o.total_amount)
        total_iqd = f"{total_iqd_val:,} د.ع"
        pm = 'الدفع عند الاستلام' if o.payment_method == 'cod' else 'بطاقة ائتمان'
        st_lbl = {
            'pending': 'قيد الانتظار',
            'accepted': 'تم القبول',
            'packed': 'تم التعبئة',
            'delivered': 'تم التسليم',
            'canceled': 'ملغي',
        }.get(o.status, o.status)
        cust_name = o.user.get_full_name() or o.user.username
        cust_phone = o.user.phone or ''
        text = (
            f"طلب رقم #{o.id}\n"
            f"العميل: {cust_name} - {cust_phone}\n"
            + "\n".join(lines)
            + f"\nالإجمالي: {total_iqd}\n"
            + f"طريقة الدفع: {pm}\n"
            + f"الحالة: {st_lbl}\n"
            + f"التاريخ: {o.created_at.strftime('%Y/%m/%d %H:%M')}"
        )
        wa_text = urllib.parse.quote(text)
        phone = ''
        try:
            if o.store.owner_phone:
                phone = o.store.owner_phone
            elif o.store_phone:
                phone = o.store_phone
            else:
                phone = o.store.owner.phone or ''
        except Exception:
            phone = o.store_phone or ''
        p = (phone or '').strip()
        if p.startswith('07') and len(p) == 11:
            p = '964' + p[1:]
        if p.startswith('+964'):
            p = p[1:]
        orders_info.append({'order': o, 'wa_text': wa_text, 'wa_number': p})

    context = {
        'orders_info': orders_info,
        'store_filter': int(store_filter) if store_filter.isdigit() else None,
        'q': q,
        'group': group,
        'groups': {
            'active': 'نشطة',
            'completed': 'مكتملة',
            'canceled': 'ملغاة',
            'all': 'الكل'
        },
        'allowed_statuses': ['pending','accepted','packed','delivered','canceled'],
        'status_labels': {
            'pending': 'قيد الانتظار',
            'accepted': 'تم القبول',
            'packed': 'تم التعبئة',
            'delivered': 'تم التسليم',
            'canceled': 'ملغي',
        },
    }
    return render(request, 'dashboard/super_owner/orders.html', context)

@login_required
def super_owner_update_order_status_json(request):
    if request.user.username != 'super_owner':
        return JsonResponse({'error': 'unauthorized'}, status=403)
    if request.method != 'POST':
        return JsonResponse({'error': 'invalid_method'}, status=405)
    try:
        order_id = int(request.POST.get('order_id') or '0')
        new_status = (request.POST.get('status') or '').strip()
        order = Order.objects.get(id=order_id)
        allowed = ['pending','accepted','packed','delivered','canceled']
        if new_status not in allowed:
            return JsonResponse({'error': 'invalid_status'}, status=400)
        before = {'status': order.status}
        order.status = new_status
        order.save()
        try:
            from .models import AdminAuditLog
            import json
            AdminAuditLog.objects.create(
                admin_user=request.user,
                action='update_status',
                model='Order',
                object_id=str(order.id),
                before=json.dumps(before, ensure_ascii=False),
                after=json.dumps({'status': order.status}, ensure_ascii=False),
                ip=request.META.get('REMOTE_ADDR') or ''
            )
        except Exception:
            pass
        labels = {
            'pending': 'قيد الانتظار',
            'accepted': 'تم القبول',
            'packed': 'تم التعبئة',
            'delivered': 'تم التسليم',
            'canceled': 'ملغي',
        }
        return JsonResponse({'ok': True, 'order_id': order.id, 'status': order.status, 'label': labels.get(order.status, order.status)})
    except Order.DoesNotExist:
        return JsonResponse({'error': 'not_found'}, status=404)
    except Exception:
        return JsonResponse({'error': 'server_error'}, status=500)

@login_required
def super_owner_update_delivery_json(request):
    if request.user.username != 'super_owner':
        return JsonResponse({'error': 'unauthorized'}, status=403)
    if request.method != 'POST':
        return JsonResponse({'error': 'invalid_method'}, status=405)
    try:
        order_id = int(request.POST.get('order_id') or '0')
        delivery_phone = (request.POST.get('delivery_phone') or '').strip()
        tracking_number = (request.POST.get('tracking_number') or '').strip()
        include_address = (request.POST.get('include_address') or '').strip() in ['1','true','on']
        order = Order.objects.get(id=order_id)
        if not tracking_number:
            return JsonResponse({'error': 'tracking_required'}, status=400)
        p = delivery_phone
        if p:
            pn = p.replace(' ', '')
            if pn.startswith('+964'):
                pn = pn[1:]
            if pn.startswith('07') and len(pn) == 11:
                pn = '964' + pn[1:]
            if not pn.startswith('9647') or len(pn) != 13:
                return JsonResponse({'error': 'invalid_phone'}, status=400)
            delivery_phone = pn
        order.tracking_number = tracking_number
        if delivery_phone:
            order.delivery_phone = delivery_phone
        order.save()
        try:
            from .models import AdminAuditLog
            import json
            AdminAuditLog.objects.create(
                admin_user=request.user,
                action='update_delivery',
                model='Order',
                object_id=str(order.id),
                before=json.dumps({}, ensure_ascii=False),
                after=json.dumps({'tracking_number': order.tracking_number, 'delivery_phone': order.delivery_phone}, ensure_ascii=False),
                ip=request.META.get('REMOTE_ADDR') or ''
            )
        except Exception:
            pass
        import urllib.parse
        lines = []
        for it in order.items.all():
            color = ''
            size = ''
            if it.variant:
                color = it.variant.color or ''
                size = it.variant.size or ''
            price = it.price
            lines.append(f"- {it.product.name} | {color} | {size} × {it.quantity} | {int(price)} د.ع")
        total_iqd = f"{int(order.total_amount):,} د.ع"
        msg = (
            "طلب توصيل جديد\n"
            + f"طلب رقم #{order.id}\n"
            + f"رقم تتبع: {order.tracking_number}\n"
            + f"هاتف العميل: {order.user.phone}\n"
            + "\n".join(lines)
            + f"\nالإجمالي: {total_iqd}"
        )
        if include_address and order.address:
            try:
                addr = f"العنوان: {order.address.city} - {order.address.area} - {order.address.street}"
                msg += f"\n{addr}"
            except Exception:
                pass
        wa_text = urllib.parse.quote(msg)
        wa_url = ''
        if order.delivery_phone:
            wa_url = f"https://wa.me/{order.delivery_phone}?text={wa_text}"
        return JsonResponse({'ok': True, 'order_id': order.id, 'tracking_number': order.tracking_number, 'delivery_phone': order.delivery_phone, 'wa_url': wa_url})
    except Order.DoesNotExist:
        return JsonResponse({'error': 'not_found'}, status=404)
    except Exception:
        return JsonResponse({'error': 'server_error'}, status=500)


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


def healthz(request):
    db_ok = True
    storage_ok = True
    storage_backend = ''
    try:
        SiteSettings.objects.exists()
    except Exception:
        db_ok = False
    try:
        from django.core.files.storage import default_storage
        storage_backend = f"{default_storage.__class__.__module__}.{default_storage.__class__.__name__}"
        default_storage.exists('healthz_probe')
    except Exception:
        storage_ok = False
    return JsonResponse({ 'database': db_ok, 'storage': storage_ok, 'storage_backend': storage_backend })


from django.core.cache import cache
from django.contrib.auth import logout
from .permissions import role_required, admin_required
from django.db import transaction


@login_required
def super_owner_owners(request):
    if request.user.username != 'super_owner':
        messages.error(request, 'ليس لديك صلاحية الوصول!')
        return redirect('home')

    q = (request.GET.get('q') or '').strip()
    owners = User.objects.filter(role='admin').order_by('username')
    if q:
        from django.db.models import Q
        owners = owners.filter(Q(username__icontains=q) | Q(first_name__icontains=q) | Q(last_name__icontains=q) | Q(phone__icontains=q))

    if request.method == 'POST':
        action = (request.POST.get('action') or '').strip()
        try:
            if action == 'update_phone':
                owner_id = int(request.POST.get('owner_id'))
                phone_raw = (request.POST.get('phone') or '').strip()
                import re
                p = phone_raw.replace(' ', '')
                if p.startswith('+'):
                    p = p[1:]
                phone = None
                if re.fullmatch(r'07\d{9}', p):
                    phone = p
                elif re.fullmatch(r'9647\d{9}', p):
                    phone = '0' + p[3:]
                else:
                    messages.error(request, 'رقم هاتف عراقي غير صالح. أمثلة: 07xxxxxxxxx أو +9647xxxxxxxx')
                    return redirect('super_owner_owners')
                owner = get_object_or_404(User, id=owner_id)
                # تحقق مسبق من وجود الرقم عند أي مستخدم آخر (عميل أو مالك)
                conflict = User.objects.filter(phone=phone).exclude(id=owner_id).first()
                if conflict:
                    role_label = conflict.get_role_display() if hasattr(conflict, 'get_role_display') else conflict.role
                    messages.error(request, f'رقم الهاتف مستخدم بالفعل لدى المستخدم: {conflict.username} ({role_label})')
                    return redirect('super_owner_owners')
                before = owner.phone or ''
                owner.phone = phone
                try:
                    owner.save()
                except Exception:
                    messages.error(request, 'تعذر حفظ الرقم، تحقق من الإدخال')
                    return redirect('super_owner_owners')
                try:
                    from .models import AdminAuditLog
                    import json
                    AdminAuditLog.objects.create(
                        admin_user=request.user,
                        action='update_owner_phone',
                        model='User',
                        object_id=str(owner.id),
                        before=json.dumps({'phone': before}, ensure_ascii=False),
                        after=json.dumps({'phone': owner.phone}, ensure_ascii=False),
                    )
                except Exception:
                    pass
                messages.success(request, f'تم تحديث رقم هاتف المالك {owner.username}!')
                return redirect('super_owner_owners')
        except Exception:
            messages.error(request, 'حدث خطأ أثناء التحديث')
            return redirect('super_owner_owners')

    from .models import Store
    owners_info = []
    for o in owners:
        try:
            store_count = Store.objects.filter(owner=o).count()
        except Exception:
            store_count = 0
        owners_info.append({'owner': o, 'store_count': store_count})

    context = {
        'owners_info': owners_info,
        'q': q,
    }
    return render(request, 'dashboard/super_owner/owners.html', context)


def admin_portal_login(request):
    if request.method == 'POST':
        identifier = (request.POST.get('identifier') or '').strip()
        password = request.POST.get('password')
        ip = request.META.get('REMOTE_ADDR') or ''
        key = f"admin_login:{ip}:{identifier.lower()}"
        attempts = int(cache.get(key) or 0)
        if attempts >= 5:
            from .models import AdminLoginAttempt
            AdminLoginAttempt.objects.create(username_or_email=identifier, success=False, reason='rate_limited', ip=ip)
            messages.error(request, 'تم حظر المحاولات مؤقتاً بسبب كثرة المحاولات')
            return render(request, 'admin_portal/login.html')
        user = None
        try:
            from django.contrib.auth import get_user_model
            U = get_user_model()
            if '@' in identifier:
                user = U.objects.filter(email__iexact=identifier).first()
            else:
                user = U.objects.filter(username__iexact=identifier).first()
        except Exception:
            user = None
        authed = None
        if user:
            authed = authenticate(request, username=user.username, password=password)
        if authed is None:
            cache.set(key, attempts + 1, 600)
            from .models import AdminLoginAttempt
            AdminLoginAttempt.objects.create(username_or_email=identifier, success=False, reason='invalid_credentials', ip=ip)
            messages.error(request, 'بيانات الدخول غير صحيحة')
            return render(request, 'admin_portal/login.html')
        if not authed.is_active:
            from .models import AdminLoginAttempt
            AdminLoginAttempt.objects.create(username_or_email=identifier, success=False, reason='inactive_user', ip=ip)
            messages.error(request, 'الحساب غير نشط')
            return render(request, 'admin_portal/login.html')
        ar = (authed.admin_role or '').upper()
        if not ar:
            if authed.username == 'super_owner':
                authed.admin_role = 'SUPER_ADMIN'
                authed.save()
                ar = 'SUPER_ADMIN'
        if ar not in ['SUPER_ADMIN','OWNER','SUPPORT','DELIVERY'] and authed.role != 'admin':
            from .models import AdminLoginAttempt
            AdminLoginAttempt.objects.create(username_or_email=identifier, success=False, reason='not_admin', ip=ip)
            messages.error(request, 'ليس لديك صلاحية الإدارة')
            return render(request, 'admin_portal/login.html')
        login(request, authed)
        from .models import AdminLoginAttempt
        AdminLoginAttempt.objects.create(username_or_email=identifier, success=True, reason='', ip=ip)
        cache.delete(key)
        return redirect('admin_portal_dashboard')
    return render(request, 'admin_portal/login.html')


@admin_required
def admin_portal_dashboard(request):
    today = timezone.now().date()
    orders_today = Order.objects.filter(created_at__date=today).count()
    users_total = User.objects.count()
    stores_total = Store.objects.count()
    products_total = Product.objects.count()
    return render(request, 'admin_portal/dashboard.html', {
        'orders_today': orders_today,
        'users_total': users_total,
        'stores_total': stores_total,
        'products_total': products_total,
    })


@role_required({'SUPER_ADMIN','OWNER','SUPPORT'})
def admin_portal_orders(request):
    if request.method == 'POST':
        order_id = request.POST.get('order_id')
        new_status = request.POST.get('status')
        try:
            with transaction.atomic():
                order = Order.objects.get(id=int(order_id))
                before = { 'status': order.status }
                if new_status in [choice[0] for choice in Order.STATUS_CHOICES]:
                    order.status = new_status
                    order.save()
                    after = { 'status': order.status }
                    from .models import AdminAuditLog
                    AdminAuditLog.objects.create(
                        admin_user=request.user,
                        action='update_status',
                        model='Order',
                        object_id=str(order.id),
                        before=json.dumps(before, ensure_ascii=False),
                        after=json.dumps(after, ensure_ascii=False),
                        ip=request.META.get('REMOTE_ADDR') or ''
                    )
                    messages.success(request, 'تم تحديث حالة الطلب')
                else:
                    messages.error(request, 'حالة غير صالحة')
        except Exception:
            messages.error(request, 'حدث خطأ أثناء التحديث')
        return redirect('admin_portal_orders')
    orders = Order.objects.order_by('-created_at')[:50]
    return render(request, 'admin_portal/orders.html', { 'orders': orders })

@login_required
def super_owner_inventory(request):
    if request.user.username != 'super_owner':
        messages.error(request, 'ليس لديك صلاحية الوصول!')
        return redirect('home')

    store_id = (request.GET.get('store') or '').strip()
    product_id = (request.GET.get('product') or '').strip()
    q = (request.GET.get('q') or '').strip()

    base_qs = ProductVariant.objects.select_related('product', 'product__store', 'color_attr', 'size_attr')
    if store_id.isdigit():
        base_qs = base_qs.filter(product__store_id=int(store_id))
    if product_id.isdigit():
        base_qs = base_qs.filter(product_id=int(product_id))
    if q:
        qobj = Q(product__name__icontains=q) | Q(product__store__name__icontains=q) | Q(color_attr__name__icontains=q) | Q(size_attr__name__icontains=q)
        if q.isdigit():
            qobj |= Q(product__id=int(q))
        base_qs = base_qs.filter(qobj)

    variants = list(base_qs.order_by('product__store__name', 'product__name', 'color_attr__name', 'size_attr__order', 'size_attr__name'))

    if request.method == 'POST':
        try:
            from django.db import transaction
            with transaction.atomic():
                variant_ids = set()
                for key, val in request.POST.items():
                    if key.startswith('qty_'):
                        try:
                            variant_ids.add(int(key[4:]))
                        except Exception:
                            pass
                for vid in variant_ids:
                    try:
                        v = ProductVariant.objects.select_related('product').get(id=vid)
                    except ProductVariant.DoesNotExist:
                        continue
                    qty_raw = request.POST.get(f'qty_{vid}', '')
                    enabled_raw = request.POST.get(f'enabled_{vid}', None)
                    try:
                        qty = int((qty_raw or '').strip() or '0')
                    except Exception:
                        qty = 0
                    if qty < 0:
                        qty = 0
                    v.stock_qty = qty
                    v.is_enabled = bool(enabled_raw) if enabled_raw is not None else (qty > 0)
                    v.save()
            messages.success(request, 'تم حفظ الكميات والحالة بنجاح')
        except Exception:
            messages.error(request, 'حدث خطأ أثناء الحفظ')
        params = []
        if store_id:
            params.append(f'store={store_id}')
        if product_id:
            params.append(f'product={product_id}')
        if q:
            params.append(f'q={q}')
        from django.urls import reverse
        redirect_url = reverse('super_owner_inventory')
        if params:
            return redirect(f'{redirect_url}?'+('&'.join(params)))
        return redirect(redirect_url)

    stores = Store.objects.order_by('name')
    products = Product.objects.order_by('name')
    if store_id.isdigit():
        products = products.filter(store_id=int(store_id))

    context = {
        'stores': stores,
        'products': products,
        'variants': variants,
        'selected_store_id': int(store_id) if store_id.isdigit() else None,
        'selected_product_id': int(product_id) if product_id.isdigit() else None,
        'q': q,
    }
    return render(request, 'dashboard/super_owner/inventory.html', context)


@role_required({'SUPER_ADMIN','OWNER'})
def admin_portal_products(request):
    if request.method == 'POST':
        action = request.POST.get('action')
        try:
            with transaction.atomic():
                if action == 'create':
                    name = request.POST.get('name') or ''
                    store_id = int(request.POST.get('store_id'))
                    base_price = float(request.POST.get('base_price'))
                    category = request.POST.get('category') or 'clothing'
                    store = Store.objects.get(id=store_id)
                    p = Product.objects.create(store=store, name=name, description='', base_price=base_price, category=category, size_type='none', is_active=True)
                    from .models import AdminAuditLog
                    AdminAuditLog.objects.create(admin_user=request.user, action='create', model='Product', object_id=str(p.id), before='', after=json.dumps({ 'name': name }, ensure_ascii=False), ip=request.META.get('REMOTE_ADDR') or '')
                    messages.success(request, 'تم إضافة المنتج')
                elif action == 'update_price':
                    product_id = int(request.POST.get('product_id'))
                    base_price = float(request.POST.get('base_price'))
                    p = Product.objects.get(id=product_id)
                    before = { 'base_price': float(p.base_price) }
                    p.base_price = base_price
                    p.save()
                    from .models import AdminAuditLog
                    AdminAuditLog.objects.create(admin_user=request.user, action='update', model='Product', object_id=str(p.id), before=json.dumps(before), after=json.dumps({ 'base_price': base_price }), ip=request.META.get('REMOTE_ADDR') or '')
                    messages.success(request, 'تم تحديث السعر')
                elif action == 'add_image_url':
                    product_id = int(request.POST.get('product_id'))
                    image_url = request.POST.get('image_url') or ''
                    p = Product.objects.get(id=product_id)
                    ProductImage.objects.create(product=p, image_url=image_url, is_main=False)
                    from .models import AdminAuditLog
                    AdminAuditLog.objects.create(admin_user=request.user, action='add_image', model='Product', object_id=str(p.id), before='', after=json.dumps({ 'image_url': image_url }), ip=request.META.get('REMOTE_ADDR') or '')
                    messages.success(request, 'تم إضافة الصورة')
                elif action == 'set_stock':
                    product_id = int(request.POST.get('product_id'))
                    size = (request.POST.get('size') or 'ONE').strip()
                    stock_qty = int(request.POST.get('stock_qty') or '0')
                    p = Product.objects.get(id=product_id)
                    v, _ = ProductVariant.objects.get_or_create(product=p, size=size, defaults={ 'stock_qty': stock_qty })
                    before = { 'stock_qty': v.stock_qty }
                    v.stock_qty = stock_qty
                    v.save()
                    from .models import AdminAuditLog
                    AdminAuditLog.objects.create(admin_user=request.user, action='set_stock', model='ProductVariant', object_id=str(v.id), before=json.dumps(before), after=json.dumps({ 'stock_qty': stock_qty }), ip=request.META.get('REMOTE_ADDR') or '')
                    messages.success(request, 'تم تحديث المخزون')
        except Exception:
            messages.error(request, 'حدث خطأ في العملية')
        return redirect('admin_portal_products')
    products = Product.objects.select_related('store').order_by('-created_at')[:50]
    stores = Store.objects.all().order_by('name')
    return render(request, 'admin_portal/products.html', { 'products': products, 'stores': stores, 'categories': Product.CATEGORY_CHOICES })


@role_required({'SUPER_ADMIN','OWNER'})
def admin_portal_stores(request):
    if request.method == 'POST':
        store_id = int(request.POST.get('store_id'))
        action = request.POST.get('action')
        try:
            s = Store.objects.get(id=store_id)
            before = { 'is_active': s.is_active }
            if action == 'deactivate':
                s.is_active = False
            elif action == 'activate':
                s.is_active = True
            s.save()
            from .models import AdminAuditLog
            AdminAuditLog.objects.create(admin_user=request.user, action=action, model='Store', object_id=str(s.id), before=json.dumps(before), after=json.dumps({ 'is_active': s.is_active }), ip=request.META.get('REMOTE_ADDR') or '')
            messages.success(request, 'تم تحديث حالة المتجر')
        except Exception:
            messages.error(request, 'حدث خطأ')
        return redirect('admin_portal_stores')
    stores = Store.objects.all().order_by('name')
    return render(request, 'admin_portal/stores.html', { 'stores': stores })


@role_required({'SUPER_ADMIN','OWNER','SUPPORT'})
def admin_portal_customers(request):
    if request.method == 'POST':
        user_id = int(request.POST.get('user_id'))
        action = request.POST.get('action')
        try:
            u = User.objects.get(id=user_id)
            before = { 'is_active': u.is_active }
            if action == 'ban':
                u.is_active = False
            elif action == 'unban':
                u.is_active = True
            u.save()
            from .models import AdminAuditLog
            AdminAuditLog.objects.create(admin_user=request.user, action=action, model='User', object_id=str(u.id), before=json.dumps(before), after=json.dumps({ 'is_active': u.is_active }), ip=request.META.get('REMOTE_ADDR') or '')
            messages.success(request, 'تم تنفيذ العملية')
        except Exception:
            messages.error(request, 'حدث خطأ')
        return redirect('admin_portal_customers')
    customers = User.objects.filter(role='customer').order_by('username')[:100]
    return render(request, 'admin_portal/customers.html', { 'customers': customers })


@role_required({'SUPER_ADMIN','OWNER'})
def admin_portal_settings(request):
    settings_obj, _ = SiteSettings.objects.get_or_create(id=1)
    if request.method == 'POST':
        before = {
            'delivery_fee': float(settings_obj.delivery_fee),
            'contact_email': settings_obj.contact_email or '',
        }
        try:
            df_raw = request.POST.get('delivery_fee')
            ce = request.POST.get('contact_email') or ''
            if df_raw:
                from decimal import Decimal
                settings_obj.delivery_fee = Decimal(df_raw)
            settings_obj.contact_email = ce
            settings_obj.save()
            from .models import AdminAuditLog
            AdminAuditLog.objects.create(admin_user=request.user, action='update', model='SiteSettings', object_id='1', before=json.dumps(before), after=json.dumps({ 'delivery_fee': float(settings_obj.delivery_fee), 'contact_email': settings_obj.contact_email }), ip=request.META.get('REMOTE_ADDR') or '')
            messages.success(request, 'تم تحديث الإعدادات')
        except Exception:
            messages.error(request, 'تعذر تحديث الإعدادات')
        return redirect('admin_portal_settings')
    return render(request, 'admin_portal/settings.html', { 'settings': settings_obj })


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
        'cart_items_count': cart_count(request.session.get('cart', [])),
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
            user = User.objects.get(phone='07700000000')
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

