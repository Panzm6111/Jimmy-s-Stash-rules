# 进度、验证与接续说明

更新时间：2026-10-19（北京时间）。仓库 `Panzm6111/Jimmy-s-Stash-rules`，远程默认分支 `main`，本地分支 `work`。沿用这一套稳定文件，不改变仓库可见性。

## 最新范围

本轮接续：用户要求五个地区之外节点可见，并增加不分国家的全节点大组；同时反馈启动后的DNS证书及连接错误。已增加“全部节点”和“其他地区”，保留旧“手动节点”名称，共18组。其他地区为常见国家正向匹配、手动选择，不是严格补集；未知名仍在全部节点。已提交并实际推送到`main`，本轮代码发布为`5a01d672f298eaf75b100f493c3289c17435ee67`。原固定URL实际HTTP 200、232,532字节；64/64个公共运行资源HTTP 200且哈希与本地一致，报告已更新。

对本轮日志只保留脱敏结论，不保存原日志、设备地址、实际流量数据或凭据：当时有配置启动；出现本项目没有的Google/NCloud、dot.pub及四个fallback DNS，需核对实际生效配置/覆写/界面设置；流量提示被选为节点。不能根据这段运行日志断言Jimmy导入通过，也不能把所有故障归因于主配置。已补充逐步排查，始终保留TLS验证。

平铺节点列表新增常见提示前缀过滤，正则生成器`tools/generate_node_filters.py`只使用锚点、字符类和或分支，不依赖未核实的负向前瞻或exclude-filter。应用于全部节点、旧手动和各软件的平铺列表，不重写订阅、也不按协议删节点；已知前缀外的提示、含国家名的提示仍需手动识别。英国GB简写限于纯GB/GB编号，避免把流量单位当英国。

公开`config/stash.yaml`改用与已读原生Stash模块相同的`script-providers.url/interval`，11份脚本由Stash从本仓库下载，初次需要联网；公共规则仍内嵌。本地离线包保留content方式。此调整减少对历史开发用content模式的依赖，**不声称它是本次日志错误的根因或手机修复证明**。

用户已明确授权发布到当前GitHub仓库，使用订阅链接导入。首次代码发布提交为`376a4317f70f143d9c7d76fd6b72aaaa3d5dedaa`，当时入口为16组、238,463字节、内嵌脚本；现由本轮18组/远程脚本声明替换，固定路径不变。最新发布证据见`research/subscription-published.json`、`research/published-audit.json`。

[订阅导入教程](docs/SUBSCRIBE.md)：一份文件含原分流、基础广告、40款专项与11份JS声明，不再要求逐项添加公共覆写。机场URL保存在设备本地私人覆写，不放入远程主配置。

[手机简明教程](docs/QUICKSTART.md)优先指向订阅入口。本地包和原分层方式保留为可选方式，由同一套源文件生成；未增加新App或签到功能。入口更新后本机私人层的关联、界面选择、证书保留和iPhone效果仍待原生验收，不能把模型检查或发布成功写成手机通过。

**用户已明确暂停自动签到，只保留备忘。** 本轮专注 Stash 主配置、地区池、软件分流、机场订阅兼容、去广告、私人信息隔离、更新回退与中文教程。不再等待用户选择签到平台，不要求账号或 Cookie，不开发任务或捕获器。

已记录用户自述设备为 iPhone 18 Pro Max、Stash 最新版；精确 iOS/Stash 版本未经核对，不作为当前继续开发的前提。不要从机型推断 iOS 版本。

## 本轮完成与修正

