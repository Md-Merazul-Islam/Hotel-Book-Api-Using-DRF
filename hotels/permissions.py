from rest_framework.permissions import BasePermission

class IsAuthorOrReadOnly(BasePermission):
    """
    Custom permission to only allow authors of an object to edit or delete it.
    """
    def has_object_permission(self, request, view, obj):
        if request.method in ['GET', 'HEAD', 'OPTIONS']:
            return True
        return obj.user == request.user
