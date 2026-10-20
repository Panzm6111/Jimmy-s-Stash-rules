# 来源、许可证与维护

核实日期 2026-10-20。未运行第三方签到代码；已读取的文件、完整 Git SHA、内容 SHA256 与仓库最新提交时间分别见 [projects.json](../research/projects.json) 和 [sources.lock.json](../research/sources.lock.json)。仓库有新提交不证明每个旧脚本仍然有效。

## 实际复用内容

| 来源 | 许可 | 本项目使用 | 维护/兼容证据 |
|---|---|---|---|
| [blackmatrix7/ios_rule_script](https://github.com/blackmatrix7/ios_rule_script) @ `7dd06b44f5093dd5404e1e5f3bca5452d97146ef` | GPL-2.0，原文 [licenses/blackmatrix7-GPL-2.0.txt](../licenses/blackmatrix7-GPL-2.0.txt) | Netflix、YouTube、Telegram、China 和 AdvertisingLite 数据。只转为 native 基本 classical 规则，不导入 Clash 配置/内核专用功能 | 仓库最后提交 2026-10-18 北京时间；各数据文件头的更新时间更早。全量读取后发现部分同名 `.yaml` 是拆分片段，优先使用 Classical；去掉 PROCESS-NAME/IP-ASN 等未核实项；精确遗漏列表在 lock 中 |
| [app2smile/rules](https://github.com/app2smile/rules) @ `df6366a7024e0b3f0aa3510c5b791eea6f3cba89` | MIT，原文 [licenses/app2smile-MIT.txt](../licenses/app2smile-MIT.txt) | 修改 `bilibili-json.js` 和 `tieba-json.js` 的明确广告处理；保留归属，自己保存无外联的缩小脚本 | 实际存在 `module/bilibili.stoverride`、`module/tieba.stoverride` 原生配置，含 HTTP/MITM/script-providers 字段。仓库提交 2026-03-04，不等于 JSON 处理在当前 App 实测有效 |
| [v2fly/domain-list-community](https://github.com/v2fly/domain-list-community) @ `6ee52f2c36634aeabeb9c4ba486ca02cd84c3d4f` | MIT，原文 [licenses/v2fly-domain-list-community-MIT.txt](../licenses/v2fly-domain-list-community-MIT.txt) | 人工精选15个源文件的海外AI专用域名，转为DOMAIN/DOMAIN-SUFFIX，保留 `rules/openai.yaml` 原地址；加1条本项目既有专用主机 | 提交日期2026-10-19；实际文件及许可证已读取，SHA256、所选/剔除项见[AI来源清单](../research/ai-sources.json)。不直接导入其整套配置或把 `!cn` 分类视为非中国厂商证明；123条规则、25类服务均未做账号解锁实测 |
| 项目原创配置、教程、验证工具 | [MIT](../LICENSE) | 稳定路径、分层私人配置、较窄的Apple/Microsoft域名表、测试与工具 | 普通 YAML/脚本模型通过不等于 Stash 内核验收；完整能力限制另列 |

上游原始规则以公开源码形式可取得；锁文件记录每个来源路径及 SHA，刷新脚本就是本项目转换流程。修改后的广告脚本保留 MIT 归属与修改说明。第三方数据仍保持其原许可，不用根 MIT 重新授权。没有复制未明确授权的广告/签到包。

本项目把规则数据复用与配置兼容分开：读取某目录名为 Clash 的**规则数据**，转换为可审计的基本规则类型，不等于套用 Clash Meta 配置。没有执行 Mihomo/Surge/QX 来冒充 Stash 验证。

## 更新策略

设备每天请求的是**本仓库快照**；不在手机自动执行上游最新未知代码。上游提交改变不会自动进入本仓库，维护者应先审查差异，再明确更新固定 SHA。

```sh
# 将 FULL_REVIEWED_COMMIT 换成已审查的上游完整 40 位 commit：
python tools/refresh_rules.py --revision FULL_REVIEWED_COMMIT
# 预览通过并审核差异后才加 --write：
python tools/refresh_rules.py --revision FULL_REVIEWED_COMMIT --write
python tools/validate.py
python tools/audit_remote.py upstream
```

TLS 与已有源内容校验保持开启。刷新同一 SHA 必须匹配原校验值；新 SHA 的许可变化必须先人工审查，不能关闭 TLS 或改预期 checksum 让不匹配的数据通过。刷新只改公共快照/锁文件，不接触私人设备配置；更新后需同步本页核实日期、设备行为与 PROGRESS。

广告脚本不自动拉取上游最新源码：上游广泛修改和日志可能影响隐私/正常功能，须重新阅读代码、更新归属和测试后再替换本项目原路径。

海外AI规则独立记录于 `research/ai-sources.json`，不由 `refresh_rules.py` 全量刷新。维护者先审阅新的源提交、许可及专用域名，再更新清单的选取/剔除项与哈希，运行 `python tools/generate_ai_rules.py --source-dir /可信的上游源码路径 --write`、`python tools/build_subscription.py --write` 与项目验证。该工具可离线逐字校验上游文件、重现规则，不下载私人订阅；手机端不需要执行。范围和共享登录限制见[AI-COVERAGE](AI-COVERAGE.md)。

## 调查但未复用

24 平台的项目、许可、维护、实际代码和适配判断详见 [签到调查](CHECKIN-RESEARCH.md)。其中没有许可证的项目只用于发现实现线索，不复制脚本；Android Auto.js 不能当 Stash JS；Python/Node.js 需明确改写不能直接导入。外部签名/推送服务、抽奖/分享/购买/兑换等均不作为默认功能。

## 官方来源

Stash 官方文档入口：https://stash.wiki/ 。当前访问受云网络 CONNECT 403 阻塞；没有假称读过最新正文，也不编造最低版本号。已有原生公开模块仅作为辅助证据。具体未核实清单见 [STASH-CAPABILITIES.md](STASH-CAPABILITIES.md)。

## 当前广告来源与修改（AD-20261020.1）

| 来源与固定版本 | 许可、实际读取与取用 | 当前边界 |
|---|---|---|
| [fmz200/wool_scripts](https://github.com/fmz200/wool_scripts) @ `5d5f63fcf98bc69d5f8f1b1bae6f86a01ee4bb97` | [GPL-3.0-only原文](../licenses/fmz200-GPL-3.0.txt)；`rewrite.snippet`、`weibo.snippet`、`myBlockAds.js`、小红书、阿里云盘、菜鸟、京东、微博JS已读；当前源文件日期与行号/哈希在[修复证据](../research/ad-repair-evidence.json) | 手工审查并适配，不整包导入QX。补充明确广告端点/字段/素材；没有复制微博第三方launch整包或小红书水印/下载/画质/用户改写/完整正文日志 |
| blackmatrix7/ios_rule_script，版本见上表 | GPL-2.0；京东/美团仅提取启动已知字段；旧原生Advertising文件只作历史格式参考，另读AdvertisingScript中的`argument`声明并锁定哈希 | 当前改用用户提供官方调查中的url-rewrite；不把历史rewrite证明成当前别名。京东fmz平铺结构只作事实线索，未把其整包GPL3代码混入GPL2脚本 |
| [NobyDa/Script](https://github.com/NobyDa/Script) @ `0b8d083d444f4476700cb9d5d059c07b42da85eb` | [GPL-3.0-only原文](../licenses/NobyDa-GPL-3.0.txt)；公众号getappmsgad广告数组与数量分支，保留appid | 仅文章广告，不含聊天/朋友圈/视频号。原生IPA-Installer模块及调用方式仅作历史API阅读，不复制/运行安装器功能 |
| app2smile/rules，版本见上表 | MIT；B站/贴吧原分支继续保留，使用本项目共同运行保护模板 | B站protobuf未实现；不因存在Stash模块便认定当前广告全部有效 |
| 项目原创运行模板、诊断工具 | MIT原创部分；派生运行JS仍按各自MIT/GPL2/GPL3归属，完整可读转换源在`tools/ad_transforms` | 11个响应JS各自独立构建，另有默认关闭的只读probe。不捕获Cookie、不外联、不写账号存储 |

基础38条与扩展38,066条仍来自同一固定AdvertisingLite Classical快照，不增加数量冒充效果。原主入口保留广告RULE-SET，expanded现在有实际引用；局域网、关键系统服务与私人精确白名单优先。所有原40款范围保留，具体匹配和通用规则重叠见[模块目录](AD-MODULES.md)。

2026-10-20另查HEAD：fmz200和app2smile仍等于所用固定提交；blackmatrix7推进至`f9e403a75bbc4bee939c6d8dd766cf78f1b512f3`，但本轮用到的startup.js、AdvertisingScript原生声明、AdvertisingLite Classical三个文件与固定版本逐字相同，保留原已审查快照。维护状态证据在ad-repair-evidence.json。

本轮45/45个锁定公开来源HTTP200且哈希一致（含未改动AI来源）；这只证明这些文件可获取和版本一致，不证明上游每个旧接口仍有效。没有请求真实账号业务接口，没有保存私人订阅响应或生产抓包。上游提交日期/文件头日期都不等于最新版App测试成功。当前独立官方正文复核仍被网络403阻断，最小版本未编造；用户提供的当前官方调查与本地证据明确分开记录。

原固定空JSON/空正文的共享request脚本已删除，微博两条开屏也用原生reject-dict，联通两条恢复reject-img；不再把QX动作未经核实挪入旧rewrite字段。Mock评估后本轮不需要：已有原生固定空结果可表达，条件性响应处理仍保留JS。原生字段采用用户提供的当前官方能力清单，手机返回类型/业务回退仍需验收。

本地包只改变承载：分流保留优先级展开，11份独立广告JS用`script-providers.content`内嵌，probe在独立临时诊断文件中。content历史原生参考已停止维护，本项目没有复制其中无许可代码，也不把它当最低版本证明。ZIP包含来源、许可证和可读源；整包广告增强仅总开关，与单App模式互斥。

调查但未复用：[Maasea/sgmodule](https://github.com/Maasea/sgmodule) @ `65075cdb388fc5e3094afd7e7314c67b243f3525`（Apache-2.0）的YouTube方案含二进制、请求/响应配套及其他功能，本轮没有复制。Spotify等修改会员权限的方案不纳入。`Muldec/stash-wiki`实际是另一媒体库产品，不作为iPhone Stash官方资料。没有许可、混淆且未审清或影响正常权益的代码不盲目复制。

## 广告构建与证据同步

`research/ad-catalog.json`是35个生成模块的源数据；原5款模块在原路径维护。`tools/ad_transforms`保存11份有归属的广告转换源，`build_ad_scripts.py`生成同名稳定JS，`build_ad_diagnostics.py`生成只读probe。`build_subscription.py`构建原公共入口，`build_local_bundle.py`构建同逻辑本地包。详细规格的真实声明/完整JS附录由`render_ad_architecture.py`生成，避免文档再次保留旧代码。

维护者执行`python tools/build_ads.py --write --bundle`重建，再运行`python tools/validate.py`及私人配置回归。输出哈希由构建同步，**不改变上游固定SHA或源哈希**；升级来源仍须先审查许可、实际代码与业务影响。不能为通过审计修改源校验值或关闭TLS。真实手机验收单独记录，当前均未完成。