- 主配置与公共覆写：18个策略组，5个地区池、其他地区手选入口和全部节点大组；各软件可独立选地区、跟随总代理或独立手选具体节点。旧共享“手动节点”保留，不随意改名。
- 地区筛选：兼容中文/繁体、英文、缩写、数字后缀和旗帜；移除宽泛 `America` 关键词，防止 South America/Latin America/North America 等洲级名称被当成美国。
- 基础与扩展广告：基础 21 条；可选扩展 38,066 条。**扩展覆写现在只替换原广告 provider URL，不再前插广告规则**，因此保留局域网、通知、指定登录/更新服务的直连优先级。基础规则均包含在扩展包中，不叠加执行。
- 图片新增需求：1320×26408长图分12段人工核对，提取135个可见App名称；“隐藏的App”入口未计入。截图和裁剪都未放入仓库，只保存名称及范围判断。
- 新增35款独立广告专项，与图片中既有的B站/淘宝/小红书/微博合计39款；另外8款找到公开方案但暂缓，88款保留通用规则并逐款说明原因。前轮贴吧仍保留，不冒充图片中存在。
- 广告模块现共41个覆写：40款App专项＋1个扩展包；11个响应脚本、12条响应handler、32条原生HTTP拒绝重写、41个去重后精确MITM主机。原模块保留独立启停；本轮一体化订阅已经合并全部40款，不能重复叠加同款模块。HTTP/MITM和本机证书仍须设备设置，不能仅凭这些计数宣称实际去广告通过。
- 新增响应脚本：阿里云盘、菜鸟、京东、美团、瑞幸、微信公众号文章。保留备份、券/积分、订单、包裹、文章appid等正常字段；未知/失败响应放行，无日志/存储/外联。微信不含朋友圈/视频号。
- 独立广告域名专项：云闪付、京东金融、东方财富、铁路12306、携程、UC，以及高德模块的2条；不做银行/支付MITM。与扩展包重叠的8个目标主机已经列出，不能把重叠算作新增效果。
- 原生重写来源：已实际读取blackmatrix7的Stash原生覆写，手工选取fmz明确广告端点，未直接导入QX配置。reject不声称等于原reject-dict/img/200；是否出现空白、等待和真实拦截效果待设备验收。
- 8款暂缓：滴滴、盒马、夸克、Spotify、Starbucks、微信读书、YouTube、YouTube Music。原因包括删安全/券入口、混淆、会员字段、原小程序与App不同、UI精简非广告、二进制/客户端适配尚未完成；不是声称永久不能实现。
- 独立天猫购物 App 尚无专项实现：未找到明确链路，不把淘宝或天猫精灵/养车的结果作为它的完成证据。详情见 [APP-SPLASH.md](docs/APP-SPLASH.md)。
- 私人信息：仅设备端填写机场 URL；示例使用占位符、文档地址及零值 UUID；证书由用户在设备生成。
- 教程：已移除签到确认/账号填写步骤，保留导入、选地区、订阅漏节点、广告误杀、白名单、关闭模块、更新与完整回退说明。
- 验证：增加“扩展包误含局域网/指定系统服务时仍优先直连”的回归检查；地区空池/失效仅报告结构证据，不再用自写的 first-alive 小模型冒充原生 fallback 验证。

## 文件入口

| 内容 | 路径 |
|---|---|
| 从零使用 | [README.md](README.md) |
| 固定订阅入口、最少导入步骤 | `config/stash.yaml`、[SUBSCRIBE.md](docs/SUBSCRIBE.md) |
| 本机启动模板、公共分流 | `config/main.yaml`、`config/core.stoverride` |
| 私人订阅与白名单占位示例 | `examples/private-provider.stoverride`、`examples/private-allowlist.stoverride` |
| 模拟 SS/VLESS 数据 | `examples/provider-simulated.yaml` |
| 规则与来源快照 | `rules/`、`rules/vendor/`、`research/sources.lock.json` |
| 可选广告模块与脚本 | `modules/ads/`、`scripts/ads/` |
| 分流、订阅、广告、更新教程 | `docs/ROUTING.md`、`docs/SUBSCRIPTION.md`、`docs/ADBLOCKING.md`、`docs/APP-SPLASH.md`、`docs/UPDATES.md` |
| 图片135款调查、独立模块导入与通用重叠 | `docs/APP-INVENTORY.md`、`docs/AD-MODULES.md`、`research/app-inventory.json`、`research/ad-catalog.json` |
| 官方能力证据与待核实项 | [STASH-CAPABILITIES.md](docs/STASH-CAPABILITIES.md) |
| 手机验收与脱敏反馈 | [PHONE-CHECKLIST.md](docs/PHONE-CHECKLIST.md) |
| 签到调查备忘（暂停） | [CHECKIN-RESEARCH.md](docs/CHECKIN-RESEARCH.md)、`research/checkin-plan.json` |
| 验证、敏感扫描、资源校验与刷新 | `tools/`、`tests/`、`.github/workflows/validate.yml` |

