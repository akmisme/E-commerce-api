# accounts/serializers.py
from rest_framework import serializers
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.exceptions import AuthenticationFailed
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import Group, Permission
from .models import User
from accounts.helpers import mmt  # ✅ Myanmar time formatter
from django.utils import timezone    

class CustomTokenObtainPairSerializer(serializers.Serializer):
    login    = serializers.CharField()
    password = serializers.CharField(style={"input_type": "password"})

    def validate(self, attrs):
        login = attrs.get("login")
        password = attrs.get("password")

        user = authenticate(
            request=self.context.get("request"),
            username=login,
            password=password,
        )
        if not user:
            raise AuthenticationFailed(
                _("Invalid username/email/phone or password"), code="authorization"
            )
        if not user.is_active:
            raise AuthenticationFailed(_("Account is disabled."), code="authorization")

        # ➋  last_login ကို Myanmar time aware datetime နဲ့ သိမ်း
        user.last_login = timezone.now()           # (settings.TIME_ZONE = 'Asia/Yangon')
        user.save(update_fields=["last_login"])
        user.refresh_from_db(fields=["last_login"])  # memory ထဲကို sync

        refresh = RefreshToken.for_user(user)

        return {
            "refresh": str(refresh),
            "access":  str(refresh.access_token),
            "user": {
                "id":          user.id,
                "username":    user.username,
                "email":       user.email,
                "phone":       user.phone,
                "date_joined": mmt(user.date_joined),
                "last_login":  mmt(user.last_login),   # ➌ null မထွက်တော့ပါ
            },
            "message": "Login successful",
        }


class UserRegisterSerializer(serializers.ModelSerializer):
    password        = serializers.CharField(write_only=True, style={"input_type": "password"})
    confirm_password = serializers.CharField(write_only=True, style={"input_type": "password"})

    class Meta:
        model  = User
        fields = ["username", "email", "phone", "password", "confirm_password"]

    def validate(self, attrs):
        if attrs["password"] != attrs["confirm_password"]:
            raise serializers.ValidationError({"confirm_password": "Passwords do not match."})
        return attrs

    def create(self, validated_data):
        validated_data.pop("confirm_password")  # serializer-level only; not needed for model
        user = User.objects.create_user(
            username=validated_data["username"],
            email   = validated_data["email"],
            phone   = validated_data["phone"],
            password=validated_data["password"],
        )
        return user
    


# ========= Mini Serializers =========
class GroupMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Group
        fields = ["id", "name"]

class PermMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Permission
        fields = ["id", "codename", "name"]


class PermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Permission
        fields = ['id', 'codename', 'name']

# ========= Main Group Serializer =========
class GroupSerializer(serializers.ModelSerializer):
    # -------- OUTPUT --------
    permissions = PermMiniSerializer(many=True, read_only=True)

    # -------- INPUT (IDs only) --------
    permission_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Permission.objects.all(),
        write_only=True,
        required=False,
        source="permissions"        # <– same m2m field
    )

    class Meta:
        model  = Group
        fields = ["id", "name", "permissions", "permission_ids"]

    # -------- create / update override --------
    def create(self, validated_data):
        perms = validated_data.pop("permissions", [])   # IDs come via `permission_ids`
        group = Group.objects.create(**validated_data)
        if perms:
            group.permissions.set(perms)
        return group

    def update(self, instance, validated_data):
        perms = validated_data.pop("permissions", None)
        instance = super().update(instance, validated_data)
        if perms is not None:                           # if key present → replace
            instance.permissions.set(perms)
        return instance



class UserListSerializer(serializers.ModelSerializer):
    status      = serializers.SerializerMethodField()
    role        = serializers.SerializerMethodField()
    date_joined = serializers.SerializerMethodField()
    last_login  = serializers.SerializerMethodField()

    groups      = GroupMiniSerializer(many=True, read_only=True)
    permissions = serializers.SerializerMethodField()          # merged perms list

    class Meta:
        model  = User
        fields = [
            "id", "username", "email", "phone",
            "date_joined", "last_login",
            "is_active", "is_staff", "is_superuser",
            "status", "role",
            "groups", "permissions",                # ⭐️ new
        ]

    # ---------- helpers ----------
    def get_status(self, obj):
        return "Active" if obj.is_active else "Inactive"

    def get_role(self, obj):
        if obj.is_superuser:
            return "Admin"
        elif obj.is_staff:
            return "Staff"
        return "User"

    def get_date_joined(self, obj):
        return mmt(obj.date_joined)

    def get_last_login(self, obj):
        return mmt(obj.last_login) if obj.last_login else None

    def get_permissions(self, obj):
        """Return list of 'app_label.codename' strings from direct + group perms"""
        return list(obj.get_all_permissions())