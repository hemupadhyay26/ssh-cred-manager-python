import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
from cli.session_status import session_command
from core.runtime import external_environment


class FrozenRuntimeTests(unittest.TestCase):
    def test_source_worker_runs_with_python_script(self):
        with patch.object(sys, 'frozen', False, create=True):
            command = session_command(Path('/tmp/session.json'), Path('/tmp/result'))
            self.assertEqual(command[0], sys.executable)
            self.assertTrue(command[1].endswith('session_runner.py'))

    def test_frozen_worker_reuses_binary_without_python_script(self):
        with patch.object(sys, 'frozen', True, create=True):
            self.assertEqual(session_command(Path('/tmp/session.json'), Path('/tmp/result')),
                [sys.executable, '--_ssc-session-worker', '/tmp/session.json', '/tmp/result'])

    def test_frozen_external_tools_use_original_library_path(self):
        with patch.object(sys, 'frozen', True, create=True), patch.dict(os.environ, {'LD_LIBRARY_PATH': '/bundle', 'LD_LIBRARY_PATH_ORIG': '/system'}, clear=True):
            self.assertEqual(external_environment()['LD_LIBRARY_PATH'], '/system')
            self.assertEqual(os.environ['LD_LIBRARY_PATH'], '/bundle')
        with patch.object(sys, 'frozen', True, create=True), patch.dict(os.environ, {'LD_LIBRARY_PATH': '/bundle'}, clear=True):
            self.assertNotIn('LD_LIBRARY_PATH', external_environment())
