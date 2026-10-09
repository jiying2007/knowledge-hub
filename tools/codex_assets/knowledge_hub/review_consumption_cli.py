"""Record explicit review-packet consumption without changing lifecycle or owner gates."""

from __future__ import annotations

import argparse
import json

from .common import repository_root, KnowledgeHubError
from .review_batches import record_consumption
from .private_io import PrivateWriteUncertain


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', default='')
    parser.add_argument('--item-id', required=True)
    parser.add_argument('--decision', required=True, choices=('accepted', 'deferred', 'changes-requested'))
    parser.add_argument('--reviewer', required=True)
    parser.add_argument('--evidence-ref', required=True)
    parser.add_argument('--body-sha256', required=True)
    parser.add_argument('--next-review-at', default='')
    parser.add_argument('--review-seconds', type=float, default=None)
    parser.add_argument('--review-event-id', default='')
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args(argv)
    try:
        payload = record_consumption(repository_root(args.root), args.item_id, args.decision, args.reviewer,
                                     args.evidence_ref, args.body_sha256, next_review_at=args.next_review_at,
                                     review_seconds=args.review_seconds, review_event_id=args.review_event_id, apply=args.apply)
        print(json.dumps(payload, ensure_ascii=False))
        return 3 if payload.get('applied') is None or payload.get('pending_status') == 'needs-review' else 0
    except PrivateWriteUncertain as exc:
        print(json.dumps({'status':'needs-recovery-review', 'error':str(exc), 'applied':None}, ensure_ascii=False))
        return 3
    except (KnowledgeHubError, ValueError, OSError) as exc:
        print(json.dumps({'status':'blocked', 'error':str(exc), 'applied':False}, ensure_ascii=False))
        return 3


if __name__ == '__main__':
    raise SystemExit(main())
