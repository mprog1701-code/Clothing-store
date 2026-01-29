from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.db.models import Q
from django.core.cache import cache
from .models import User, Store, Product, Address, Order, ProductVariant, ProductColor, ProductImage, AttributeColor, AttributeSize, FeatureFlag
import logging
import json
from urllib.request import Request, urlopen
from urllib.parse import urlencode
from urllib.error import URLError
from .serializers import (
    UserSerializer, UserRegistrationSerializer, StoreSerializer, 
    ProductSerializer, AddressSerializer, OrderSerializer, OrderCreateSerializer
)
from .permissions import (
    IsCustomer, IsStoreOwner, IsAdmin, IsStoreOwnerOfStore, 
    IsOwnerOfOrder, IsStoreOwnerOfOrder
)


class AuthViewSet(viewsets.ViewSet):
    @action(detail=False, methods=['post'], permission_classes=[])
    def register(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            refresh = RefreshToken.for_user(user)
            return Response({
                'user': UserSerializer(user).data,
                'access': str(refresh.access_token),
                'refresh': str(refresh)
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'], permission_classes=[])
    def login(self, request):
        ip = (request.META.get('HTTP_X_FORWARDED_FOR') or '').split(',')[0].strip() or (request.META.get('REMOTE_ADDR') or '')
        ident = (request.data.get('username') or request.data.get('phone') or '').strip()
        limit = 5
        window = 60
        def over(k):
            if not k:
                return False
            v = cache.get(k)
            if v is None:
                cache.set(k, 1, timeout=window)
                return False
            if v >= limit:
                return True
            try:
                cache.incr(k)
            except Exception:
                cache.set(k, (int(v) + 1), timeout=window)
            return False
        if over(f"rl:login:ip:{ip}") or over(f"rl:login:id:{ident}"):
            return Response({'error': 'rate_limited'}, status=status.HTTP_429_TOO_MANY_REQUESTS)
        username = request.data.get('username')
        password = request.data.get('password')
        
        user = authenticate(username=username, password=password)
        if user:
            refresh = RefreshToken.for_user(user)
            return Response({
                'user': UserSerializer(user).data,
                'access': str(refresh.access_token),
                'refresh': str(refresh)
            })
        return Response({'error': 'بيانات الدخول غير صحيحة'}, status=status.HTTP_401_UNAUTHORIZED)
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)


class StoreViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Store.objects.filter(is_active=True)
    serializer_class = StoreSerializer
    permission_classes = []
    
    def get_queryset(self):
        queryset = super().get_queryset()
        city = self.request.query_params.get('city')
        q = self.request.query_params.get('q')
        category = self.request.query_params.get('category')
        ordering = self.request.query_params.get('ordering')
        if city:
            queryset = queryset.filter(city=city)
        if category:
            queryset = queryset.filter(category=category)
        if q:
            queryset = queryset.filter(
                Q(name__icontains=q) | Q(description__icontains=q) | Q(city__icontains=q)
            )
        if ordering:
            allowed = ['name', '-name', 'created_at', '-created_at', 'rating', '-rating']
            if ordering in allowed:
                queryset = queryset.order_by(ordering)
        return queryset
    
    @action(detail=False, methods=['get', 'post', 'put', 'patch'], permission_classes=[IsStoreOwner])
    def my_store(self, request):
        try:
            store = Store.objects.get(owner=request.user)
        except Store.DoesNotExist:
            if request.method == 'GET':
                return Response({'detail': 'ليس لديك متجر'}, status=status.HTTP_404_NOT_FOUND)
            store = None
        
        if request.method == 'GET':
            serializer = StoreSerializer(store)
            return Response(serializer.data)
        
        if request.method in ['POST', 'PUT', 'PATCH']:
            if store and request.method == 'POST':
                return Response({'detail': 'لديك متجر بالفعل'}, status=status.HTTP_400_BAD_REQUEST)
            
            serializer = StoreSerializer(store, data=request.data, partial=request.method == 'PATCH')
            if serializer.is_valid():
                if not store:
                    serializer.save(owner=request.user)
                else:
                    serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Product.objects.filter(is_active=True)
    serializer_class = ProductSerializer
    permission_classes = []
    
    def get_queryset(self):
        queryset = super().get_queryset()
        store_id = self.request.query_params.get('store')
        category = self.request.query_params.get('category')
        city = self.request.query_params.get('city')
        q = self.request.query_params.get('q')
        min_price = self.request.query_params.get('min_price')
        max_price = self.request.query_params.get('max_price')
        ordering = self.request.query_params.get('ordering')
        if store_id:
            queryset = queryset.filter(store_id=store_id)
        if category:
            queryset = queryset.filter(category=category)
        if city:
            queryset = queryset.filter(store__city=city)
        if q:
            queryset = queryset.filter(Q(name__icontains=q) | Q(description__icontains=q) | Q(store__name__icontains=q))
        try:
            if min_price:
                queryset = queryset.filter(base_price__gte=float(min_price))
            if max_price:
                queryset = queryset.filter(base_price__lte=float(max_price))
        except ValueError:
            pass
        if ordering:
            allowed = ['created_at', '-created_at', 'base_price', '-base_price', 'rating', '-rating', 'name', '-name']
            if ordering in allowed:
                queryset = queryset.order_by(ordering)
        return queryset
    
    @action(detail=False, methods=['get', 'post', 'put', 'patch', 'delete'], permission_classes=[IsStoreOwner])
    def my_products(self, request):
        try:
            store = Store.objects.get(owner=request.user)
        except Store.DoesNotExist:
            return Response({'detail': 'ليس لديك متجر'}, status=status.HTTP_404_NOT_FOUND)
        
        if request.method == 'GET':
            products = Product.objects.filter(store=store)
            serializer = ProductSerializer(products, many=True)
            return Response(serializer.data)
        
        elif request.method == 'POST':
            serializer = ProductSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save(store=store)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['get'], url_path='sizes-for-color')
    def sizes_for_color(self, request, pk=None):
        color = (request.query_params.get('color') or '').strip()
        product = self.get_object()
        variants = product.variants.filter(color=color)
        data = [
            {
                'id': v.id,
                'size': v.size,
                'stock_qty': v.stock_qty,
                'price': float(v.price),
            }
            for v in variants
        ]
        return Response({'color': color, 'sizes': data})


class AddressViewSet(viewsets.ModelViewSet):
    serializer_class = AddressSerializer
    
    def get_queryset(self):
        return Address.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['post'], url_path='reverse-geocode', permission_classes=[])
    def reverse_geocode(self, request):
        """
        Accepts lat,lng and returns parsed address using OpenStreetMap Nominatim.
        Restricted to Iraq and Arabic language.
        """
        logger = logging.getLogger('geo')
        try:
            lat = float(request.data.get('lat') or request.data.get('latitude'))
            lon = float(request.data.get('lng') or request.data.get('longitude'))
        except Exception:
            return Response({'error': 'إحداثيات غير صالحة'}, status=status.HTTP_400_BAD_REQUEST)

        params = {
            'format': 'jsonv2',
            'lat': lat,
            'lon': lon,
            'accept-language': 'ar',
        }
        url = 'https://nominatim.openstreetmap.org/reverse?' + urlencode(params)
        try:
            req = Request(url, headers={'User-Agent': 'clothing-store/1.0 (contact: admin@example.com)'} )
            resp = urlopen(req, timeout=8)
            data = json.loads(resp.read().decode('utf-8'))
        except URLError as e:
            logger.error(f"reverse_geocode error: {e}")
            return Response({'error': 'تعذر التعرف على العنوان'}, status=status.HTTP_502_BAD_GATEWAY)
        except Exception as e:
            logger.error(f"reverse_geocode unexpected: {e}")
            return Response({'error': 'حدث خطأ غير متوقع'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        addr = data.get('address') or {}
        city = addr.get('city') or addr.get('town') or addr.get('village') or addr.get('state') or ''
        area = addr.get('suburb') or addr.get('neighbourhood') or addr.get('quarter') or addr.get('district') or addr.get('county') or ''
        street = (addr.get('road') or '') + (' ' + addr.get('house_number') if addr.get('house_number') else '')
        result = {
            'city': city,
            'area': area,
            'street': street.strip(),
            'formatted': data.get('display_name') or '',
            'provider': 'nominatim',
            'provider_place_id': str(data.get('place_id') or ''),
            'lat': lat,
            'lng': lon,
        }
        return Response(result)

    @action(detail=False, methods=['get'], url_path='autocomplete', permission_classes=[])
    def autocomplete(self, request):
        """
        Autocomplete by query using Nominatim search. Restricted to Iraq.
        """
        logger = logging.getLogger('geo')
        q = (request.query_params.get('q') or '').strip()
        if not q:
            return Response({'results': []})
        params = {
            'format': 'jsonv2',
            'q': q,
            'accept-language': 'ar',
            'countrycodes': 'iq',
            'limit': 6,
        }
        url = 'https://nominatim.openstreetmap.org/search?' + urlencode(params)
        try:
            req = Request(url, headers={'User-Agent': 'clothing-store/1.0 (contact: admin@example.com)'} )
            resp = urlopen(req, timeout=8)
            items = json.loads(resp.read().decode('utf-8'))
        except URLError as e:
            logger.error(f"autocomplete error: {e}")
            return Response({'results': []}, status=status.HTTP_502_BAD_GATEWAY)
        except Exception as e:
            logger.error(f"autocomplete unexpected: {e}")
            return Response({'results': []}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        results = []
        for it in (items or [])[:6]:
            addr = it.get('address') or {}
            city = addr.get('city') or addr.get('town') or addr.get('village') or addr.get('state') or ''
            area = addr.get('suburb') or addr.get('neighbourhood') or addr.get('quarter') or addr.get('district') or addr.get('county') or ''
            road = addr.get('road') or ''
            hn = addr.get('house_number') or ''
            street = (road + (' ' + hn if hn else '')).strip()
            results.append({
                'label': it.get('display_name') or street or city,
                'city': city,
                'area': area,
                'street': street,
                'lat': it.get('lat'),
                'lng': it.get('lon'),
                'provider': 'nominatim',
                'provider_place_id': str(it.get('place_id') or ''),
            })
        return Response({'results': results})


class FeatureFlagAdminList(APIView):
    permission_classes = [IsAdmin]
    def get(self, request):
        initial = ['NEW_ARRIVALS_SECTION', 'ADS_SECTION', 'OWNER_DASHBOARD_REPORTS']
        for k in initial:
            if not FeatureFlag.objects.filter(key=k).exists():
                FeatureFlag.objects.create(key=k, enabled=True, scope='global', store=None)
        items = FeatureFlag.objects.all().order_by('key')
        data = []
        for it in items:
            data.append({'key': it.key, 'enabled': bool(it.enabled), 'scope': it.scope, 'storeId': (it.store_id or None)})
        return Response({'flags': data})


class FeatureFlagAdminUpdate(APIView):
    permission_classes = [IsAdmin]
    def patch(self, request, key):
        enabled = request.data.get('enabled')
        scope = (request.data.get('scope') or '').strip() or None
        store_id = request.data.get('storeId')
        try:
            ff = FeatureFlag.objects.filter(key=key).first()
            if not ff:
                ff = FeatureFlag(key=key)
            if enabled is not None:
                ff.enabled = bool(enabled)
            if scope in ['global','store']:
                ff.scope = scope
            if store_id:
                try:
                    ff.store = Store.objects.get(id=int(store_id))
                except Exception:
                    ff.store = None
            if not store_id and (scope == 'global' or scope is None):
                ff.store = None
            ff.save()
            try:
                cache.delete('feature_flags_cache')
            except Exception:
                pass
            return Response({'key': ff.key, 'enabled': bool(ff.enabled), 'scope': ff.scope, 'storeId': (ff.store_id or None)})
        except Exception as e:
            return Response({'error': 'failed'}, status=status.HTTP_400_BAD_REQUEST)


class OrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderSerializer
    
    def get_queryset(self):
        user = self.request.user
        if user.role == 'customer':
            return Order.objects.filter(user=user)
        elif user.role == 'store_owner':
            return Order.objects.filter(store__owner=user)
        elif user.role == 'admin':
            return Order.objects.all()
        return Order.objects.none()
    
    def get_serializer_class(self):
        if self.action == 'create':
            
            return OrderCreateSerializer
        return OrderSerializer
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            try:
                order = serializer.save()
                return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)
            except Exception as e:
                return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['patch'], permission_classes=[IsStoreOwner])
    def update_status(self, request, pk=None):
        order = self.get_object()
        new_status = request.data.get('status')
        
        if new_status not in [choice[0] for choice in Order.STATUS_CHOICES]:
            return Response({'error': 'حالة غير صحيحة'}, status=status.HTTP_400_BAD_REQUEST)
        
        order.status = new_status
        order.save()
        
        serializer = OrderSerializer(order)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], permission_classes=[IsStoreOwner])
    def store_orders(self, request):
        orders = Order.objects.filter(store__owner=request.user)
        serializer = OrderSerializer(orders, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], permission_classes=[IsAdmin])
    def all_orders(self, request):
        orders = Order.objects.all()
        serializer = OrderSerializer(orders, many=True)
        return Response(serializer.data)

