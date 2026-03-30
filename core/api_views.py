from rest_framework import viewsets, status
from rest_framework.permissions import AllowAny
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.db.models import Q
from django.core.cache import cache
from django.core.mail import send_mail
from django.conf import settings
from django.core.signing import TimestampSigner, BadSignature, SignatureExpired
from django.db import connection
from django.utils import timezone
from .models import User, Store, Product, Address, Order, ProductVariant, ProductColor, ProductImage, AttributeColor, AttributeSize, FeatureFlag
import logging
import json
import os
import random
from urllib.request import Request, urlopen
from urllib.parse import urlencode
from urllib.error import URLError, HTTPError
try:
    import firebase_admin
    from firebase_admin import auth as firebase_auth
    from firebase_admin import credentials as firebase_credentials
except Exception:
    firebase_admin = None
    firebase_auth = None
    firebase_credentials = None
from .serializers import (
    UserSerializer, UserRegistrationSerializer, StoreSerializer, 
    ProductSerializer, AddressSerializer, OrderSerializer, OrderCreateSerializer,
    CartItemSerializer
)
from ads.serializers import AdvertisementSerializer
from .permissions import (
    IsCustomer, IsStoreOwner, IsAdmin, IsStoreOwnerOfStore, 
    IsOwnerOfOrder, IsStoreOwnerOfOrder
)


def _related_user_ids_for_user(user):
    if not user or not getattr(user, 'is_authenticated', False):
        return []
    try:
        phone = (getattr(user, 'phone', '') or '').strip()
        if not phone:
            return [user.id]
        ids = list(User.objects.filter(phone=phone).values_list('id', flat=True))
        return ids or [user.id]
    except Exception:
        return [user.id]


