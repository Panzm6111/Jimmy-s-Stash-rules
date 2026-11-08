"""Stash-only AI DNS/routing guard; no private nodes or service-unlock claims.

Native semantics: https://stash.wiki/features/dns-server (iOS 3.6+).
Keep this out of Mihomo: follow-rule is a Stash option, not respect-rules.
"""
import copy

AI_SUFFIXES = ('chatgpt.com', 'openai.com', 'oaistatic.com', 'oaiusercontent.com')
AI_RESOLVERS = ('https://1.1.1.1/dns-query', 'https://8.8.8.8/dns-query')
BOOTSTRAP = ('https://223.5.5.5/dns-query', 'https://1.12.12.12/dns-query')
DNS_ROUTES = (
    'IP-CIDR,1.1.1.1/32,海外AI,no-resolve',
    'IP-CIDR,8.8.8.8/32,海外AI,no-resolve',
    'DOMAIN,dns.alidns.com,DIRECT',
    'DOMAIN,doh.pub,DIRECT',
)
CORE_ROUTES = tuple('DOMAIN-SUFFIX,' + host + ',海外AI' for host in AI_SUFFIXES)
STASH_ONLY_ROUTES = DNS_ROUTES + CORE_ROUTES


def apply(source):
    config = copy.deepcopy(source)
    dns = config['dns']
    # A separate direct, encrypted node resolver prevents DNS -> proxy -> DNS
    # recursion when the private airport uses domain names for server addresses.
    dns.update({'follow-rule': True, 'default-nameserver': list(BOOTSTRAP),
                'proxy-server-nameserver': list(BOOTSTRAP)})
    policy = {'+.' + host: list(AI_RESOLVERS) for host in AI_SUFFIXES}
    ai_sets = list(dict.fromkeys(r.split(',')[1] for r in config['rules']
                               if r.startswith('RULE-SET,') and r.split(',')[2] == '海外AI'))
    if not ai_sets:
        raise ValueError('AI DNS guard requires the maintained AI rule providers')
    policy['rule-set:' + ','.join(ai_sets)] = list(AI_RESOLVERS)
    dns['nameserver-policy'] = policy
    # Resolver IPs are dedicated to AI DNS here. Pin their traffic to exactly
    # the same selector as AI connections, before ads/GeoIP/MATCH can intercept.
    config['rules'] = list(DNS_ROUTES) + config['rules']
    # Preserve existing LAN/system exceptions. Core services remain proxied
    # even if an HTTP rule provider is empty/unavailable during startup.
    slot = config['rules'].index('RULE-SET,系统直连例外,DIRECT') + 1
    config['rules'][slot:slot] = CORE_ROUTES
    for group in config['proxy-groups']:
        if group['type'] == 'url-test':
            group['tolerance'] = 50
    return config


def for_clash(source, baseline):
    """Retain the established Clash DNS/groups; do not copy Stash-only options."""
    config = copy.deepcopy(source)
    config['dns'] = copy.deepcopy(baseline['dns'])
    baseline_groups = {g['name']: g for g in baseline['proxy-groups']}
    for group in config['proxy-groups']:
        if group['type'] == 'url-test':
            original = baseline_groups.get(group['name'], {})
            if 'tolerance' in original:
                group['tolerance'] = original['tolerance']
            else:
                group.pop('tolerance', None)
    config['rules'] = [r for r in config['rules'] if r not in STASH_ONLY_ROUTES]
    return config
