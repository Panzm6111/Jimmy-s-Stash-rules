"""Stash-only AI DNS/routing guard; no private nodes or service-unlock claims.

Native semantics: https://stash.wiki/features/dns-server (iOS 3.6+).
Keep this out of Mihomo: follow-rule is a Stash option, not respect-rules.
"""
import copy
from config_helpers import pool_tolerance_ms
from service_health import add_stash_selectors

AI_SUFFIXES = ('chatgpt.com', 'openai.com', 'oaistatic.com', 'oaiusercontent.com')
AI_RESOLVERS = ('https://1.1.1.1/dns-query', 'https://8.8.8.8/dns-query')
# Stash routes the connection to the resolver by destination IP. Separate
# addresses keep Claude DNS on its selected exit even when GPT changes exits.
CLAUDE_DNS_IPS = ('1.0.0.1', '8.8.4.4')
CLAUDE_RESOLVERS = tuple(f'https://{ip}/dns-query' for ip in CLAUDE_DNS_IPS)
BOOTSTRAP = ('https://223.5.5.5/dns-query', 'https://1.12.12.12/dns-query')
DNS_ROUTES = (
    'IP-CIDR,1.1.1.1/32,海外AI,no-resolve',
    'IP-CIDR,8.8.8.8/32,海外AI,no-resolve',
    'DOMAIN,dns.alidns.com,DIRECT',
    'DOMAIN,doh.pub,DIRECT',
) + tuple(f'IP-CIDR,{ip}/32,Claude,no-resolve' for ip in CLAUDE_DNS_IPS)
CORE_ROUTES = tuple('DOMAIN-SUFFIX,' + host + ',海外AI' for host in AI_SUFFIXES)
TIKTOK_ENTRY_HOSTS = ('www.tiktok.com', 'api16-normal-c-useast1a.tiktokv.com',
                     'api16-normal-c-alisg.tiktokv.com', 'v16.tiktokcdn.com')
TIKTOK_ROUTES = tuple('DOMAIN,' + host + ',TikTok' for host in TIKTOK_ENTRY_HOSTS)
STASH_ONLY_ROUTES = DNS_ROUTES


def claude_dns_policy(rules, resolvers):
    """Use the same domain boundaries for DNS and the Claude web selector."""
    policy = {}
    for rule in rules:
        fields = rule.split(',')
        if len(fields) == 3 and fields[2] == 'Claude' and fields[0] in ('DOMAIN', 'DOMAIN-SUFFIX'):
            key = ('+.' if fields[0] == 'DOMAIN-SUFFIX' else '') + fields[1]
            policy[key] = list(resolvers)
    return policy


def apply(source):
    config = copy.deepcopy(source)
    dns = config['dns']
    # A separate direct, encrypted node resolver prevents DNS -> proxy -> DNS
    # recursion when the private airport uses domain names for server addresses.
    dns.update({'follow-rule': True, 'default-nameserver': list(BOOTSTRAP),
                'proxy-server-nameserver': list(BOOTSTRAP)})
    policy = {'+.' + host: list(AI_RESOLVERS) for host in AI_SUFFIXES}
    policy.update(claude_dns_policy(config['rules'], CLAUDE_RESOLVERS))
    ai_sets = list(dict.fromkeys(r.split(',')[1] for r in config['rules']
                               if r.startswith('RULE-SET,') and r.split(',')[2] == '海外AI'))
    if not ai_sets:
        raise ValueError('AI DNS guard requires the maintained AI rule providers')
    policy['rule-set:' + ','.join(ai_sets)] = list(AI_RESOLVERS)
    dns['nameserver-policy'] = policy
    # Resolver IPs are dedicated to AI DNS here. Pin their traffic to exactly
    # the same selector as AI connections, before ads/GeoIP/MATCH can intercept.
    config['rules'] = list(DNS_ROUTES) + [r for r in config['rules'] if r not in CORE_ROUTES + TIKTOK_ROUTES + DNS_ROUTES]
    # Preserve existing LAN/system exceptions. Core services remain proxied
    # even if an HTTP rule provider is empty/unavailable during startup.
    slot = config['rules'].index('RULE-SET,系统直连例外,DIRECT') + 1
    config['rules'][slot:slot] = CORE_ROUTES
    slot = config['rules'].index('RULE-SET,TikTok广告,广告拦截') + 1
    config['rules'][slot:slot] = TIKTOK_ROUTES
    for group in config['proxy-groups']:
        if group['type'] == 'url-test':
            group['tolerance'] = pool_tolerance_ms(group['name'])
    add_stash_selectors(config)
    return config


def for_clash(source, baseline):
    """Retain the established Clash DNS/groups; do not copy Stash-only options."""
    config = copy.deepcopy(source)
    config['dns'] = copy.deepcopy(baseline['dns'])
    config['proxy-groups'] = copy.deepcopy(baseline['proxy-groups'])
    config['rules'] = [r for r in config['rules'] if r not in STASH_ONLY_ROUTES]
    return config
