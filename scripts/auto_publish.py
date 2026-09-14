"""Watch reading HTML on Windows and publish after 15 seconds without changes."""
import argparse
import logging
from logging.handlers import RotatingFileHandler
import os
from pathlib import Path
import subprocess
import time

from build_library import ROOT, build

STATE = ROOT / '.auto-publish'
PATHS = ['index.html', ':(glob)html/**/*.html', ':(glob)html/**/*.htm',
         ':(glob)html/**/*.HTML', ':(glob)html/**/*.HTM']


def git(*args):
    env = dict(os.environ, GIT_TERMINAL_PROMPT='0', GCM_INTERACTIVE='never')
    result = subprocess.run(['git', *args], cwd=ROOT, env=env,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            encoding='utf-8', errors='replace', timeout=90,
                            creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
    if result.returncode:
        raise RuntimeError(f'git {args[0]}: {result.stderr.strip()}')
    return result.stdout.strip()


def snapshot():
    return {p.relative_to(ROOT).as_posix(): (p.stat().st_mtime_ns, p.stat().st_size)
            for p in (ROOT / 'html').rglob('*')
            if p.is_file() and p.suffix.lower() in ('.html', '.htm')}


def publish():
    if git('branch', '--show-current') != 'main':
        raise RuntimeError('Switch to main to resume automatic publishing.')
    gitdir = Path(git('rev-parse', '--absolute-git-dir'))
    if any((gitdir / name).exists() for name in
           ('MERGE_HEAD', 'CHERRY_PICK_HEAD', 'REVERT_HEAD', 'rebase-merge', 'rebase-apply', 'index.lock')):
        raise RuntimeError('Git operation in progress; publishing postponed.')
    # Only publish reading files, leaving unrelated staged changes untouched.
    if git('status', '--porcelain', '--', *PATHS):
        build()
        changed = set(filter(None, git('diff', 'HEAD', '--name-only', '-z', '--', *PATHS).split('\0')))
        changed.update(filter(None, git('ls-files', '--others', '--exclude-standard', '-z', '--', *PATHS).split('\0')))
        if changed:
            literal_paths = [':(literal)' + path for path in sorted(changed)]
            git('add', '--', *literal_paths)
            message = 'Update reading library ' + time.strftime('%Y-%m-%d %H:%M:%S')
            git('commit', '--only', '-m', message, '--', *literal_paths)
            logging.info('Committed reading HTML and generated library.')
    # Fetch before deciding whether a previous failed push needs retrying.
    git('fetch', 'origin', 'main')
    behind, ahead = map(int, git('rev-list', '--left-right', '--count',
                                'origin/main...HEAD').split())
    if behind:
        raise RuntimeError('Remote main has newer commits. Reconcile branches manually; no force push attempted.')
    if ahead:
        git('push', 'origin', 'HEAD:main')
        logging.info('Pushed main. GitHub Pages workflow will deploy it.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--once', action='store_true')
    args = parser.parse_args()
    STATE.mkdir(exist_ok=True)
    handler = RotatingFileHandler(STATE / 'publish.log', maxBytes=500_000,
                                 backupCount=2, encoding='utf-8')
    logging.basicConfig(handlers=[handler], level=logging.INFO,
                        format='%(asctime)s %(levelname)s %(message)s')
    import msvcrt
    with (STATE / 'watcher.lock').open('a+b') as lock:
        lock.seek(0)
        if not lock.read(1):
            lock.write(b'0')
            lock.flush()
        lock.seek(0)
        try:
            msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1)
        except OSError:
            return
        (STATE / 'watcher.pid').write_text(str(os.getpid()), encoding='ascii')
        if args.once:
            publish()
            return
        logging.info('Watcher started. Poll: 3 seconds; quiet period: 15 seconds; retry: 60 seconds.')
        previous = snapshot()
        changed_at = time.monotonic()
        attempted_at = 0
        pending = True
        while not (STATE / 'stop').exists():
            try:
                current = snapshot()
                now = time.monotonic()
                if current != previous:
                    previous, changed_at, pending = current, now, True
                if pending and now - changed_at >= 15 and now - attempted_at >= 60:
                    attempted_at = now
                    publish()
                    # Keep the pre-publish snapshot so saves during Git/network work
                    # are noticed on the next poll rather than silently absorbed.
                    pending = False
            except Exception:
                logging.exception('Publish deferred; retrying after 60 seconds.')
                pending = True
            time.sleep(3)
        logging.info('Watcher stopped by stop file.')


if __name__ == '__main__':
    main()