## 验证结果与边界

| 检查 | 结果 | 边界 |
|---|---|---|
| `python tools/validate.py` | 27项Python检查、43项Node行为测试通过；0失败/跳过；新增分组、前缀过滤、DNS来源检查；GB修正后相关检查单独重跑通过 | 包含全部单模块、正反序全量、1,640个有序模块对的合并检查、下载包资源/ZIP验证和固定订阅入口生成一致性；唯一YAML键、引用与环检测、地区正反例、路由优先级、私人URL合并模型、完整135款清单和暂停签到保护；不是原生Stash核心测试 |
| `python tools/build_subscription.py` | 固定入口与维护源码一致；18个策略组，11份远程JS、12条handler、32条重写、41个精确MITM主机；私人URL模型和代表性路由一致 | 推荐入口不再使用历史开发用content模式；Stash下载11份JS需要联网。设备本机覆写、原生筛选和实际效果仍须验收 |
| `python tools/build_local_bundle.py` | 主配置5,169条静态规则；扩展快照43,214条含业务规则；11份内嵌JS与源码逐字一致；84个前后路由比较通过；ZIP校验、包内敏感扫描通过 | 生成`dist/Jimmy-Stash.zip`及顶层主配置/广告增强，报告`research/local-bundle-audit.json`；没有iPhone原生导入证明 |
| `python tools/check_provider.py` | 公开模拟 SS=1、VLESS=1，基础字段通过 | 不是实际订阅解析、全协议兼容或连接成功证明 |
| 当前文件与 Git 历史敏感模式扫描 | 发布前115个候选公共文件和已有历史无命中；新发布的文件及历史再扫描无命中；ZIP实际成员另做扫描 | 工具不打印命中值；不能证明未知秘密格式绝不存在；提交前已审查暂存路径和差异，未上传抓包、证书、截图、ZIP或私人配置 |
| 锁定上游资源 | 27/27个不同公开URL均HTTP 200，SHA256匹配 | 包含规则/广告源、原生Stash重写参考、fmz实际JS、NobyDa微信及许可、Maasea实际YouTube代码和模块；按URL去重；记录在 `research/upstream-audit.json` |
| 同一SHA重放规则刷新（前轮） | 6个输出及lock文件零字节差异 | 证明刷新可重放，不表示自动跟随上游所有变化 |
| GitHub Actions引用（前轮） | 3个固定SHA的action.yml均200；工作流已上传 | 云端运行结果未作为本轮通过证据，可在仓库Actions页面查看 |
| 正式公共资源发布 | 64/64个实际HTTP 200，SHA256均与本地一致 | 包含一体化入口、原分层入口、41个覆写、规则和脚本；证明可下载，不证明手机运行效果 |
| 真实 Stash 导入/合并、空池/全失败、代理连接、服务解锁、广告效果、选择保留 | 未运行 | 无法操作用户iPhone；不得把离线模拟改写为实机通过 |
| 自动签到 | 已暂停、未开发、未启用 | 不属于本轮验收或继续工作的前提 |

通用合并模型占位输出位于仓库外`/tmp/jimmy-merged-placeholder.yaml`；新本地包在被gitignore排除的`dist/`重建，源文件仍统一维护。没有真实订阅响应、Cookie、登录token或证书私钥。

## 尚未解决的非签到限制

1. **官方文档仍被现行云网络策略以CONNECT 403拒绝。** 本轮环境状态仍为revision=1、自定义allowed_hosts为空。原放行草稿已保存但未生效；草稿包含 `stash.wiki`、`www.stash.wiki`、`api.github.com`。需环境设置应用后才能完成当前文档、精确版本、原生覆写/空池/缓存语义复核。不是自动审批审查拒绝。
2. **手机验收待用户设备执行。** 使用固定订阅入口后，按手机清单核对原生导入/合并和行为；官方复核仍待网络条件解决。若原生空池或全失败会直连/跨地区，必须先修配置，不通过移除拒绝保护“救活”。

