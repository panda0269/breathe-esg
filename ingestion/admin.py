from django.contrib import admin
from .models import Client, IngestionBatch, RawRecord, NormalizedRecord, AuditLog

admin.site.register(Client)
admin.site.register(IngestionBatch)
admin.site.register(RawRecord)
admin.site.register(NormalizedRecord)
admin.site.register(AuditLog)