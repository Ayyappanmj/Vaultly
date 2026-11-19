import 'dart:async';
import 'dart:convert';
import 'dart:math';
import 'package:dio/dio.dart';
import 'package:uuid/uuid.dart';

enum SyncOpStatus { pending, syncing, synced, failed, conflict }

class SyncOperation {
  final String id;
  final String entityType; // RECEIPT, WARRANTY, SUBSCRIPTION
  final String entityId;
  final String operation; // CREATE, UPDATE, DELETE
  final Map<String, dynamic> payload;
  final String idempotencyKey;
  int retryCount;
  SyncOpStatus status;
  String? lastError;
  final DateTime createdAt;

  SyncOperation({
    required this.id,
    required this.entityType,
    required this.entityId,
    required this.operation,
    required this.payload,
    required this.idempotencyKey,
    this.retryCount = 0,
    this.status = SyncOpStatus.pending,
    this.lastError,
    DateTime? createdAt,
  }) : createdAt = createdAt ?? DateTime.now();

  Map<String, dynamic> toJson() => {
        'id': id,
        'entity_type': entityType,
        'entity_id': entityId,
        'operation': operation,
        'payload': payload,
        'idempotency_key': idempotencyKey,
        'retry_count': retryCount,
        'status': status.name.toUpperCase(),
        'last_error': lastError,
        'created_at': createdAt.toIso8601String(),
      };
}

class SyncManager {
  final Dio dio;
  final List<SyncOperation> _queue = [];
  bool _isSyncing = false;
  final bool autoSync;
  static const int maxRetries = 5;

  SyncManager({required this.dio, this.autoSync = true});

  List<SyncOperation> get queue => List.unmodifiable(_queue);
  int get pendingCount => _queue.where((o) => o.status == SyncOpStatus.pending).length;
  int get failedCount => _queue.where((o) => o.status == SyncOpStatus.failed).length;
  int get conflictCount => _queue.where((o) => o.status == SyncOpStatus.conflict).length;

  /// Enqueue a change to be sent when online
  String enqueue({
    required String entityType,
    required String entityId,
    required String operation,
    required Map<String, dynamic> payload,
  }) {
    final opId = const Uuid().v4();
    final idempotencyKey = 'sync-$opId';

    final op = SyncOperation(
      id: opId,
      entityType: entityType,
      entityId: entityId,
      operation: operation,
      payload: payload,
      idempotencyKey: idempotencyKey,
    );

    _queue.add(op);
    // Trigger opportunistic sync if enabled
    if (autoSync) {
      unawaited(processQueue());
    }
    return opId;
  }

  /// Process pending operations against backend /api/v1/sync
  Future<void> processQueue() async {
    if (_isSyncing) return;
    final pendingOps = _queue.where((o) => o.status == SyncOpStatus.pending).toList();
    if (pendingOps.isEmpty) return;

    _isSyncing = true;
    for (final op in pendingOps) {
      op.status = SyncOpStatus.syncing;
      try {
        final response = await dio.post(
          '/sync',
          data: {
            'operations': [
              {
                'operation_id': op.id,
                'entity_type': op.entityType,
                'entity_id': op.entityId,
                'action': op.operation,
                'idempotency_key': op.idempotencyKey,
                'client_version': op.payload['client_version'] ?? 1,
                'payload': op.payload,
              }
            ],
            'last_pulled_at': DateTime.now().subtract(const Duration(days: 7)).toIso8601String(),
          },
        );

        if (response.statusCode == 200) {
          final results = response.data['results'] as List<dynamic>?;
          final res = results?.firstWhere(
            (r) => r['operation_id'] == op.id,
            orElse: () => null,
          );

          if (res != null && res['status'] == 'CONFLICT') {
            op.status = SyncOpStatus.conflict;
            op.lastError = 'Server version ${res['server_version']} conflicts with client.';
          } else {
            op.status = SyncOpStatus.synced;
          }
        } else {
          _handleOpFailure(op, 'HTTP ${response.statusCode}');
        }
      } catch (e) {
        _handleOpFailure(op, e.toString());
      }
    }
    _isSyncing = false;
  }

  void _handleOpFailure(SyncOperation op, String error) {
    op.retryCount++;
    op.lastError = error;
    if (op.retryCount >= maxRetries) {
      op.status = SyncOpStatus.failed;
    } else {
      op.status = SyncOpStatus.pending;
      // Exponential backoff with jitter
      final backoffMs = (pow(2, op.retryCount) * 1000) + Random().nextInt(500);
      Timer(Duration(milliseconds: backoffMs.toInt()), () {
        unawaited(processQueue());
      });
    }
  }

  /// Resolve conflict manually: user chooses keep local or accept server
  void resolveConflict(String opId, {required bool keepLocal}) {
    final opIndex = _queue.indexWhere((o) => o.id == opId);
    if (opIndex == -1) return;

    if (keepLocal) {
      // Force push by incrementing client version and resetting status
      _queue[opIndex].status = SyncOpStatus.pending;
      _queue[opIndex].payload['force_override'] = true;
      unawaited(processQueue());
    } else {
      // Discard local operation
      _queue.removeAt(opIndex);
    }
  }

  void retryFailed() {
    for (final op in _queue.where((o) => o.status == SyncOpStatus.failed)) {
      op.retryCount = 0;
      op.status = SyncOpStatus.pending;
    }
    unawaited(processQueue());
  }

  void clearSynced() {
    _queue.removeWhere((o) => o.status == SyncOpStatus.synced);
  }
}
