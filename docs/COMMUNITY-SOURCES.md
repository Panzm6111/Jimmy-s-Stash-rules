# 社区规则接入与维护

2026-10-29按已确认需求，从手工补域名转为接入持续维护的完整分类。Stash与Clash共享19个远程规则集、20个策略组和8个测速池；保留既有地区、应用及私人机场接入。Stash的HTTP改写和脚本保持现状，Clash继续只采用域名广告层。

## 已采用来源

| 来源 | 完整采用范围 | 维护与许可 |
|---|---|---|
| [blackmatrix7/ios_rule_script](https://github.com/blackmatrix7/ios_rule_script) | Netflix、YouTube、Telegram、国内、扩展广告、TikTok、Instagram、Twitter，新增整份Apple、Microsoft、GitHub；原基础广告SDK兼容子集仍保留 | 12份规则输入，固定提交与SHA256见 [sources.lock.json](../research/sources.lock.json)；GPL-2.0 |
| [MetaCubeX/meta-rules-dat](https://github.com/MetaCubeX/meta-rules-dat) | TikTok功能与广告独立分类；AI；海外社交、Discord、WhatsApp、LINE、Signal；通用海外域名 | 9份完整domain YAML；跟踪生成数据的 `meta` 分支，许可独立跟踪 `master`；[GPL-3.0原文](../licenses/MetaCubeX-GPL-3.0.txt) |
| [SukkaW/Surge](https://github.com/SukkaW/Surge) | 完整AI源的可通用域名规则，与MetaCubeX去重合并 | 1份源；[AGPL-3.0原文](../licenses/SukkaW-AGPL-3.0.txt)，保留归属和对应源代码 |

完整接入是集合层面的采用：不再人工挑选其中哪些域名属于某个服务。转换仅处理 `+.` 到 `DOMAIN-SUFFIX`、精确域名到 `DOMAIN`、重复项合并及明确不兼容的规则类型。Apple/Microsoft/GitHub源中的进程匹配不适合两端通用规则集，按既有基本类型过滤器记录遗漏；Sukka的一条URL正则明确未采用。现行完整清单、两份聚合关系、遗漏及每份输入/输出哈希见 [community-sources.json](../research/community-sources.json)。

当前AI聚合231条，社交聚合694条，通用海外27,271条；这些数量是当前快照，会随维护源更新。MetaCubeX的域名分类也来自v2fly/domain-list-community等维护体系，不能把两个发布地址当作完全独立的数据证据。

## TikTok规则优先级

核查发现旧版在8个公开上游TikTok主机上漏分流或误拦截。新顺序为：系统/已审查路径例外 → 上游TikTok广告分类 → 上游TikTok功能分类 → 其他广告 → AI → 各平台 → 社交补充 → Apple/GitHub/Microsoft → 通用海外 → 国内/GeoIP/兜底。

`ttcdn-us.com`、`ttlivecdn.com`、`ttoverseaus.net`、`ttwstatic.com`及上游4个 `roovza.*.appsflyersdk.com` 主机由功能分类送入TikTok组，即使DNS结果被模拟为CN也不落入国内兜底；`analytics.tiktok.com`仍由上游广告分类拦截。没有本地新增功能域名白名单。所有平台仍由同一个TikTok组选择出口，Instagram、X、Facebook、Discord、WhatsApp、LINE、Signal等按维护集进入该组，Telegram继续沿用自己的原有组。

这证明修正了可复现的规则问题，不能证明它是手机失败的唯一原因。TikTok可能仍受实际节点IP、账号、设备和地区状态影响；“都选美国”也不保证两组是同一条具体节点。

## 比较但未采用的方案

- [v2fly/domain-list-community](https://github.com/v2fly/domain-list-community)：检查了TikTok和AI原始分类；采用MetaCubeX生成产物避免本地维护另一套include/属性展开引擎。
- [ACL4SSR](https://github.com/ACL4SSR/ACL4SSR)：存在可用分类，但本轮不再叠加另一份重叠的大型媒体分类；保留现有应用策略语义。
- [QuixoticHeart/rule-set](https://github.com/QuixoticHeart/rule-set)：检查了代码、生成分支与README；部分分类共享域范围更广，且README另列发布/使用限制，本轮不引入。

这些是本项目的来源选择，不是对其他项目质量或许可效力的法律判断。没有用star数量代替源内容、更新时间和许可证核查。

## 自动维护与客户端操作

沿用每日12点Windows任务和 [维护工具](MAINTENANCE.md)：当前12份blackmatrix7输入加10份社区输入均可检查、机械适配；完整分类自动同步。许可变化、陌生规则类型、大规模增删、来源完整性失败或测试失败会停止，HTTP/MITM与专项脚本仍需审查。只有注释/发布头变化时不提交。

手机先刷新原Stash主配置，确认 `ROUTE-20261029.1`，再刷新规则集并重连；TikTok组先选与全局成功时相同的具体节点验证。Clash远程配置刷新主订阅和规则集；使用本地扩展脚本或全局Merge时还须换入新版结构，单独更新机场只会更新节点。19集均按86400秒尝试刷新。

本机侧对话交付的 `.local/clash-global-merge-20261029/` v2含18集和 `Jimmy · ` 前缀，属于当时快照；本轮保留它的文件与记录，不把其18集数量当作当前公开19集结构。公开配置、生成脚本与其节点保留测试是本轮交付范围。真实手机与Clash界面导入/业务效果仍待验收。

本轮另存本机Merge v3于 `.local/clash-global-merge-community-v3/`：按当前19集生成并保留 `Jimmy · ` 前缀。独立Mihomo20项模拟验证通过，原v2文件不变。需要全局覆写的本机用户可备份原内容后全文换入v3；没有自动写入正在使用的Clash。
