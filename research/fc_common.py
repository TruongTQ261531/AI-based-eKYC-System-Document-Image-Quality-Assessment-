"""Prospective, matched-data ablations; all earlier results remain immutable."""
from research.hp_common import ROOT, CONFIG, read, save, sha, stable_hash
from research.hp_common import DATA as HP_DATA, OUT as HP_OUT, CACHE as HP_CACHE
from research.hp_common import preserve as preserve_hp, signature as hp_signature
from research.v3_common import DATA as V3_DATA, OUT as V3_OUT

DATA = ROOT/'research/data/fair_controls_v1'
CACHE = ROOT/'research/cache/fair_controls_v1'
OUT = ROOT/'research/results/fair_controls_v1'
ARMS = ('uniform', 'hard', 'random', 'repeat')
SEEDS = (42, 31415)
KEYS = tuple(f'{arm}_{s}' for s in SEEDS for arm in ARMS)
NEW_ARMS = ('random', 'repeat')


def freeze_previous():
    path = OUT/'previous_artifacts.json'
    if path.exists():
        preserve()
        return
    preserve_hp()
    files = list(HP_OUT.glob('*.json'))
    files += list((ROOT/'research').glob('hp_*.py'))
    files += list((ROOT/'research').glob('HARD_PAIR*.md'))
    save(path, dict(hp_signature=hp_signature(),
        files=[dict(path=p.relative_to(ROOT).as_posix(), sha256=sha(p)) for p in sorted(files)]))


def preserve():
    counts = preserve_hp()
    old = read(OUT/'previous_artifacts.json')
    if old['hp_signature'] != hp_signature():
        raise ValueError('Frozen hard-pair contract changed')
    if any(sha(ROOT/r['path']) != r['sha256'] for r in old['files']):
        raise ValueError('A prior hard-pair artifact changed')
    return counts


def signature():
    names = ('fc_common.py', 'fc_data.py', 'fc_acquire.py', 'fc_study.py', 'fc_statistics.py', 'fc_preflight.py',
             'FAIR_CONTROLS_PROTOCOL.md')
    result = {n:sha(ROOT/'research'/n) for n in names}
    result.update(previous_index=sha(OUT/'previous_artifacts.json'),
                  dataset_card=sha(OUT/'dataset_card.json'),
                  runtime_choice=sha(OUT/'runtime_choice.json'),
                  analysis_plan=sha(OUT/'analysis_plan.json'),
                  pixel_manifest=sha(OUT/'pixel_manifest.json'),
                  training_design=sha(OUT/'training_design.json'))
    return stable_hash(result)


def train_rows(arm):
    if arm not in ARMS:
        raise ValueError('Unknown arm')
    if sha(DATA/'train.json') != read(OUT/'dataset_card.json')['train_sha256']:
        raise ValueError('Training data changed')
    return read(DATA/'train.json')[arm]


def eval_rows(role):
    if role not in ('development', 'test'):
        raise ValueError('Unknown evaluation role')
    if sha(DATA/'evaluation.json') != read(OUT/'dataset_card.json')['evaluation_sha256']:
        raise ValueError('Evaluation data changed')
    return [r for r in read(DATA/'evaluation.json') if r['role'] == role]