class AuthViewSet(viewsets.ViewSet):
    def _create_code(self):
        return ''.join(str(random.randint(0, 9)) for _ in range(6))

    def _send_email_code(self, email, subject, message):
        if not email:
            return False
        try:
            send_mail(subject, message, getattr(settings, 'DEFAULT_FROM_EMAIL', None), [email], fail_silently=False)
            return True
        except Exception:
            return False

    def _make_reset_ticket(self, user_id, code):
        signer = TimestampSigner(salt='password-reset')
        return signer.sign(f"{int(user_id)}:{str(code)}")

    def _read_reset_ticket(self, ticket, max_age=10 * 60):
        signer = TimestampSigner(salt='password-reset')
        raw = signer.unsign(ticket, max_age=max_age)
        uid, code = str(raw).split(':', 1)
        return int(uid), str(code)

    def _make_signup_ticket(self, phone, code):
        signer = TimestampSigner(salt='signup-otp')
        return signer.sign(f"{str(phone)}:{str(code)}")

    def _read_signup_ticket(self, ticket, max_age=10 * 60):
        signer = TimestampSigner(salt='signup-otp')
        raw = signer.unsign(ticket, max_age=max_age)
        phone, code = str(raw).split(':', 1)
        return str(phone), str(code)

    def _to_e164_iq(self, phone):
        p = str(phone or '').strip().replace(' ', '')
        digits = ''.join(ch for ch in p if ch.isdigit())
        if digits.startswith('00964'):
            return f"+{digits[2:]}"
        if digits.startswith('964'):
            return f"+{digits}"
        if digits.startswith('07') and len(digits) == 11:
            return f"+964{digits[1:]}"
        if digits.startswith('7') and len(digits) == 10:
            return f"+964{digits}"
        if p.startswith('+') and digits:
            return f"+{digits}"
        return p

    def _from_e164_iq(self, phone):
        p = str(phone or '').strip().replace(' ', '')
        digits = ''.join(ch for ch in p if ch.isdigit())
        if digits.startswith('00964'):
            digits = digits[2:]
        if digits.startswith('964') and len(digits) == 13:
            return f"0{digits[3:]}"
        if digits.startswith('7') and len(digits) == 10:
            return f"0{digits}"
        if digits.startswith('07') and len(digits) == 11:
            return digits
        return p

    def _init_firebase(self):
        if not firebase_admin or not firebase_auth or not firebase_credentials:
            return False, 'FIREBASE_SDK_NOT_INSTALLED'
        try:
            if firebase_admin._apps:
                return True, ''
            cred_path = (os.environ.get('FIREBASE_SERVICE_ACCOUNT_PATH') or '').strip()
            cred_json = (os.environ.get('FIREBASE_SERVICE_ACCOUNT_JSON') or '').strip()
            project_id = (os.environ.get('FIREBASE_PROJECT_ID') or '').strip()
            cred_obj = None
            if cred_json:
                cred_obj = firebase_credentials.Certificate(json.loads(cred_json))
            elif cred_path:
                cred_obj = firebase_credentials.Certificate(cred_path)
            if cred_obj is not None:
                opts = {'projectId': project_id} if project_id else None
                if opts:
                    firebase_admin.initialize_app(cred_obj, opts)
                else:
                    firebase_admin.initialize_app(cred_obj)
                return True, ''
            if project_id:
                firebase_admin.initialize_app(options={'projectId': project_id})
                return True, ''
            return False, 'FIREBASE_CONFIG_MISSING'
        except Exception:
            return False, 'FIREBASE_INIT_FAILED'

    def _verify_firebase_phone(self, id_token):
        ok, err = self._init_firebase()
        if not ok:
            return None, err
        try:
            decoded = firebase_auth.verify_id_token(str(id_token), check_revoked=False)
            phone = str(decoded.get('phone_number') or '').strip()
            if not phone:
                identities = (((decoded.get('firebase') or {}).get('identities') or {}).get('phone') or [])
                if identities:
                    phone = str(identities[0] or '').strip()
            if not phone:
                return None, 'FIREBASE_PHONE_MISSING'
            return self._from_e164_iq(phone), ''
        except Exception:
            return None, 'FIREBASE_TOKEN_INVALID'

    def _send_sms_code(self, phone, code, purpose='signup'):
        url = (os.environ.get('SMS_OTP_PROVIDER_URL') or '').strip()
        if not url:
            return False
        method = (os.environ.get('SMS_OTP_PROVIDER_METHOD') or 'POST').strip().upper()
        api_key = (os.environ.get('SMS_OTP_API_KEY') or '').strip()
        sender = (os.environ.get('SMS_OTP_SENDER') or '').strip()
        to = self._to_e164_iq(phone)
        message = f"Your verification code is: {code}" if purpose == 'signup' else f"Your password reset code is: {code}"
        payload = {
            'to': to,
            'phone': to,
            'recipient': to,
            'message': message,
            'text': message,
            'code': str(code),
        }
        if sender:
            payload['sender'] = sender
            payload['from'] = sender
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        if api_key:
            headers['Authorization'] = f"Bearer {api_key}"
            headers['X-API-Key'] = api_key
        data = urlencode(payload).encode('utf-8')
        try:
            req = Request(url, data=data if method != 'GET' else None, headers=headers, method=method)
            if method == 'GET':
                req = Request(f"{url}?{urlencode(payload)}", headers=headers, method='GET')
            with urlopen(req, timeout=12) as resp:
                status_code = int(getattr(resp, 'status', 200) or 200)
                return 200 <= status_code < 300
        except (HTTPError, URLError, Exception):
            return False

    @action(detail=False, methods=['post'], permission_classes=[])
    def register(self, request):
        phone = (request.data.get('phone') or '').strip()
        otp_code = (request.data.get('otp_code') or '').strip()
        otp_ticket = (request.data.get('otp_ticket') or '').strip()
        existing_user = None
        if phone:
            existing_user = User.objects.filter(phone=phone).order_by('-is_superuser', '-is_staff', '-date_joined').first()
            if existing_user and bool(getattr(existing_user, 'is_customer', False)):
                return Response({'code': 'PHONE_ALREADY_HAS_ACCOUNT'}, status=status.HTTP_409_CONFLICT)
        if not otp_code:
            if not phone:
                return Response({'error': 'PHONE_REQUIRED'}, status=status.HTTP_400_BAD_REQUEST)
            code = self._create_code()
            cache.set(f"verify:signup:{phone}", code, timeout=10 * 60)
            sms_sent = self._send_sms_code(phone, code, purpose='signup')
            payload = {
                'ok': True,
                'requires_otp': True,
                'phone': phone,
                'otp_ticket': self._make_signup_ticket(phone, code),
                'sms_sent': bool(sms_sent),
                'message': 'تم إرسال رمز التحقق إلى رقم الهاتف' if sms_sent else 'تعذر إرسال SMS حالياً، استخدم الرمز المؤقت',
            }
            if settings.DEBUG:
                payload['debug_otp'] = code
            return Response(payload)
        otp_valid = False
        expected = cache.get(f"verify:signup:{phone}")
        if expected and str(expected) == str(otp_code):
            otp_valid = True
        if otp_ticket:
            try:
                t_phone, t_code = self._read_signup_ticket(otp_ticket, max_age=10 * 60)
                if str(t_phone) == str(phone) and str(t_code) == str(otp_code):
                    otp_valid = True
            except (BadSignature, SignatureExpired, ValueError):
                pass
        if not otp_valid:
            return Response({'error': 'OTP_INVALID_OR_EXPIRED', 'message': 'رمز التحقق غير صحيح أو منتهي'}, status=status.HTTP_400_BAD_REQUEST)
        serializer = UserRegistrationSerializer(data=request.data, context={'existing_user': existing_user} if existing_user else {})
        if serializer.is_valid():
            user = serializer.save()
            user.is_active = True
            user.save(update_fields=['is_active'])
            try:
                from django.utils import timezone
                from .models import StoreOwnerInvite, Store
                qs = StoreOwnerInvite.objects.filter(phone=user.phone, status='pending')
                now = timezone.now()
                qs = qs.filter(Q(expires_at__isnull=True) | Q(expires_at__gt=now))
                inv = qs.first()
                if inv:
                    user.is_store_admin = True
                    user.is_staff = True
                    user.save(update_fields=['is_store_admin', 'is_staff', 'role'])
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
            cache.delete(f"verify:signup:{phone}")
            refresh = RefreshToken.for_user(user)
            return Response({
                'user': UserSerializer(user).data,
                'access': str(refresh.access_token),
                'refresh': str(refresh),
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'], permission_classes=[])
    def firebase_login(self, request):
        id_token = (request.data.get('id_token') or request.data.get('firebase_id_token') or '').strip()
        if not id_token:
            return Response({'error': 'ID_TOKEN_REQUIRED'}, status=status.HTTP_400_BAD_REQUEST)
        phone, err = self._verify_firebase_phone(id_token)
        if not phone:
            return Response({'error': err or 'FIREBASE_VERIFICATION_FAILED'}, status=status.HTTP_400_BAD_REQUEST)
        email = (request.data.get('email') or '').strip().lower()
        full_name = (request.data.get('full_name') or '').strip()
        city = (request.data.get('city') or '').strip() or 'Baghdad'
        password = (request.data.get('password') or '').strip()
        user = User.objects.filter(phone=phone).order_by('-is_superuser', '-is_staff', '-date_joined').first()
        created = False
        if not user:
            username = f"user_{phone[-6:]}" if len(phone) >= 6 else f"user_{self._create_code()}"
            counter = 1
            base = username
            while User.objects.filter(username=username).exists():
                username = f"{base}_{counter}"
                counter += 1
            first_name = ''
            last_name = ''
            if full_name:
                parts = full_name.split(' ', 1)
                first_name = parts[0]
                last_name = parts[1] if len(parts) > 1 else ''
            user = User.objects.create_user(
                username=username,
                email=email,
                phone=phone,
                city=city,
                first_name=first_name,
                last_name=last_name,
                is_customer=True,
                is_active=True,
            )
            if password:
                user.set_password(password)
                user.save(update_fields=['password', 'role'])
            created = True
        else:
            updates = []
            if not getattr(user, 'is_customer', False):
                user.is_customer = True
                updates.append('is_customer')
            if email and not user.email:
                user.email = email
                updates.append('email')
            if city and not user.city:
                user.city = city
                updates.append('city')
            if full_name and not (user.first_name or user.last_name):
                parts = full_name.split(' ', 1)
                user.first_name = parts[0]
                user.last_name = parts[1] if len(parts) > 1 else ''
                updates.extend(['first_name', 'last_name'])
            if not user.is_active:
                user.is_active = True
                updates.append('is_active')
            if password:
                user.set_password(password)
                updates.append('password')
            if updates:
                updates.append('role')
                user.save(update_fields=list(dict.fromkeys(updates)))
        refresh = RefreshToken.for_user(user)
        return Response({
            'ok': True,
            'created': created,
            'user': UserSerializer(user).data,
            'access': str(refresh.access_token),
            'refresh': str(refresh),
        }, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'], permission_classes=[])
    def firebase_reset_password(self, request):
        id_token = (request.data.get('id_token') or request.data.get('firebase_id_token') or '').strip()
        new_password = (request.data.get('new_password') or '').strip()
        if not id_token or not new_password:
            return Response({'error': 'MISSING_REQUIRED_FIELDS'}, status=status.HTTP_400_BAD_REQUEST)
        if len(new_password) < 6:
            return Response({'error': 'كلمة المرور يجب أن تكون 6 أحرف على الأقل'}, status=status.HTTP_400_BAD_REQUEST)
        phone, err = self._verify_firebase_phone(id_token)
        if not phone:
            return Response({'error': err or 'FIREBASE_VERIFICATION_FAILED'}, status=status.HTTP_400_BAD_REQUEST)
        user = User.objects.filter(phone=phone).order_by('-is_superuser', '-is_staff', '-date_joined').first()
        if not user:
            return Response({'error': 'المستخدم غير موجود'}, status=status.HTTP_404_NOT_FOUND)
        user.set_password(new_password)
        if not getattr(user, 'is_customer', False):
            user.is_customer = True
            user.save(update_fields=['password', 'is_customer', 'role'])
        else:
            user.save(update_fields=['password', 'role'])
        return Response({'ok': True}, status=status.HTTP_200_OK)
    
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
        username = (request.data.get('username') or request.data.get('phone') or '').strip()
        password = (request.data.get('password') or '').strip()
        if username and username.startswith('+964') and len(username) == 14:
            username = '0' + username[4:]
        elif username and username.startswith('964') and len(username) == 13:
            username = '0' + username[3:]
        elif username and username.startswith('7') and len(username) == 10:
            username = '0' + username
        phone_candidate = username if username.startswith('07') and len(username) == 11 else ''
        if phone_candidate:
            try:
                u = User.objects.filter(phone=phone_candidate).order_by('-is_superuser', '-is_staff', '-date_joined').first()
                if u:
                    username = u.username
            except Exception:
                pass
        try:
            pending_user = User.objects.filter(username=username).first()
            if pending_user and (not pending_user.is_active) and pending_user.check_password(password):
                code = self._create_code()
                cache.set(f"verify:register:{pending_user.phone}", code, timeout=10 * 60)
                email_sent = self._send_email_code(
                    pending_user.email,
                    'رمز تفعيل الحساب',
                    f'رمز تفعيل حسابك هو: {code}\nصالح لمدة 10 دقائق.',
                )
                payload = {
                    'error': 'ACCOUNT_NOT_VERIFIED',
                    'requires_verification': True,
                    'phone': pending_user.phone,
                    'email': pending_user.email,
                    'email_sent': bool(email_sent),
                }
                if settings.DEBUG:
                    payload['debug_code'] = code
                return Response(payload, status=status.HTTP_403_FORBIDDEN)
        except Exception:
            pass
        user = authenticate(username=username, password=password)
        if user:
            refresh = RefreshToken.for_user(user)
            return Response({
                'user': UserSerializer(user).data,
                'access': str(refresh.access_token),
                'refresh': str(refresh)
            })
        return Response({'error': 'بيانات الدخول غير صحيحة'}, status=status.HTTP_401_UNAUTHORIZED)

    @action(detail=False, methods=['post'], permission_classes=[])
    def verify_registration(self, request):
        phone = (request.data.get('phone') or '').strip()
        code = (request.data.get('code') or '').strip()
        if not phone or not code:
            return Response({'error': 'يرجى إدخال رقم الهاتف والرمز'}, status=status.HTTP_400_BAD_REQUEST)
        expected = cache.get(f"verify:register:{phone}")
        if not expected or str(expected) != str(code):
            return Response({'error': 'رمز التفعيل غير صحيح أو منتهي'}, status=status.HTTP_400_BAD_REQUEST)
        user = User.objects.filter(phone=phone).first()
        if not user:
            return Response({'error': 'المستخدم غير موجود'}, status=status.HTTP_404_NOT_FOUND)
        user.is_active = True
        user.save(update_fields=['is_active'])
        cache.delete(f"verify:register:{phone}")
        refresh = RefreshToken.for_user(user)
        return Response({
            'user': UserSerializer(user).data,
            'access': str(refresh.access_token),
            'refresh': str(refresh),
        })

    @action(detail=False, methods=['post'], permission_classes=[])
    def resend_verification(self, request):
        phone = (request.data.get('phone') or '').strip()
        user = User.objects.filter(phone=phone).first()
        if not user or user.is_active:
            return Response({'error': 'الحساب غير قابل لإعادة الإرسال'}, status=status.HTTP_400_BAD_REQUEST)
        code = self._create_code()
        cache.set(f"verify:register:{user.phone}", code, timeout=10 * 60)
        email_sent = self._send_email_code(
            user.email,
            'إعادة إرسال رمز التفعيل',
            f'رمز تفعيل حسابك هو: {code}\nصالح لمدة 10 دقائق.',
        )
        payload = {'ok': True, 'email_sent': bool(email_sent)}
        if settings.DEBUG:
            payload['debug_code'] = code
        return Response(payload)

    @action(detail=False, methods=['post'], permission_classes=[])
    def forgot_password_request(self, request):
        identifier = (request.data.get('identifier') or request.data.get('phone') or request.data.get('email') or '').strip()
        if not identifier:
            return Response({'error': 'يرجى إدخال رقم الهاتف أو البريد الإلكتروني'}, status=status.HTTP_400_BAD_REQUEST)
        user = User.objects.filter(Q(phone=identifier) | Q(email__iexact=identifier)).first()
        if not user:
            return Response({'ok': True, 'message': 'إذا كانت البيانات صحيحة سيتم إرسال رمز الاسترجاع'})
        code = self._create_code()
        cache.set(f"verify:reset:{user.phone}", code, timeout=10 * 60)
        sms_sent = self._send_sms_code(user.phone, code, purpose='reset')
        email_sent = False
        if user.email:
            email_sent = self._send_email_code(
                user.email,
                'رمز استعادة كلمة المرور',
                f'رمز استعادة كلمة المرور هو: {code}\nصالح لمدة 10 دقائق.',
            )
        payload = {'ok': True, 'email_sent': bool(email_sent), 'sms_sent': bool(sms_sent), 'phone': user.phone}
        payload['reset_ticket'] = self._make_reset_ticket(user.id, code)
        if sms_sent:
            payload['message'] = 'تم إرسال رمز الاسترجاع عبر رسالة نصية'
        elif email_sent:
            payload['message'] = 'تم إرسال رمز الاسترجاع إلى البريد الإلكتروني'
        else:
            payload['message'] = 'تعذر إرسال SMS والبريد، تم توفير رمز الاسترجاع مباشرة'
            payload['reset_code'] = code
        if settings.DEBUG:
            payload['debug_code'] = code
        return Response(payload)

    @action(detail=False, methods=['post'], permission_classes=[])
    def forgot_password_confirm(self, request):
        identifier = (request.data.get('identifier') or request.data.get('phone') or request.data.get('email') or '').strip()
        code = (request.data.get('code') or '').strip()
        new_password = (request.data.get('new_password') or '').strip()
        if not identifier or not code or not new_password:
            return Response({'error': 'البيانات المطلوبة غير مكتملة'}, status=status.HTTP_400_BAD_REQUEST)
        user = User.objects.filter(Q(phone=identifier) | Q(email__iexact=identifier)).first()
        if not user:
            return Response({'error': 'المستخدم غير موجود'}, status=status.HTTP_404_NOT_FOUND)
        ticket = (request.data.get('reset_ticket') or '').strip()
        ticket_valid = False
        if ticket:
            try:
                uid, tcode = self._read_reset_ticket(ticket, max_age=10 * 60)
                ticket_valid = (uid == int(user.id) and str(tcode) == str(code))
            except (BadSignature, SignatureExpired, ValueError):
                ticket_valid = False
        expected = cache.get(f"verify:reset:{user.phone}")
        cache_valid = bool(expected) and str(expected) == str(code)
        if not ticket_valid and not cache_valid:
            return Response({'error': 'رمز الاسترجاع غير صحيح أو منتهي'}, status=status.HTTP_400_BAD_REQUEST)
        if len(new_password) < 6:
            return Response({'error': 'كلمة المرور يجب أن تكون 6 أحرف على الأقل'}, status=status.HTTP_400_BAD_REQUEST)
        user.set_password(new_password)
        user.save(update_fields=['password'])
        cache.delete(f"verify:reset:{user.phone}")
        return Response({'ok': True})
    
    @action(detail=False, methods=['get', 'patch', 'put'])
    def me(self, request):
        if request.method == 'GET':
            serializer = UserSerializer(request.user)
            return Response(serializer.data)
        allowed_fields = {'username', 'email', 'city', 'first_name', 'last_name'}
        incoming = request.data or {}
        payload = {k: incoming.get(k) for k in allowed_fields if k in incoming}
        serializer = UserSerializer(request.user, data=payload, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'], permission_classes=[])
    def logout(self, request):
        return Response({'ok': True})


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


class AdvertisementViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = AdvertisementSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        try:
            from ads.models import Advertisement
        except Exception:
            return []
        position = self.request.query_params.get('position')
        logger = logging.getLogger(__name__)
        logger.info(f"API Ads requested for position: {position}")
        qs = Advertisement.get_active_ads(position=position)
        logger.info(f"Found {qs.count()} ads")
        return qs

    @action(detail=True, methods=['post'], permission_classes=[AllowAny])
    def click(self, request, pk=None):
        from ads.models import Advertisement
        Advertisement.objects.filter(id=pk).update(clicks=F('clicks') + 1)
        return Response({'ok': True})

    @action(detail=True, methods=['post'], permission_classes=[AllowAny])
    def impression(self, request, pk=None):
        from ads.models import Advertisement
        Advertisement.objects.filter(id=pk).update(impressions=F('impressions') + 1)
        return Response({'ok': True})


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
        
        # 🔧 DIAGNOSTIC: Check query results
        print(f"[API] Returning {queryset.count()} products")
        
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
        qs = product.variants.all()
        if color:
            if color.lower().startswith('a'):
                try:
                    cid = int(color[1:])
                    qs = qs.filter(color_attr_id=cid)
                except Exception:
                    qs = qs.none()
            else:
                try:
                    cid = int(color)
                    qs = qs.filter(color_obj_id=cid)
                except Exception:
                    from django.db.models import Q
                    qs = qs.filter(Q(color_obj__name=color) | Q(color_attr__name=color))
        data = []
        for v in qs:
            try:
                data.append({
                    'id': v.id,
                    'size': getattr(v, 'size_display', v.size),
                    'stock_qty': int(getattr(v, 'stock_qty', 0)),
                    'price': float(v.price),
                })
            except Exception:
                continue
        return Response({'color': color, 'sizes': data})

    @action(detail=True, methods=['get'], url_path='variant-price', permission_classes=[AllowAny], authentication_classes=[])
    def variant_price(self, request, pk=None):
        """
        Returns price information for a product variant given color and size.
        Query params:
          - color: Either numeric color_obj_id, or 'A<attr_id>' for AttributeColor
          - size:  Size string or AttributeSize.name
        Response:
          - {found: bool, price: number|null, sale_price: number|null, currency: str, fallback_price: number|null}
        """
        product = self.get_object()
        color = (request.query_params.get('color') or '').strip()
        size = (request.query_params.get('size') or '').strip()
        from django.db.models import Q
        qs = product.variants.all()
        # filter by color if provided
        if color:
            if color.startswith('A'):
                try:
                    cid = int(color[1:])
                    qs = qs.filter(color_attr_id=cid)
                except Exception:
                    qs = qs.none()
            else:
                try:
                    cid = int(color)
                    qs = qs.filter(color_obj_id=cid)
                except Exception:
                    qs = qs.none()
        # filter by size if provided
        if size:
            qs = qs.filter(Q(size=size) | Q(size_attr__name=size))
        v = qs.first()
        currency = 'د.ع'
        try:
            base_price = float(product.base_price)
        except Exception:
            base_price = None
        if not v:
            return Response({'found': False, 'price': None, 'sale_price': None, 'currency': currency, 'fallback_price': base_price})
        # If explicit inventory price exists use it; otherwise treat as not found and fallback to product base_price
        if v.price_override is not None:
            try:
                vp = float(v.price_override)
            except Exception:
                vp = None
            try:
                base_price_num = float(product.base_price)
            except Exception:
                base_price_num = None
            sale_old = None
            try:
                if base_price_num is not None and vp is not None and base_price_num > vp:
                    sale_old = base_price_num
            except Exception:
                sale_old = None
            return Response({'found': True, 'price': vp, 'sale_price': sale_old, 'currency': currency})
        return Response({'found': False, 'price': None, 'sale_price': None, 'currency': currency, 'fallback_price': base_price})

class CategoryList(APIView):
    permission_classes = []
    authentication_classes = []
    def get(self, request):
        items = []
        for key, label in Product.CATEGORY_CHOICES:
            items.append({'key': key, 'label': label})
        return Response({'categories': items})

class BannerList(APIView):
    permission_classes = []
    authentication_classes = []
    def get(self, request):
        from django.utils import timezone
        from ads.models import Banner
        placement = (request.query_params.get('placement') or '').strip()
        placement_norm = placement.lower().replace('home_', 'home_') if placement else ''
        allowed = {'home_top', 'home_middle', 'home_bottom'}
        now = timezone.now()
        qs = Banner.objects.filter(is_active=True)
        if placement_norm and placement_norm in allowed:
            qs = qs.filter(placement=placement_norm)
        qs = qs.filter(Q(starts_at__isnull=True) | Q(starts_at__lte=now))
        qs = qs.filter(Q(ends_at__isnull=True) | Q(ends_at__gte=now))
        qs = qs.order_by('-priority', '-id')
        items = []
        for b in qs[:50]:
            try:
                img = b.get_image_url() if hasattr(b, 'get_image_url') else (b.image.url if b.image else '')
                if img and not (img.startswith('http://') or img.startswith('https://')):
                    try:
                        img = request.build_absolute_uri(img)
                    except Exception:
                        pass
            except Exception:
                img = ''
            items.append({
                'id': b.id,
                'title': b.title,
                'image': img,
                'image_url': img,
                'action_url': b.link_target or '',
                'link': b.link_target or '',
                'link_type': b.link_type,
                'link_target': b.link_target or '',
                'placement': b.placement,
                'priority': int(b.priority or 0),
                'starts_at': (b.starts_at.isoformat() if b.starts_at else None),
                'ends_at': (b.ends_at.isoformat() if b.ends_at else None),
            })
        try:
            logger = logging.getLogger('banners')
            first = items[0] if items else {}
            logger.info(f"[banners] now={now.isoformat()} first.starts_at={first.get('starts_at')} first.ends_at={first.get('ends_at')} placement={placement or '(any)'} count={len(items)}")
        except Exception:
            pass
        return Response(items)

class AdsList(APIView):
    permission_classes = []
    authentication_classes = []
    def get(self, request):
        from django.utils import timezone
        position = (request.query_params.get('position') or '').strip()
        if position:
            try:
                from ads.models import Banner
            except Exception:
                return Response([])
            placement_norm = position.lower().replace('home_', 'home_')
            allowed = {'home_top', 'home_middle', 'home_bottom'}
            now = timezone.now()
            qs = Banner.objects.filter(is_active=True)
            if placement_norm in allowed:
                qs = qs.filter(placement=placement_norm)
            qs = qs.filter(Q(starts_at__isnull=True) | Q(starts_at__lte=now))
            qs = qs.filter(Q(ends_at__isnull=True) | Q(ends_at__gte=now))
            qs = qs.order_by('-priority', '-id')
            items = []
            for b in qs[:50]:
                try:
                    img = b.get_image_url() if hasattr(b, 'get_image_url') else (b.image.url if b.image else '')
                    if img and not (img.startswith('http://') or img.startswith('https://')):
                        try:
                            img = request.build_absolute_uri(img)
                        except Exception:
                            pass
                except Exception:
                    img = ''
                items.append({
                    'id': b.id,
                    'title': b.title,
                    'image': img,
                    'image_url': img,
                    'action_url': b.link_target or '',
                    'link': b.link_target or '',
                    'link_type': b.link_type,
                    'link_target': b.link_target or '',
                    'placement': b.placement,
                    'priority': int(b.priority or 0),
                    'starts_at': (b.starts_at.isoformat() if b.starts_at else None),
                    'ends_at': (b.ends_at.isoformat() if b.ends_at else None),
                })
            return Response(items)
        try:
            from core.models import Campaign
        except Exception:
            return Response([])
        now = timezone.now()
        qs = Campaign.objects.filter(is_active=True, start_date__lte=now, end_date__gte=now).order_by('-start_date', '-id')
        if not qs.exists():
            qs = Campaign.objects.filter(is_active=True).order_by('-start_date', '-id')
        items = []
        for c in qs[:50]:
            try:
                img = c.get_banner_url() if hasattr(c, 'get_banner_url') else (c.banner_image.url if c.banner_image else '')
                if img and not (img.startswith('http://') or img.startswith('https://')):
                    try:
                        img = request.build_absolute_uri(img)
                    except Exception:
                        pass
            except Exception:
                img = ''
            items.append({
                'id': c.id,
                'title': c.title,
                'description': c.description,
                'image': img,
                'image_url': img,
                'discount_percent': int(c.discount_percent or 0),
                'starts_at': c.start_date.isoformat() if c.start_date else None,
                'ends_at': c.end_date.isoformat() if c.end_date else None,
                'action_url': c.action_url or '',
                # Add missing fields to match Banner structure to prevent app crash
                'placement': 'campaign',
                'priority': 0,
                'media_type': 'image', # For new app version compatibility
            })
        return Response(items)

class BannerHomeTop(APIView):
    permission_classes = []
    authentication_classes = []
    def get(self, request):
        from django.utils import timezone
        try:
            from ads.models import Banner
        except Exception:
            return Response({'results': [], 'count': 0}, status=status.HTTP_200_OK)
        now = timezone.now()
        qs = Banner.objects.filter(is_active=True, placement='home_top')
        qs = qs.filter(Q(starts_at__isnull=True) | Q(starts_at__lte=now))
        qs = qs.filter(Q(ends_at__isnull=True) | Q(ends_at__gte=now))
        qs = qs.order_by('-priority', '-id')
        items = []
        for b in qs[:20]:
            try:
                img = b.image.url if b.image else ''
                if img and not (img.startswith('http://') or img.startswith('https://')):
                    try:
                        img = request.build_absolute_uri(img)
                    except Exception:
                        pass
            except Exception:
                img = ''
            items.append({
                'id': b.id,
                'title': b.title,
                'image': img,
                'image_url': img,
                'action_url': b.link_target or '',
                'link': b.link_target or '',
                'link_type': b.link_type,
                'link_target': b.link_target or '',
                'placement': b.placement,
                'priority': int(b.priority or 0),
                'starts_at': (b.starts_at.isoformat() if b.starts_at else None),
            })
        return Response(items)

class Health(APIView):
    permission_classes = []
    authentication_classes = []
    def get(self, request):
        try:
            connection.ensure_connection()
            db_ok = True
        except Exception:
            db_ok = False
        return Response({'ok': True, 'db': db_ok})

class CartViewSet(viewsets.ModelViewSet):
    serializer_class = CartItemSerializer
    from rest_framework.permissions import IsAuthenticated
    permission_classes = [IsAuthenticated]
    def get_queryset(self):
        return CartItem.objects.filter(user=self.request.user).select_related('product', 'variant', 'product__store').order_by('-updated_at')
    def initial(self, request, *args, **kwargs):
        try:
            auth_hdr = request.META.get('HTTP_AUTHORIZATION', '')
            masked = ''
            if auth_hdr.startswith('Bearer '):
                tok = auth_hdr[7:]
                masked = f"Bearer {tok[:6]}...{tok[-4:]}" if len(tok) > 10 else "Bearer ****"
            logger = logging.getLogger('cart')
            logger.info(f"[cart] user={getattr(request.user, 'id', None)} role={getattr(request.user, 'role', '')} auth_present={bool(auth_hdr)} auth_masked={masked}")
        except Exception:
            pass
        return super().initial(request, *args, **kwargs)
    def list(self, request, *args, **kwargs):
        qs = self.filter_queryset(self.get_queryset())
        logger = logging.getLogger('cart')
        try:
            data = self.get_serializer(qs, many=True).data
            return Response(data)
        except Exception as e:
            try:
                logger.exception(f"[cart] list serialize failed user={getattr(request.user, 'id', None)} err={e}")
            except Exception:
                pass
            safe = []
            for it in qs:
                try:
                    safe.append(self.get_serializer(it).data)
                except Exception as item_err:
                    try:
                        logger.exception(f"[cart] item serialize failed id={getattr(it, 'id', None)} user={getattr(request.user, 'id', None)} err={item_err}")
                    except Exception:
                        pass
            return Response(safe)

class DevSeed(APIView):
    permission_classes = []
    authentication_classes = []
    def post(self, request):
        from django.conf import settings
        if not settings.DEBUG:
            return Response({'error': 'forbidden'}, status=status.HTTP_403_FORBIDDEN)
        from django.core.management import call_command
        try:
            call_command('populate_sample_data')
        except Exception as e:
            pass
        try:
            Product.objects.all().update(status='ACTIVE', is_active=True)
        except Exception:
            pass
        try:
            from .models import Campaign
            if not Campaign.objects.filter(is_active=True).exists():
                Campaign.objects.create(title='افتتاح المنصة', description='خصومات حصرية', discount_percent=15, is_active=True)
                Campaign.objects.create(title='الشتاء الدافئ', description='خصم 25% على الألبسة الشتوية', discount_percent=25, is_active=True)
        except Exception:
            pass
        return Response({'ok': True})

class AddressViewSet(viewsets.ModelViewSet):
    serializer_class = AddressSerializer
    
    def get_queryset(self):
        related_ids = _related_user_ids_for_user(self.request.user)
        return Address.objects.filter(user_id__in=related_ids).order_by('-id')
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['get','post'], url_path='reverse-geocode', permission_classes=[AllowAny], authentication_classes=[])
    def reverse_geocode(self, request):
        logger = logging.getLogger('geo')

        def _f(v):
            s = str(v).strip()
            s = s.replace('،', ',')
            if ('.' not in s) and (s.count(',') == 1):
                s = s.replace(',', '.')
            return float(s)

        def _format_fallback_text(city, area, street, lat_v, lon_v):
            parts = [p for p in [street, area, city] if p]
            if parts:
                return ', '.join(parts)
            return f"{lat_v:.6f}, {lon_v:.6f}"

        def _safe_log_raw(provider, payload):
            try:
                raw = json.dumps(payload, ensure_ascii=False)
            except Exception:
                raw = str(payload)
            logger.info("reverse_geocode provider=%s raw=%s", provider, raw[:2000])

        def _build_response(city, area, street, formatted, provider, place_id, lat_v, lon_v):
            city = (city or '').strip()
            area = (area or '').strip()
            street = (street or '').strip()
            formatted = (formatted or '').strip() or _format_fallback_text(city, area, street, lat_v, lon_v)
            return Response({
                'city': city,
                'area': area,
                'street': street,
                'formatted': formatted,
                'provider': provider,
                'provider_place_id': str(place_id or ''),
                'lat': lat_v,
                'lng': lon_v,
            })

        def _parse_google_result(result):
            components = result.get('address_components') or []
            city = ''
            area = ''
            street_name = ''
            street_number = ''
            for comp in components:
                types = set(comp.get('types') or [])
                value = (comp.get('long_name') or '').strip()
                if not value:
                    continue
                if not city and ('locality' in types or 'administrative_area_level_2' in types or 'administrative_area_level_1' in types):
                    city = value
                if not area and ('sublocality' in types or 'sublocality_level_1' in types or 'neighborhood' in types):
                    area = value
                if not street_name and 'route' in types:
                    street_name = value
                if not street_number and 'street_number' in types:
                    street_number = value
            street = (f"{street_name} {street_number}".strip() if street_name else '')
            formatted = (result.get('formatted_address') or '').strip()
            return city, area, street, formatted

        def _parse_osm_payload(data_json):
            address = (data_json or {}).get('address') or {}
            city = (
                address.get('city')
                or address.get('town')
                or address.get('village')
                or address.get('municipality')
                or address.get('state_district')
                or address.get('state')
                or ''
            )
            area = (
                address.get('suburb')
                or address.get('neighbourhood')
                or address.get('quarter')
                or address.get('city_district')
                or address.get('district')
                or address.get('county')
                or ''
            )
            road = (
                address.get('road')
                or address.get('pedestrian')
                or address.get('residential')
                or address.get('footway')
                or ''
            )
            house_number = address.get('house_number') or ''
            street = (f"{road} {house_number}".strip() if road else '')
            formatted = (data_json.get('display_name') or data_json.get('formatted') or '').strip()
            return city, area, street, formatted

        def _offline_city_from_coords(lat_v, lon_v):
            points = [
                ('Baghdad', 33.3152, 44.3661),
                ('Basra', 30.5085, 47.7804),
                ('Mosul', 36.3456, 43.1575),
                ('Erbil', 36.1911, 44.0092),
                ('Najaf', 31.9896, 44.3148),
                ('Karbala', 32.6160, 44.0249),
            ]
            best_name = ''
            best_dist = None
            for name, c_lat, c_lon in points:
                d = ((lat_v - c_lat) ** 2 + (lon_v - c_lon) ** 2) ** 0.5
                if best_dist is None or d < best_dist:
                    best_dist = d
                    best_name = name
            if best_dist is not None and best_dist <= 1.0:
                return best_name
            if 28.0 <= lat_v <= 38.5 and 38.0 <= lon_v <= 49.5:
                return 'Iraq'
            return ''

        try:
            lat = _f((request.data.get('lat') or request.query_params.get('lat') or request.data.get('latitude') or request.query_params.get('latitude')))
            lon = _f((request.data.get('lng') or request.query_params.get('lng') or request.data.get('longitude') or request.query_params.get('longitude')))
        except Exception:
            return Response({'error': 'إحداثيات غير صالحة'}, status=status.HTTP_400_BAD_REQUEST)

        g_key = (os.environ.get('MAPS_API_KEY') or os.environ.get('GOOGLE_MAPS_API_KEY') or '').strip()
        if g_key:
            try:
                g_url = 'https://maps.googleapis.com/maps/api/geocode/json?' + urlencode({'latlng': f'{lat},{lon}', 'key': g_key, 'language': 'ar', 'region': 'iq'})
                g_req = Request(g_url, headers={'User-Agent': 'clothing-store/1.0'})
                g_resp = urlopen(g_req, timeout=8)
                g_data = json.loads(g_resp.read().decode('utf-8'))
                _safe_log_raw('google', g_data)
                if g_data.get('status') == 'OK' and (g_data.get('results') or []):
                    first = g_data['results'][0]
                    city, area, street, formatted = _parse_google_result(first)
                    return _build_response(city, area, street, formatted, 'google', first.get('place_id'), lat, lon)
                logger.info("reverse_geocode provider=google status=%s", g_data.get('status'))
            except HTTPError as e:
                logger.info("reverse_geocode provider=google status=%s", getattr(e, 'code', 0))
            except URLError as e:
                logger.info("reverse_geocode provider=google status=0 err=%s", str(e))
            except Exception as e:
                logger.info("reverse_geocode provider=google status=0 err=%s", str(e))

        try:
            n_url = 'https://nominatim.openstreetmap.org/reverse?' + urlencode({'format': 'jsonv2', 'lat': lat, 'lon': lon, 'accept-language': 'ar', 'countrycodes': 'iq', 'addressdetails': 1})
            n_req = Request(n_url, headers={'User-Agent': 'clothing-store/1.0 (contact: admin@example.com)'})
            n_resp = urlopen(n_req, timeout=8)
            n_data = json.loads(n_resp.read().decode('utf-8'))
            _safe_log_raw('nominatim', n_data)
            city, area, street, formatted = _parse_osm_payload(n_data)
            return _build_response(city, area, street, formatted, 'nominatim', n_data.get('place_id'), lat, lon)
        except HTTPError as e:
            logger.info("reverse_geocode provider=nominatim status=%s", getattr(e, 'code', 0))
        except URLError as e:
            logger.info("reverse_geocode provider=nominatim status=0 err=%s", str(e))
        except Exception as e:
            logger.info("reverse_geocode provider=nominatim status=0 err=%s", str(e))

        try:
            bdc_url = 'https://api.bigdatacloud.net/data/reverse-geocode-client?' + urlencode({'latitude': lat, 'longitude': lon, 'localityLanguage': 'ar'})
            bdc_req = Request(bdc_url, headers={'User-Agent': 'clothing-store/1.0'})
            bdc_resp = urlopen(bdc_req, timeout=8)
            bdc_data = json.loads(bdc_resp.read().decode('utf-8'))
            _safe_log_raw('bigdatacloud', bdc_data)
            city = (
                bdc_data.get('city')
                or bdc_data.get('locality')
                or bdc_data.get('principalSubdivision')
                or bdc_data.get('localityInfo', {}).get('administrative', [{}])[-1].get('name')
                or ''
            )
            area = (
                bdc_data.get('locality')
                or bdc_data.get('principalSubdivision')
                or ''
            )
            street = ''
            for item in (bdc_data.get('localityInfo', {}).get('informative') or []):
                candidate = (item.get('name') or '').strip()
                c_low = candidate.lower()
                if ('شارع' in candidate) or ('street' in c_low) or ('st.' in c_low):
                    street = candidate
                    break
            formatted_parts = [
                bdc_data.get('locality') or '',
                bdc_data.get('city') or '',
                bdc_data.get('principalSubdivision') or '',
                bdc_data.get('countryName') or '',
            ]
            formatted = ', '.join([p.strip() for p in formatted_parts if str(p or '').strip()])
            return _build_response(city, area, street, formatted, 'bigdatacloud', bdc_data.get('localityInfo', {}).get('isoName'), lat, lon)
        except Exception as e:
            logger.info("reverse_geocode provider=bigdatacloud status=0 err=%s", str(e))

        try:
            fb_url = 'https://geocode.maps.co/reverse?' + urlencode({'lat': lat, 'lon': lon})
            fb_req = Request(fb_url, headers={'User-Agent': 'clothing-store/1.0 (contact: admin@example.com)'})
            fb_resp = urlopen(fb_req, timeout=8)
            fb_data = json.loads(fb_resp.read().decode('utf-8'))
            _safe_log_raw('maps.co', fb_data)
            city, area, street, formatted = _parse_osm_payload(fb_data)
            return _build_response(city, area, street, formatted, 'maps.co', fb_data.get('place_id'), lat, lon)
        except Exception as e:
            logger.info("reverse_geocode provider=fallback status=0 err=%s", str(e))

        city_guess = _offline_city_from_coords(lat, lon)
        return _build_response(city_guess, '', '', '', 'fallback', '', lat, lon)

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
        if not getattr(user, 'is_authenticated', False):
            return Order.objects.none()
        if getattr(user, 'is_superuser', False) or getattr(user, 'is_staff', False):
            return Order.objects.all()
        if getattr(user, 'role', '') == 'store_admin':
            from django.db.models import Q
            return Order.objects.filter(Q(store__owner_user=user) | Q(store__owner=user))
        if getattr(user, 'role', '') == 'customer':
            return Order.objects.filter(user=user)
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

