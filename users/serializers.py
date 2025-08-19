from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView

User = get_user_model()

class UserRegistrationSerializer(serializers.ModelSerializer):

    password = serializers.CharField(
        write_only=True,
        required=True,
        min_length=8,
        validators=[validate_password],
    )
    password2 = serializers.CharField(
        write_only=True,
        required=True,
    )

    class Meta:
        model = User
        fields = [
            'email', 'first_name',
            'last_name', 'password', 'password2', 'role'
        ]
        extra_kwargs = {
            'password': {'write_only': True},
            'password2': {'write_only': True},
            'role': {'required': False, 'default': 'customer'}
        }

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError("Passwords do not match")
        return attrs
        
    def create(self, validated_data):
        validated_data.pop('password2')
        user = User.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            role=validated_data.get('role', 'customer')
        )
        return user
    
class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):

    def validate(self, attrs):
        data = super().validate(attrs)
        
        # Add custom user data to the response
        data.update({
            'user_id': self.user.id,
            'email': self.user.email,
            'first_name': self.user.first_name,
            'last_name': self.user.last_name,
            'role': self.user.role,
            'is_active': self.user.is_active,
            'is_staff': self.user.is_staff,
        })
        return data
    
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        
        # Add custom claims to the token
        token['email'] = user.email
        token['user_id'] = user.id
        token['name'] = f"{user.first_name} {user.last_name}"
        token['role'] = user.role

        return token


class UserProfileSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = User
        fields = [
            'id', 'email', 'first_name',
            'last_name', 'role'
        ]
        read_only_fields = [
            'id', 'role', 'email'
        ]

class PasswordChangeSerializer(serializers.Serializer):
    old_password = serializers.CharField(
        required=True,
        style={'input_type': 'password'}
    )
    new_password = serializers.CharField(
        required=True,
        validators=[validate_password],
        style={'input_type': 'password'}
    )
    confirm_new_password = serializers.CharField(
        required=True,
        style={'input_type': 'password'}
    )

    def validate(self, attrs):
        if attrs['new_password'] != attrs['confirm_new_password']:
            raise serializers.ValidationError(
                {"new_password": "Password fields didn't match."}
            )
        return attrs

    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Old password is incorrect")
        return value        