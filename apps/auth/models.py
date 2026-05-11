from django.db import models
from django.contrib.auth import get_user_model

from apps.common.models import BaseModel

User = get_user_model()

class TokenTypes(BaseModel):
    type_code = models.CharField(max_length=20)
    token_type = models.CharField(max_length=20)

    def __str__(self) -> str:
        return self.token_type

class ActivationTokens(BaseModel):

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    token = models.TextField()
    is_activated = models.BooleanField(default=False)
    token_type = models.ForeignKey(TokenTypes, on_delete=models.CASCADE, null=True, blank=True)
    
    def __str__(self) -> str:
        return self.user.first_name + self.token
