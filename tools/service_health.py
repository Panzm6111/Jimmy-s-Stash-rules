"""Service endpoints and Stash selectors; native URL tests remain the default fallback."""
ROUTING_VERSION = 'ROUTE-20261112.3'
GPT_POOL = 'ai'
TIKTOK_POOL = 'AI最速'
ENDPOINTS = {GPT_POOL: 'https://chatgpt.com/', TIKTOK_POOL: 'https://www.tiktok.com/foryou'}
# (business selector, native pool, selector owned by the optional on-device check)
SERVICES = (('海外AI', GPT_POOL, 'GPT 服务优选'), ('TikTok', TIKTOK_POOL, 'TikTok 服务优选'))
MANAGED = {selector: pool for _, pool, selector in SERVICES}


def add_stash_selectors(config):
    groups = {g['name']: g for g in config['proxy-groups']}
    for business, pool, selector in SERVICES:
        native = groups[pool]
        # Preserve a working first choice if the private script is not enabled.
        # The filter includes the native pool itself, as well as its real exits.
        if not native['filter'].endswith('|REJECT)$'):
            raise ValueError('Expected an anchored curated pool with a REJECT sentinel')
        allowed = native['filter'].removesuffix('|REJECT)$') + '|' + pool + ')$'
        config['proxy-groups'].append({'name': selector, 'type': 'select',
            'proxies': [pool], 'use': native['use'][:], 'filter': allowed, 'interval': -1})
        groups[business]['proxies'].insert(0, selector)

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
