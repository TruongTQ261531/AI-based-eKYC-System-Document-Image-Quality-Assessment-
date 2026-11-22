"""Finish a pending owner closure strictly through the existing signed workflow."""
import argparse
from pathlib import Path

from ..adjudication.post_p6_closure import unsigned_payload
from ..adjudication.workflow import build_packet
from ..oracle_reliability.verify_post_p6 import verify_round
from ..reviewer_tools.strict import canonical, digest, loads, need
from ..task55.data import EC, read, save_new, sha

BASE = '81557747d9f1a3467b0f6bdb0dad6f60805a9fe4'
SOURCE = EC/'local/post_p6/run_20261122094004'
PUBLIC = EC/'execution/master_01/post_p6_20261122_094004Z'
AGG_HASH = '786cca653ab97f47d4925117360366a706253f4adaaf12c908d59aee9019b809'


def frozen():
    need(sha(PUBLIC/'aggregate.json')==AGG_HASH,'Unexpected owner baseline')
    state=read(PUBLIC/'aggregate.json')['round1']
    verify_round(SOURCE,state)
    views=read(SOURCE/'review_views.json')
    original=unsigned_payload(views.values(),None,None)
    need(canonical(original)==(SOURCE/'closure_payload.canonical.json').read_bytes()
         and digest(original)==state['pending_payload_sha256'],'Original closure draft mismatch')
    return original,views


def signed_packet(envelope):
    draft,views=frozen()
    need(isinstance(envelope,dict) and isinstance(envelope.get('payload'),dict),'Invalid closure envelope')
    actual=envelope['payload']
    expected=dict(draft,authority_id=actual.get('authority_id'),timestamp=actual.get('timestamp'))
    need(expected==actual,'Signed payload differs from owner cutoff or roster')
    return build_packet(list(views.values()),envelope)


if __name__=='__main__':
    from .prepare import private_run
    parser=argparse.ArgumentParser()
    parser.add_argument('run')
    parser.add_argument('signed_envelope',type=Path)
    args=parser.parse_args()
    envelope=loads(args.signed_envelope.read_bytes())
    packet=signed_packet(envelope)
    dest=private_run(args.run)
    dest.mkdir(parents=True,exist_ok=True)
    # Write both objects as one immutable evidence record only after verification.
    save_new(dest/'signed_round1.json',dict(envelope=envelope,packet=packet,
        signed_envelope_sha256=digest(envelope),status='SIGNED_CLOSURE_VERIFIED'))
