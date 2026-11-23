"""Evidence-selected airport names shared by both subscription formats."""
import re

AI = ('HKG C', 'HKG M', '美国 B', 'HKG J', '美国 E', '美国 C', '台湾 C', '新加坡 C')
NODE_FAST = ('台湾 C', 'HKG C', '日本 B', 'HKG H', 'HKG M', '美国 B', 'HKG D', 'HKG F')
GEMINI_CLAUDE = ('美国 B', '美国 E', '美国 C', '台湾 C', '美国 A', '美国 D', '新加坡 C', '新加坡 2 直连 CTCM')
TIKTOK = ('美国 E', '美国 C', '美国 A', '美国 D', '新加坡 A', '美国 F', '美国 I', '美国 H')
MEMBERS = {'AI组': AI, '最优速组': NODE_FAST, 'GeminiClaude': GEMINI_CLAUDE, 'TikTok': TIKTOK}
MANUAL_DEFAULT = '手动默认 · HKG A'
MANUAL_NODE = 'HKG A'
CHECK_INTERVAL = 3
CLASH_CHECK_INTERVAL = 60
STASH_CHECK_TIMEOUT = 3


def name_filter(names, reject=True):
    values = [*names, *(['REJECT'] if reject else [])]
    return '^(' + '|'.join(re.escape(n).replace(r'\ ', ' ') for n in values) + ')$'
