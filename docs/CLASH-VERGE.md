# Clash Verge 使用方法

当前推荐 **完整自动订阅**：规则内容、策略组、规则顺序和规则集声明都从远程更新。保留20个策略组、海外AI的日本+美国池及统一TikTok社交组；仅采用基础域名去广告。旧Merge、旧完整配置和脚本保留兼容，不再作为免维护方案。

## 完整自动订阅（推荐）

```text
https://raw.githubusercontent.com/Panzm6111/Jimmy-s-Stash-rules/main/config/clash-verge-auto.yaml
```

首次迁移一次，之后无需复制Merge：

1. 保留原机场订阅卡片，并备份全局Merge与私人扩展。导入上面的公开URL，命名为“Jimmy 全自动”。
2. 在新卡片的“编辑信息”开启自动更新，间隔 **360分钟**。这是Clash Verge的远程订阅定时器；YAML里的86400不是主订阅的更新开关。
3. 在新卡片的“编辑扩展配置”只保留私人机场和必要的个人设置。最小内容如下；URL仅在本机填写，不能放进GitHub。现有DNS、hosts等自定义设置可以保存在这里，不能复制旧的Jimmy策略组、rules或rule-providers。

```yaml
proxy-providers:
  机场:
    url: "在本机填写原机场的Clash订阅URL"
```

4. 将旧Jimmy全局Merge停用；如果全局Merge只有本项目的三项内容，备份后设为 `{}`。若包含个人设置，仅移除旧Jimmy路由结构。旧订阅扩展脚本也不能重复接管新卡片。激活“Jimmy 全自动”，使用规则模式。
5. 确认20个 `Jimmy · ` 组、17个规则集和机场节点已载入。海外AI/TikTok默认美国；原有可用的具体节点选择可保留或重选。基础广告源为完整MetaCubeX `category-ads`，本轮844条；不带Stash专项脚本、专项广告域名或HTTP路径例外。

| 内容 | 谁自动更新 |
|---|---|
| 策略组、新增组、组内选项、规则顺序、规则集声明及公开默认配置 | Clash Verge每360分钟下载完整远程订阅，并重新应用；私人覆写与应用自身管理的设置优先 |
| 广告、AI、社交与其他分流规则正文 | Mihomo的17个HTTP规则集，每86400秒尝试更新 |
| 机场节点增删与协议参数 | 本机机场proxy-provider，每86400秒尝试更新；从原机场直接获取 |
| 公开上游同步、生成与发布 | 原Windows每天12点任务；有实际变化且验证通过才提交推送 |

客户端关闭、电脑休眠、断网时不能保证准点更新。私人URL变化仍需改本机地址。以后调整本项目策略结构并发布后，客户端下一次主订阅更新就会取得，不能把“自动更新”理解为自动设计新策略。

### 首次启用只有策略组、没有节点

机场URL如果需要代理才能访问，空缓存下的DIRECT下载会失败。此时使用本机已有节点作为启动后备，机场仍通过HTTP订阅自动更新：

1. 保留原机场卡片的已下载配置，备份新卡片私人Merge。用 `tools/prepare_clash_bootstrap.py --airport <原机场本地YAML> --merge <私人Merge> --output <新的本地私人文件>` 生成启动后备；输出包含节点凭据，只保存本机，不能提交或上传。
2. 将输出放入“Jimmy 全自动”的私人扩展配置。工具保留原URL/DNS/hosts，新增provider的payload，下载代理设为 `Jimmy · 手动节点`。公共URL不变。
3. 启用后，在“Jimmy · 手动节点”明确选一次原来可用的节点，再刷新“代理集 → 机场”。初始空组可能保留REJECT，看到节点后仍须完成这次选择。新版自动入口过滤“请勿连接/跳转域名”提示项；它们不是真实节点。正常业务可继续使用各自地区组。
4. 确认刷新成功后，节点继续按86400秒自动更新；公开结构仍每360分钟更新。只有机场URL失效或所有已保存节点都不可用时，需要恢复原机场并重新取得有效接入信息。启动payload只作兜底，不能据此声称远程刷新成功。

