from rest_framework import permissions

class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to edit it.
    """
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions are only allowed to the owner of the snippet.
        return obj.user == request.user


class CompleteArchivePermissions(permissions.BasePermission):
    """
    Archive can be get if you are the user, you are admin or user is global.
    Archive can be created by anyone.
    Archive Update and Modify only by admin and owner
    """
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return obj.user == request.user or obj.user.username == "global" or request.user.is_staff
        elif request.method == 'POST':
                return True
        return obj.user == request.user or request.user.is_staff


class CompleteArchiveEntryPermissions(permissions.BasePermission):
    """
    Archive Entries can be get if you are the user, you are admin or user is global.
    Archive Entries can not be updated, deleted, ... via api.
    """
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return obj.archive.user == request.user or obj.archive.user.username == "global" or request.user.is_staff
        else:
            return obj.archive.user == request.user  or request.user.is_staff

########################################################################################################################








class IsOwnerOfArchiveEntryOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to edit it.
    """
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions are only allowed to the owner of the snippet.
        return obj.archive.user == request.user

class IsAdminUserOrReadOnly(permissions.IsAdminUser):

    def has_permission(self, request, view):
        is_admin = super(
            IsAdminUserOrReadOnly,
            self).has_permission(request, view)
        # Python3: is_admin = super().has_permission(request, view)
        return request.method in permissions.SAFE_METHODS or request.user.is_staff


class IsOwnerOrGlobalOrAdminReadOnly(permissions.IsAdminUser):
    """
    """
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return obj.user == request.user or obj.user.username == "global"

    def has_permission(self, request, view):

        return True




