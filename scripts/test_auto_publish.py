import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import auto_publish as watcher


class PublishTest(unittest.TestCase):
    def test_publish_retry_and_unrelated_staging(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            repo, remote = base / 'repo', base / 'remote.git'
            def run(*args, cwd=base):
                return subprocess.run(['git', *args], cwd=cwd, check=True,
                                      capture_output=True).stdout
            run('init', '--bare', str(remote))
            run('init', '-b', 'main', str(repo))
            run('config', 'user.name', 'Test', cwd=repo)
            run('config', 'user.email', 'test@example.test', cwd=repo)
            (repo / 'html').mkdir()
            (repo / 'note.txt').write_text('first')
            run('add', '.', cwd=repo)
            run('commit', '-m', 'initial', cwd=repo)
            run('remote', 'add', 'origin', str(remote), cwd=repo)
            run('push', '-u', 'origin', 'main', cwd=repo)
            (repo / 'note.txt').write_text('unrelated staged edit')
            run('add', 'note.txt', cwd=repo)
            (repo / 'html/새 책.html').write_text('<h1>New book</h1>', encoding='utf-8')
            def build():
                (repo / 'index.html').write_text('library')
                (repo / 'html/index.html').write_text('library')
            with patch.object(watcher, 'ROOT', repo), patch.object(watcher, 'build', build):
                watcher.publish()
                self.assertEqual(run('diff', '--cached', '--name-only', cwd=repo).strip(), b'note.txt')
                self.assertEqual(run('rev-parse', 'HEAD', cwd=repo),
                                 run('rev-parse', 'origin/main', cwd=repo))
                head = run('rev-parse', 'HEAD', cwd=repo)
                watcher.publish()
                self.assertEqual(head, run('rev-parse', 'HEAD', cwd=repo))


if __name__ == '__main__':
    unittest.main()
