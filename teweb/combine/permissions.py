from rest_framework import permissions

class IsAdminUserOrReadOnly(permissions.IsAdminUser):

    def has_permission(self, request, view):
        is_admin = super(
            IsAdminUserOrReadOnly,
            self).has_permission(request, view)
        # Python3: is_admin = super().has_permission(request, view)
        return request.method in permissions.SAFE_METHODS or request.user.is_staff



class CompleteArchivePermissions(permissions.BasePermission):
    """
    Archive can be get if you are the user, you are admin or user is global.
    Archive can be created by anyone.
    Archive Update and Modify only by admin and owner
    """
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return obj.user == request.user or obj.user.username in ["global","Anonymous"] or request.user.is_staff
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
            return obj.archive.user == request.user or request.user.is_staff or obj.archive.user.username  in ["global","Anonymous"]
        else:
            return obj.archive.user == request.user  or request.user.is_staff

class ZipTreePermissions(permissions.IsAdminUser):
    """
    """
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return obj.user == request.user or obj.user.username in ["global","Anonymous"]

    def has_permission(self, request, view):
        return True

########################################################################################################################










