import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../core/constants.dart';

class ReceiptsScreen extends ConsumerStatefulWidget {
  const ReceiptsScreen({super.key});

  @override
  ConsumerState<ReceiptsScreen> createState() => _ReceiptsScreenState();
}

class _ReceiptsScreenState extends ConsumerState<ReceiptsScreen> {
  final TextEditingController _searchController = TextEditingController();

  // Mock initial offline-first cache
  final List<Map<String, dynamic>> _mockReceipts = [
    {
      'id': 'rec-001',
      'merchant': 'Apple Store Fifth Ave',
      'date': '2026-11-10',
      'amount': 1299.00,
      'currency': 'USD',
      'category': 'Electronics',
      'synced': true,
    },
    {
      'id': 'rec-002',
      'merchant': 'Whole Foods Market',
      'date': '2026-11-14',
      'amount': 84.50,
      'currency': 'USD',
      'category': 'Groceries',
      'synced': true,
    },
    {
      'id': 'rec-003',
      'merchant': 'Target Supercenter',
      'date': '2026-11-17',
      'amount': 42.15,
      'currency': 'USD',
      'category': 'Home',
      'synced': false, // pending local sync
    },
  ];

  @override
  Widget build(BuildContext context) {
    final filtered = _mockReceipts.where((r) {
      final q = _searchController.text.toLowerCase();
      if (q.isEmpty) return true;
      return r['merchant'].toString().toLowerCase().contains(q) ||
          r['category'].toString().toLowerCase().contains(q);
    }).toList();

    return Scaffold(
      backgroundColor: AppConstants.background,
      appBar: AppBar(
        title: const Text('Receipts Vault', style: TextStyle(fontWeight: FontWeight.bold)),
        backgroundColor: Colors.white,
        foregroundColor: AppConstants.textPrimary,
        elevation: 0.5,
        actions: [
          IconButton(
            icon: const Icon(Icons.sync),
            tooltip: 'Sync Status',
            onPressed: () => context.push('/sync'),
          ),
        ],
      ),
      body: Column(
        children: [
          // Search & Offline Bar
          Padding(
            padding: const EdgeInsets.all(16.0),
            child: TextField(
              controller: _searchController,
              onChanged: (_) => setState(() {}),
              decoration: InputDecoration(
                hintText: 'Search merchant, category...',
                prefixIcon: const Icon(Icons.search),
                filled: true,
                fillColor: Colors.white,
                contentPadding: const EdgeInsets.symmetric(vertical: 0, horizontal: 16),
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(12),
                  borderSide: const BorderSide(color: AppConstants.border),
                ),
                enabledBorder: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(12),
                  borderSide: const BorderSide(color: AppConstants.border),
                ),
              ),
            ),
          ),

          // Offline sync banner
          Container(
            margin: const EdgeInsets.symmetric(horizontal: 16),
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
            decoration: BoxDecoration(
              color: Colors.indigo.shade50,
              borderRadius: BorderRadius.circular(8),
            ),
            child: Row(
              children: [
                Icon(Icons.cloud_done_outlined, size: 18, color: Colors.indigo.shade700),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(
                    'Offline-first: 1 item waiting to sync to cloud',
                    style: TextStyle(fontSize: 12, color: Colors.indigo.shade900),
                  ),
                ),
                GestureDetector(
                  onTap: () => context.push('/sync'),
                  child: Text(
                    'View Queue',
                    style: TextStyle(
                      fontSize: 12,
                      fontWeight: FontWeight.bold,
                      color: Colors.indigo.shade700,
                    ),
                  ),
                ),
              ],
            ),
          ),

          const SizedBox(height: 12),

          // Receipts List
          Expanded(
            child: ListView.separated(
              padding: const EdgeInsets.all(16),
              itemCount: filtered.length,
              separatorBuilder: (_, __) => const SizedBox(height: 12),
              itemBuilder: (context, index) {
                final r = filtered[index];
                return Container(
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(
                    color: Colors.white,
                    borderRadius: BorderRadius.circular(12),
                    border: Border.all(color: AppConstants.border),
                  ),
                  child: Row(
                    children: [
                      Container(
                        width: 44,
                        height: 44,
                        decoration: BoxDecoration(
                          color: Colors.indigo.shade50,
                          borderRadius: BorderRadius.circular(10),
                        ),
                        child: const Icon(Icons.receipt_long, color: AppConstants.primary),
                      ),
                      const SizedBox(width: 14),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              r['merchant'],
                              style: const TextStyle(
                                fontWeight: FontWeight.bold,
                                fontSize: 15,
                                color: AppConstants.textPrimary,
                              ),
                            ),
                            const SizedBox(height: 4),
                            Row(
                              children: [
                                Text(
                                  r['date'],
                                  style: const TextStyle(
                                    fontSize: 12,
                                    color: AppConstants.textSecondary,
                                  ),
                                ),
                                const SizedBox(width: 8),
                                Container(
                                  padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                                  decoration: BoxDecoration(
                                    color: Colors.slate.shade100,
                                    borderRadius: BorderRadius.circular(4),
                                  ),
                                  child: Text(
                                    r['category'],
                                    style: TextStyle(fontSize: 10, color: Colors.slate.shade700),
                                  ),
                                ),
                              ],
                            ),
                          ],
                        ),
                      ),
                      Column(
                        crossAxisAlignment: CrossAxisAlignment.end,
                        children: [
                          Text(
                            '\$${r['amount'].toStringAsFixed(2)}',
                            style: const TextStyle(
                              fontWeight: FontWeight.bold,
                              fontSize: 16,
                              color: AppConstants.textPrimary,
                            ),
                          ),
                          const SizedBox(height: 4),
                          Icon(
                            r['synced'] ? Icons.cloud_done : Icons.cloud_upload_outlined,
                            size: 16,
                            color: r['synced'] ? Colors.green : Colors.amber.shade700,
                          ),
                        ],
                      ),
                    ],
                  ),
                );
              },
            ),
          ),
        ],
      ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: () => context.push('/ocr-review'),
        backgroundColor: AppConstants.primary,
        icon: const Icon(Icons.camera_alt, color: Colors.white),
        label: const Text('Scan Receipt', style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
      ),
    );
  }
}
