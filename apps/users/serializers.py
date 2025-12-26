from rest_framework import serializers

from apps.users.models import User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id','username','email','bio','avatar']
        read_only_fields = ['id','username','email']
        _write_only = []
        extra_kwargs = {
            field: {'write_only': True} for field in _write_only
        }