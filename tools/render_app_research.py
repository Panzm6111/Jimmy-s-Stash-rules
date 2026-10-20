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
           f'核对日期：{inv["checked_at"]}（北京时间）。共 **{len(rows)} 个可见名称**；其中 **{implemented} 款有专项实现并已纳入整合入口**，{deferred}款找到方案但暂缓，其余{generic}款保留通用规则。这里记录实现范围，实际去广告效果仍待设备验收。', '',
           inv['extraction'], '', '“隐藏的 App”是系统入口，未推测其中内容。点点、Fantopia、换机助手、鼾声分析器、钱迹、遥控器等名称不足以唯一定位开发者，未强行套用近似名称规则。', '',
           '## 调查依据与边界', '', inv['limits'], '',
           '调查时已直接读取固定版本的公开源码、模块与许可，并核对主要仓库HEAD；不是只读项目介绍。本次表述整理没有重新调查接口或扩大实现范围。原检索范围：', '']
    out += ['- ' + item for item in inv['search_scope']]
    out += ['', '来源与文件哈希见 [ad-catalog.json](../research/ad-catalog.json) 和 [sources.lock.json](../research/sources.lock.json)。源文件2024/2025年的日期不因仓库2026年仍有提交就变成已验证有效。原生Stash格式参考能支持实现选择，仍不替代当前官方文档和手机实测。', '',
            '## 完整清单', '',
            '“通用”指域名规则可能拦第三方广告SDK，不表示已确认这个App使用该SDK；没有专项的条目也经过逐款名称检索和范围判断。下表不记录账号、版本、凭据或截图。', '',
            '| 序号 | 图片名称 | 实现来源 / 状态 | 范围、依据或暂缓原因 |', '|---|---|---|---|']
    for row in rows:
        links = '、'.join(f'[{Path(f).stem}](../{f})' for f in row['modules']) or row['decision']
        text = (row['scope'].rstrip('。；') + '；' + row['reason']) if row['modules'] else row['reason']
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
            '日常只使用原[公共订阅入口](SUBSCRIBE.md)，已整合所有已有专项，无需逐个导入；逐App开关已从当前需求中移除。[实现目录](AD-MODULES.md)用于查范围和来源，不是额外安装步骤。仅已审阅的精确主机进入MITM，不是把135款App都进行MITM。自动签到继续暂停。', '']

    mods = sorted((ROOT / 'modules/ads').glob('*.stoverride'))
    parsed = [yaml.safe_load(p.read_text()) for p in mods]
    scripts = sum(len(m.get('http', {}).get('script', [])) for m in parsed)
    rewrites = sum(len(m.get('http', {}).get('url-rewrite', [])) for m in parsed)
    hosts = sorted({h for m in parsed for h in m.get('http', {}).get('mitm', [])})
    out2 = ['# 广告专项实现范围与来源目录', '',
            f'当前保留{len(mods)}份维护源文件：{len(mods)-1}个App专项（含贴吧，不在本次图片内），另有1个扩展域名包。图中{len(rows)}款中{implemented}款有专项实现。已采用的专项全部纳入整合入口，**实际效果待设备实测**。此页用于查实现范围和来源，无需逐款导入。', '',
            '当前需求已统一为[整合入口](SUBSCRIBE.md)，不再要求逐App开关。原config/stash.yaml包含全部40款已有专项、11份内嵌响应JS和扩展域名包引用；刷新主配置即可取得当前处理。已有额外App/广告增强/expanded覆写应停用以免重复，私人订阅覆写继续保留。源文件路径不变，供生成器维护及旧安装兼容使用。', '',
            '## 当前接入约定', '',
            '日常只刷新整合主配置，不把下表链接当作安装清单。HTTP去广告沿用设备上已信任的自建CA；只有首次配置时才按[证书教程](ADBLOCKING.md)安装。域名级解密可涉及同主机其他请求，实际改写仍限于表内路径；不解密支付或银行主域。', '',
            '“广告拦截→DIRECT”只放行域名规则，HTTP/MITM需单独关闭才能暂停HTTPS改写。广告无效或业务异常时，按[恢复与诊断教程](ADBLOCKING.md)处理；当前不提供逐App启停操作。', '',
            '旧main.yaml＋core及单独覆写文件保留用于已有安装兼容，不属于当前日常安装要求，不与整合主配置叠加。', '',
            f'## 目录生成的{len(catalog["modules"])}项实现', '',
            '2026-10-20修订：固定响应使用`http.url-rewrite`原生动作，区分reject、reject-200、reject-dict、reject-img；联通图片语义恢复。共享空响应JS及请求handler已移除。11个响应handler只处理已知广告结构，默认不记录日志；临时在对应handler设置`argument: diagnostic=1`可输出版本和固定状态，排查后恢复0。', '',
            '| App | 仅处理的范围 | 需MITM / 精确主机 | 维护源链接 |', '|---|---|---|---|']
    for item in catalog['modules']:
        host_text = '是：' + '、'.join(f'`{h}`' for h in item['mitm']) if item['mitm'] else '否；仅独立广告域名'
        out2.append(f'| {item["app"]} | {item["scope"]} | {host_text} | [{item["id"]}]({RAW+item["file"]}) |')
    out2 += ['', '另有5项既有实现：[B站](../modules/ads/bilibili.stoverride)、[贴吧](../modules/ads/tieba.stoverride)、[淘宝](../modules/ads/taobao.stoverride)、[小红书](../modules/ads/xiaohongshu.stoverride)、[微博](../modules/ads/weibo.stoverride)，同样已纳入整合入口。淘宝/小红书/微博的细节见[专项范围说明](APP-SPLASH.md)。[扩展域名维护源](../modules/ads/expanded.stoverride)不需证书，整合主配置已默认引用扩展快照，无需额外开启expanded；基础包仅保留给旧分层安装，二者不同时叠加。完整关系见[去广告技术总览](AD-ARCHITECTURE.md)。', '',
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
             f'基础维护快照{len(basic)}条，整合入口默认引用的扩展快照{len(expanded):,}条。全部专项在构建时合并为 **{scripts}条脚本handler（全部响应阶段）、{rewrites}条原生URL重写、{len(hosts)}个去重后的精确MITM主机**。这些计数不代表实测有效。整合入口已在生成时去重MITM主机，原生解析、动作最低版本和实际处理仍待设备验收。', '',
             '离线验证覆盖每个单模块、全部模块的正序/反序、每个有序模块对和所有端点的正反例；检查没有跨App业务URL误匹配。它不能证明HTTP/3、证书固定、私有协议、原生合并或当前App版本可用。', '',
             '各维护源可引用相同MITM主机，整合生成器会去重，不重复挂载同一路径handler。不要再叠加另一整包重写或同款覆写；未知第三方模块优先级不在项目验证范围。', '',
             '## 更新和维护', '',
             '新增模块从人工审核的 `research/ad-catalog.json` 生成；修改原条目后运行 `python tools/generate_ad_modules.py --write`，再运行 `python tools/validate.py`。不要直接编辑生成文件造成下次回写丢失。清单文字由 `python tools/render_app_research.py --write` 同步。旧5款保持原模块路径维护；所有JS由`tools/ad_transforms/`和`tools/build_ad_scripts.py`生成，再构建入口与本地包。', '',
             '新增/调整端点前重读源代码、许可、正常权益影响和设备反馈；固定SHA更新，保留脚本失败放行和无外联约束。公共更新不改设备私人订阅。规则集与机场代理集按现有24小时间隔尝试刷新；建议主配置每周手动刷新一次，发布修复时及时刷新，内嵌JS随主配置更新。间隔并非北京时间固定时刻，也不保证断网更新；完整机制见[更新教程](UPDATES.md)。', '']
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
            if args.write: p.write_text(body, encoding='utf-8', newline='\n')
    print(f'{len(drift)} research documents ' + ('written' if args.write else 'differ'))
    return 0 if args.write or not drift else 1

if __name__ == '__main__': raise SystemExit(main())
