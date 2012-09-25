from django.db.models.aggregates import Count
from rbac.models import  PermissionAsigment, UserRole, DataContextPermission

def check_roles_permission(object):
    """ Check the roles that have an allowed operation over an object

    object = string, the name of the object
    returns an array with a dict with keys: role and operation

    """
    permissions=PermissionAsigment.objects.filter(object__object_name=object)
    role_operations=[]
    for perm in permissions:
        r_o=dict(role=perm.role, operation=perm.operation)
        role_operations.append(r_o)
    return role_operations

def has_permission(user, operation, object):
    """ Checks if a user has certain permission over an object

    user.- django auth user object
    operation.- rbac operation object
    object.- string, the name of the subject

    returns True if the user has permission, False if not

    """
    user_role=UserRole.objects.filter(user=user)
    for u_role in user_role:
        permission = PermissionAsigment.objects.filter(object__object_name=object,
            role=u_role.role, operation=operation)
        if permission:
            return True
    return False

def get_buildings_context(user):
    """Gets and return a dict with the different buildings in the DataContextPermission
    for the active user
    """
    datacontext = DataContextPermission.objects.filter(user_role__user=user).values(
        "building__building_name", "building").annotate(Count("building"))
    buildings=[]
    for building in datacontext:
        buildings.append(dict(building_pk=building['building'],
            building_name=building['building__building_name']))
    return buildings