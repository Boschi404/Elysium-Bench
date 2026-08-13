# Code Review: auth.py diff

## 1. Hardcoded production secret — CRITICAL
- **File/line**: `auth.py:4` (`SECRET_KEY = "hunter2-2024-production-secret"`)
- **Problem**: A production credential committed in source. Anyone with repo
  access can forge sessions and impersonate users.
- **Fix**: Remove the constant. Load it from an environment variable or a
  secret manager (`os.getenv("SECRET_KEY")`), and rotate the leaked value.

## 2. SQL injection in `verify_login` — CRITICAL
- **File/line**: `auth.py:11-12`
  (`query = "SELECT password_hash FROM users WHERE username = '%s'" % username`)
- **Problem**: String-interpolated SQL. A username like
  `' OR '1'='1` alters the query semantics.
- **Fix**: Parameterized query:
  `cur.execute("SELECT password_hash FROM users WHERE username = ?", (username,))`
  (already used correctly in `get_user`).

## 3. MD5 password hashing — HIGH
- **File/line**: `auth.py:16` and `auth.py:35`
- **Problem**: MD5 is cryptographically broken and unsalted; identical
  passwords produce identical hashes, and dictionary/rainbow attacks are
  trivial.
- **Fix**: Use a slow, salted KDF — `bcrypt` or `argon2` — with per-user salt
  and constant-time comparison.

## 4. TOCTOU race in `transfer_funds` — HIGH
- **File/line**: `auth.py:44-50`
- **Problem**: Balance is SELECTed and checked outside a transaction, then
  two UPDATEs run inside a try block that swallows ALL exceptions and still
  returns True. Concurrent transfers can overdraw, and on error the caller
  is told the transfer succeeded while the commit may have rolled back.
- **Fix**: Wrap read+check+update in a single transaction
  (`BEGIN IMMEDIATE`), verify `cur.rowcount`, re-check the balance inside the
  transaction, and do NOT `return True` when an exception occurred — roll
  back and re-raise.

## 5. Weak session token + path traversal exposure — HIGH
- **File/line**: `auth.py:34-39` (`create_session`) and `auth.py:43-45`
  (`read_file_for_user`)
- **Problem**: The session token is MD5(user_id + epoch seconds) — trivially
  guessable with a small search window. `read_file_for_user` then opens any
  caller-supplied path with no authorization check (the comment claims the
  caller does it) and no path confinement.
- **Fix**: Use `secrets.token_urlsafe(32)` for tokens, and resolve paths
  against an allow-listed base directory (`os.path.realpath` +
  `commonpath` check) with the admin check enforced inside the function.

## Summary
| Severity | Count |
|----------|-------|
| Critical | 2 |
| High     | 3 |
| Medium   | 0 |
| Low      | 0 |

The diff must not merge until issues 1-4 are fixed; issue 5 requires a
redesign of session handling.
