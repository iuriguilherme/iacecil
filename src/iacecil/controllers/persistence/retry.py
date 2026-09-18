"""Conflict retry, shared by every store in this package.

Concurrent writers race on lazily created ZODB structures — a chat's
container, a store's root containers. ZODB resolves BTree inserts, so
re-running the transaction is the standard answer, and both the neutral
store and the chat store need exactly the same loop with exactly the
same retry count.

Copyleft 2012-2026 Iuri Guilherme <https://iuri.neocities.org/>

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
MA 02110-1301, USA.
"""

import random
import time

from ZODB.POSException import ConflictError

MAX_COMMIT_RETRIES = 10

## Backoff between attempts, in seconds. Retrying immediately is what
## failed in production: a burst of writers (Matrix replaying history on
## connect) collided, retried in lockstep, and collided again until the
## retries ran out and records were dropped. A randomized, growing pause
## spreads them out so they commit one after another instead.
BACKOFF_BASE = 0.005
BACKOFF_CAP = 0.5


def backoff(attempt: int) -> float:
    """Full-jitter delay before the given retry attempt (0-based)."""
    return random.uniform(0, min(BACKOFF_CAP, BACKOFF_BASE * (2 ** attempt)))


def commit_with_retry(fn, *args, sleep=time.sleep):
    """Re-run a transaction function on ConflictError, with backoff.

    Runs inside asyncio.to_thread, so it must stay synchronous and the
    pause blocks only its own worker thread. The last attempt re-raises:
    a conflict that survives every try is a real failure, not something
    to swallow.
    """
    for attempt in range(MAX_COMMIT_RETRIES):
        try:
            return fn(*args)
        except ConflictError:
            if attempt == MAX_COMMIT_RETRIES - 1:
                raise
            sleep(backoff(attempt))
