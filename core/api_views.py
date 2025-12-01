from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.db.models import Q
from .models import User, Store, Product, Address, Order
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
        if city:
            queryset = queryset.filter(city=city)
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
        
        if store_id:
            queryset = queryset.filter(store_id=store_id)
        if category:
            queryset = queryset.filter(category=category)
        if city:
            queryset = queryset.filter(store__city=city)
        
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


class AddressViewSet(viewsets.ModelViewSet):
    serializer_class = AddressSerializer
    
    def get_queryset(self):
        return Address.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


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