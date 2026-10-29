# Clash Verge 使用方法

本轮两端同步：原“日本+美国”改为日本、美国、新加坡、台湾四地区 `ai`，带前缀入口为 `Jimmy · ai`，30分钟HTTPS测速选优。11个业务select组可选，各自原默认项不变，国家池/自动池/隐藏下载回退组不引用ai。主订阅刷新取得新结构；旧本地Merge/扩展脚本须换成同路径新版。曾选旧组名的位置需核对并重选ai，保留私人机场、DNS和其他个人设置。

推荐完整自动订阅：规则、策略组和规则顺序都随主订阅更新。原21个业务组保留，另有1个隐藏的订阅更新回退组；19个规则集，基础域名去广告，不执行Stash的HTTP改写和脚本。

## 完整自动订阅（推荐）

```text
https://raw.githubusercontent.com/Panzm6111/Jimmy-s-Stash-rules/main/config/clash-verge-auto.yaml
```

### 已使用“Jimmy 全自动”的本机升级

1. 保留可用配置作为备份。在“Jimmy 全自动 → 编辑扩展配置”中，只删除机场provider下旧的 `proxy: Jimmy · 手动节点` 行（旧版若写DIRECT也删除）；私人URL、payload节点后备和DNS保留。公开配置会指定自动回退组，不再把出口固定在本机。
2. 更新“Jimmy 全自动”主订阅并应用。用户自行控制这一步，以免切换影响正在进行的工作。旧全局Merge保持 `{}`。
3. 在“编辑信息”中开启自动更新，将间隔改为 **1440分钟（24小时）**。这个值是客户端定时器，不能靠YAML注释自动修改已有卡片。
4. 在“代理集”刷新“机场”，确认最近更新时间。原21个业务组、19份规则仍在；新增下载组使用隐藏提示，具体是否显示由客户端界面决定。无需再为订阅更新固定选择“日本 B”。

首次接入：导入公开URL，并在新卡片的私人Merge填入原机场URL。如机场必须经代理才能下载，先使用已有机场卡片的节点生成本机启动后备：

```text
python -X utf8 tools/prepare_clash_bootstrap.py --airport <原机场本地YAML> --merge <私人Merge> --output <新的本地私人文件>
```

输出含节点凭据，只保存在本机；不能上传到GitHub或在线转换网站。工具保留私人URL、节点及个人设置，移除旧生成器固定的下载代理，让公开订阅控制下载策略。私人Merge不保存rules、proxy-groups或rule-providers的公开结构快照。

| 内容 | 自动更新方式 |
|---|---|
| 机场节点 | HTTP代理集每86400秒尝试更新，经过“Jimmy · 订阅更新”自动回退组 |
| 下载出口 | 机场provider每300秒主动健康检查；当前出口不可用时按顺序选择可用节点，独立于AI/TikTok和手动组 |
| 19份规则正文 | 每86400秒尝试更新 |
| 策略组、规则顺序、规则集声明和公开默认配置 | Clash Verge主订阅每1440分钟重新下载和应用 |
| GitHub公开上游同步 | 原Windows每天12点任务；真实变化且验证通过才提交推送 |

本机payload与缓存用于无网/首次启动兜底，后续仍从机场订阅更新节点。全部出口失效、机场URL过期或机场服务器故障时，不能保证取得新节点；保留最后有效节点，网络/出口恢复后继续尝试。健康检查证明一般连接可用，不保证每个出口都能访问所有网站。

## 国内应用直连

两端采用MetaCubeX完整 `cn` 集（当前110177条），国内域名优先于通用海外分类；Apple/Microsoft/GitHub、AI和明确海外媒体等业务策略继续保留。GEOIP仍作为后备，避免污染的CN解析结果盖过已知海外域名。

东方财富整份维护集另作保护：在Stash明确的App广告域名之后、大广告集合之前直连，修复 `push2.eastmoney.com` 被旧广告集合拦截的问题。Clash使用同一保护集。其余国内常见App通过完整cn分类直连，不本地编写域名白名单。属于已知域名分流修正，不代表已经完成每个App的真机性能验收。

## 验证与恢复

[原生自动回退测试](../tools/validate_clash_download_native.py)覆盖冷启动、首个节点失效、定时更新经备用节点成功、节点增删及全部节点失败后恢复；没有调用手动选节点或手动刷新API，测试使用缩短的定时间隔。真实物理WLAN隔离测试也通过自动选择出口刷新59条节点（过滤1个提示项），最终19份规则原生加载成功。

[完整结构测试](../tools/validate_clash_auto_native.py)覆盖19项结构/后备/更新检查。2026-10-29已按用户最新授权完成本机迁移：实际机场重新下载成功59节点，19份规则加载，1440分钟自动更新开启；下一次定时触发和实际App体验仍待验收。状态和证据见[PROGRESS](../PROGRESS.md)。恢复时切回原机场卡片，并按需恢复原全局Merge备份。

