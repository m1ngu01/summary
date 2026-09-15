"""Compatibility command: publish once. No watcher or background loop."""
from publish_library import publish

if __name__ == '__main__':
    publish(log=print)
