from rest_framework.permissions import BasePermission


class IsObjectOwner(BasePermission):

    #if api details=True, only has_permission is checked
    #if api details=False, check both has_permission and has_object_permission
    #with error, display IsObjectOwner.message

    message = "you do no have permission to access this object."

    def has_object_permission(self, request, view, obj):
        return request.user == obj.user