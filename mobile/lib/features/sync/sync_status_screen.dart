import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/constants.dart';

class SyncStatusScreen extends ConsumerStatefulWidget {
  const SyncStatusScreen({super.key});

  @override
  ConsumerState<SyncStatusScreen> createState() => _SyncStatusScreenState();
}

class _SyncStatusScreenState extends ConsumerState<SyncStatusScreen> {
  bool _isSyncing = false;

  final List<Map<String, dynamic>> _mockQueue = [
    {
      'id': 'op-001',
      'entity_type': 'RECEIPT',
      'action': 'CREATE',
      'entity_name': 'Target Supercenter (\$42.15)',
      'status': 'PENDING',
      'retry_count': 0,
      'time': 'Just now',
    },
    {
      'id': 'op-002',
      'entity_type': 'WARRANTY',
      'action': 'UPDATE',
      'entity_name': 'MacBook Pro Coverage Update',
      'status': 'SYNCED',
      'retry_count': 0,
      'time': '2 hours ago',
    },
    {
      'id': 'op-003',
      'entity_type': 'RECEIPT',
      'action': 'UPDATE',
      'entity_name': 'Whole Foods Memo Revision',
      'status': 'CONFLICT',
      'retry_count': 1,
      'time': 'Yesterday',
      'conflict_desc': 'Server has version 3; local client has version 2.',
    },
  ];

  Future<void> _triggerSync() async {
    setState(() => _isSyncing = true);
    await Future.delayed(const Duration(seconds: 2));
    if (mounted) {
      setState(() {
        _isSyncing = false;
        final pending = _mockQueue.firstWhere((o) => o['status'] == 'PENDING');
        pending['status'] = 'SYNCED';
      });
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Offline queue synchronized with Vaultly backend!')),
      );
    }
  }

  void _showConflictDialog(Map<String, dynamic> item) {
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Resolve Sync Conflict'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(item['entity_name'], style: const TextStyle(fontWeight: FontWeight.bold)),
            const SizedBox(height: 8),
            Text(item['conflict_desc'] ?? 'Version discrepancy detected between device and cloud.'),
            const SizedBox(height: 12),
            const Text(
              'Select which version to retain:',
              style: TextStyle(fontSize: 12, color: AppConstants.textSecondary),
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () {
              Navigator.pop(ctx);
              setState(() => item['status'] = 'SYNCED');
              ScaffoldMessenger.of(context).showSnackBar(
                const SnackBar(content: Text('Kept cloud server version.')),
              );
            },
            child: const Text('Accept Server Version'),
          ),
          ElevatedButton(
            onPressed: () {
              Navigator.pop(ctx);
              setState(() => item['status'] = 'PENDING');
              ScaffoldMessenger.of(context).showSnackBar(
                const SnackBar(content: Text('Local version prioritized for overwrite.')),
              );
            },
            style: ElevatedButton.styleFrom(backgroundColor: AppConstants.primary),
            child: const Text('Force Overwrite (Keep Local)', style: TextStyle(color: Colors.white)),
          ),
        ],
      ),
    );
  }

  Widget _buildStatusBadge(String status) {
    Color bg;
    Color fg;

    switch (status) {
      case 'PENDING':
        bg = Colors.amber.shade50;
        fg = Colors.amber.shade900;
        break;
      case 'SYNCED':
        bg = Colors.green.shade50;
        fg = Colors.green.shade800;
        break;
      case 'CONFLICT':
        bg = Colors.red.shade50;
        fg = Colors.red.shade800;
        break;
      default:
        bg = Colors.slate.shade100;
        fg = Colors.slate.shade700;
    }

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
      decoration: BoxDecoration(color: bg, borderRadius: BorderRadius.circular(12)),
      child: Text(
        status,
        style: TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: fg),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppConstants.background,
      appBar: AppBar(
        title: const Text('Offline Sync Status', style: TextStyle(fontWeight: FontWeight.bold)),
        backgroundColor: Colors.white,
        foregroundColor: AppConstants.textPrimary,
        elevation: 0.5,
      ),
      body: Column(
        children: [
          // Header summary
          Container(
            padding: const EdgeInsets.all(20),
            color: Colors.white,
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                const Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'Local Drift SQLite Queue',
                      style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
                    ),
                    SizedBox(height: 4),
                    Text(
                      'Idempotent delta sync with exponential backoff',
                      style: TextStyle(fontSize: 12, color: AppConstants.textSecondary),
                    ),
                  ],
                ),
                ElevatedButton.icon(
                  onPressed: _isSyncing ? null : _triggerSync,
                  icon: _isSyncing
                      ? const SizedBox(
                          width: 14,
                          height: 14,
                          child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                        )
                      : const Icon(Icons.sync, size: 16),
                  label: Text(_isSyncing ? 'Syncing...' : 'Sync Now'),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: AppConstants.primary,
                    foregroundColor: Colors.white,
                  ),
                ),
              ],
            ),
          ),

          const Divider(height: 1),

          // Queue Items List
          Expanded(
            child: ListView.separated(
              padding: const EdgeInsets.all(16),
              itemCount: _mockQueue.length,
              separatorBuilder: (_, __) => const SizedBox(height: 12),
              itemBuilder: (context, index) {
                final item = _mockQueue[index];
                final isConflict = item['status'] == 'CONFLICT';

                return Container(
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(
                    color: Colors.white,
                    borderRadius: BorderRadius.circular(12),
                    border: Border.all(
                      color: isConflict ? Colors.red.shade300 : AppConstants.border,
                    ),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          Row(
                            children: [
                              Container(
                                padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                                decoration: BoxDecoration(
                                  color: Colors.slate.shade100,
                                  borderRadius: BorderRadius.circular(4),
                                ),
                                child: Text(
                                  '${item['action']} ${item['entity_type']}',
                                  style: TextStyle(
                                    fontSize: 10,
                                    fontWeight: FontWeight.bold,
                                    color: Colors.slate.shade700,
                                  ),
                                ),
                              ),
                              const SizedBox(width: 8),
                              Text(
                                item['time'],
                                style: const TextStyle(fontSize: 11, color: AppConstants.textSecondary),
                              ),
                            ],
                          ),
                          _buildStatusBadge(item['status']),
                        ],
                      ),
                      const SizedBox(height: 8),
                      Text(
                        item['entity_name'],
                        style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14),
                      ),
                      if (isConflict) ...[
                        const SizedBox(height: 8),
                        Text(
                          item['conflict_desc'],
                          style: TextStyle(fontSize: 12, color: Colors.red.shade700),
                        ),
                        const SizedBox(height: 10),
                        OutlinedButton(
                          onPressed: () => _showConflictDialog(item),
                          style: OutlinedButton.styleFrom(
                            foregroundColor: Colors.red.shade700,
                            side: BorderSide(color: Colors.red.shade300),
                            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                          ),
                          child: const Text('Resolve Conflict'),
                        ),
                      ],
                    ],
                  ),
                );
              },
            ),
          ),
        ],
      ),
    );
  }
}