已找到声明迁移至官方文档的历史 `jinzaizhichi/stash-example`，其中旧例包含fallback、use、VLESS；该文件明确停止维护，原组织示例路径当前404。只用作历史参考，不复制无明确许可的代码，不替代当前官方文档。

当前是**公共订阅已发布、离线检查和正式下载检查通过的交付**，尚不宣称已达到iPhone生产可用或严格地区出口保证。前轮上传前0/63的404记录已由本轮64/64成功结果替换。

## 本轮可重放维护

公共订阅由`python tools/build_subscription.py --write`从同一套主项目生成，稳定路径始终为`config/stash.yaml`。默认不带`--write`只检查生成差异。维护原配置/模块/脚本后，重建入口并运行`python tools/validate.py`，提交推送后运行`python tools/audit_remote.py published`。刷新主配置与机场代理集的interval是不同机制；本地私人覆写不改为远程模板，更新后核对关联与地区选择。

修改提示前缀后先运行`python tools/generate_node_filters.py --write`同步原core中的平铺列表filter，再重建公开入口。地区正向名称仍维护在原core中；不要加入尚未核实的排除字段或复杂负向断言来冒充严格补集。全部节点始终不按国家/协议筛选，除已知提示前缀外保留原候选。

运行`python tools/build_local_bundle.py`从当前主项目重建同名下载包。下载产物不进Git，用户设备上填好的配置不回传。公共规则展开保持首条匹配顺序、no-resolve位置和系统例外；JS使用原正文，仅改变承载方式。ZIP包含独立许可、可读源码和可选逐款开关；构建报告排除在ZIP源码快照外，避免哈希自引用。本地快照不自动刷新公共规则/JS，更新前在设备备份并复制私人订阅、记录地区选择。

`research/ad-catalog.json`是新增35款模块的人工审核输入，`python tools/generate_ad_modules.py --write`更新原路径；默认不带--write只检查差异。`research/app-inventory.json`是图片名称与逐款结论，`python tools/render_app_research.py --write`同步两份清单文档。两个生成工具已通过零差异复核。

新增端点不能盲目抓取上游整包。先审读源码/许可和正常权益影响，再更新目录、锁文件、行为测试与原文件；运行 `python tools/validate.py`。上游HASH校验与原生Stash/iPhone有效性分开记录。

## 签到备忘

全部24个平台的历史调查仍保留，包含拼多多、云闪付，排除什么值得买、苏宁易购。`research/checkin-plan.json` 状态为 `deferred-by-user`，enabled=[]、runtime_scripts_created=false、cron_entries_created=false、credentials_collected=false。

只有用户以后**明确提出恢复自动签到**，才重新核实接口、许可、资格和Stash调度/API并讨论具体功能。不能把通用“继续”当成恢复授权，不自动启用旧候选或照抄旧接口。

## Git与环境实际状态

- 本地文件已保存、创建提交并实际推送到`main`；未创建PR，采用用户授权的直接发布。本轮代码发布提交为`5a01d672f298eaf75b100f493c3289c17435ee67`，发布检查记录随后在同一分支补充提交。
- 发布起点为 `3eb0d2d29a09fc4e1c5bbbca4cae2aa7b964eae6`（Initial commit）；推送为快进，没有强推或覆盖后来提交。`git ls-remote`已确认代码发布提交位于远端`main`。
- 仓库可见性未更改；真实私人信息没有写进项目。
- 稳定Raw链接使用实际仓库和main分支；已运行 `python tools/audit_remote.py published`，64/64通过。以后更新运行文件仍需重跑。
- 环境仅保存过网络新增域名草稿，没有保存安装/启动服务脚本，没有声称草稿已应用或环境已发布。

## 接续顺序

沿用当前checkout，不创建worktree或重复版本。先确认实际Git状态，保持签到暂停。

环境网络条件改变后，读取当前官方文档并记录精确来源和版本，优先核实filter/use、fallback+REJECT、覆写数组合并、代理集格式/更新失败缓存、UI选择保留；调整原文件并跑受影响检查。不得使用其他代理内核代替Stash验证。

发布前审查公共文件及历史，排除本机最终配置、订阅响应、凭据存储、抓包与证书。发布后检查正式链接，再记录手机“已验证/失败/未测”结果，保留设备端私人配置和原组名。
