"""Shared current-config serialization, rule expansion and script URL helpers.

This module does not build a second Stash installation or legacy ZIP package.
"""
import copy
import yaml
from validate import ROOT, RAW, RULE_KINDS, load, local_public_path
from build_ad_scripts import VERSION as SCRIPT_VERSION

class ConfigDumper(yaml.SafeDumper): pass

def pool_tolerance_ms(name):
    """Use the shared, unprefixed pool name for both subscription formats."""
    return {'ai': 250, 'AI最速': 100}.get(name, 50)

def dump(data):
    return yaml.dump(data, Dumper=ConfigDumper, allow_unicode=True, sort_keys=False, width=120)

def flatten(config, keep_providers=()):
    result = copy.deepcopy(config)
    providers = result.pop('rule-providers', {})
    retained = {k:v for k,v in providers.items() if k in keep_providers}
    if retained: result['rule-providers'] = retained
    rules = []
    for rule in result['rules']:
        fields = rule.split(',')
        if fields[0] == 'RULE-SET':
            if fields[1] in retained:
                rules.append(rule)
                continue
            provider = providers[fields[1]]
            for entry in load(local_public_path(provider['url']))['payload']:
                parts = entry.split(',')
                if parts[0] not in RULE_KINDS: raise ValueError('unsupported classical rule')
                # A payload's optional no-resolve follows the policy in flat rules.
                rules.append(','.join(parts[:2] + [fields[2]] + parts[2:] + fields[3:]))
        else:
            rules.append(rule)
            if fields[0] == 'MATCH': break  # later rules were already unreachable
    result['rules'] = list(dict.fromkeys(rules))
    return result

def script_references(config):
    """Keep native URL providers; content-only lacks the sources named by the reported core error."""
    result = copy.deepcopy(config)
    for name, provider in result.get('script-providers', {}).items():
        url = provider.get('url', '')
        if not url.startswith(RAW): raise ValueError('non-project script source')
        path = ROOT / local_public_path(url)
        if path.parent != ROOT / 'scripts/ads' or path.suffix != '.js': raise ValueError('unexpected script path')
        if not path.is_file(): raise ValueError('missing script source')
        if set(provider) != {'url', 'interval'} or provider['interval'] != 86400:
            raise ValueError('unexpected script provider declaration')
        provider['url'] = RAW + path.relative_to(ROOT).as_posix() + '?v=' + SCRIPT_VERSION
    if 'mitm' in result.get('http', {}):
        result['http']['mitm'] = list(dict.fromkeys(result['http']['mitm']))
    return result
