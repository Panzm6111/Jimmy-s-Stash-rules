# Jimmy 的 iPhone Stash 项目

当前ROUTE-20261029.5：每端17份规则直订维护上游，6份必要转换由GitHub执行；21业务策略组与原分流逻辑保留。[更新链路与电脑任务状态](docs/UPDATES.md)。

2026-10-29分流版本 `ROUTE-20261029.2`：已接入维护中的TikTok、AI、其他常用社交及通用海外完整分类，两端19个远程规则集。先刷新主配置，再刷新规则集并重连；[来源、优先级和边界](docs/COMMUNITY-SOURCES.md)。

Clash推荐[完整自动订阅](config/clash-verge-auto.yaml)：Jimmy前缀、原20业务组加自动下载回退组、规则顺序和18规则集声明随主订阅更新，私人机场留在本机。按[迁移教程](docs/CLASH-VERGE.md#完整自动订阅推荐)接入一次，开启1440分钟自动更新，以后无需复制Merge。旧全局Merge/脚本保留兼容。

项目接续先读 [PROGRESS.md](PROGRESS.md) 顶部的当前SOP总览；协作约束见 [AGENTS.md](AGENTS.md)。现有Stash HTTP去广告继续保留；另提供[Clash Verge完整分流版](docs/CLASH-VERGE.md)，广告层只用域名规则。

供个人长期维护的公共分流、地区池与去广告项目。**支持Stash；另提供Clash Verge完整分流版（域名去广告）**，无需自建服务器、购买额外服务或把订阅交给第三方转换网站。

> 公共订阅沿用`main`的原入口，最新提交与HTTP/哈希校验结果见[PROGRESS.md](PROGRESS.md)。配置只有占位符，私人订阅和证书始终留在设备。历史云端任务未能取得部分官方文档正文，原生语义和最低版本仍待复核；2026-10-28已取得规则集、脚本及托管订阅官文，最低版本和HTTP效果仍需分别核验；尚未完成iPhone验收，不能把发布成功当作真实连接/去广告通过。自动签到继续暂停。

> **当前约定：使用整合入口，不需要逐App开关。** `AD-20261020.5` 保留已审查的40款专项、11份响应脚本和扩展广告规则集引用，保留手动自检页并补齐fmz200部分广告分支。日常只维护下面的一条公共配置链接；私人订阅留在设备。旧App覆写路径保留为维护源和旧安装兼容文件，不是新增安装步骤。

**本次按fmz200公开源码补齐广告功能，仍更新下面的原链接。** 新增和保留范围、未采用分支及理由见[接入明细](docs/FMZ-INTEGRATION.md)。`.4`的手机记录已证明B站、京东等脚本运行，但淘宝/小红书等无响应脚本记录且仍有广告；`.5`补齐接口与HTTP匹配，不代表这些开屏已经实测解决。

## 使用：粘贴一条链接导入

在Stash配置管理中选择“从URL/链接下载”，粘贴：

```text
https://raw.githubusercontent.com/Panzm6111/Jimmy-s-Stash-rules/main/config/stash.yaml
```

1. 按[订阅导入教程](docs/SUBSCRIBE.md)在**设备本地私人覆写**填一次机场URL，并关联这份配置；不要在GitHub填写。
2. 刷新“机场”，将“总代理”从 `REJECT` 改为“自动节点”或所需地区，使用规则模式连接。“海外AI”默认美国，Apple/Microsoft默认直连；各软件仍可独立选择。
3. 本入口已经包含原分流、扩展广告规则集引用和已审查App专项；主配置声明11份响应脚本及1份自检脚本的原仓库URL，由Stash联网加载。**无需另装App覆写或expanded**。沿用设备已完全信任的自建CA，HTTP/MITM保持开启；没有装过额外广告覆写就直接跳过停用步骤。

若日志显示`dot.pub / NotValidForName`，或出现本项目没有的`Google/NCloud`策略组，先按[运行中排障](docs/SUBSCRIBE.md#已启动但打不开网页或出现dns证书错误)核对选中配置、覆写与DNS设置。确认选中“Jimmy 本机配置”，在“手动节点”手选真节点；流量提示不是节点。日志显示启动成功不等于这份配置已经导入成功。

已经能用的用户：保留原私人订阅覆写、已信任证书和配置备份；若曾额外安装广告增强/App/expanded覆写，先停用这些广告条目，未安装就跳过；刷新原主配置，确认顶部`AD-20261020.5`后断开再连接Stash。不要重新填写机场URL或重装证书。详细步骤及首次使用的私人模板见[SUBSCRIBE.md](docs/SUBSCRIBE.md)。

自检仅新增精确`example.com`解密主机，页面脚本仅处理`/jimmy-stash-check`路径。开始排查后只在本机保存版本、时间和固定状态计数，15分钟后停止新增记录；不存URL、正文或凭据，不上传结果、不发通知。自检成功只证明该测试主机的HTTP脚本/MITM运行，App实际命中与广告效果仍需看记录并实测。

已有完整机场YAML、但私人覆写方式仍无法使用时，可按[完整文件合成说明](docs/SUBSCRIBE.md#已有完整机场文件合成一个本机导入文件)生成一个直接导入的私人主配置。节点连接字段保留、提示条目排除，公共分流与广告仍取同一项目；输入输出在仓库外。该方式的节点和内嵌规则是快照，更新需重新合成，不能承诺自动跟随机场。

## 你会得到什么

- “自动节点”、美国、日本、香港、新加坡、台湾、“其他地区”和“ai”共8个自动测速池，按最近成功的HTTPS探测延迟选最低者；30分钟检测一次，不保证任意时刻最快。“自动节点”可跨国家切换，“其他地区”可在其中多个国家间切换；需要手选全部节点时使用保留的“手动节点”。两端的“ai”由原“日本+美国”扩展为日本、美国、新加坡、台湾四地区，11个业务select组均可选择，原默认值不变。
- “海外AI”取代原OpenAI组，涵盖常用海外AI服务，默认选美国；可另选地区、跟随总代理或手选具体节点。Netflix、YouTube、Telegram默认跟随总代理；各软件选择互不影响。Apple/Microsoft 默认直连，并对通知、登录和更新做更具体的处理。AI覆盖范围与遗漏边界见[说明](docs/AI-COVERAGE.md)。
- 局域网直连、国内常用域名规则、国内 GeoIP 兜底、域名广告拦截策略组和未匹配流量组。“广告拦截→DIRECT”只放行域名规则，不关闭HTTP处理。
- 整合入口默认引用扩展广告域名包，并包含40款App的已审查专项。图片已提取135个名称，其中39款有专项文件，另有此前的贴吧专项；其余逐款记录原因。文件数量不等于实际有效数量，**广告效果均待手机测试**，不处理会员解锁。
- 自动签到已暂停；含拼多多、云闪付的 [24 平台调查备忘](docs/CHECKIN-RESEARCH.md) 保留供日后参考。
- 固定主路径、来源与许可证记录、离线验证、本地上游检查与规则更新工具、排障和回退教程。

## 先记住公私边界

| 可以公开 | 只留在你的 iPhone |
|---|---|
| 本仓库的配置模板、地区组、域名规则、无凭据脚本、教程 | 机场 URL/token、节点密码/UUID、登录 Cookie、登录令牌、MITM 证书私钥 |

**不要直接在 GitHub 网页编辑器中填订阅。不要把本机导出的最终配置、订阅响应、抓包文件或证书上传，也不要放进聊天。** 本仓库 `.gitignore` 和扫描工具只是额外防护，不能撤回已经泄露的密钥。

<a id="可选原分层方式安装"></a>

## 维护源与旧安装兼容

当前使用要求已经统一为整合入口，**逐App独立开关不再是交付要求或待完成事项**。`config/main.yaml`、`config/core.stoverride` 和 `modules/ads/*.stoverride` 保留原路径，供构建主入口、审查来源及兼容已存在的旧安装；不再作为新用户安装路线，也不与整合入口叠加。

旧安装迁移时先保留本机可用备份，再从本页公共URL导入整合配置并关联原私人订阅覆写；停用旧公共core和广告覆写，确认地区选择后重连。不要删除含私人信息的备份。原[本地包](docs/LOCAL-IMPORT.md)和[私人节点文件合成](docs/SUBSCRIBE.md#已有完整机场文件合成一个本机导入文件)保留为特殊情况下的静态交付工具，它们的更新方式与远程订阅不同。

自动签到按用户决定暂停，只保留[24平台调查备忘](docs/CHECKIN-RESEARCH.md)，不创建凭据捕获或定时任务。

## 日常运行、更新与耗电

建议“持续开启＋规则分流”：Stash 持续接管连接，但国内/局域网按规则直连，不等于所有流量都走机场。关闭 Stash 后，网络层拦截和 MITM 响应处理停止工作；App 已缓存广告也可能继续显示。

按需连接适合不需要持续去广告的情况：在 Stash 里手动连接/断开。系统按需连接入口如可用，必须以当前版本真实选项为准，不能承诺识别每个 App/网站后精准启停。本项目不制作虚假的快捷指令导入文件。

建议保持现有频率：

| 项目 | 建议与当前设置 |
|---|---|
| 全部19个远程规则集（AI/社交/软件/广告/例外） | 每24小时自动尝试刷新一次，现为`interval: 86400` |
| 机场节点 | 每24小时自动尝试刷新一次，现为`interval: 86400`；机场通知变更或节点失效时手动刷新 |
| 公共主配置 | Stash已加入首行#SUBSCRIBED，官方默认12小时检查；Clash完整自动订阅首次开启1440分钟自动更新，策略组和分流结构随之更新 |
| 远程广告脚本 | 由主配置引用，现为`interval: 86400`；新增主机或handler时必须同时更新主配置 |
| 节点测速 | 保留30分钟，现为`interval: 1800`；这是HTTPS延迟探测，不是规则更新或服务解锁检测 |

这些间隔不是固定北京时间的定时任务；关闭Stash、断网或客户端后台状态都可能影响执行。规则集只取得本仓库已经发布的快照。上游检查建议**每天一次**，由电脑运行本项目的维护工具；普通规则可批量更新并验证，App脚本有相关变化时仍需审查适配。手机刷新、电脑检查上游、发布到GitHub是三个独立步骤，机制见[更新教程](docs/UPDATES.md)。不做高频轮询，也不承诺耗电百分比。

平时保留原配置、组名与“机场”provider名称；私人URL在本机层维护。更新前记下各软件的地区选择，更新后核对私人覆写关联和选择；原生保留行为仍待手机验收。若机场更换了订阅URL，需要在设备私人覆写中换成新URL，自动刷新无法自行发现新地址。

## 在电脑上维护上游

已有本地工具，默认只检查公开来源并生成中文报告：

```sh
python tools/maintain.py check
```

确认需要同步普通规则后运行`python tools/maintain.py update`。此命令只做本地更新；日常任务使用tools/auto_update.py完成检查、隔离验证和必要的提交推送。App脚本变化仍先审查。**本地更新成功后，发布到GitHub才会改变手机那条订阅链接的内容。**

建议每天检查一次，有变化才处理。工具需在安装了Python、Git的电脑上运行，更新验证还需要Node.js；iPhone里的Stash不能直接运行这个Python程序。安装、Windows/macOS步骤、本地定时任务和回退见[本地维护教程](docs/MAINTENANCE.md)。现有Windows中午任务已获授权升级为自动检查、隔离验证并只发布实际变化；没有变化不提交不推送。未部署GitHub定时同步。

## 文档导航

- [策略组、规则优先级与地区池](docs/ROUTING.md)
- [海外AI覆盖范围、来源与限制](docs/AI-COVERAGE.md)
- [整合入口导入与本机私人设置](docs/SUBSCRIBE.md)
- [订阅兼容、漏节点与 SS/VLESS](docs/SUBSCRIPTION.md)
- [广告覆盖、MITM、整体暂停与恢复](docs/ADBLOCKING.md)
- [完整去广告方案与调查规格：配置原文、40款范围、广告JS与诊断源码](docs/AD-ARCHITECTURE.md)
- [图片135款App名称与逐款调查](docs/APP-INVENTORY.md)
- [专项维护源、覆盖范围与通用规则重叠](docs/AD-MODULES.md)
- [淘宝、小红书、微博与独立天猫的专项范围](docs/APP-SPLASH.md)
- [24 平台自动签到调查备忘（已暂停）](docs/CHECKIN-RESEARCH.md)
- [Stash 能力来源与当前文档阻塞](docs/STASH-CAPABILITIES.md)
- [资源来源、许可证与快照更新](docs/SOURCES.md)
- [更新、误分流排查、关闭与回退](docs/UPDATES.md)
- [本地上游检查、规则更新与定时维护](docs/MAINTENANCE.md)
- [手机验收与安全反馈](docs/PHONE-CHECKLIST.md)
- [验证结果与接续事项](PROGRESS.md)

## 开发者验证（手机用户无需执行）

Python 3.12、Node.js 22 或 24；验证依赖只有 PyYAML，不运行其他代理内核：

```sh
python -m pip install -r requirements-dev.txt
python tools/build_ads.py
python tools/validate.py
python -m unittest discover -s tests -p test_private_config.py -v
python tools/check_provider.py
python tools/build_subscription.py
python tools/generate_node_filters.py
python tools/generate_ad_modules.py
python tools/render_app_research.py
python tools/audit_remote.py upstream
# 正式发布后检查HTTP返回与内容哈希：
python tools/audit_remote.py published
```

可在仓库外输出**仅含占位符**的合并模型：`python tools/validate.py --emit-merged /tmp/jimmy-merged-placeholder.yaml`。工具不接受真实机场 URL，不会拿私人数据做云端测试。GitHub Actions 工作流已随源文件上传，云端执行结果在仓库Actions页面查看；本地测试结果不代表云端执行已经通过。

许可证：本项目原创部分采用 MIT；第三方规则和脚本分别保留其 MIT、GPL-2.0 或 GPL-3.0 许可与归属。精确文件、固定版本及修改来源见[来源记录](docs/SOURCES.md)，不将第三方文件统一重标为 MIT。

TikTok、Instagram和X统一由“TikTok”组选择出口，默认美国；两端的“海外AI”均可选四地区“ai”（Clash前缀入口显示为“Jimmy · ai”）。Windows每天12点检查见[维护教程](docs/MAINTENANCE.md)。
