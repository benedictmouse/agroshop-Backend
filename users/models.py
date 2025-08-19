from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin

class CustomManager(BaseUserManager):

    def create_user(self, email, password, first_name, last_name, **extra_fields):
        if not email:
            raise ValueError('Email is required')
        if not password:
            raise ValueError('Password is required')
        
        email = self.normalize_email(email)
        user = self.model(
            email=email,
            first_name=first_name,
            last_name=last_name,
            **extra_fields
        )
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        
        # Extract first_name and last_name from extra_fields or set defaults
        first_name = extra_fields.pop('first_name', '')
        last_name = extra_fields.pop('last_name', '')
        
        return self.create_user(email, password, first_name, last_name, **extra_fields)
    
class CustomUser(AbstractBaseUser, PermissionsMixin):
        
    ROLE_CHOICES = (
        ("admin", "Admin"),
        ("vendor", "Vendor"),
        ("customer", "Customer"),  
    )

    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='customer')
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = CustomManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    def __str__(self):
        return self.email

    def get_by_natural_key(self, email):
        return self.__class__.objects.get(email=email)