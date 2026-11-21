"""Evidence-selected names and deterministic stable failover, without credentials."""
import copy
import re

STABLE = ('HKG B', 'HKG C', 'HKG J', '新加坡 A', '台湾 B', '日本 A', '美国 B')
AI_FAST = ('日本 A', '日本 B', 'HKG B', 'HKG C', 'HKG J')
NODE_FAST = ('日本 A', '日本 B', 'HKG B', 'HKG C', 'HKG A', 'HKG I', 'HKG J', 'HKG M')
GEMINI = ('日本 A', '日本 B', '新加坡 A', '新加坡 B', '台湾 B', '美国 B', '美国 D')
MEMBERS = {'Gemini': GEMINI, 'AI组': STABLE, 'AI最速组': AI_FAST, '最优速组': NODE_FAST}
PRIORITY_PREFIX = 'AI稳备 · '
CHECK_INTERVAL = 3
CLASH_CHECK_INTERVAL = 60
STASH_CHECK_TIMEOUT = 3


def name_filter(names, reject=True):
    values = [*names, *(['REJECT'] if reject else [])]
    return '(?i)^(' + '|'.join(re.escape(n).replace(r'\ ', ' ') for n in values) + ')$'


def apply_ordered_stable(config):
    """One filtered child per name prevents provider order overriding priority.

    A REJECT sentinel makes missing provider members fail closed. Child URL tests
    contain at most one real node; they cannot choose a faster lower-priority node.
    """
    groups = {g['name']: g for g in config['proxy-groups']}
    stable = groups['AI组']
    if stable.get('proxies') == [PRIORITY_PREFIX + n for n in STABLE]:
        return config
    use = stable.pop('use')
    stable.pop('filter', None)
    stable.pop('tolerance', None)
    stable.update(type='fallback', proxies=[PRIORITY_PREFIX+n for n in STABLE],
                  interval=CHECK_INTERVAL, lazy=False)
    children = [dict(name=PRIORITY_PREFIX+n, type='url-test',
                     proxies=['REJECT'], use=copy.deepcopy(use),
                     filter=name_filter((n,)), url=stable['url'],
                     interval=CHECK_INTERVAL, lazy=False, tolerance=50, hidden=True)
                for n in STABLE]
    config['proxy-groups'].extend(children)
    return config
