import 'package:drift/drift.dart';

// Table for offline Receipts
class LocalReceipts extends Table {
  TextColumn get id => text()();
  TextColumn get merchantName => text().withLength(min: 1, max: 255)();
  DateTimeColumn get purchaseDate => dateTime()();
  RealColumn get totalAmount => real()();
  TextColumn get currency => text().withLength(min: 3, max: 3).withDefault(const Constant('USD'))();
  TextColumn get notes => text().nullable()();
  TextColumn get status => text().withDefault(const Constant('CONFIRMED'))();
  IntColumn get serverVersion => integer().withDefault(const Constant(1))();
  BoolColumn get isDeleted => boolean().withDefault(const Constant(false))();
  DateTimeColumn get createdAt => dateTime()();
  DateTimeColumn get updatedAt => dateTime()();

  @override
  Set<Column> get primaryKey => {id};
}

// Table for offline Warranties
class LocalWarranties extends Table {
  TextColumn get id => text()();
  TextColumn get title => text()();
  IntColumn get durationMonths => integer()();
  DateTimeColumn get startDate => dateTime()();
  DateTimeColumn get expiryDate => dateTime()();
  TextColumn get status => text()(); // ACTIVE, EXPIRING_SOON, EXPIRED, UNKNOWN
  TextColumn get notes => text().nullable()();
  IntColumn get serverVersion => integer().withDefault(const Constant(1))();

  @override
  Set<Column> get primaryKey => {id};
}

// Table for offline Subscriptions
class LocalSubscriptions extends Table {
  TextColumn get id => text()();
  TextColumn get name => text()();
  RealColumn get amount => real()();
  TextColumn get currency => text().withDefault(const Constant('USD'))();
  TextColumn get billingFrequency => text()(); // weekly, monthly, quarterly, yearly
  TextColumn get status => text()(); // active, paused, cancelled, trial
  DateTimeColumn get nextBillingDate => dateTime()();
  RealColumn get monthlyEquivalent => real().nullable()();
  IntColumn get serverVersion => integer().withDefault(const Constant(1))();

  @override
  Set<Column> get primaryKey => {id};
}

// Table for Offline Sync Queue
class SyncQueueTable extends Table {
  TextColumn get id => text()();
  TextColumn get entityType => text()(); // RECEIPT, WARRANTY, SUBSCRIPTION
  TextColumn get entityId => text()();
  TextColumn get operation => text()(); // CREATE, UPDATE, DELETE
  TextColumn get payload => text()(); // JSON string
  TextColumn get idempotencyKey => text()();
  TextColumn get status => text().withDefault(const Constant('PENDING'))(); // PENDING, SYNCING, SYNCED, FAILED, CONFLICT
  IntColumn get retryCount => integer().withDefault(const Constant(0))();
  TextColumn get lastError => text().nullable()();
  DateTimeColumn get createdAt => dateTime()();

  @override
  Set<Column> get primaryKey => {id};
}
