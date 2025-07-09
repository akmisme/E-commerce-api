import uuid
from django.db import models
from ckeditor.fields import RichTextField
# Create your models here.

class Categories(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = RichTextField()
    image = models.ImageField(null=True,blank=True, upload_to='categories')
    description = RichTextField(null=True,blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now_add=True)