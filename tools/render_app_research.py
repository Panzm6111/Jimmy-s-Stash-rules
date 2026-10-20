#!/usr/bin/env python3
"""Render public name-only inventory and the reviewed module index. No screenshots or private data."""
import argparse
import json
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[1]
RAW = 'https://raw.githubusercontent.com/Panzm6111/Jimmy-s-Stash-rules/main/'

def render():
    inv = json.loads((ROOT / 'research/app-inventory.json').read_text())
    catalog = json.loads((ROOT / 'research/ad-catalog.json').read_text())
    by_file = {m['file']: m for m in catalog['modules']}
    rows = inv['apps']
    implemented = sum(bool(row['modules']) for row in rows)
    deferred = sum(row['decision'] == '找到方案但暂缓采用' for row in rows)
    generic = len(rows) - implemented - deferred
    out = ['# 图片 App 名称与逐款去广告调查', '',
           f'核对日期：{inv["checked_at"]}（北京时间）。共 **{len(rows)} 个可见名称**；其中 **{implemented} 款有本地专项文件**，{deferred}款找到方案但暂缓，其余{generic}款保留通用规则。专项文件存在不等于实际广告已去除。', '',
           inv['extraction'], '', '“隐藏的 App”是系统入口，未推测其中内容。点点、Fantopia、换机助手、鼾声分析器、钱迹、遥控器等名称不足以唯一定位开发者，未强行套用近似名称规则。', '',
           '## 调查依据与边界', '', inv['limits'], '',
           '本轮直接读取固定版本的公开源码、模块与许可，并核对主要仓库HEAD；不是只读项目介绍。检索范围：', '']
    out += ['- ' + item for item in inv['search_scope']]
    out += ['', '来源与文件哈希见 [ad-catalog.json](../research/ad-catalog.json) 和 [sources.lock.json](../research/sources.lock.json)。源文件2024/2025年的日期不因仓库2026年仍有提交就变成已验证有效。原生Stash格式参考能支持实现选择，仍不替代当前官方文档和手机实测。', '',
            '## 完整清单', '',
            '“通用”指域名规则可能拦第三方广告SDK，不表示已确认这个App使用该SDK；没有专项的条目也经过逐款名称检索和范围判断。下表不记录账号、版本、凭据或截图。', '',
            '| 序号 | 图片名称 | 本地处理 | 范围、依据或暂缓原因 |', '|---|---|---|---|']
    for row in rows:
        links = '、'.join(f'[{Path(f).stem}](../{f})' for f in row['modules']) or row['decision']
        text = (row['scope'] + '；' + row['reason']) if row['modules'] else row['reason']
        if row['modules']:
            file = row['modules'][0]
            if file in by_file:
                source = catalog['sources'][by_file[file]['source']]
                text += f' 来源：[{source["repository"]}]({source["url"]})，{source["license"]}。'
            else: text += ' 来源与许可见[既有专项说明](APP-SPLASH.md)及[来源记录](SOURCES.md)。'
        elif row['public_source_matches']:
            match = row['public_source_matches'][0]
            source = catalog['sources']['fmz-rewrite']
            url = f'https://github.com/{source["repository"]}/blob/{source["revision"]}/{source["path"]}#L{match["line"]}'
            text += f' [公开合集对应段落]({url})（GPL-3.0）。'
        out.append(f'| {row["index"]} | {row["name"]} | {links} | {text.replace(chr(124), "／")} |')
    out += ['', '## 如何使用这些结果', '',
            '不用继续从零报一遍名称。已有这份清单，后续沿用原模块路径更新；如有漏广告，只需说明App名、广告位置、App版本和现象。不要发送抓包、登录信息或带私人参数的完整URL。', '',
            '先按[模块目录](AD-MODULES.md)逐个导入自己需要的专项；不是把135款App都进行MITM。不需要专项的系统工具不添加空模块。自动签到继续暂停，这份图片清单不会扩大签到范围。', '']

    mods = sorted((ROOT / 'modules/ads').glob('*.stoverride'))
    parsed = [yaml.safe_load(p.read_text()) for p in mods]
    scripts = sum(len(m.get('http', {}).get('script', [])) for m in parsed)
    rewrites = sum(len(m.get('http', {}).get('rewrite', [])) for m in parsed)
    hosts = sorted({h for m in parsed for h in m.get('http', {}).get('mitm', [])})
    out2 = ['# 广告专项模块目录与开关', '',
            f'当前共{len(mods)}个独立覆写：{len(mods)-1}个App专项（含前轮贴吧，不在本次图片内），另有1个扩展域名包。图中{len(rows)}款中{implemented}款有专项文件。全部是**候选实现、待设备实测**。本页逐款文件用于按需模式，默认不额外导入。', '',
            '推荐的[一体化订阅入口](SUBSCRIBE.md)已经组装40款专项，不要再叠加本页同款handler。需要逐款开关时改用core分层或本地包基础主配置；原文件和稳定名称持续维护，实际发布检查见[PROGRESS](../PROGRESS.md)。', '',
            '## 添加和关闭', '',
            '1. 先按[README](../README.md)完成主配置、私人订阅和公共分流。',
            '2. 在下表找App，复制“远程覆写地址”，在Stash覆写管理中添加并关联主配置。先只启用一款。',
            '3. “需MITM=是”时，按[证书教程](ADBLOCKING.md)在自己设备生成并信任CA；只使用该行列出的精确主机。域名级解密能看到同主机其他请求，广告处理本身仍限于表内路径；不愿接受此范围则保持关闭。',
            '4. 重启目标App，分别检查广告和登录/支付/消息/播放/普通领券；原有缓存不会被脚本删除。广告无效、空白等待或业务异常就关闭该覆写并重建连接。',
            '5. “广告拦截→DIRECT”只放行域名规则。要停止HTTP重写或响应脚本，必须关闭对应覆写；域名白名单不能停止它们。关闭域名专项后若扩展包仍含同一主机，也会继续被扩展包阻断。', '',
            f'## 本次新增{len(catalog["modules"])}款', '',
            '2026-10-19修订：16条原本要求空JSON/空200的端点改用Stash请求脚本，分别返回200与`{}`或空正文；微博另有2条。仅匹配来源已明确的广告路径，不伪造订单/权益等业务成功。原生普通拒绝保留14条；联通2条来源为reject-img，仍用普通拒绝，图片返回语义未实现，不声称等价。响应修改脚本仍只改已知结构，异常放行。', '',
            '| App | 仅处理的范围 | 需MITM / 精确主机 | 远程覆写地址 |', '|---|---|---|---|']
    for item in catalog['modules']:
        host_text = '是：' + '、'.join(f'`{h}`' for h in item['mitm']) if item['mitm'] else '否；仅独立广告域名'
        out2.append(f'| {item["app"]} | {item["scope"]} | {host_text} | [{item["id"]}]({RAW+item["file"]}) |')
    out2 += ['', '既有5款：[B站](../modules/ads/bilibili.stoverride)、[贴吧](../modules/ads/tieba.stoverride)、[淘宝](../modules/ads/taobao.stoverride)、[小红书](../modules/ads/xiaohongshu.stoverride)、[微博](../modules/ads/weibo.stoverride)。淘宝/小红书/微博的细节见[原专项说明](APP-SPLASH.md)。[远程扩展域名包](../modules/ads/expanded.stoverride)不需证书，仅在保留基础广告RULE-SET的core分层中替换provider；直接叠加到已展开规则的一体化主配置不能启用扩展包。本地包另有整套有序规则的扩展域名静态覆写。完整关系见[去广告技术总览](AD-ARCHITECTURE.md)。', '',
             '## 与原通用包是否重叠', '',
             '以下按**目标主机**实际匹配现有基本域名/关键词规则；不推断该App全部流量，IP规则没有在此推演。通用包已命中时，专项可能只是提供较小范围/独立入口，并不额外增加一次拦截。基础和扩展二选一；同一请求按首条规则处理。', '',
             '| App | 目标主机 | 基础规则 | 扩展规则 |', '|---|---|---|---|']
    from validate import matches
    basic = yaml.safe_load((ROOT / 'rules/ads-basic.yaml').read_text())['payload']
    expanded = yaml.safe_load((ROOT / 'rules/vendor/ads-expanded.yaml').read_text())['payload']
    for item in catalog['modules']:
        targets = sorted(set(item['mitm'] + item['domains']))
        for host in targets:
            a = [rule for rule in basic if matches(rule,host)]
            b = [rule for rule in expanded if matches(rule,host)]
            out2.append(f'| {item["app"]} | `{host}` | '+('有命中' if a else '未命中')+' | '+('有命中：`'+b[0]+'`' if b else '未命中')+' |')
    out2 += ['', '这张表也解释了为什么通用包不能代替所有App专项：共享业务网关若整域拦截会伤到正常功能，而路径处理只选广告端点。反过来，已被扩展包阻断的独立广告域名不必再叠加同一作用模块。', '',
             '## 合并、优先级与验收', '',
             f'基础{len(basic)}条、扩展{len(expanded):,}条。全部模块合并预期有 **{scripts}条脚本handler（18请求/10响应）、{rewrites}条HTTP拒绝重写、{len(hosts)}个去重后的精确MITM主机**。这些计数不代表实测有效；不同模块共享主机可能在原生预览重复出现，不同路径互不重叠。当前官方数组合并语义仍待复核，必须确认没有只保留最后一款。', '',
             '离线验证覆盖每个单模块、全部模块的正序/反序、每个有序模块对和所有端点的正反例；检查没有跨App业务URL误匹配。它不能证明HTTP/3、证书固定、私有协议、原生合并或当前App版本可用。', '',
             '模块内部规则已去重；跨模块共享MITM域名是独立启停带来的重复声明，不重复运行同一路径handler。不要安装另一整包重写与这些端点竞争；未知第三方模块优先级不在项目验证范围。', '',
             '## 更新和维护', '',
             '新增模块从人工审核的 `research/ad-catalog.json` 生成；修改原条目后运行 `python tools/generate_ad_modules.py --write`，再运行 `python tools/validate.py`。不要直接编辑生成文件造成下次回写丢失。清单文字由 `python tools/render_app_research.py --write` 同步。旧5款保持原路径维护。', '',
             '新增/调整端点前重读源代码、许可、正常权益影响和设备反馈；固定SHA更新，保留脚本失败放行和无外联约束。公共更新不改设备私人订阅；覆写手动刷新、provider间隔更新等区别见[更新教程](UPDATES.md)。', '']
    return {'docs/APP-INVENTORY.md':'\n'.join(out), 'docs/AD-MODULES.md':'\n'.join(out2)}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write', action='store_true')
    args = parser.parse_args()
    drift = []
    for name, body in render().items():
        p = ROOT / name
        if not p.is_file() or p.read_text() != body:
            drift.append(name)
            if args.write: p.write_text(body)
    print(f'{len(drift)} research documents ' + ('written' if args.write else 'differ'))
    return 0 if args.write or not drift else 1

if __name__ == '__main__': raise SystemExit(main())
