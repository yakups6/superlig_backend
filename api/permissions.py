from rest_framework import permissions


class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Okuma (GET, HEAD, OPTIONS) herkes için açıktır;
    oluşturma, güncelleme ve silme işlemleri yalnızca yönetici (is_staff) kullanıcılara izin verir.
    """

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return bool(request.user and request.user.is_authenticated and request.user.is_staff)
