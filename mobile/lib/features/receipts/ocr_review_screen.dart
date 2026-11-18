import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../core/constants.dart';

class OcrReviewScreen extends ConsumerStatefulWidget {
  const OcrReviewScreen({super.key});

  @override
  ConsumerState<OcrReviewScreen> createState() => _OcrReviewScreenState();
}

class _OcrReviewScreenState extends ConsumerState<OcrReviewScreen> {
  final _merchantController = TextEditingController(text: 'Target Supercenter');
  final _totalController = TextEditingController(text: '42.15');
  final _dateController = TextEditingController(text: '2026-11-17');
  final _notesController = TextEditingController(text: 'Household supplies');

  // Confidence indicators (from OCR engine)
  final double _merchantConfidence = 0.95;
  final double _totalConfidence = 0.98;
  final double _dateConfidence = 0.82;

  // Duplicate detection state
  final bool _isDuplicateSuspected = false;

  Widget _buildConfidenceBadge(double confidence) {
    final pct = (confidence * 100).toInt();
    final isHigh = confidence >= 0.85;
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
      decoration: BoxDecoration(
        color: isHigh ? Colors.green.shade50 : Colors.amber.shade50,
        borderRadius: BorderRadius.circular(4),
        border: Border.all(
          color: isHigh ? Colors.green.shade200 : Colors.amber.shade300,
        ),
      ),
      child: Text(
        '$pct% OCR Match',
        style: TextStyle(
          fontSize: 10,
          fontWeight: FontWeight.bold,
          color: isHigh ? Colors.green.shade800 : Colors.amber.shade900,
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppConstants.background,
      appBar: AppBar(
        title: const Text('Review OCR Scan', style: TextStyle(fontWeight: FontWeight.bold)),
        backgroundColor: Colors.white,
        foregroundColor: AppConstants.textPrimary,
        elevation: 0.5,
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            // Duplicate warning banner if detected
            if (_isDuplicateSuspected)
              Container(
                padding: const EdgeInsets.all(12),
                margin: const EdgeInsets.only(bottom: 16),
                decoration: BoxDecoration(
                  color: Colors.amber.shade50,
                  borderRadius: BorderRadius.circular(8),
                  border: Border.all(color: Colors.amber.shade300),
                ),
                child: Row(
                  children: [
                    Icon(Icons.warning_amber_rounded, color: Colors.amber.shade800),
                    const SizedBox(width: 10),
                    Expanded(
                      child: Text(
                        'Possible duplicate: A receipt with this merchant, total, and date already exists in your vault.',
                        style: TextStyle(color: Colors.amber.shade900, fontSize: 12),
                      ),
                    ),
                  ],
                ),
              ),

            // Scan Preview Header
            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: Colors.indigo.shade50,
                borderRadius: BorderRadius.circular(12),
              ),
              child: Row(
                children: [
                  Container(
                    width: 48,
                    height: 48,
                    decoration: BoxDecoration(
                      color: AppConstants.primary,
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: const Icon(Icons.document_scanner, color: Colors.white),
                  ),
                  const SizedBox(width: 14),
                  const Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          'Tesseract OCR Parsed',
                          style: TextStyle(fontWeight: FontWeight.bold, fontSize: 14),
                        ),
                        SizedBox(height: 2),
                        Text(
                          'Review extracted fields before confirming to your vault.',
                          style: TextStyle(fontSize: 12, color: AppConstants.textSecondary),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),

            const SizedBox(height: 20),

            // Merchant Field
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                const Text('Merchant Name', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13)),
                _buildConfidenceBadge(_merchantConfidence),
              ],
            ),
            const SizedBox(height: 6),
            TextField(
              controller: _merchantController,
              decoration: const InputDecoration(
                border: OutlineInputBorder(),
                filled: true,
                fillColor: Colors.white,
              ),
            ),

            const SizedBox(height: 16),

            // Total Amount Field
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                const Text('Total Amount (\$ USD)', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13)),
                _buildConfidenceBadge(_totalConfidence),
              ],
            ),
            const SizedBox(height: 6),
            TextField(
              controller: _totalController,
              keyboardType: const TextInputType.numberWithOptions(decimal: true),
              decoration: const InputDecoration(
                border: OutlineInputBorder(),
                filled: true,
                fillColor: Colors.white,
              ),
            ),

            const SizedBox(height: 16),

            // Purchase Date Field
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                const Text('Purchase Date', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13)),
                _buildConfidenceBadge(_dateConfidence),
              ],
            ),
            const SizedBox(height: 6),
            TextField(
              controller: _dateController,
              decoration: const InputDecoration(
                border: OutlineInputBorder(),
                filled: true,
                fillColor: Colors.white,
              ),
            ),

            const SizedBox(height: 16),

            // Notes / Memo
            const Text('Notes / Memo', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13)),
            const SizedBox(height: 6),
            TextField(
              controller: _notesController,
              maxLines: 2,
              decoration: const InputDecoration(
                border: OutlineInputBorder(),
                filled: true,
                fillColor: Colors.white,
              ),
            ),

            const SizedBox(height: 28),

            // Action Buttons
            ElevatedButton(
              onPressed: () {
                // Confirm and add to offline queue
                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(content: Text('Receipt confirmed & stored in offline vault!')),
                );
                context.pop();
              },
              style: ElevatedButton.styleFrom(
                backgroundColor: AppConstants.primary,
                foregroundColor: Colors.white,
                padding: const EdgeInsets.symmetric(vertical: 16),
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
              ),
              child: const Text('Confirm Receipt', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
            ),

            const SizedBox(height: 10),

            OutlinedButton(
              onPressed: () => context.pop(),
              style: OutlinedButton.styleFrom(
                padding: const EdgeInsets.symmetric(vertical: 14),
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
              ),
              child: const Text('Cancel Scan'),
            ),
          ],
        ),
      ),
    );
  }
}
