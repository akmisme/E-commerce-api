# accounts/views.py
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.response import Response
from rest_framework import status
from .serializers import CustomTokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import *
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny,IsAuthenticated
from .models import User
from .helpers import mmt  
from django.shortcuts import get_object_or_404
from datetime import datetime
from rest_framework.pagination import PageNumberPagination
from django.db.models import Q
import json
from rest_framework import permissions

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer
    

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data      # refresh/access/user
        data["message"] = "Login successful"
        return Response(data, status=status.HTTP_200_OK)


@api_view(["POST"])
@permission_classes([AllowAny])
def register_user(request):
    serializer = UserRegisterSerializer(data=request.data)
    if serializer.is_valid():
        user    = serializer.save()
        refresh = RefreshToken.for_user(user)

        return Response(
            {
                "message": "User created successfully.",
                "user": {
                    "id":          user.id,
                    "username":    user.username,
                    "email":       user.email,
                    "phone":       user.phone,
                    "date_joined": mmt(user.date_joined),
                    "last_login":  mmt(user.last_login),
                },
                "refresh": str(refresh),
                "access":  str(refresh.access_token),
            },
            status=status.HTTP_201_CREATED,
        )
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



# @api_view(["GET"])
# def user_list(request):
#     queryset = User.objects.all()

#     # 🔍 search
#     q = request.query_params.get("search")
#     if q:
#         queryset = queryset.filter(
#             Q(username__icontains=q) |
#             Q(email__icontains=q) |
#             Q(phone__icontains=q)
#         )

#     # 🔧 filter
#     is_active = request.query_params.get("is_active")
#     if is_active is not None:
#         queryset = queryset.filter(is_active=is_active.lower() == "true")

#     is_staff = request.query_params.get("is_staff")
#     if is_staff is not None:
#         queryset = queryset.filter(is_staff=is_staff.lower() == "true")

#     is_superuser = request.query_params.get("is_superuser")
#     if is_superuser is not None:
#         queryset = queryset.filter(is_superuser=is_superuser.lower() == "true")

#     # status filter - "Active" or "Inactive"
#     status = request.query_params.get("status")
#     if status is not None:
#         if status.lower() == "active":
#             queryset = queryset.filter(is_active=True)
#         elif status.lower() == "inactive":
#             queryset = queryset.filter(is_active=False)

#     # role filter - "Admin", "Staff", "User"
#     role = request.query_params.get("role")
#     if role is not None:
#         role = role.lower()
#         if role == "admin":
#             queryset = queryset.filter(is_superuser=True)
#         elif role == "staff":
#             queryset = queryset.filter(is_staff=True, is_superuser=False)
#         elif role == "user":
#             queryset = queryset.filter(is_staff=False, is_superuser=False)

#     # 📄 pagination
#     paginator = PageNumberPagination()
#     paginator.page_size = 2
#     page = paginator.paginate_queryset(queryset, request)

#     # ✅ serializer ကို တိုက်ရိုက်သုံး
#     serializer = UserListSerializer(page, many=True)

#     return paginator.get_paginated_response({
#         "message": "User list fetched successfully.",
#         "users": serializer.data
#     })


@api_view(["GET"])
def user_list(request):
    queryset = User.objects.all()

    # 🔍 search
    q = request.query_params.get("search")
    if q:
        queryset = queryset.filter(
            Q(username__icontains=q) |
            Q(email__icontains=q) |
            Q(phone__icontains=q)
        )

    # 🔧 boolean filters
    bool_params = {
        "is_active": "is_active",
        "is_staff": "is_staff",
        "is_superuser": "is_superuser",
    }
    for param, field in bool_params.items():
        val = request.query_params.get(param)
        if val is not None:
            queryset = queryset.filter(**{field: val.lower() == "true"})

    # status (derived)
    status_param = request.query_params.get("status")
    if status_param:
        queryset = queryset.filter(is_active=(status_param.lower() == "active"))

    # role (derived)
    role = request.query_params.get("role")
    if role:
        role = role.lower()
        if role == "admin":
            queryset = queryset.filter(is_superuser=True)
        elif role == "staff":
            queryset = queryset.filter(is_staff=True, is_superuser=False)
        elif role == "user":
            queryset = queryset.filter(is_staff=False, is_superuser=False)

    # 📅 date range filter — start_date & end_date on date_joined
    start_date = request.query_params.get("start_date")
    end_date   = request.query_params.get("end_date")

    if start_date:
        try:
            sd = datetime.fromisoformat(start_date).date()
            queryset = queryset.filter(date_joined__date__gte=sd)
        except ValueError:
            return Response({"detail": "start_date format must be YYYY-MM-DD"}, status=400)

    if end_date:
        try:
            ed = datetime.fromisoformat(end_date).date()
            queryset = queryset.filter(date_joined__date__lte=ed)
        except ValueError:
            return Response({"detail": "end_date format must be YYYY-MM-DD"}, status=400)

    # 📄 pagination
    paginator = PageNumberPagination()
    paginator.page_size = 2
    page = paginator.paginate_queryset(queryset, request)

    serializer = UserListSerializer(page, many=True)

    return paginator.get_paginated_response({
        "message": "User list fetched successfully.",
        "users": serializer.data
    })


