from rest_framework import permissions
from functools import wraps
from django.shortcuts import redirect
from django.http import HttpResponseForbidden


class IsCustomer(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role == 'customer'


class IsStoreOwner(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role == 'store_admin'


class IsAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and (request.user.is_staff or request.user.role == 'store_admin')


class IsStoreOwnerOfStore(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if hasattr(obj, 'store'):
            owner_user = getattr(obj.store, 'owner_user', None)
            return owner_user == request.user
        owner_user = getattr(obj, 'owner_user', None)
        return owner_user == request.user


class IsOwnerOfOrder(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.user == request.user


class IsStoreOwnerOfOrder(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        owner_user = getattr(obj.store, 'owner_user', None)
        return owner_user == request.user


def role_required(allowed_roles):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped(request, *args, **kwargs):
            user = getattr(request, 'user', None)
            if not user or not user.is_authenticated:
                return redirect('/admin-portal/login/')
            ar = (user.admin_role or '').upper()
            has_owner_role = ('OWNER' in allowed_roles) and (user.role == 'store_admin')
            if ar in {r.upper() for r in allowed_roles} or has_owner_role:
                return view_func(request, *args, **kwargs)
            return HttpResponseForbidden('Forbidden')
        return _wrapped
    return decorator


def admin_required(view_func):
    return role_required({'SUPER_ADMIN', 'OWNER', 'SUPPORT'})(view_func)
