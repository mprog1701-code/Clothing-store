from rest_framework import viewsets, status
from rest_framework.permissions import AllowAny
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
import os
from urllib.request import Request, urlopen
from urllib.parse import urlencode
from urllib.error import URLError, HTTPError
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
        phone = (request.data.get('phone') or '').strip()
        if phone and User.objects.filter(phone=phone).exists():
            return Response({'code': 'PHONE_ALREADY_HAS_ACCOUNT'}, status=status.HTTP_409_CONFLICT)
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            try:
                from django.utils import timezone
                from .models import StoreOwnerInvite, Store
                qs = StoreOwnerInvite.objects.filter(phone=user.phone, status='pending')
                now = timezone.now()
                qs = qs.filter(Q(expires_at__isnull=True) | Q(expires_at__gt=now))
                inv = qs.first()
                if inv:
                    user.role = 'store_admin'
                    user.is_staff = True
                    user.save()
                    try:
                        st = Store.objects.get(id=inv.store_id)
                        st.owner_user = user
                        st.save()
                    except Exception:
                        pass
                    inv.status = 'claimed'
                    try:
                        from django.utils import timezone as _tz
                        inv.claimed_at = _tz.now()
                    except Exception:
                        inv.claimed_at = None
                    inv.save()
            except Exception:
                pass
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
    queryset = Product.objects.filter(is_active=True, status='ACTIVE')
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

    @action(detail=False, methods=['get','post'], url_path='reverse-geocode', permission_classes=[AllowAny], authentication_classes=[])
    def reverse_geocode(self, request):
        """
        Accepts lat,lng and returns parsed address using OpenStreetMap Nominatim.
        Restricted to Iraq and Arabic language.
        """
        logger = logging.getLogger('geo')
        def _f(v):
            s = str(v).strip()
            s = s.replace('،', ',')
            if ('.' not in s) and (s.count(',') == 1):
                s = s.replace(',', '.')
            return float(s)
        try:
            lat = _f((request.data.get('lat') or request.query_params.get('lat') or request.data.get('latitude') or request.query_params.get('latitude')))
            lon = _f((request.data.get('lng') or request.query_params.get('lng') or request.data.get('longitude') or request.query_params.get('longitude')))
        except Exception:
            return Response({'error': 'إحداثيات غير صالحة'}, status=status.HTTP_400_BAD_REQUEST)

        mb_token = (os.environ.get('MAPBOX_ACCESS_TOKEN') or '').strip()
        g_key = (os.environ.get('MAPS_API_KEY') or '').strip()
        did_log = False
        if mb_token:
            try:
                mb_url = 'https://api.mapbox.com/geocoding/v5/mapbox.places/{},{}.json?'.format(lon, lat) + urlencode({'access_token': mb_token, 'language': 'ar', 'limit': 1})
                mb_req = Request(mb_url, headers={'User-Agent': 'clothing-store/1.0'})
                mb_resp = urlopen(mb_req, timeout=8)
                mb_data = json.loads(mb_resp.read().decode('utf-8'))
                feats = (mb_data.get('features') or [])
                if feats:
                    it = feats[0]
                    label = it.get('place_name') or ''
                    ctx = it.get('context') or []
                    city = ''
                    area = ''
                    street = ''
                    for c in ctx:
                        tid = c.get('id') or ''
                        if tid.startswith('place') and not city:
                            city = c.get('text') or ''
                        elif tid.startswith('locality') and not area:
                            area = c.get('text') or ''
                        elif tid.startswith('neighborhood') and not area:
                            area = c.get('text') or ''
                    if not did_log:
                        try:
                            logger.info(f"reverse_geocode provider=mapbox status=200")
                            did_log = True
                        except Exception:
                            pass
                    return Response({'city': city, 'area': area, 'street': street, 'formatted': label, 'provider': 'mapbox', 'provider_place_id': str(it.get('id') or ''), 'lat': lat, 'lng': lon})
                if not did_log:
                    try:
                        logger.info(f"reverse_geocode provider=mapbox status=200")
                        did_log = True
                    except Exception:
                        pass
                return Response({'city': '', 'area': '', 'street': '', 'formatted': '', 'provider': 'mapbox', 'provider_place_id': '', 'lat': lat, 'lng': lon})
            except HTTPError as e:
                if not did_log:
                    try:
                        logger.info(f"reverse_geocode provider=mapbox status={getattr(e, 'code', 0)}")
                        did_log = True
                    except Exception:
                        pass
                return Response({'city': '', 'area': '', 'street': '', 'formatted': '', 'provider': 'mapbox', 'provider_place_id': '', 'lat': lat, 'lng': lon})
            except Exception as e:
                if not did_log:
                    try:
                        logger.info(f"reverse_geocode provider=mapbox status=0")
                        did_log = True
                    except Exception:
                        pass
                return Response({'city': '', 'area': '', 'street': '', 'formatted': '', 'provider': 'mapbox', 'provider_place_id': '', 'lat': lat, 'lng': lon})
        if g_key:
            try:
                g_url = 'https://maps.googleapis.com/maps/api/geocode/json?' + urlencode({'latlng': f'{lat},{lon}', 'key': g_key, 'language': 'ar'})
                g_req = Request(g_url, headers={'User-Agent': 'clothing-store/1.0'})
                g_resp = urlopen(g_req, timeout=8)
                g_data = json.loads(g_resp.read().decode('utf-8'))
                status_code = g_data.get('status')
                if status_code == 'OK' and g_data.get('results'):
                    res = g_data['results'][0]
                    comps = res.get('address_components') or []
                    city = ''
                    area = ''
                    street = ''
                    for c in comps:
                        ts = c.get('types') or []
                        if 'locality' in ts and not city:
                            city = c.get('long_name') or ''
                        elif 'administrative_area_level_1' in ts and not city:
                            city = c.get('long_name') or ''
                        elif ('sublocality' in ts or 'neighborhood' in ts) and not area:
                            area = c.get('long_name') or ''
                        elif 'route' in ts:
                            street = c.get('long_name') or street
                        elif 'street_number' in ts and street:
                            street = (street + ' ' + c.get('long_name'))
                    if not did_log:
                        try:
                            logger.info(f"reverse_geocode provider=google status=OK")
                            did_log = True
                        except Exception:
                            pass
                    return Response({'city': city, 'area': area, 'street': (street or '').strip(), 'formatted': (res.get('formatted_address') or ''), 'provider': 'google', 'provider_place_id': str(res.get('place_id') or ''), 'lat': lat, 'lng': lon})
                if not did_log:
                    try:
                        logger.info(f"reverse_geocode provider=google status={status_code}")
                        did_log = True
                    except Exception:
                        pass
                return Response({'city': '', 'area': '', 'street': '', 'formatted': '', 'provider': 'google', 'provider_place_id': '', 'lat': lat, 'lng': lon})
            except Exception as e:
                if not did_log:
                    try:
                        logger.info(f"reverse_geocode provider=google status=0")
                        did_log = True
                    except Exception:
                        pass
                return Response({'city': '', 'area': '', 'street': '', 'formatted': '', 'provider': 'google', 'provider_place_id': '', 'lat': lat, 'lng': lon})
        params = {'format': 'jsonv2', 'lat': lat, 'lon': lon, 'accept-language': 'ar'}
        url = 'https://nominatim.openstreetmap.org/reverse?' + urlencode(params)
        def _parse(data_json):
            a = (data_json or {}).get('address') or {}
            _city = a.get('city') or a.get('town') or a.get('village') or a.get('state') or ''
            _area = a.get('suburb') or a.get('neighbourhood') or a.get('quarter') or a.get('district') or a.get('county') or ''
            _street = (a.get('road') or '') + (' ' + a.get('house_number') if a.get('house_number') else '')
            return _city, _area, _street
        try:
            req = Request(url, headers={'User-Agent': 'clothing-store/1.0 (contact: admin@example.com)'} )
            resp = urlopen(req, timeout=8)
            data = json.loads(resp.read().decode('utf-8'))
            c,a,s = _parse(data)
            if not did_log:
                try:
                    logger.info(f"reverse_geocode provider=nominatim status=200")
                    did_log = True
                except Exception:
                    pass
            return Response({'city': c, 'area': a, 'street': s.strip(), 'formatted': (data.get('display_name') or ''), 'provider': 'nominatim', 'provider_place_id': str(data.get('place_id') or ''), 'lat': lat, 'lng': lon})
        except Exception:
            try:
                fb_url = 'https://geocode.maps.co/reverse?' + urlencode({'lat': lat, 'lon': lon})
                fb_req = Request(fb_url, headers={'User-Agent': 'clothing-store/1.0 (contact: admin@example.com)'} )
                fb_resp = urlopen(fb_req, timeout=8)
                fb_data = json.loads(fb_resp.read().decode('utf-8'))
                c,a,s = _parse(fb_data)
                return Response({'city': c, 'area': a, 'street': s.strip(), 'formatted': (fb_data.get('display_name') or fb_data.get('formatted') or ''), 'provider': 'maps.co', 'provider_place_id': str(fb_data.get('place_id') or ''), 'lat': lat, 'lng': lon})
            except Exception as e:
                if not did_log:
                    try:
                        logger.info(f"reverse_geocode provider=fallback status=0")
                        did_log = True
                    except Exception:
                        pass
                return Response({'city': '', 'area': '', 'street': '', 'formatted': '', 'provider': 'fallback', 'provider_place_id': '', 'lat': lat, 'lng': lon})

    @action(detail=False, methods=['get'], url_path='autocomplete', permission_classes=[AllowAny], authentication_classes=[])
    def autocomplete(self, request):
        """
        Autocomplete by query using Nominatim search. Restricted to Iraq.
        """
        logger = logging.getLogger('geo')
        q = (request.query_params.get('q') or '').strip()
        if not q:
            return Response({'results': []})
        mb_token = (os.environ.get('MAPBOX_ACCESS_TOKEN') or '').strip()
        g_key = (os.environ.get('MAPS_API_KEY') or '').strip()
        if mb_token:
            try:
                mb_url = 'https://api.mapbox.com/geocoding/v5/mapbox.places/{}.json?'.format(q) + urlencode({'access_token': mb_token, 'language': 'ar', 'limit': 6})
                mb_req = Request(mb_url, headers={'User-Agent': 'clothing-store/1.0'})
                mb_resp = urlopen(mb_req, timeout=8)
                mb_data = json.loads(mb_resp.read().decode('utf-8'))
                results = []
                for it in (mb_data.get('features') or [])[:6]:
                    results.append({'label': it.get('place_name') or '', 'city': '', 'area': '', 'street': '', 'lat': it.get('center')[1] if it.get('center') else it.get('geometry', {}).get('coordinates', [None, None])[1], 'lng': it.get('center')[0] if it.get('center') else it.get('geometry', {}).get('coordinates', [None, None])[0], 'provider': 'mapbox', 'provider_place_id': str(it.get('id') or '')})
                return Response({'results': results})
            except Exception as e:
                logger.error(f"mapbox search error: {e}")
                return Response({'results': []}, status=status.HTTP_502_BAD_GATEWAY)
        if g_key:
            try:
                g_url = 'https://maps.googleapis.com/maps/api/geocode/json?' + urlencode({'address': q, 'key': g_key, 'language': 'ar'})
                g_req = Request(g_url, headers={'User-Agent': 'clothing-store/1.0'})
                g_resp = urlopen(g_req, timeout=8)
                g_data = json.loads(g_resp.read().decode('utf-8'))
                items = []
                if g_data.get('status') == 'OK':
                    for it in (g_data.get('results') or [])[:6]:
                        loc = (it.get('geometry') or {}).get('location') or {}
                        items.append({'label': it.get('formatted_address') or '', 'city': '', 'area': '', 'street': '', 'lat': loc.get('lat'), 'lng': loc.get('lng'), 'provider': 'google', 'provider_place_id': str(it.get('place_id') or '')})
                return Response({'results': items})
            except Exception as e:
                logger.error(f"google search error: {e}")
                return Response({'results': []}, status=status.HTTP_502_BAD_GATEWAY)
        params = {'format': 'jsonv2', 'q': q, 'accept-language': 'ar', 'countrycodes': 'iq', 'limit': 6}
        url = 'https://nominatim.openstreetmap.org/search?' + urlencode(params)
        def _map_item(it):
            a = it.get('address') or {}
            _city = a.get('city') or a.get('town') or a.get('village') or a.get('state') or ''
            _area = a.get('suburb') or a.get('neighbourhood') or a.get('quarter') or a.get('district') or a.get('county') or ''
            _road = a.get('road') or ''
            _hn = a.get('house_number') or ''
            _street = (_road + (' ' + _hn if _hn else '')).strip()
            return {
                'label': it.get('display_name') or _street or _city,
                'city': _city,
                'area': _area,
                'street': _street,
                'lat': it.get('lat'),
                'lng': it.get('lon'),
                'provider': 'nominatim',
                'provider_place_id': str(it.get('place_id') or ''),
            }
        try:
            req = Request(url, headers={'User-Agent': 'clothing-store/1.0 (contact: admin@example.com)'} )
            resp = urlopen(req, timeout=8)
            items = json.loads(resp.read().decode('utf-8'))
            results = [_map_item(it) for it in (items or [])[:6]]
            return Response({'results': results})
        except Exception:
            try:
                fb_url = 'https://geocode.maps.co/search?' + urlencode({'q': q})
                fb_req = Request(fb_url, headers={'User-Agent': 'clothing-store/1.0 (contact: admin@example.com)'} )
                fb_resp = urlopen(fb_req, timeout=8)
                fb_items = json.loads(fb_resp.read().decode('utf-8'))
                mapped = []
                for it in (fb_items or [])[:6]:
                    mapped.append({
                        'label': it.get('display_name') or '',
                        'city': '',
                        'area': '',
                        'street': '',
                        'lat': it.get('lat'),
                        'lng': it.get('lon'),
                        'provider': 'maps.co',
                        'provider_place_id': str(it.get('place_id') or ''),
                    })
                return Response({'results': mapped})
            except Exception as e:
                logger.error(f"autocomplete fallback error: {e}")
                return Response({'results': []}, status=status.HTTP_502_BAD_GATEWAY)


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

