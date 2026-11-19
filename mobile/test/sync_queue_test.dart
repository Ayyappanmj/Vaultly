import 'package:flutter_test/flutter_test.dart';
import 'package:dio/dio.dart';
import 'package:vaultly/data/sync/sync_manager.dart';

void main() {
  group('SyncManager Offline Queue Tests', () {
    late SyncManager syncManager;
    late Dio mockDio;

    setUp(() {
      mockDio = Dio();
      syncManager = SyncManager(dio: mockDio, autoSync: false);
    });

    test('enqueue creates unique operation with idempotency key', () {
      final opId = syncManager.enqueue(
        entityType: 'RECEIPT',
        entityId: 'rec-123',
        operation: 'CREATE',
        payload: {
          'merchant_name': 'Test Store',
          'total_amount': 25.50,
        },
      );

      expect(opId, isNotEmpty);
      expect(syncManager.queue.length, equals(1));

      final op = syncManager.queue.first;
      expect(op.id, equals(opId));
      expect(op.idempotencyKey, startsWith('sync-'));
      expect(op.status, equals(SyncOpStatus.pending));
      expect(op.retryCount, equals(0));
      expect(syncManager.pendingCount, equals(1));
    });

    test('manual conflict resolution keeps local or discards', () {
      final opId = syncManager.enqueue(
        entityType: 'WARRANTY',
        entityId: 'war-456',
        operation: 'UPDATE',
        payload: {'duration_months': 24},
      );

      // Force conflict status
      syncManager.queue.first.status = SyncOpStatus.conflict;
      expect(syncManager.conflictCount, equals(1));

      // Resolve keeping local
      syncManager.resolveConflict(opId, keepLocal: true);
      expect(syncManager.queue.first.status, equals(SyncOpStatus.pending));
      expect(syncManager.queue.first.payload['force_override'], isTrue);

      // Resolve accepting server
      syncManager.resolveConflict(opId, keepLocal: false);
      expect(syncManager.queue.isEmpty, isTrue);
    });

    test('retryFailed resets retry count and sets status to pending', () {
      syncManager.enqueue(
        entityType: 'SUBSCRIPTION',
        entityId: 'sub-789',
        operation: 'DELETE',
        payload: {},
      );

      final op = syncManager.queue.first;
      op.status = SyncOpStatus.failed;
      op.retryCount = 5;

      expect(syncManager.failedCount, equals(1));

      syncManager.retryFailed();
      expect(op.status, equals(SyncOpStatus.pending));
      expect(op.retryCount, equals(0));
      expect(syncManager.failedCount, equals(0));
    });
  });
}
