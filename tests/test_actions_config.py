"""Run in remote CI only; no real Tailscale, SSH, Docker or Telegram calls."""
import contextlib
import io
import os
from pathlib import Path
import subprocess
import unittest
from unittest.mock import Mock, patch

from scripts import notify


class ActionsConfigTests(unittest.TestCase):
    def test_missing_configuration_lists_names_without_values(self):
        names = ('TS_OAUTH_CLIENT_ID', 'TS_OAUTH_SECRET', 'SSH_PRIVATE_KEY',
                 'SSH_KNOWN_HOSTS', 'TELEGRAM_BOT_TOKEN', 'DEPLOY_HOST',
                 'DEPLOY_USER', 'DOCKER_CONTAINER')
        script = Path(__file__).resolve().parent.parent / 'scripts/check-actions-config.sh'
        configured = dict(os.environ, **{name: 'private-test-value' for name in names})
        for missing in (None, *names):
            with self.subTest(missing=missing):
                env = dict(configured)
                if missing:
                    env[missing] = ''
                result = subprocess.run(['bash', str(script)], env=env,
                                        capture_output=True, text=True, timeout=5)
                self.assertEqual(result.returncode, 2 if missing else 0)
                if missing:
                    self.assertIn('Missing Actions configuration: ' + missing + '.', result.stdout)
                self.assertNotIn('private-test-value', result.stdout + result.stderr)


@patch.dict(os.environ, {'ACTION': 'stop', 'CHAT_ID': '42', 'REQUEST_ID': '123',
                        'RESULT': 'failure', 'TELEGRAM_BOT_TOKEN': 'private-test-token',
                        'GITHUB_REPOSITORY': 'owner/repo', 'GITHUB_RUN_ID': '456'}, clear=True)
class NotifyTests(unittest.TestCase):
    @patch('scripts.notify.httpx.post')
    def test_missing_token_fails_before_network(self, post):
        with patch.dict(os.environ, {'TELEGRAM_BOT_TOKEN': ''}):
            with self.assertRaisesRegex(SystemExit, 'Missing Actions secret: TELEGRAM_BOT_TOKEN'):
                notify.main()
        post.assert_not_called()

    @patch('scripts.notify.httpx.post', return_value=Mock(status_code=200, json=lambda: {'ok': True}))
    def test_missing_host_still_reports_control_failure(self, post):
        notify.main()
        text = post.call_args.kwargs['json']['text']
        self.assertIn('failure', text)
        self.assertIn('未配置 DEPLOY_HOST', text)
        self.assertIn('123', text)

    @patch('scripts.notify.time.sleep')
    @patch('scripts.notify.httpx.post')
    def test_invalid_token_fails_clearly_without_leaking_response(self, post, sleep):
        post.return_value = Mock(status_code=401, json=lambda: {'description': 'private-test-token'})
        output = io.StringIO()
        with contextlib.redirect_stderr(output):
            with self.assertRaisesRegex(SystemExit, 'Check Actions TELEGRAM_BOT_TOKEN'):
                notify.main()
        post.assert_called_once()
        sleep.assert_not_called()
        self.assertIn('HTTP 401', output.getvalue())
        self.assertNotIn('private-test-token', output.getvalue())

    @patch('scripts.notify.time.sleep')
    @patch('scripts.notify.httpx.post')
    def test_temporary_failure_retries_and_then_succeeds(self, post, sleep):
        post.side_effect = [Mock(status_code=503), Mock(status_code=200, json=lambda: {'ok': True})]
        with contextlib.redirect_stderr(io.StringIO()):
            notify.main()
        self.assertEqual(post.call_count, 2)
