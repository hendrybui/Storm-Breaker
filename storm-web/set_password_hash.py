#!/usr/bin/env python3
"""Set/rotate an operator's PBKDF2 password hash (P7.1).

Usage:
    python3 storm-web/set_password_hash.py <username>

Writes storm-web/operator_auth.json (0600, gitignored).  Once a hash
exists for a user, the legacy plaintext in config.php is no longer
accepted for that user.  Rollback: delete operator_auth.json (or the
user's entry) to fall back to config.php plaintext.
"""
import getpass
import sys

from app.core.passwords import set_password_hash


def main() -> int:
    if len(sys.argv) != 2:
        print('usage: set_password_hash.py <username>', file=sys.stderr)
        return 2
    username = sys.argv[1]
    pw1 = getpass.getpass('new password for %s: ' % username)
    pw2 = getpass.getpass('repeat: ')
    if pw1 != pw2:
        print('passwords do not match', file=sys.stderr)
        return 1
    if not pw1:
        print('empty password rejected', file=sys.stderr)
        return 1
    set_password_hash(username, pw1)
    print('hash stored for %r (plaintext fallback disabled for this user)' %
          username)
    return 0


if __name__ == '__main__':
    sys.path.insert(0, __file__.rsplit('/', 1)[0])
    sys.exit(main())
