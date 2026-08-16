import 'package:dio/dio.dart';
import 'package:hermes_linguamind/core/constants/api_endpoints.dart';
import 'package:hermes_linguamind/core/utils/logger.dart';
import 'package:hermes_linguamind/data/adapters/api_client.dart';
import 'package:hermes_linguamind/data/models/chat_models.dart';

class ChatAdapter {
  factory ChatAdapter() => _instance;
  ChatAdapter._();
  static final ChatAdapter _instance = ChatAdapter._();

  final ApiClient _client = ApiClient();

  Future<ChatResponse> sendMessage(final ChatRequest request) async {
    try {
      final response = await _client.post<dynamic>(
        ApiEndpoints.chat,
        data: request.toJson(),
      );
      return ChatResponse.fromJson(response.data as Map<String, dynamic>);
    } on DioException catch (e) {
      AppLogger.error('Chat message failed', e);
      throw _handleError(e);
    }
  }

  Exception _handleError(final DioException e) {
    final response = e.response;
    if (response != null) {
      final data = response.data as Map<String, dynamic>?;
      final message =
          data?['detail'] as String? ??
          data?['message'] as String? ??
          'Chat request failed';
      return Exception(message);
    }
    return Exception('Network error. Please check your connection.');
  }
}
