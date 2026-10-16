import base64
import json
import os
import unittest
from unittest.mock import patch, Mock
from fastapi.testclient import TestClient
from api.webhook import app
from bot import handlers, supabase_client, docker_manager
from bot.config import OperationError


class BotTests(unittest.TestCase):
    def message(self, text, **changes):
        update = {"update_id": 123, "message": {"message_id": 1, "text": text,
                  "from": {"id": 42}, "chat": {"id": 42, "type": "private"}}}
        update["message"].update(changes)
        return update

    @patch('bot.handlers.telegram.send')
    @patch('bot.handlers.allowed', side_effect=AssertionError('must stay public'))
    def test_id_public(self, allowed, send):
        handlers.handle(self.message('/id'))
        send.assert_called_once_with(42, '你的 Telegram User ID：42')

    @patch('bot.handlers.telegram.send')
    @patch('bot.handlers.dispatch')
    @patch('bot.handlers.allowed', return_value=False)
    def test_denied_does_not_dispatch(self, allowed, dispatch, send):
        handlers.handle(self.message('/docker start'))
        dispatch.assert_not_called()
        self.assertIn('权限不足', send.call_args.args[1])

    def test_secret_parser_rejects_missing_duplicate_unknown(self):
        for text in ('API_KEY=x', 'API_KEY=x API_KEY=y API_SECRET=z',
                     'API_KEY=x API_SECRET=', 'API_KEY=x API_SECRET=y EXTRA=z', '"'):
            with self.subTest(text=text), self.assertRaises(OperationError):
                handlers.parse_secret(text)
        self.assertEqual(handlers.parse_secret('API_SECRET="y z" API_KEY=x'),
                         {'API_KEY': 'x', 'API_SECRET': 'y z'})

    @patch('bot.handlers.telegram.send')
    @patch('bot.handlers.claim', return_value=False)
    @patch('bot.handlers.allowed', return_value=True)
    @patch('bot.handlers.dispatch')
    def test_duplicate_does_not_dispatch(self, dispatch, allowed, claim, send):
        handlers.handle(self.message('/docker start'))
        dispatch.assert_not_called()

    @patch('bot.handlers.telegram.send')
    @patch('bot.handlers.claim')
    @patch('bot.handlers.allowed', return_value=True)
    @patch('bot.handlers.dispatch')
    def test_shell_injection_rejected(self, dispatch, allowed, claim, send):
        handlers.handle(self.message('/docker start; whoami'))
        claim.assert_not_called()
        dispatch.assert_not_called()

    @patch('bot.handlers.telegram.send')
    @patch('bot.handlers.telegram.delete', return_value=True)
    @patch('bot.handlers.allowed', return_value=True)
    @patch('bot.handlers.claim', return_value=True)
    @patch('bot.handlers.update_secret')
    def test_update_deletes_and_does_not_echo(self, update, claim, allowed, delete, send):
        handlers.handle(self.message('/update_secret API_KEY=private-key API_SECRET=private-secret'))
        delete.assert_called_once_with(42, 1)
        update.assert_called_once_with({'API_KEY': 'private-key', 'API_SECRET': 'private-secret'})
        self.assertNotIn('private-key', send.call_args.args[1])
        self.assertNotIn('private-secret', send.call_args.args[1])

    @patch.dict(os.environ, {'SUPABASE_SECRET_ID': '1'})
    @patch('bot.supabase_client.database')
    def test_patch_is_scoped(self, database):
        database.return_value = Mock(status_code=200, json=lambda: [{'id': 1}])
        supabase_client.update_secret({'API_KEY': 'x', 'API_SECRET': 'y'})
        self.assertEqual(database.call_args.kwargs['params'], {'id': 'eq.1', 'select': 'id'})
        database.return_value = Mock(status_code=200, json=lambda: [])
        with self.assertRaises(OperationError):
            supabase_client.update_secret({'API_KEY': 'x', 'API_SECRET': 'y'})

    @patch('bot.supabase_client.database', return_value=Mock(status_code=409))
    def test_unique_claim(self, database):
        self.assertFalse(supabase_client.claim(123))

    @patch.dict(os.environ, {'SUPABASE_KEY': 'sb_publishable_test', 'SUPABASE_URL': 'https://example.supabase.co/'})
    @patch('bot.supabase_client.request')
    def test_public_key_writes_and_duplicate_claim(self, request):
        request.return_value = Mock(status_code=201)
        self.assertTrue(supabase_client.claim(123))
        self.assertEqual(request.call_args.args, ('POST', 'https://example.supabase.co/rest/v1/bot_updates'))
        self.assertEqual(request.call_args.kwargs['headers'],
                         {'apikey': 'sb_publishable_test', 'Prefer': 'return=minimal'})
        self.assertEqual(request.call_args.kwargs['json'], {'update_id': 123})
        request.return_value = Mock(status_code=409)
        self.assertFalse(supabase_client.claim(123))
        request.return_value = Mock(status_code=403)
        with self.assertRaises(OperationError):
            supabase_client.claim(124)

    @patch.dict(os.environ, {'SUPABASE_KEY': 'sb_publishable_test', 'SUPABASE_URL': 'https://example.supabase.co',
                            'SUPABASE_SECRET_ID': '7'})
    @patch('bot.supabase_client.request')
    def test_public_patch_returns_only_id(self, request):
        request.return_value = Mock(status_code=200, json=lambda: [{'id': 7}])
        supabase_client.update_secret({'API_KEY': 'x', 'API_SECRET': 'y'})
        self.assertEqual(request.call_args.kwargs['headers'],
                         {'apikey': 'sb_publishable_test', 'Prefer': 'return=representation'})
        self.assertEqual(request.call_args.kwargs['params'], {'id': 'eq.7', 'select': 'id'})
        request.return_value = Mock(status_code=403)
        with self.assertRaises(OperationError):
            supabase_client.update_secret({'API_KEY': 'x', 'API_SECRET': 'y'})

    @patch.dict(os.environ, {'SUPABASE_URL': 'https://example.supabase.co'})
    @patch('bot.supabase_client.request')
    def test_legacy_anon_and_reject_private_keys(self, request):
        def jwt(role):
            payload = base64.urlsafe_b64encode(json.dumps({'role': role}).encode()).decode().rstrip('=')
            return 'header.' + payload + '.signature'

        with patch.dict(os.environ, {'SUPABASE_KEY': jwt('anon')}):
            supabase_client.database('POST', 'bot_updates', representation=False, json={'update_id': 1})
            self.assertEqual(request.call_args.kwargs['headers']['apikey'], jwt('anon'))
            self.assertNotIn('Authorization', request.call_args.kwargs['headers'])
        request.reset_mock()
        for key in ('sb_secret_test', jwt('service_role'), 'not-a-key', 'x.invalid!.y', 'x.bnVsbA.y', ''):
            with self.subTest(key=key), patch.dict(os.environ, {'SUPABASE_KEY': key}), self.assertRaises(OperationError):
                supabase_client.database('POST', 'bot_updates', json={'update_id': 1})
        request.assert_not_called()

    @patch.dict(os.environ, {'TELEGRAM_WEBHOOK_SECRET': 'test-secret'})
    @patch('api.webhook.handle')
    def test_webhook_source_and_payload(self, handle):
        client = TestClient(app)
        self.assertEqual(client.post('/api/webhook', json={}).status_code, 403)
        handle.assert_not_called()
        headers = {'X-Telegram-Bot-Api-Secret-Token': 'test-secret'}
        self.assertEqual(client.post('/api/webhook', json=[], headers=headers).status_code, 400)
        self.assertEqual(client.post('/api/webhook', content=b'x' * 65537, headers=headers).status_code, 413)
        self.assertEqual(client.post('/api/webhook', json={'update_id': 1}, headers=headers).status_code, 200)
        handle.assert_called_once_with({'update_id': 1})

    @patch.dict(os.environ, {'GITHUB_OWNER': 'owner', 'GITHUB_REPO': 'repo', 'GITHUB_TOKEN': 'token', 'GITHUB_REF': 'main'})
    @patch('bot.docker_manager.request', return_value=Mock(status_code=204))
    def test_dispatch_only_means_accepted(self, request):
        docker_manager.dispatch('start', 42, 123)
        self.assertEqual(request.call_args.kwargs['json']['inputs'],
                         {'action': 'start', 'chat_id': '42', 'request_id': '123'})
        with self.assertRaises(OperationError):
            docker_manager.dispatch('restart', 42, 123)

    @patch('bot.handlers.telegram.send')
    @patch('bot.handlers.allowed', return_value=True)
    @patch('bot.handlers.dispatch')
    def test_group_admin_command_rejected(self, dispatch, allowed, send):
        handlers.handle(self.message('/docker stop', chat={'id': -42, 'type': 'group'}))
        dispatch.assert_not_called()
        self.assertIn('私聊', send.call_args.args[1])


if __name__ == '__main__':
    unittest.main()
