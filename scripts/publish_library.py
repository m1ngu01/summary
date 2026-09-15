"""Explicit, single-run publishing shared by ver1 and ver2."""
from contextlib import contextmanager
import os
from pathlib import Path
import subprocess
import time
from build_library import ROOT, build

HTML_PATHS = ['index.html', ':(glob,icase)html/**/*.html', ':(glob,icase)html/**/*.htm']


def git(root, *args):
    result = subprocess.run(
        ['git', *args], cwd=root,
        env=dict(os.environ, GIT_TERMINAL_PROMPT='0', GCM_INTERACTIVE='never'),
        capture_output=True, encoding='utf-8', errors='replace', timeout=120,
        creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
    if result.returncode:
        raise RuntimeError(f'git {args[0]}: {result.stderr.strip()}')
    return result.stdout


@contextmanager
def publish_lock(root):
    state = root / '.summary'
    state.mkdir(exist_ok=True)
    with (state / 'publish.lock').open('a+b') as handle:
        handle.seek(0, 2)
        if handle.tell() == 0:
            handle.write(b'0')
            handle.flush()
        handle.seek(0)
        try:
            if os.name == 'nt':
                import msvcrt
                msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as exc:
            raise RuntimeError('다른 창에서 게시 중입니다. 완료 후 다시 실행하세요.') from exc
        try:
            yield
        finally:
            handle.seek(0)
            if os.name == 'nt':
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def is_html(path):
    return path == 'index.html' or (path.startswith('html/') and Path(path).suffix.lower() in ('.html', '.htm'))


def publish(root=ROOT, extra_paths=(), log=print, prepare=None):
    root = Path(root).resolve()
    extras = set()
    for name in extra_paths:
        path = (root / name).resolve()
        relative = path.relative_to(root).as_posix()
        if not relative.startswith('원본 유튜브 요약 텍스트/') or path.suffix != '.txt':
            raise ValueError('추가 게시 대상은 원본 텍스트 폴더의 TXT만 허용합니다.')
        extras.add(relative)
    paths = HTML_PATHS + [':(literal)' + name for name in sorted(extras)]
    with publish_lock(root):
        if git(root, 'branch', '--show-current').strip() != 'main':
            raise RuntimeError('main 브랜치에서 실행하세요.')
        gitdir = Path(git(root, 'rev-parse', '--absolute-git-dir').strip())
        if any((gitdir / name).exists() for name in (
                'MERGE_HEAD', 'CHERRY_PICK_HEAD', 'REVERT_HEAD',
                'rebase-merge', 'rebase-apply', 'index.lock')):
            raise RuntimeError('진행 중인 Git 작업을 먼저 완료하세요.')
        log('원격 main 확인 중…')
        git(root, 'fetch', 'origin', 'main')
        behind, ahead = map(int, git(root, 'rev-list', '--left-right', '--count', 'origin/main...HEAD').split())
        if behind:
            raise RuntimeError('원격 main에 새 커밋이 있습니다. 먼저 수동으로 동기화하세요.')
        # Push sends commits, not a path subset. Never silently send other work.
        if ahead:
            for commit in git(root, 'rev-list', 'origin/main..HEAD').split():
                names = git(root, 'diff-tree', '--root', '-m', '--no-commit-id', '--name-only', '-r', '-z', commit)
                if any(not is_html(p) and p not in extras for p in names.split('\0') if p):
                    raise RuntimeError('미푸시 커밋에 게시 범위 밖의 파일이 있습니다. 해당 커밋은 직접 푸시한 뒤 실행하세요.')
        if prepare:
            prepare()
        log('서재 목록 갱신 중…')
        count = build(root)
        changed = set(filter(None, git(root, 'diff', 'HEAD', '--name-only', '-z', '--', *paths).split('\0')))
        changed.update(filter(None, git(root, 'ls-files', '--others', '--exclude-standard', '-z', '--', *paths).split('\0')))
        if changed:
            literal = [':(literal)' + p for p in sorted(changed)]
            git(root, 'add', '--', *literal)
            git(root, 'commit', '--only', '-m', 'Update reading library ' + time.strftime('%Y-%m-%d %H:%M:%S'), '--', *literal)
            log(f'{len(changed)}개 파일 커밋 완료')
        if changed or ahead:
            git(root, 'push', 'origin', 'HEAD:main')
            log('GitHub 푸시 완료. Pages 배포 결과는 GitHub Actions에서 확인하세요.')
        else:
            log('게시할 변경 사항이 없습니다.')
        return count


if __name__ == '__main__':
    publish()
