from rest_framework import serializers


class UUIDSerializer(serializers.Serializer):
    id = serializers.UUIDField()


class EmailSerializer(serializers.Serializer):
    email = serializers.EmailField()