@api_view(['GET'])
def user_detail(request, pk):
    user = get_object_or_404(User, pk=pk)
    serializer = UserListSerializer(user)
    return Response({
        "message": "User detail retrieved successfully.",
        "detail": f"Details for user id {pk}",
        "data": serializer.data
    }, status=status.HTTP_200_OK)


# @api_view(['PUT', 'PATCH'])
# def user_update(request, pk):
#     user = get_object_or_404(User, pk=pk)
#     serializer = UserListSerializer(user, data=request.data, partial=True)  # partial=True ဆို PATCH method အတွက်ပါ
#     if serializer.is_valid():
#         serializer.save()
#         return Response({
#             "message": "User updated successfully.",
#             "data": serializer.data
#         }, status=status.HTTP_200_OK)
#     return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



@api_view(["PUT", "PATCH"])
def user_update(request, pk):
    user = get_object_or_404(User, pk=pk)

    data = request.data.copy()                 # mutable copy

    group_ids = data.pop("groups", None)
    perm_ids  = data.pop("permissions", None)

    # 🔄 if sent as string (e.g. "[1,2]"), convert to list
    def _ensure_list(val):
        if isinstance(val, str):
            try:
                return json.loads(val)         # "['1',2]" -> [1,2]
            except json.JSONDecodeError:
                return []
        return val

    group_ids = _ensure_list(group_ids)
    perm_ids  = _ensure_list(perm_ids)

    serializer = UserListSerializer(user, data=data, partial=True,
                                    context={"request": request})
    if serializer.is_valid():
        serializer.save()

        if group_ids is not None:
            user.groups.set(group_ids)
        if perm_ids is not None:
            user.user_permissions.set(perm_ids)

        return Response({"message": "User updated successfully.",
                         "data": serializer.data})
    return Response(serializer.errors, status=400)





@api_view(['DELETE'])
def user_delete(request, pk):
    user = get_object_or_404(User, pk=pk)
    user.delete()
    return Response({"message": "User deleted successfully."}, status=status.HTTP_204_NO_CONTENT)




@api_view(["GET"])
def group_list(request):
    queryset = Group.objects.all()

    # 🔍 search by name
    search = request.query_params.get("search")
    if search:
        queryset = queryset.filter(name__icontains=search)

    # 🔧 filter by permission IDs (?permissions=5,6 or ?permissions=5&permissions=6)
    perm_param = request.query_params.get("permissions")
    perm_list  = request.query_params.getlist("permissions")

    # handle both comma‑string & repeated params
    if perm_param and not perm_list:
        # e.g. permissions=5,6
        perm_list = [x.strip() for x in perm_param.split(",") if x.strip()]

    if perm_list:
        try:
            perm_ids = [int(p) for p in perm_list]
            queryset = queryset.filter(permissions__id__in=perm_ids).distinct()
        except ValueError:
            return Response({"detail": "permissions must be integers"}, status=status.HTTP_400_BAD_REQUEST)

    # 📄 pagination
    paginator = PageNumberPagination()
    paginator.page_size = 2                       # default page size
    paginator.page_size_query_param = "page_size"  # allow ?page_size=xx
    page = paginator.paginate_queryset(queryset, request)

    serializer = GroupSerializer(page, many=True)
    return paginator.get_paginated_response({
        "message": "Group list fetched successfully.",
        "groups": serializer.data
    })

@api_view(['POST'])
def group_create(request):
    serializer = GroupSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()                     # group ကို create သွားပြီ
        return Response(
            {
                "message": "Group created successfully.",
                "data": serializer.data       # id / name / permissions အကုန်ပါလိမ့်မယ်
            },
            status=status.HTTP_201_CREATED
        )
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
def group_detail(request, pk):
    group = get_object_or_404(Group, pk=pk)
    serializer = GroupSerializer(group)
    return Response({
        "message": "Group detail fetched successfully.",
        "detail": serializer.data
    })


@api_view(['PUT', 'PATCH'])
def group_update(request, pk):
    group = get_object_or_404(Group, pk=pk)
    partial = request.method == "PATCH"

    serializer = GroupSerializer(group, data=request.data, partial=partial)
    if serializer.is_valid():
        serializer.save()
        return Response(
            {
                "message": "Group updated successfully.",
                "data": serializer.data
            },
            status=status.HTTP_200_OK
        )
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['DELETE'])
def group_delete(request, pk):
    group = get_object_or_404(Group, pk=pk)
    group.delete()
    return Response(
        {"message": "Group deleted successfully."},
        status=200
    )


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])  # လိုအပ်သလို permission များပြောင်းလဲနိုင်ပါသည်
def permission_list_view(request):
    permissions_qs = Permission.objects.all()
    serializer = PermissionSerializer(permissions_qs, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)
