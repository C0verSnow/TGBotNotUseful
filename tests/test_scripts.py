"""Remote CI executes actual shell entrypoints with a fake Docker binary."""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parent.parent


class ScriptTests(unittest.TestCase):
    def run_script(self, action, container='configured-container', fail=False):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            docker = path / 'docker'
            docker.write_text('''#!/usr/bin/env bash
printf '%s\\n' "$*" >> "$CALL_LOG"
[[ "${FAIL:-}" != yes ]] || exit 1
if [[ "$*" == *--format* ]]; then
  if [[ "$ACTION" == start ]]; then echo true; else echo false; fi
fi
''')
            docker.chmod(0o700)
            env = dict(os.environ, PATH=directory + ':' + os.environ['PATH'],
                       CALL_LOG=str(path / 'calls'), ACTION=action, FAIL='yes' if fail else 'no')
            result = subprocess.run(['bash', str(ROOT / 'scripts' / f'{action}-docker.sh'), container],
                                    env=env, capture_output=True, timeout=5)
            calls = (path / 'calls').read_text() if (path / 'calls').exists() else ''
            return result, calls

    def test_start_and_stop_use_configured_container(self):
        for action in ('start', 'stop'):
            with self.subTest(action=action):
                result, calls = self.run_script(action)
                self.assertEqual(result.returncode, 0)
                self.assertIn(f'container {action}', calls)
                self.assertEqual(calls.count('configured-container'), 3)
                self.assertIn('--format', calls)

    def test_docker_failure_is_failure(self):
        result, calls = self.run_script('start', fail=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn('container start', calls)

    def test_injected_container_never_reaches_docker(self):
        result, calls = self.run_script('stop', container='name; whoami')
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(calls, '')
