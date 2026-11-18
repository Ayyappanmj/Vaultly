import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/constants.dart';

class WarrantiesScreen extends ConsumerWidget {
  const WarrantiesScreen({super.key});

  final List<Map<String, dynamic>> _mockWarranties = const [
    {
      'id': 'w-1',
      'title': 'MacBook Pro M3 Max',
      'duration': 12,
      'expiry': '2027-11-10',
      'status': 'ACTIVE',
      'notes': 'AppleCare+ Agreement #928192',
    },
    {
      'id': 'w-2',
      'title': 'Sony WH-1000XM5 Headphones',
      'duration': 24,
      'expiry': '2026-12-05',
      'status': 'EXPIRING_SOON',
      'notes': 'Best Buy Geek Squad Protection',
    },
    {
      'id': 'w-3',
      'title': 'Dyson V12 Vacuum',
      'duration': 24,
      'expiry': '2025-08-15',
      'status': 'EXPIRED',
      'notes': 'Expired standard warranty',
    },
  ];

  Widget _buildStatusBadge(String status) {
    Color bg;
    Color text;
    String label;

    switch (status) {
      case 'ACTIVE':
        bg = Colors.green.shade50;
        text = Colors.green.shade800;
        label = 'Active';
        break;
      case 'EXPIRING_SOON':
        bg = Colors.amber.shade50;
        text = Colors.amber.shade900;
        label = 'Expiring Soon';
        break;
      case 'EXPIRED':
        bg = Colors.red.shade50;
        text = Colors.red.shade800;
        label = 'Expired';
        break;
      default:
        bg = Colors.slate.shade100;
        text = Colors.slate.shade700;
        label = status;
    }

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
      decoration: BoxDecoration(
        color: bg,
        borderRadius: BorderRadius.circular(12),
      ),
      child: Text(
        label,
        style: TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: text),
      ),
    );
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return Scaffold(
      backgroundColor: AppConstants.background,
      appBar: AppBar(
        title: const Text('Warranties', style: TextStyle(fontWeight: FontWeight.bold)),
        backgroundColor: Colors.white,
        foregroundColor: AppConstants.textPrimary,
        elevation: 0.5,
      ),
      body: ListView.separated(
        padding: const EdgeInsets.all(16),
        itemCount: _mockWarranties.length,
        separatorBuilder: (_, __) => const SizedBox(height: 12),
        itemBuilder: (context, index) {
          final w = _mockWarranties[index];
          return Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: Colors.white,
              borderRadius: BorderRadius.circular(12),
              border: Border.all(color: AppConstants.border),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Expanded(
                      child: Text(
                        w['title'],
                        style: const TextStyle(
                          fontSize: 15,
                          fontWeight: FontWeight.bold,
                          color: AppConstants.textPrimary,
                        ),
                      ),
                    ),
                    _buildStatusBadge(w['status']),
                  ],
                ),
                const SizedBox(height: 10),
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Text(
                      'Coverage: ${w['duration']} Months',
                      style: const TextStyle(fontSize: 12, color: AppConstants.textSecondary),
                    ),
                    Text(
                      'Expires: ${w['expiry']}',
                      style: const TextStyle(
                        fontSize: 12,
                        fontWeight: FontWeight.w600,
                        color: AppConstants.textPrimary,
                      ),
                    ),
                  ],
                ),
                if (w['notes'] != null) ...[
                  const SizedBox(height: 8),
                  Text(
                    w['notes'],
                    style: TextStyle(fontSize: 11, color: Colors.slate.shade500, fontStyle: FontStyle.italic),
                  ),
                ],
              ],
            ),
          );
        },
      ),
    );
  }
}
