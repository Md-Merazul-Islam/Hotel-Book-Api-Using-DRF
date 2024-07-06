# from rest_framework.permissions import BasePermission

# class IsAuthorOrReadOnly(BasePermission):
#     """
#     Custom permission to only allow authors of an object to edit or delete it.
#     """
#     def has_object_permission(self, request, view, obj):
#         if request.method in ['GET', 'HEAD', 'OPTIONS']:
#             return True
#         return obj.user == request.user



from rest_framework import permissions

class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow admin users to create, update, or delete objects.
    """
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.user.is_staff
