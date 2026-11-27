"""Evidence-selected airport names shared by both subscription formats."""
import re

AI = ('美国 E', 'HKG M', '台湾 B', '新加坡 C', '日本 B', '美国 C', '美国 B', '美国 A')
NODE_FAST = ('HKG M', 'HKG G', 'HKG J', 'HKG H', '美国 E', '美国 C', '美国 B', '日本 A')
GEMINI_CLAUDE = ('美国 B', '美国 E', '美国 C', '台湾 B', '美国 A', '美国 D', '新加坡 C', '日本 B')
TIKTOK = ('美国 E', '美国 C', '美国 A', '美国 D', '新加坡 A', '美国 F', '美国 I', '日本 B')
MEMBERS = {'AI组': AI, '最优速组': NODE_FAST, 'GeminiClaude': GEMINI_CLAUDE, 'TikTok': TIKTOK}
MANUAL_DEFAULT = '手动默认 · HKG A'
MANUAL_NODE = 'HKG A'
CHECK_INTERVAL = 3
CLASH_CHECK_INTERVAL = 60
STASH_CHECK_TIMEOUT = 3


def name_filter(names, reject=True):
    values = [*names, *(['REJECT'] if reject else [])]
    return '^(' + '|'.join(re.escape(n).replace(r'\ ', ' ') for n in values) + ')$'
