from rest_framework import serializers
from .models import Client, IngestionBatch, RawRecord, NormalizedRecord, AuditLog


class ClientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Client
        fields = '__all__'


class IngestionBatchSerializer(serializers.ModelSerializer):
    class Meta:
        model = IngestionBatch
        fields = '__all__'


class RawRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = RawRecord
        fields = '__all__'


class NormalizedRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = NormalizedRecord
        fields = '__all__'


class AuditLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuditLog
        fields = '__all__'