import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import publish_library as publisher


class PublishTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.repo, self.remote = self.base / 'repo', self.base / 'remote.git'
        self.run_git('init', '--bare', str(self.remote), cwd=self.base)
        self.run_git('init', '-b', 'main', str(self.repo), cwd=self.base)
        self.run_git('config', 'user.name', 'Test')
        self.run_git('config', 'user.email', 'test@example.test')
        (self.repo / 'html').mkdir()
        (self.repo / 'note.txt').write_text('first')
        self.run_git('add', '.')
        self.run_git('commit', '-m', 'initial')
        self.run_git('remote', 'add', 'origin', str(self.remote))
        self.run_git('push', '-u', 'origin', 'main')

    def run_git(self, *args, cwd=None):
        return subprocess.run(['git', *args], cwd=cwd or self.repo, check=True,
                              capture_output=True).stdout

    def publish(self, **kwargs):
        return publisher.publish(self.repo, log=lambda _: None, **kwargs)

    def test_html_only_mixed_case_deletion_and_unrelated_staging(self):
        (self.repo / 'note.txt').write_text('staged change')
        self.run_git('add', 'note.txt')
        book = self.repo / 'html/새 책.Html'
        book.write_text('<h1>New book</h1>', encoding='utf-8')
        (self.repo / 'html/private.txt').write_text('excluded')
        self.assertEqual(self.publish(), 1)
        self.assertEqual(self.run_git('diff', '--cached', '--name-only').strip(), b'note.txt')
        self.assertEqual(self.run_git('rev-parse', 'HEAD'), self.run_git('rev-parse', 'origin/main'))
        head = self.run_git('rev-parse', 'HEAD')
        self.publish()
        self.assertEqual(head, self.run_git('rev-parse', 'HEAD'))
        book.unlink()
        self.assertEqual(self.publish(), 0)
        tracked = self.run_git('ls-tree', '-r', '--name-only', 'HEAD').decode('utf-8')
        self.assertNotIn('private.txt', tracked)
        self.assertNotIn('.Html', tracked)

    def test_failed_push_can_retry_without_duplicate_commit(self):
        (self.repo / 'html/book.html').write_text('<h1>Book</h1>')
        real = publisher.git
        def fail_push(root, *args):
            if args[0] == 'push':
                raise RuntimeError('simulated network failure')
            return real(root, *args)
        with patch.object(publisher, 'git', side_effect=fail_push):
            with self.assertRaisesRegex(RuntimeError, 'network failure'):
                self.publish()
        head = self.run_git('rev-parse', 'HEAD')
        self.publish()
        self.assertEqual(head, self.run_git('rev-parse', 'HEAD'))
        self.assertEqual(head, self.run_git('rev-parse', 'origin/main'))

    def test_unrelated_ahead_commit_is_not_pushed(self):
        (self.repo / 'note.txt').write_text('local commit')
        self.run_git('commit', '-am', 'unrelated')
        remote_head = self.run_git('rev-parse', 'origin/main')
        with self.assertRaisesRegex(RuntimeError, '범위 밖'):
            self.publish()
        self.assertEqual(remote_head, self.run_git('rev-parse', 'origin/main'))
        self.assertFalse((self.repo / 'index.html').exists())

    def test_remote_ahead_and_wrong_branch(self):
        other = self.base / 'other'
        self.run_git('clone', '-b', 'main', str(self.remote), str(other), cwd=self.base)
        for key, value in [('user.name', 'Test'), ('user.email', 'test@example.test')]:
            self.run_git('config', key, value, cwd=other)
        (other / 'note.txt').write_text('remote changed')
        self.run_git('commit', '-am', 'remote', cwd=other)
        self.run_git('push', 'origin', 'main', cwd=other)
        with self.assertRaisesRegex(RuntimeError, '동기화'):
            self.publish()
        self.assertFalse((self.repo / 'index.html').exists())
        self.run_git('checkout', '-b', 'work')
        with self.assertRaisesRegex(RuntimeError, 'main'):
            self.publish()

    def test_ver2_only_selected_raw_text(self):
        folder = self.repo / '원본 유튜브 요약 텍스트'
        folder.mkdir()
        selected = folder / 'selected.txt'
        selected.write_text('source')
        (folder / 'other.txt').write_text('not selected')
        self.publish(extra_paths=[selected.relative_to(self.repo).as_posix()])
        tracked = self.run_git('-c', 'core.quotepath=false', 'ls-tree', '-r', '--name-only', 'HEAD').decode('utf-8')
        self.assertIn('selected.txt', tracked)
        self.assertNotIn('other.txt', tracked)

    def test_lock_prevents_concurrent_publish(self):
        with publisher.publish_lock(self.repo):
            with self.assertRaisesRegex(RuntimeError, '게시 중'):
                self.publish()


if __name__ == '__main__':
    unittest.main()