机制依据：[Mihomo自动回退](https://wiki.metacubex.one/config/proxy-groups/fallback/)、[代理组检查参数](https://wiki.metacubex.one/config/proxy-groups/)、[机场payload后备](https://wiki.metacubex.one/config/proxy-providers/)、[Clash扩展合并](https://www.clashverge.dev/guide/extend.html)。

## 保留原机场订阅：全局Merge

本节为旧兼容方案，结构仍需手动更新；新用户和希望全部自动更新的用户使用上面的完整自动订阅。

正式文件：[config/clash-verge-merge.yaml](../config/clash-verge-merge.yaml)。它已将侧对话v3方案纳入生成器和每日维护，不再依赖.local临时文件。

```text
https://raw.githubusercontent.com/Panzm6111/Jimmy-s-Stash-rules/main/config/clash-verge-merge.yaml
```

1. 保持原机场订阅为当前订阅，在其编辑信息中开启自动更新（建议1440分钟）。已有机场URL不需要重新填写。
2. 备份“全局扩展覆写配置 / 全局扩展配置 / Merge”中的原内容，再全文换入上面文件。停用重复覆盖Jimmy规则/策略组的旧扩展脚本或订阅扩展；如原全局覆写还有你自己的设置，先保留备份并合并这些设置。
3. 保存，使用规则模式，刷新规则集。`Jimmy · 总代理`初始为自动节点；`Jimmy · 海外AI`和`Jimmy · TikTok`默认美国，可改为具体节点。11个业务select组提供`Jimmy · ai`选项，原默认项保留。

这份覆写只写入rules、proxy-groups、rule-providers，保留原机场节点、代理集、DNS、TUN和端口设置。20个组统一加`Jimmy · `前缀，避免“台湾/美国/日本/TikTok”等机场节点重名。include-all包含当前订阅的节点和代理集；空地区使用REJECT，规则集通过`Jimmy · 自动节点`下载。

机场更新并重新应用配置后，节点增删会进入这些组；20个规则集内容按86400秒尝试更新。**组结构和规则顺序属于本地覆写快照**，本仓库生成器和每日维护会生成/发布新版文件，但客户端需要换入新版才能得到结构变化。固定下载URL不能让已经粘贴的本地覆写自动替换自身。

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
5. 使用“规则”模式，首次将“总代理”从REJECT改为所需地区或自动节点。“海外AI”可选美国、日本、ai或具体节点；TikTok组统一管理TikTok/Instagram/X，默认美国。

日常无需再次复制代码：21个远程规则集按86400秒尝试更新，机场代理集按自身间隔更新。主配置的自动更新用于取得策略组、匹配顺序、DNS及provider声明等结构变化。客户端关闭、断网或下载失败会影响更新，不能保证每天固定时刻成功。

## 更新链路与能力边界

| 内容 | 更新入口 |
|---|---|
| AI、社交、Netflix/YouTube/Telegram、Apple/Microsoft、国内分流、全部域名广告和例外 | 20个HTTP rule-providers，各自24小时尝试刷新；每个有独立缓存路径 |
| 策略组结构、国家组合、规则集顺序、DNS、provider声明 | 上方远程主配置订阅的自动更新；不由机场节点刷新替代 |
| 机场节点 | 本机私人机场proxy-provider；URL更换时需本人修改本机覆写 |
| Stash HTTP改写/响应JS/自检 | Clash不执行；Stash用自己的主配置及script-providers更新 |

扩展脚本不能直接执行网络/文件IO，复制到本机的脚本不会因为刷新机场订阅而更新自身。上方全局Merge与旧脚本均需手动换入新版结构；选择完整远程主配置并开启自动更新时，结构由主订阅取得。

## 原机场扩展脚本：兼容方式

[config/clash-verge.js](../config/clash-verge.js)仍保留，供必须在原机场订阅上转换的用户使用。**需先复制一次新版脚本**：新版不再展开规则正文，改为引用21个远程规则集，所以规则集内容之后可以自动刷新。但这个本地脚本里的策略组、provider清单和顺序仍是固定版本；将来结构变更时需重新复制脚本。它不能替代完整远程主配置的结构更新。

如节点名与本项目策略组冲突，转换会明确停止，不静默丢节点。其他全局/订阅扩展可能再次覆盖规则，应检查最终生效配置。

## 恢复与验证

切回原机场订阅可恢复原用法；将广告拦截切DIRECT可对照域名误伤。日常保留能用的私人配置备份。真实节点连通、TikTok地区可用性、AI解锁和实际广告效果仍需设备验证。

2026-10-29已在独立Mihomo v1.19.32进程验证全部19个HTTP规则集，AI测试条目数由231变为232，主配置不重载、策略组保持；规则加载测试仅使用虚构节点，不修改系统代理。当前接入维护中的完整社区分类，来源与顺序见[社区规则说明](COMMUNITY-SOURCES.md)。

正式Merge另有20项独立原生模拟验证：同名节点、原节点/provider保留、地区筛选、空池拒绝、规则下载代理、节点更新与规则无重载刷新。复现工具为[validate_clash_merge_native.py](../tools/validate_clash_merge_native.py)，需显式提供本机Mihomo和公开Country.mmdb路径；只建立本机临时测试服务，不下载依赖或修改现用Clash。原生模拟仍不代表真实机场、Clash界面导入或TikTok播放已验收。

依据：[Clash扩展规则](https://www.clashverge.dev/guide/extend.html)、[脚本能力](https://www.clashverge.dev/guide/script.html)、[订阅响应头](https://www.clashverge.dev/guide/url_schemes.html)、[Mihomo远程规则集](https://wiki.metacubex.one/config/rule-providers/)。进度与发布结果见[PROGRESS](../PROGRESS.md)。
