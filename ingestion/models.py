from django.db import models
from django.contrib.auth.models import User


class Client(models.Model):
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class IngestionBatch(models.Model):
    SOURCE_TYPES = [
        ('SAP', 'SAP Fuel & Procurement'),
        ('UTILITY', 'Utility Electricity'),
        ('TRAVEL', 'Corporate Travel'),
    ]
    STATUS_CHOICES = [
        ('PROCESSING', 'Processing'),
        ('DONE', 'Done'),
        ('FAILED', 'Failed'),
    ]

    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    source_type = models.CharField(max_length=20, choices=SOURCE_TYPES)
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    file_name = models.CharField(max_length=255)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PROCESSING')
    row_count = models.IntegerField(default=0)
    error_count = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.client.name} - {self.source_type} - {self.uploaded_at.date()}"


class RawRecord(models.Model):
    PARSE_STATUS = [
        ('OK', 'OK'),
        ('FAILED', 'Failed'),
        ('SUSPICIOUS', 'Suspicious'),
    ]

    batch = models.ForeignKey(IngestionBatch, on_delete=models.CASCADE)
    row_number = models.IntegerField()
    raw_data = models.JSONField()
    parse_status = models.CharField(max_length=20, choices=PARSE_STATUS, default='OK')
    parse_error = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Row {self.row_number} - Batch {self.batch.id}"


class NormalizedRecord(models.Model):
    SOURCE_TYPES = [
        ('SAP', 'SAP Fuel & Procurement'),
        ('UTILITY', 'Utility Electricity'),
        ('TRAVEL', 'Corporate Travel'),
    ]
    SCOPE_CHOICES = [
        (1, 'Scope 1 - Direct'),
        (2, 'Scope 2 - Electricity'),
        (3, 'Scope 3 - Travel'),
    ]
    CATEGORY_CHOICES = [
        ('FUEL', 'Fuel'),
        ('ELECTRICITY', 'Electricity'),
        ('FLIGHT', 'Flight'),
        ('HOTEL', 'Hotel'),
        ('GROUND_TRANSPORT', 'Ground Transport'),
    ]
    STATUS_CHOICES = [
        ('PENDING', 'Pending Review'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('FLAGGED', 'Flagged as Suspicious'),
    ]

    raw_record = models.OneToOneField(RawRecord, on_delete=models.CASCADE)
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    source_type = models.CharField(max_length=20, choices=SOURCE_TYPES)
    scope = models.IntegerField(choices=SCOPE_CHOICES)
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES)

    activity_date = models.DateField()
    quantity = models.FloatField()
    unit = models.CharField(max_length=20)
    original_quantity = models.FloatField()
    original_unit = models.CharField(max_length=20)

    location = models.CharField(max_length=255, blank=True, null=True)
    vendor = models.CharField(max_length=255, blank=True, null=True)
    cost_amount = models.FloatField(blank=True, null=True)
    cost_currency = models.CharField(max_length=10, blank=True, null=True)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_locked = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.client.name} - {self.category} - {self.activity_date}"


class AuditLog(models.Model):
    ACTION_CHOICES = [
        ('CREATED', 'Created'),
        ('EDITED', 'Edited'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('FLAGGED', 'Flagged'),
        ('LOCKED', 'Locked'),
    ]

    record = models.ForeignKey(NormalizedRecord, on_delete=models.CASCADE)
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    performed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    performed_at = models.DateTimeField(auto_now_add=True)
    old_value = models.JSONField(null=True, blank=True)
    new_value = models.JSONField(null=True, blank=True)

    def __str__(self):
        return f"{self.action} by {self.performed_by} at {self.performed_at}"