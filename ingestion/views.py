import io
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth.models import User

from .models import Client, IngestionBatch, RawRecord, NormalizedRecord, AuditLog
from .serializers import NormalizedRecordSerializer, IngestionBatchSerializer
from .parsers import parse_sap_csv, parse_utility_csv, parse_travel_csv


PARSER_MAP = {
    'SAP': parse_sap_csv,
    'UTILITY': parse_utility_csv,
    'TRAVEL': parse_travel_csv,
}


class UploadFileView(APIView):
    def post(self, request):
        client_id = request.data.get('client_id')
        source_type = request.data.get('source_type')
        uploaded_file = request.FILES.get('file')
        if not all([client_id, source_type, uploaded_file]):
            return Response(
                {'error': 'client_id, source_type and file are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if source_type not in PARSER_MAP:
            return Response(
                {'error': f'source_type must be one of {list(PARSER_MAP.keys())}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            client = Client.objects.get(id=client_id)
        except Client.DoesNotExist:
            return Response({'error': 'Client not found'}, status=404)
        file_content = uploaded_file.read().decode('utf-8', errors='replace')
        existing = IngestionBatch.objects.filter(
            client=client,
            source_type=source_type,
            file_name=uploaded_file.name,
            status='DONE'
        ).first()

        if existing:
            return Response({
                'error': f'File "{uploaded_file.name}" was already uploaded on {existing.uploaded_at.date()}. Rename the file if this is new data.'
            }, status=status.HTTP_400_BAD_REQUEST)
        batch = IngestionBatch.objects.create(
            client=client,
            source_type=source_type,
            uploaded_by=request.user if request.user.is_authenticated else None,
            file_name=uploaded_file.name,
            status='PROCESSING',
        )
        parser = PARSER_MAP[source_type]
        parsed_rows = parser(file_content)

        row_count = 0
        error_count = 0

        for i, parsed in enumerate(parsed_rows):
            raw = RawRecord.objects.create(
                batch=batch,
                row_number=i + 1,
                raw_data=parsed['raw_data'],
                parse_status=parsed['parse_status'],
                parse_error=parsed['parse_error'],
            )

            row_count += 1
            if parsed['parse_status'] == 'FAILED':
                error_count += 1
                continue
            n = parsed['normalized']
            if n['activity_date'] is None:
                error_count += 1
                continue

            normalized = NormalizedRecord.objects.create(
                raw_record=raw,
                client=client,
                source_type=source_type,
                scope=n['scope'],
                category=n['category'],
                activity_date=n['activity_date'],
                quantity=n['quantity'],
                unit=n['unit'],
                original_quantity=n['original_quantity'],
                original_unit=n['original_unit'],
                location=n.get('location', ''),
                vendor=n.get('vendor', ''),
                cost_amount=n.get('cost_amount'),
                cost_currency=n.get('cost_currency', ''),
                status='FLAGGED' if parsed['parse_status'] == 'SUSPICIOUS' else 'PENDING',
            )
            AuditLog.objects.create(
                record=normalized,
                action='CREATED',
                performed_by=request.user if request.user.is_authenticated else None,
                new_value={'source': 'ingestion', 'batch_id': batch.id},
            )
        batch.status = 'DONE'
        batch.row_count = row_count
        batch.error_count = error_count
        batch.save()
        return Response({
            'batch_id': batch.id,
            'rows_processed': row_count,
            'errors': error_count,
            'message': f'Successfully ingested {row_count - error_count} records'
        }, status=status.HTTP_201_CREATED)


class RecordsListView(APIView):
    def get(self, request):
        records = NormalizedRecord.objects.all().select_related(
            'client', 'raw_record', 'reviewed_by'
        )
        client_id = request.query_params.get('client_id')
        record_status = request.query_params.get('status')
        source_type = request.query_params.get('source_type')

        if client_id:
            records = records.filter(client_id=client_id)
        if record_status:
            records = records.filter(status=record_status)
        if source_type:
            records = records.filter(source_type=source_type)

        records = records.order_by('-created_at')
        serializer = NormalizedRecordSerializer(records, many=True)
        return Response(serializer.data)


class ReviewRecordView(APIView):
    def patch(self, request, pk):
        try:
            record = NormalizedRecord.objects.get(id=pk)
        except NormalizedRecord.DoesNotExist:
            return Response({'error': 'Record not found'}, status=404)

        if record.is_locked:
            return Response({'error': 'Record is locked and cannot be modified'}, status=400)

        new_status = request.data.get('status')
        notes = request.data.get('notes', '')

        if new_status not in ['APPROVED', 'REJECTED', 'FLAGGED']:
            return Response({'error': 'status must be APPROVED, REJECTED or FLAGGED'}, status=400)

        old_status = record.status

        record.status = new_status
        record.notes = notes
        record.reviewed_by = request.user if request.user.is_authenticated else None
        record.reviewed_at = timezone.now()
        if new_status == 'APPROVED':
            record.is_locked = True

        record.save()
        AuditLog.objects.create(
            record=record,
            action=new_status,
            performed_by=request.user if request.user.is_authenticated else None,
            old_value={'status': old_status},
            new_value={'status': new_status, 'notes': notes},
        )

        return Response({'message': f'Record {new_status.lower()} successfully'})


class DashboardStatsView(APIView):
    def get(self, request):
        client_id = request.query_params.get('client_id')
        records = NormalizedRecord.objects.all()

        if client_id:
            records = records.filter(client_id=client_id)

        stats = {
            'total': records.count(),
            'pending': records.filter(status='PENDING').count(),
            'approved': records.filter(status='APPROVED').count(),
            'rejected': records.filter(status='REJECTED').count(),
            'flagged': records.filter(status='FLAGGED').count(),
            'by_source': {
                'SAP': records.filter(source_type='SAP').count(),
                'UTILITY': records.filter(source_type='UTILITY').count(),
                'TRAVEL': records.filter(source_type='TRAVEL').count(),
            },
            'by_scope': {
                'Scope 1': records.filter(scope=1).count(),
                'Scope 2': records.filter(scope=2).count(),
                'Scope 3': records.filter(scope=3).count(),
            }
        }
        return Response(stats)


class ClientListView(APIView):

    def get(self, request):
        from .serializers import ClientSerializer
        clients = Client.objects.all()
        serializer = ClientSerializer(clients, many=True)
        return Response(serializer.data)