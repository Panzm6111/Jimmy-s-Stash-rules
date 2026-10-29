# 社区规则接入与维护

> 2026-10-29简化更新：当前每端17份规则直订上游，6份必要转换迁到GitHub，每天北京时间12:17计划运行。旧电脑每日任务已在云端验证后禁用，并按用户要求移除登记，XML备份保留（2026-10-29）。下文的输入数量和Windows维护步骤包含历史阶段，当前入口与逐项分工以[更新说明](UPDATES.md)和[PROGRESS](../PROGRESS.md)为准。Adobe官网补充仍是需审查的固定事实快照。

2026-10-29按已确认需求，从手工补域名转为接入持续维护的完整分类。当前Stash20个远程规则集、Clash自动入口18个；共享20个业务策略组和8个测速池，Clash另加1个隐藏下载回退组。保留既有地区、应用及私人机场接入。Stash的HTTP改写和脚本保持现状，Clash继续只采用域名广告层。

## 本次国内应用改善（2026-10-29）

新增MetaCubeX完整cn（110177条）及eastmoney（8条）分类，固定数据提交74246501fd12b938b73482f406a6163d1e4a460f；cn文件最新提交为2026-10-29 01:56:58 UTC。对照blackmatrix7 ChinaMaxNoIP同期110178条，覆盖接近；选择已接入的MetaCubeX维护链，复用GPL-3.0许可、哈希和异常差量保护，不并列堆叠两套高度重复大集合。

旧国内集合3721条，虽然包含eastmoney.com和dfcfw.com，但缺少部分相关服务；旧Stash广告集合还会拦截push2.eastmoney.com。新国内集合放在通用海外之前；东方财富保护集放在明确App广告规则之后、大广告集合之前。旧china.yaml保留兼容，现行国内provider改指向china-direct-community.yaml。原20业务策略组和HTTP实现保留。

更新后Stash20个规则集，Clash自动入口18个；社区源共13份（MetaCubeX12份、Sukka1份），全部纳入原每日维护工具。完整上游集合只作机械转换，不手写国内域名补丁。[当前客户端操作](CLASH-VERGE.md)。

## 已采用来源

### 2026-10-29复核结论

已读取仓库状态、实际采用文件的最新提交以及公开源内容。三家主要规则库均未归档或禁用：blackmatrix7最近提交为北京时间10月28日，MetaCubeX生成分支为10月28日，Sukka最近提交为10月29日，AI源文件最后修改于10月12日。MetaCubeX主分支六月的提交是构建代码，不代表生成规则停更。

发现blackmatrix7的AdvertisingLite实际文件最后修改于2025-12-21；当前Clash新自动订阅改用MetaCubeX完整`category-ads`（844条，10月28日生成）。其v2fly分类入口9月22日有更新，并继续引用社区维护的服务广告子分类；没有把生成日期等同于每个域名最近修改日期。选择范围较窄的category-ads，未选连广告商业务域名也包含的category-ads-all。不再叠加本项目Stash的App广告域名和HTTP路径例外。去广告强度与旧38066条快照不同，符合基础域名去广告要求，广告和跟踪在上游分类中并不完全可分。

Netflix/YouTube/Instagram/GitHub等部分文件较久未修改；单凭时间不足以判定失效。现有媒体IP分流和应用策略保留，海外社交、通用海外与AI由活跃完整社区集补充。没有用仅含域名的新集合静默替换含IP的旧集合。Stash专项来源app2smile更新较少，fmz仍活跃且存在1项需人工审查变化；本轮没有真机失败新证据，不替换HTTP实现，也不宣布Stash广告效果已完善。

逐文件日期、完整提交及来源决策见[source-health-review-20261029.json](../research/source-health-review-20261029.json)。新Clash广告源单独输出`rules/vendor/clash-ads-community.yaml`，进入既有许可/哈希/差量/隔离测试维护链；Stash及旧兼容入口的规则字节不受此次选择影响。

| 来源 | 完整采用范围 | 维护与许可 |
|---|---|---|
| [blackmatrix7/ios_rule_script](https://github.com/blackmatrix7/ios_rule_script) | Netflix、YouTube、Telegram、国内、扩展广告、TikTok、Instagram、Twitter，新增整份Apple、Microsoft、GitHub；原基础广告SDK兼容子集仍保留 | 12份规则输入，固定提交与SHA256见 [sources.lock.json](../research/sources.lock.json)；GPL-2.0 |
| [MetaCubeX/meta-rules-dat](https://github.com/MetaCubeX/meta-rules-dat) | TikTok功能与广告独立分类；AI；海外社交、Discord、WhatsApp、LINE、Signal；通用海外域名 | 12份完整domain YAML（含Clash基础广告、国内与东方财富）；跟踪生成数据的 `meta` 分支，许可独立跟踪 `master`；[GPL-3.0原文](../licenses/MetaCubeX-GPL-3.0.txt) |
| [SukkaW/Surge](https://github.com/SukkaW/Surge) | 完整AI源的可通用域名规则，与MetaCubeX去重合并 | 1份源；[AGPL-3.0原文](../licenses/SukkaW-AGPL-3.0.txt)，保留归属和对应源代码 |

完整接入是集合层面的采用：不再人工挑选其中哪些域名属于某个服务。转换仅处理 `+.` 到 `DOMAIN-SUFFIX`、精确域名到 `DOMAIN`、重复项合并及明确不兼容的规则类型。Apple/Microsoft/GitHub源中的进程匹配不适合两端通用规则集，按既有基本类型过滤器记录遗漏；Sukka的一条URL正则明确未采用。现行完整清单、两份聚合关系、遗漏及每份输入/输出哈希见 [community-sources.json](../research/community-sources.json)。

当前AI聚合231条，社交聚合694条，通用海外27,271条；这些数量是当前快照，会随维护源更新。MetaCubeX的域名分类也来自v2fly/domain-list-community等维护体系，不能把两个发布地址当作完全独立的数据证据。

## TikTok规则优先级（原接入阶段，国内顺序以本次改善为准）

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

后续融合：该v3方案现已正式纳入[config/clash-verge-merge.yaml](../config/clash-verge-merge.yaml)及build_clash.py，生成、校验和每日发布共用原维护链；本机临时版本保留为历史交付，不再作为当前维护源。[当前使用教程](CLASH-VERGE.md#保留原机场订阅全局merge)。
