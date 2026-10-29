"""Prepare a private startup fallback from an existing Clash airport profile.

Output contains node credentials. Keep it outside version control and paste it
only into the local profile Merge. No network calls or client changes are made.
"""
import argparse
import copy
from pathlib import Path

import yaml
from build_clash import AIRPORT_INFO_EXCLUDE


def without_nulls(value):
    if isinstance(value, dict):
        return {key: without_nulls(item) for key, item in value.items() if item is not None}
    if isinstance(value, list):
        return [without_nulls(item) for item in value if item is not None]
    return value


def prepare(airport, private_merge):
    nodes = airport.get('proxies')
    if not isinstance(nodes, list) or not nodes:
        raise ValueError('Existing airport profile must contain nonempty proxies')
    if any(not isinstance(node, dict) or not node.get('name') or not node.get('type') for node in nodes):
        raise ValueError('Invalid airport node')
    result = copy.deepcopy(private_merge)
    provider = result.get('proxy-providers', {}).get('机场', {})
    if not provider.get('url') or 'example.invalid' in provider['url']:
        raise ValueError('Private airport URL is required')
    # Mihomo payload decoding rejects null fields accepted in some downloaded YAML.
    provider['payload'] = without_nulls(nodes)
    # The public profile owns the download strategy, so future changes propagate.
    provider.pop('proxy', None)
    # Remove only the known previous generated overrides; retain custom credentials.
    if provider.get('header') == {'User-Agent': ['clash-verge/v2.5.8']}:
        provider.pop('header')
    if provider.get('exclude-filter') == AIRPORT_INFO_EXCLUDE:
        provider.pop('exclude-filter')
    result['proxy-providers']['机场'] = provider
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--airport', type=Path, required=True)
    parser.add_argument('--merge', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = prepare(yaml.safe_load(args.airport.read_text(encoding='utf-8')),
                     yaml.safe_load(args.merge.read_text(encoding='utf-8')))
    # Exclusive creation protects existing private files from accidental overwrite.
    with args.output.open('x', encoding='utf-8', newline='\n') as output:
        yaml.safe_dump(result, output, allow_unicode=True, sort_keys=False)
    print('Private Merge prepared; keep output local. The public download pool selects available nodes automatically.')


if __name__ == '__main__':
    main()
