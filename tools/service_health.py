"""Service endpoints and Stash selectors; native URL tests remain the default fallback."""
import re

ROUTING_VERSION = 'ROUTE-20261113.1'
GPT_POOL = 'AI组'
TIKTOK_POOL = 'AI最速组'
ENDPOINTS = {GPT_POOL: 'https://chatgpt.com/', TIKTOK_POOL: 'https://www.tiktok.com/foryou'}
# The installed private iOS script looks up this literal name and intersects its
# members with the GPT selector. Its code and controller secret stay on-device.
LEGACY_GPT_POOL = 'ai'
MANAGED = {'GPT 服务优选': GPT_POOL, 'TikTok 服务检测组': TIKTOK_POOL, LEGACY_GPT_POOL: GPT_POOL}


def add_stash_selectors(config):
    groups = {g['name']: g for g in config['proxy-groups']}
    for selector, pool in MANAGED.items():
        native = groups[pool]
        if not native['filter'].endswith('|REJECT)$'):
            raise ValueError('Expected an anchored curated pool with a REJECT sentinel')
        choices = [pool, LEGACY_GPT_POOL] if selector == 'GPT 服务优选' else [pool]
        allowed = native['filter'].removesuffix('|REJECT)$') + '|' + '|'.join(map(re.escape, choices)) + ')$'
        config['proxy-groups'].append({'name': selector, 'type': 'select', 'hidden': True,
            'proxies': choices, 'use': native['use'][:], 'filter': allowed, 'interval': -1})
    groups['海外AI']['proxies'].insert(0, 'GPT 服务优选')
    # An old saved TikTok service choice must fall back to the new default.
    # The new service selector is opt-in. The old on-device script leaves it alone.
    groups['TikTok']['proxies'].append('TikTok 服务检测组')

def render_private_override(root):
    # Device-local copy: its executable code cannot be replaced via a remote script update.
    from textwrap import indent
    script = (root / 'scripts/service-health.js').read_text(encoding='utf-8')
    return ("""# 导入本地副本，在「参数」中填写本机外部控制的端口与密钥。不要分享含密钥的截图。
name: GPT 与 TikTok 服务检测
desc: 每分钟通过当前出口分别检查 ChatGPT 和 TikTok。请在本设备填写控制端口与密钥。
arguments-version: 1
arguments:
  port:
    type: input
    value-type: integer
    title: 本机控制端口
    default: 9090
    minimum: 1
    maximum: 65535
  secret:
    type: input
    title: 本机控制密钥
    description: 与「设置 → 外部访问」相同，请勿截图分享。
    required: true
cron:
  script:
    - name: jimmy-service-health
      cron: '* * * * *'
      timeout: 35
      argument: '{"port":${args.port|json},"secret":${args.secret|json}}'
script-providers:
  jimmy-service-health:
    payload: |
""" + indent(script, '      '))
