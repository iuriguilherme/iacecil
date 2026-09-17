#!/usr/bin/env python
"""One-time migration: per-chat .fs files -> one chats.fs per bot.

Old clean layout (one storage per chat):

    instance/zodb/bots/<bot_id>/<connector>/chats/<chat_id>.fs

New layout (one storage per bot, chats keyed inside it):

    instance/zodb/bots/<bot_id>/chats.fs   ->  root.chats['<connector>/<chat_id>']

A ZEO server serves only the storages its configuration names at
startup, while a new chat appears at runtime; consolidating keeps the
storage set fixed. See R13 in
docs/plans/2026-06-24-001-refactor-decouple-web-survival-slice1-plan.md.

The legacy telegram-only layout (``bots/<numeric id>/chats/<chat>.fs``,
pickled aiogram objects, read through zodb_orm) has no connector
component and is deliberately left alone.

Usage:

    python scripts/migrate_chat_stores.py [--zodb-path instance/zodb] [--dry-run]

Old files are never deleted: verify the reported counts, then remove
``bots/<bot_id>/<connector>/`` by hand.
"""

import argparse
import glob
import logging
import os
import sys

import BTrees
import zc.zlibstorage
import ZODB
import ZODB.FileStorage

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from iacecil.controllers.persistence.chat_store import (  # noqa: E402
    _init_root,
)

logger = logging.getLogger('migrate_chat_stores')


def _open(path: str):
    storage = ZODB.FileStorage.FileStorage(path)
    return ZODB.DB(zc.zlibstorage.ZlibStorage(storage))


def find_old_stores(zodb_path: str):
    """Yield (bot_id, connector, chat_id, path) for the clean layout only."""
    pattern = os.path.join(
        os.path.abspath(zodb_path), 'bots', '*', '*', 'chats', '*.fs')
    for path in sorted(glob.glob(pattern)):
        chat_id = os.path.basename(path)[:-len('.fs')]
        connector = os.path.basename(
            os.path.dirname(os.path.dirname(path)))
        bot_id = os.path.basename(
            os.path.dirname(os.path.dirname(os.path.dirname(path))))
        yield bot_id, connector, chat_id, path


def migrate(zodb_path: str, dry_run: bool = False) -> dict:
    """Copy every per-chat store into its bot's consolidated storage.

    Returns per-bot counts of records and native ids copied. Re-running
    is safe: a record already carrying its old id is not copied twice,
    and native ids land in a set.
    """
    counts = {}
    targets = {}
    try:
        for bot_id, connector, chat_id, path in find_old_stores(zodb_path):
            ## Join the on-disk components verbatim. They were written
            ## by sanitize_component, which is NOT idempotent (it
            ## percent-encodes '%' itself), so re-sanitizing would turn a
            ## matrix room's '%21...' into '%2521...' and the migrated
            ## chat would never match what store_message writes at
            ## runtime.
            key = '{}/{}'.format(connector, chat_id)
            stats = counts.setdefault(bot_id, {'records': 0, 'native_ids': 0,
                'chats': 0})
            stats['chats'] += 1

            old_db = _open(path)
            try:
                with old_db.transaction() as connection:
                    root = connection.root
                    records = dict(getattr(root, 'messages', {}) or {})
                    native_ids = list(getattr(root, 'native_ids', []) or [])
            finally:
                old_db.close()

            stats['records'] += len(records)
            stats['native_ids'] += len(native_ids)
            logger.info(
                f"{bot_id}: {key} -> {len(records)} records, "
                f"{len(native_ids)} native ids"
                + (' (dry run)' if dry_run else ''))
            if dry_run:
                continue

            new_path = os.path.join(os.path.abspath(zodb_path), 'bots',
                bot_id, 'chats.fs')
            db = targets.get(new_path)
            if db is None:
                os.makedirs(os.path.dirname(new_path), exist_ok=True)
                db = _open(new_path)
                _init_root(db)
                targets[new_path] = db

            with db.transaction() as connection:
                chats = connection.root.chats
                chat = chats.get(key)
                if chat is None:
                    chat = BTrees.OOBTree.OOBTree()
                    chat['messages'] = BTrees.OOBTree.OOBTree()
                    chat['native_ids'] = BTrees.OOBTree.TreeSet()
                    chats[key] = chat
                for msg_id, record in records.items():
                    chat['messages'][msg_id] = dict(record)
                for native_id in native_ids:
                    chat['native_ids'].add(native_id)
    finally:
        for db in targets.values():
            db.close()
    return counts


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--zodb-path', default='instance/zodb')
    parser.add_argument('--dry-run', action='store_true',
        help='report what would be copied without writing')
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format='%(message)s')
    counts = migrate(args.zodb_path, dry_run=args.dry_run)
    if not counts:
        logger.info(f"No per-chat stores found under {args.zodb_path}")
        return 0
    for bot_id, stats in sorted(counts.items()):
        logger.info(
            f"{bot_id}: {stats['chats']} chats, {stats['records']} records, "
            f"{stats['native_ids']} native ids")
    if not args.dry_run:
        logger.info(
            "Old per-chat files were left in place; verify, then remove "
            "bots/<bot_id>/<connector>/ by hand.")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
