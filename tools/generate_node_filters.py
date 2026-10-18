#!/usr/bin/env python3
"""Exclude known subscription-info prefixes using basic regex only, never lookarounds.

Names are not proof of a working node. Unrecognized information names remain
visible, and an actual node beginning with one of these prefixes can be restored
by removing the device-local selector filter. No subscription is downloaded.
"""
import argparse
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'config/core.stoverride'
INFO_PREFIXES = (
    '剩余流量', '流量剩余', '到期时间', '套餐到期', '订阅到期',
    '下次重置', '重置时间', '距离下次重置',
    'remaining traffic', 'traffic remaining', 'expire', 'expiry',
    'expiration', 'update subscription',
)
SELECTORS = {'手动节点', '全部节点', 'OpenAI', 'Netflix', 'YouTube', 'Telegram', 'Apple', 'Microsoft', '未匹配流量'}

def node_filter():
    # A prefix trie expresses the complement with anchors, alternation and
    # negated character classes. It does not need (?!...), exclude-filter,
    # backreferences, or any client-specific regex extension.
    trie = {}
    for prefix in INFO_PREFIXES:
        node = trie
        for char in prefix:
            node = node.setdefault(char, {})
        node[None] = True

    def escape(text):
        # Escape regex punctuation only. Python re.escape also emits backslash-
        # space, which is unnecessary and rejected by some regular-expression
        # engines even though Python accepts it.
        return ''.join('\\' + char if char in r'\.^$|?*+()[]{}-' else char for char in text)

    def allowed(node):
        if None in node:
            return None
        choices = ['$']
        letters = sorted(node)
        if letters:
            choices.append('[^' + escape(''.join(letters)) + '].*$')
        else:
            choices.append('.*$')
        for char in letters:
            tail = allowed(node[char])
            if tail is not None:
                choices.append(escape(char) + tail)
        return '(?:' + '|'.join(choices) + ')'

    return '(?i)^' + allowed(trie)

def check(config):
    groups = {g['name']: g for g in config['proxy-groups']}
    pattern = node_filter()
    return all(groups[name].get('filter') == pattern for name in SELECTORS)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write', action='store_true')
    args = parser.parse_args()
    config = yaml.safe_load(SOURCE.read_text())
    if args.write:
        for group in config['proxy-groups']:
            if group['name'] in SELECTORS:
                group['filter'] = node_filter()
        SOURCE.write_text(yaml.safe_dump(config, allow_unicode=True, sort_keys=False, width=120))
    same = check(config)
    print(('PASS ' if same else 'DRIFT ') + 'subscription-info filters; no private input')
    return 0 if same else 1

if __name__ == '__main__': raise SystemExit(main())
