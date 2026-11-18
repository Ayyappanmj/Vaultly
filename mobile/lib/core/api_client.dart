import 'package:dio/dio.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'constants.dart';

class ApiClient {
  static final ApiClient _instance = ApiClient._internal();
  factory ApiClient() => _instance;

  late final Dio dio;
  final FlutterSecureStorage _storage = const FlutterSecureStorage();

  ApiClient._internal() {
    dio = Dio(
      BaseOptions(
        baseUrl: AppConstants.apiBaseUrl,
        connectTimeout: const Duration(seconds: 10),
        receiveTimeout: const Duration(seconds: 15),
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        },
      ),
    );

    dio.interceptors.add(
      InterceptorsWrapper(
        onRequest: (options, handler) async {
          final token = await _storage.read(key: 'vaultly_access_token');
          if (token != null) {
            options.headers['Authorization'] = 'Bearer $token';
          }
          return handler.next(options);
        },
        onError: (DioException error, handler) async {
          if (error.response?.statusCode == 401) {
            // Attempt token refresh or force sign-in
            final refreshToken = await _storage.read(key: 'vaultly_refresh_token');
            if (refreshToken != null) {
              try {
                final refreshDio = Dio(BaseOptions(baseUrl: AppConstants.apiBaseUrl));
                final res = await refreshDio.post('/auth/refresh', data: {
                  'refresh_token': refreshToken,
                });
                final newAccess = res.data['access_token'];
                final newRefresh = res.data['refresh_token'];
                await _storage.write(key: 'vaultly_access_token', value: newAccess);
                await _storage.write(key: 'vaultly_refresh_token', value: newRefresh);

                // Retry original request
                final opts = error.requestOptions;
                opts.headers['Authorization'] = 'Bearer $newAccess';
                final cloneReq = await dio.fetch(opts);
                return handler.resolve(cloneReq);
              } catch (_) {
                await _storage.deleteAll();
              }
            }
          }
          return handler.next(error);
        },
      ),
    );
  }
}