2026-10-29物理WLAN隔离测试：DIRECT冷启动0节点；私人后备60节点，选择同一个已可用节点后通过代理刷新60节点成功。私人扩展已写入本机，用户启用并选中有效节点后，实际内核在2026-10-29 10:46:27成功刷新60节点；实际客户端验收见[PROGRESS](../PROGRESS.md)，不能用独立内核结果替代。详见[排查证据](../research/clash-airport-diagnosis-20261029.json)。[Mihomo官方payload与下载代理说明](https://wiki.metacubex.one/config/proxy-providers/)。

恢复：保留新卡片，切回原机场卡片并恢复备份的全局Merge。不要把私人最终配置上传用于排障。

2026-10-29独立Mihomo测试通过19项（含机场请求格式兼容、首次失败后备、提示项过滤和恢复刷新）：完整结构新组/新provider/新顺序生效、私人URL与AI选择保留、机场节点增删、广告集刷新、无效配置拒绝和旧结构恢复。复现入口为[validate_clash_auto_native.py](../tools/validate_clash_auto_native.py)。这组模拟本身不代表Clash界面定时器或真实业务效果通过；本机迁移结果另记[PROGRESS](../PROGRESS.md)。

机制依据：[官方扩展合并顺序](https://www.clashverge.dev/guide/extend.html)、[v2.5.8远程订阅定时器](https://github.com/clash-verge-rev/clash-verge-rev/blob/v2.5.8/src-tauri/src/core/timer.rs)、[更新后重载逻辑](https://github.com/clash-verge-rev/clash-verge-rev/blob/v2.5.8/src-tauri/src/feat/profile.rs)。

## 保留原机场订阅：全局Merge

本节为旧兼容方案，结构仍需手动更新；新用户和希望全部自动更新的用户使用上面的完整自动订阅。

正式文件：[config/clash-verge-merge.yaml](../config/clash-verge-merge.yaml)。它已将侧对话v3方案纳入生成器和每日维护，不再依赖.local临时文件。

```text
https://raw.githubusercontent.com/Panzm6111/Jimmy-s-Stash-rules/main/config/clash-verge-merge.yaml
```

1. 保持原机场订阅为当前订阅，在其编辑信息中开启自动更新（建议1440分钟）。已有机场URL不需要重新填写。
2. 备份“全局扩展覆写配置 / 全局扩展配置 / Merge”中的原内容，再全文换入上面文件。停用重复覆盖Jimmy规则/策略组的旧扩展脚本或订阅扩展；如原全局覆写还有你自己的设置，先保留备份并合并这些设置。
3. 保存，使用规则模式，刷新规则集。`Jimmy · 总代理`初始为自动节点；`Jimmy · 海外AI`和`Jimmy · TikTok`默认美国，可改为具体节点。`Jimmy · 海外AI`保留`Jimmy · 日本+美国`选项。

这份覆写只写入rules、proxy-groups、rule-providers，保留原机场节点、代理集、DNS、TUN和端口设置。20个组统一加`Jimmy · `前缀，避免“台湾/美国/日本/TikTok”等机场节点重名。include-all包含当前订阅的节点和代理集；空地区使用REJECT，规则集通过`Jimmy · 自动节点`下载。

机场更新并重新应用配置后，节点增删会进入这些组；19个规则集内容按86400秒尝试更新。**组结构和规则顺序属于本地覆写快照**，本仓库生成器和每日维护会生成/发布新版文件，但客户端需要换入新版才能得到结构变化。固定下载URL不能让已经粘贴的本地覆写自动替换自身。

恢复时还原备份的全局覆写并重新应用原机场订阅；全局覆写会作用于其他订阅，切换订阅时也应核对。不要同时使用本节Merge和下节完整远程配置接管同一套规则。

## 完整远程配置：另选方式

1. 在“订阅”中从URL导入：

   https://raw.githubusercontent.com/Panzm6111/Jimmy-s-Stash-rules/main/config/clash-verge.yaml

2. 右键这张新订阅卡片，打开“编辑信息”，开启自动更新，将更新间隔设为一天（界面单位为分钟时填1440）。GitHub Raw不提供自定义的profile-update-interval响应头，不能假定导入后默认已启用。
3. 右键这张卡片的“编辑扩展配置”，只在本机填写机场URL：

```yaml
proxy-providers:
  机场:
    url: "在本机粘贴你自己的Clash格式机场订阅URL"
```

4. 保存并激活这张订阅。停用此前给原机场订阅粘贴的Jimmy扩展脚本，避免两套主配置混用；原机场订阅保留作备份。私人URL不写入GitHub。
5. 使用“规则”模式，首次将“总代理”从REJECT改为所需地区或自动节点。“海外AI”可选美国、日本、日本+美国或具体节点；TikTok组统一管理TikTok/Instagram/X，默认美国。

日常无需再次复制代码：19个远程规则集按86400秒尝试更新，机场代理集按自身间隔更新。主配置的自动更新用于取得策略组、匹配顺序、DNS及provider声明等结构变化。客户端关闭、断网或下载失败会影响更新，不能保证每天固定时刻成功。

## 更新链路与能力边界

| 内容 | 更新入口 |
|---|---|
| AI、社交、Netflix/YouTube/Telegram、Apple/Microsoft、国内分流、全部域名广告和例外 | 19个HTTP rule-providers，各自24小时尝试刷新；每个有独立缓存路径 |
| 策略组结构、国家组合、规则集顺序、DNS、provider声明 | 上方远程主配置订阅的自动更新；不由机场节点刷新替代 |
| 机场节点 | 本机私人机场proxy-provider；URL更换时需本人修改本机覆写 |
| Stash HTTP改写/响应JS/自检 | Clash不执行；Stash用自己的主配置及script-providers更新 |

扩展脚本不能直接执行网络/文件IO，复制到本机的脚本不会因为刷新机场订阅而更新自身。上方全局Merge与旧脚本均需手动换入新版结构；选择完整远程主配置并开启自动更新时，结构由主订阅取得。

## 原机场扩展脚本：兼容方式

[config/clash-verge.js](../config/clash-verge.js)仍保留，供必须在原机场订阅上转换的用户使用。**需先复制一次新版脚本**：新版不再展开规则正文，改为引用19个远程规则集，所以规则集内容之后可以自动刷新。但这个本地脚本里的策略组、provider清单和顺序仍是固定版本；将来结构变更时需重新复制脚本。它不能替代完整远程主配置的结构更新。

如节点名与本项目策略组冲突，转换会明确停止，不静默丢节点。其他全局/订阅扩展可能再次覆盖规则，应检查最终生效配置。

## 恢复与验证

切回原机场订阅可恢复原用法；将广告拦截切DIRECT可对照域名误伤。日常保留能用的私人配置备份。真实节点连通、TikTok地区可用性、AI解锁和实际广告效果仍需设备验证。

2026-10-29已在独立Mihomo v1.19.32进程验证全部19个HTTP规则集，AI测试条目数由231变为232，主配置不重载、策略组保持；规则加载测试仅使用虚构节点，不修改系统代理。当前接入维护中的完整社区分类，来源与顺序见[社区规则说明](COMMUNITY-SOURCES.md)。

正式Merge另有20项独立原生模拟验证：同名节点、原节点/provider保留、地区筛选、空池拒绝、规则下载代理、节点更新与规则无重载刷新。复现工具为[validate_clash_merge_native.py](../tools/validate_clash_merge_native.py)，需显式提供本机Mihomo和公开Country.mmdb路径；只建立本机临时测试服务，不下载依赖或修改现用Clash。原生模拟仍不代表真实机场、Clash界面导入或TikTok播放已验收。

依据：[Clash扩展规则](https://www.clashverge.dev/guide/extend.html)、[脚本能力](https://www.clashverge.dev/guide/script.html)、[订阅响应头](https://www.clashverge.dev/guide/url_schemes.html)、[Mihomo远程规则集](https://wiki.metacubex.one/config/rule-providers/)。进度与发布结果见[PROGRESS](../PROGRESS.md)。
