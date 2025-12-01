from rest_framework import permissions


class IsCustomer(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role == 'customer'


class IsStoreOwner(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role == 'store_owner'


class IsAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role == 'admin'


class IsStoreOwnerOfStore(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if hasattr(obj, 'store'):
            return obj.store.owner == request.user
        return obj.owner == request.user


class IsOwnerOfOrder(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.user == request.user


class IsStoreOwnerOfOrder(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.store.owner == request.user