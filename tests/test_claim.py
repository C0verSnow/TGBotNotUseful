"""Issue #5: exercise real claim through handlers; no live Docker dispatch."""
import os
import unittest
from unittest.mock import Mock, patch

from bot import handlers, supabase_client
from bot.config import OperationError


def response(status, code=None):
    return Mock(status_code=status, json=lambda: {'code': code})


@patch.dict(os.environ, {'SUPABASE_KEY': 'sb_publishable_test',
                        'SUPABASE_URL': 'https://example.supabase.co'})
class ClaimTests(unittest.TestCase):
    def message(self, text):
        return {'update_id': 123, 'message': {'message_id': 1, 'text': text,
                'from': {'id': 42}, 'chat': {'id': 42, 'type': 'private'}}}

    @patch('bot.handlers.allowed', return_value=True)
    @patch('bot.handlers.telegram.send')
    @patch('bot.handlers.dispatch')
    @patch('bot.supabase_client.request')
    def test_missing_table_blocks_stop_with_repair_instructions(self, request, dispatch, send, allowed):
        request.return_value = response(404, 'PGRST205')
        with self.assertLogs('bot.supabase_client', level='ERROR') as logs:
            handlers.handle(self.message('/docker stop'))
        dispatch.assert_not_called()
        self.assertIn('migrations/005_bot_updates.sql', send.call_args.args[1])
        self.assertIn('status=404 code=PGRST205', logs.output[0])

    @patch('bot.handlers.allowed', return_value=True)
    @patch('bot.handlers.telegram.send')
    @patch('bot.handlers.dispatch')
    @patch('bot.supabase_client.request')
    def test_start_stop_dispatch_once_on_repeated_delivery(self, request, dispatch, send, allowed):
        for action in ('start', 'stop'):
            with self.subTest(action=action):
                dispatch.reset_mock()
                send.reset_mock()
                request.side_effect = [response(201), response(409, '23505')]
                update = self.message('/docker ' + action)
                handlers.handle(update)
                handlers.handle(update)
                dispatch.assert_called_once_with(action, 42, 123)
                send.assert_called_once()
                self.assertIn('任务已提交', send.call_args.args[1])

    @patch('bot.handlers.allowed', return_value=True)
    @patch('bot.handlers.telegram.send')
    @patch('bot.handlers.telegram.delete', return_value=True)
    @patch('bot.handlers.update_secret')
    @patch('bot.supabase_client.request')
    def test_secret_update_still_deduplicates(self, request, update_secret, delete, send, allowed):
        request.side_effect = [response(201), response(409, '23505')]
        update = self.message('/update_secret API_KEY=x API_SECRET=y')
        handlers.handle(update)
        handlers.handle(update)
        update_secret.assert_called_once_with({'API_KEY': 'x', 'API_SECRET': 'y'})
        send.assert_called_once()

    @patch('bot.supabase_client.request')
    def test_errors_fail_closed_and_do_not_leak_response(self, request):
        cases = [(404, '42P01', '未初始化'), (403, '42501', '权限不足'),
                 (401, 'PGRST301', '查看服务日志'), (409, '23503', '查看服务日志'),
                 (409, None, '查看服务日志'), (503, None, '查看服务日志')]
        for status, code, message in cases:
            with self.subTest(status=status, code=code):
                request.return_value = Mock(status_code=status, json=lambda: {
                    'code': code, 'message': 'private-key', 'details': 'private-secret'})
                with self.assertLogs('bot.supabase_client', level='ERROR') as logs:
                    with self.assertRaisesRegex(OperationError, message):
                        supabase_client.claim(123)
                self.assertNotIn('private-key', str(logs.output))
                self.assertNotIn('private-secret', str(logs.output))
                self.assertNotIn('sb_publishable_test', str(logs.output))

    @patch('bot.supabase_client.request')
    def test_invalid_json_and_untrusted_error_codes_fail_closed(self, request):
        for error_response in (Mock(status_code=502, json=Mock(side_effect=ValueError)),
                               Mock(status_code=409, json=lambda: []),
                               response(409, 'private-secret\nforged-log'),
                               response(409, {'private-key': 'x'})):
            request.return_value = error_response
            with self.assertLogs('bot.supabase_client', level='ERROR') as logs:
                with self.assertRaises(OperationError):
                    supabase_client.claim(123)
            self.assertIn('code=unknown', logs.output[0])
            self.assertNotIn('private', str(logs.output))

    @patch('bot.supabase_client.request', side_effect=OperationError('timeout'))
    def test_transport_failure_stays_closed(self, request):
        with self.assertLogs('bot.supabase_client', level='ERROR') as logs:
            with self.assertRaisesRegex(OperationError, 'timeout'):
                supabase_client.claim(123)
        self.assertIn('transport_or_configuration_error', logs.output[0])
