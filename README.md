# Jimmy 的 iPhone Stash 项目

供个人长期维护的公共分流、地区池与去广告项目。**客户端只使用 Stash**，无需自建服务器、购买额外服务或把订阅交给第三方转换网站。

> 公共订阅沿用`main`的原入口，最新提交与HTTP/哈希校验结果见[PROGRESS.md](PROGRESS.md)。配置只有占位符，私人订阅和证书始终留在设备。官方文档站受云网络策略限制，部分原生语义和最低版本仍待复核；尚未完成iPhone验收，不能把发布成功当作真实连接/去广告通过。自动签到继续暂停。

> **AD-20261020.2 使用方式统一：** 原配置链接现在整合已审查的40款专项、11份响应脚本和扩展广告规则集引用。已经能用的用户刷新原主配置即可取得这些处理，不需要另找App开关或添加expanded覆写。保留原私人订阅和已信任证书；若之前额外装过广告覆写，先停用以免重复。详见[更新步骤](docs/ADBLOCKING.md#已安装用户怎么更新)。**整合入口没有逐App开关；尚无iPhone效果验收，不保证所有开屏消失。**

## 推荐：粘贴一条链接导入

在Stash配置管理中选择“从URL/链接下载”，粘贴：

```text
https://raw.githubusercontent.com/Panzm6111/Jimmy-s-Stash-rules/main/config/stash.yaml
```

1. 按[订阅导入教程](docs/SUBSCRIBE.md)在**设备本地私人覆写**填一次机场URL，并关联这份配置；不要在GitHub填写。
2. 刷新“机场”，将“总代理”从 `REJECT` 改为“自动节点”或所需地区，使用规则模式连接。“海外AI”默认美国，Apple/Microsoft默认直连；各软件仍可独立选择。
3. 本入口已经包含原分流、扩展广告规则集引用和已审查App专项；脚本随主配置一同下载。**无需另装App覆写或expanded**。沿用设备已完全信任的自建CA，HTTP/MITM保持开启；没有装过额外广告覆写就直接跳过停用步骤。

若日志显示`dot.pub / NotValidForName`，或出现本项目没有的`Google/NCloud`策略组，先按[运行中排障](docs/SUBSCRIBE.md#已启动但打不开网页或出现dns证书错误)核对选中配置、覆写与DNS设置。确认选中“Jimmy 本机配置”，在“手动节点”手选真节点；流量提示不是节点。日志显示启动成功不等于这份配置已经导入成功。

以后刷新同一公共链接，本机私人覆写单独保留；更新后仍需核对关联与地区选择。详细说明含可复制的私人覆写模板、证书、恢复方法，见[SUBSCRIBE.md](docs/SUBSCRIBE.md)。[本地下载包](docs/LOCAL-IMPORT.md)及下文原分层方式保留为备选，来自同一套维护文件。

已有完整机场YAML、但私人覆写方式仍无法使用时，可按[完整文件合成说明](docs/SUBSCRIBE.md#已有完整机场文件合成一个本机导入文件)生成一个直接导入的私人主配置。节点连接字段保留、提示条目排除，公共分流与广告仍取同一项目；输入输出在仓库外。该方式的节点和内嵌规则是快照，更新需重新合成，不能承诺自动跟随机场。

## 你会得到什么

- “自动节点”、美国、日本、香港、新加坡、台湾和“其他地区”共7个自动测速池，按最近成功的HTTPS探测延迟选最低者；30分钟检测一次，不保证任意时刻最快。“自动节点”可跨国家切换，“其他地区”可在其中多个国家间切换；需要手选全部节点时使用保留的“手动节点”。
- “海外AI”取代原OpenAI组，涵盖常用海外AI服务，默认选美国；可另选地区、跟随总代理或手选具体节点。Netflix、YouTube、Telegram默认跟随总代理；各软件选择互不影响。Apple/Microsoft 默认直连，并对通知、登录和更新做更具体的处理。AI覆盖范围与遗漏边界见[说明](docs/AI-COVERAGE.md)。
- 局域网直连、国内常用域名规则、国内 GeoIP 兜底、广告开关和未匹配流量组。
- 推荐入口默认引用扩展广告域名包，整合40款App的已审查广告专项；需要逐App启停时，另选下文的原分层方式。你提供的图片已提取135个名称，其中39款有专项文件，其余逐款记录原因。**实际广告效果均待手机测试**，不处理会员解锁。
- 自动签到已暂停；含拼多多、云闪付的 [24 平台调查备忘](docs/CHECKIN-RESEARCH.md) 保留供日后参考。
- 固定主路径、来源与许可证记录、离线验证、上游快照更新工具、排障和回退教程。

## 先记住公私边界

| 可以公开 | 只留在你的 iPhone |
|---|---|
| 本仓库的配置模板、地区组、域名规则、无凭据脚本、教程 | 机场 URL/token、节点密码/UUID、登录 Cookie、登录令牌、MITM 证书私钥 |

**不要直接在 GitHub 网页编辑器中填订阅。不要把本机导出的最终配置、订阅响应、抓包文件或证书上传，也不要放进聊天。** 本仓库 `.gitignore` 和扫描工具只是额外防护，不能撤回已经泄露的密钥。

## 可选：原分层方式安装

**使用上面的公共订阅入口时，整节跳过，不添加core、App覆写或expanded。** 下文仅供明确需要逐App开关的人选择另一种安装方式；它与推荐整合入口互斥。所谓“App开关”是自己导入后在覆写列表启停该条目，不是Stash自动出现的一排软件按钮。expanded同样是覆写文件名。

### 0. 确认前提

1. 你已从自己正常使用的 App Store 渠道安装 Stash，使用可用的本人机场订阅；不要切换到其他代理客户端。
2. 记录 Stash 与 iOS 版本。B站/贴吧这两个模块参考的上游标注 iOS≥15，但本项目不能因此编造 Stash 的精确最低版本。
3. 先解决 [能力核实中的阻塞](docs/STASH-CAPABILITIES.md)；然后完成本文导入与手机验收。在官方合并/空池行为确认之前，不宣称配置能保证地区锁定。
4. 远程资源的实际HTTP校验与Git状态看PROGRESS。只发布公共文件，不改变仓库可见性。

### 1. 下载本地主配置

手机 Safari 打开以下地址，下载 `main.yaml` 到“文件”App 的本机目录；再用“共享 → Stash”或 Stash 的本地文件导入入口导入（菜单文字随版本可能不同）。命名为 **Jimmy 本机主配置**。

```text
https://raw.githubusercontent.com/Panzm6111/Jimmy-s-Stash-rules/main/config/main.yaml
```

这里选择**本地文件导入**，不用带远程更新地址的主配置承载私人编辑。主配置没有真实机场地址，未启用公共分流时默认 REJECT 是正常保护，暂时不要连接。

### 2. 准备只在本机保存的私人覆写

从仓库 [examples/private-provider.stoverride](examples/private-provider.stoverride) 下载占位模板到 iPhone；在本机的文本编辑入口中，只将 `https://example.invalid/REPLACE_ON_DEVICE` 替换为你自己的机场订阅 URL。保留 `proxy-providers` 和名称“机场”。保存成**本机私人订阅.stoverride**，导入 Stash 的覆写功能，启用并关联到这份本机主配置。

不需要装第三方转换服务或把链接发给任何人。`.invalid` 不是机场地址，也不是变量；必须在设备上真实替换。若当前 Stash 不提供方便的本地覆写编辑入口，可在它的本地主配置编辑器中直接替换 `proxy-providers → 机场 → url`，同样只保存在设备。二选一，不在两个位置维护不同 URL。

机场后台优先选明确标注 **Stash** 的输出。格式、SS/VLESS 漏节点和高级字段问题先看 [订阅兼容教程](docs/SUBSCRIPTION.md)。

### 3. 添加公共分流覆写

Stash → 覆写（或配置的覆写管理）→ 添加远程覆写，粘贴：

```text
https://raw.githubusercontent.com/Panzm6111/Jimmy-s-Stash-rules/main/config/core.stoverride
```

启用“Jimmy 公共分流”，应用到 **Jimmy 本机主配置**。私人覆写对 provider URL 具有更高覆盖优先级。首次设置时，在 Stash 的最终配置/合并预览中确认：

- 只有一个名为“机场”的代理集，URL 是你在设备填写的 URL；不要分享这个预览。
- 有 18 个本项目策略组，没有循环或同名重复；本机模板的 groups 空数组没有抹掉公共组。
- 局域网/关键服务例外在基础广告之前，广告在一般国内规则之前，最后是 `MATCH,未匹配流量`；模板末尾的 `MATCH,REJECT` 即使仍存在也应位于其后。
- 私人手动放行规则若启用，应在广告规则与所有 MATCH 之前。

**离线工具只模拟本项目期望的合并，不替代这个预览。** 如果实际顺序/结构不同，停下并按 [反馈方式](docs/PHONE-CHECKLIST.md) 反馈，不能仅强行打开 VPN。

### 4. 刷新机场，并选择第一次出口

1. 在代理集页面更新“机场”。确认真实节点数和 SS/VLESS 数量，比较机场后台；解析通过不等于完整，也不等于连通。
2. 在策略组页面，将 **总代理** 从默认 `REJECT` 改为“自动节点”，或你希望的地区，例如“日本”。“自动节点”会在全机场候选中选最低探测延迟；选定五个单地区池时，配置只放该地区候选，不加入其他地区或DIRECT。
3. **海外AI默认“美国”**；Netflix、YouTube、Telegram与未匹配流量默认“总代理”。进入各软件组即可改为自己的地区或“总代理”，各软件互不影响。海外AI涵盖常用海外服务，不能穷尽所有新服务，详情见[覆盖说明](docs/AI-COVERAGE.md)。
4. 想查看和手选全节点时，进入“手动节点”，选真节点后让总代理选“手动节点”；已知流量/到期提示会过滤。想让某软件独立固定节点，直接在该软件组内选。“其他地区”仅匹配常见其他国家，非严格补集，改为组内自动选择后也可能换国家；名称未归类的候选仍在“自动节点”和“手动节点”。多个软件跟随同一个池或手动入口时，会共用该入口的结果。
5. Apple/Microsoft 默认 `DIRECT`；通知、iCloud、部分更新/登录有更高优先级直连例外。只有组内覆盖的域名会随组变动，详见 [分流原理](docs/ROUTING.md)。
6. 保持 Stash **规则模式**，点击连接并允许 iOS 添加 VPN 配置。依 [手机验收清单](docs/PHONE-CHECKLIST.md) 测试；延迟变绿不能证明 Netflix/OpenAI 服务解锁。

### 5. 先用基础广告，再逐个加可选模块

基础广告包含在公共分流中，不需要证书。若登录、付款、收消息、播放或领券出现异常，将“广告拦截”组改为 `DIRECT`；恢复正常后先定位误杀域名再重开。

| 模块 | 稳定链接（复制进 Stash 远程覆写） | 默认/作用 |
|---|---|---|
| 扩展广告 | `https://raw.githubusercontent.com/Panzm6111/Jimmy-s-Stash-rules/main/modules/ads/expanded.stoverride` | 可选，默认不导入；替换基础规则集，不需 MITM，保留系统直连例外 |
| B 站广告 | `https://raw.githubusercontent.com/Panzm6111/Jimmy-s-Stash-rules/main/modules/ads/bilibili.stoverride` | 可选，默认不导入；需 MITM，只改开屏/推荐流 JSON |
| 贴吧开屏 | `https://raw.githubusercontent.com/Panzm6111/Jimmy-s-Stash-rules/main/modules/ads/tieba.stoverride` | 可选，默认不导入；需 MITM，只改开屏 JSON |
| 淘宝开屏 | `https://raw.githubusercontent.com/Panzm6111/Jimmy-s-Stash-rules/main/modules/ads/taobao.stoverride` | 分层模式可选；专用 splash API 与明确 tao_splash 场景 |
| 小红书开屏 | `https://raw.githubusercontent.com/Panzm6111/Jimmy-s-Stash-rules/main/modules/ads/xiaohongshu.stoverride` | 分层模式可选；开屏配置、指定素材与明确标识的首页广告 |
| 微博开屏 | `https://raw.githubusercontent.com/Panzm6111/Jimmy-s-Stash-rules/main/modules/ads/weibo.stoverride` | 分层模式可选；实时/预加载、指定广告主机及有限信息流 |

另外35款包括：包含京东、拼多多、菜鸟、闲鱼、高德、美团、大众点评、知乎、网易云音乐等。**完整远程链接、精确解密域名、仅处理的广告范围和关闭步骤见[模块目录](docs/AD-MODULES.md)**。云闪付、京东金融等采用独立广告域名规则，不解密支付业务。微信仅处理公众号文章广告，不声称去除朋友圈/视频号广告。

广告策略组的 `DIRECT` 只关闭**域名拦截**；HTTP重写和响应脚本必须在覆写页面分别关闭。先逐个启用、逐个测试，不整包开启。多个模块同时启用时，合并预览必须保留各自 handler、rewrite 与精确 MITM 域名，不能只剩最后一个。全量仅供结构检查的预期计数见模块目录。目标主机与原通用包的实际重叠也在该目录列出，不将重叠规则当作新增去广告效果。

需要证书时：Stash 的 HTTP/MITM 设置中**在本机生成** CA → 按提示安装描述文件 → iOS“设置 → 通用 → 关于本机 → 证书信任设置”，只信任自己刚生成的 Stash CA → 回 Stash 开启 HTTP/MITM。具体入口依版本核对官方说明。域名严格限于各模块声明的精确主机；不解密银行、支付或全部网站，不关闭上游 TLS 校验，证书私钥绝不进入仓库。详见 [广告模块与恢复](docs/ADBLOCKING.md)；新增三款的端点、域名和独立天猫限制见 [专项开屏说明](docs/APP-SPLASH.md)。

### 6. 自动签到只保留备忘

自动签到已按用户决定暂停。不需要选平台、不需要 Cookie，不创建定时任务。现有 [24 平台调查备忘](docs/CHECKIN-RESEARCH.md) 原路径保留，日后只有你明确要求恢复时才继续。

## 日常运行、更新与耗电

建议“持续开启＋规则分流”：Stash 持续接管连接，但国内/局域网按规则直连，不等于所有流量都走机场。关闭 Stash 后，网络层拦截和 MITM 响应处理停止工作；App 已缓存广告也可能继续显示。

按需连接适合不需要持续去广告的情况：在 Stash 里手动连接/断开。系统按需连接入口如可用，必须以当前版本真实选项为准，不能承诺识别每个 App/网站后精准启停。本项目不制作虚假的快捷指令导入文件。

7个自动池使用 `url-test`，测速地址为 `https://www.gstatic.com/generate_204`，`interval: 1800`。这是HTTPS探测延迟，不是ICMP ping、下载带宽或服务解锁测试；具体切换阈值、缓存和时机仍待Stash实测。测速检查为30分钟；远程规则集和机场请求刷新间隔为24小时。推荐入口的内嵌脚本随主配置刷新；只有分层模式的远程脚本另按24小时请求刷新。覆写的获取与这些interval **不是同一机制**，见 [更新机制表](docs/UPDATES.md)。不承诺耗电百分比、不做高频轮询。当前没有签到调度，也没有需要保持运行的额外后台任务。

本次将“全部节点”改名为“自动节点”、OpenAI组改名为“海外AI”。已能上网的用户直接刷新原公共主配置；使用core分层模式的刷新原core，不重填订阅或新建私人覆写。旧组名消失后必须核对选择，总代理若回到REJECT要重选；海外AI=美国、Apple=DIRECT是配置默认，旧UI选择可能保留，更新后手动确认。手改的本地副本没有公共配置自动更新关系，更新前先在设备备份私人URL。详见[一次性迁移](docs/UPDATES.md#本次测速与海外ai调整的迁移)。

平时更新保留原配置、组名与provider名。推荐入口刷新原公共主配置，不反复删配置重建；分层模式才分别刷新原覆写/资源。私人 URL 存在设备本地层，公共更新不应改它；原生 UI 选择保留仍需手机核对，必要时手动重选。每次更改前记下地区选择并在设备本地保留上一份已工作的公共覆写。完整操作看 [更新、排障与回退](docs/UPDATES.md)。

## 文档导航

- [策略组、规则优先级与地区池](docs/ROUTING.md)
- [海外AI覆盖范围、来源与限制](docs/AI-COVERAGE.md)
- [一条链接订阅导入与本机私人设置（推荐）](docs/SUBSCRIBE.md)
- [订阅兼容、漏节点与 SS/VLESS](docs/SUBSCRIPTION.md)
- [广告覆盖、MITM、模块启停](docs/ADBLOCKING.md)
- [完整去广告方案与调查规格：配置原文、40款范围、11份广告JS＋可选诊断源码](docs/AD-ARCHITECTURE.md)
- [图片135款App名称与逐款调查](docs/APP-INVENTORY.md)
- [全部专项模块、稳定导入链接与通用规则重叠](docs/AD-MODULES.md)
- [淘宝、小红书、微博与独立天猫的专项范围](docs/APP-SPLASH.md)
- [24 平台自动签到调查备忘（已暂停）](docs/CHECKIN-RESEARCH.md)
- [Stash 能力来源与当前文档阻塞](docs/STASH-CAPABILITIES.md)
- [资源来源、许可证与快照更新](docs/SOURCES.md)
- [更新、误分流排查、关闭与回退](docs/UPDATES.md)
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

许可证：本项目原创部分 MIT；第三方规则快照 GPL-2.0；B站/贴吧脚本依据 MIT，新增三款派生模块/脚本依据 GPL-3.0 授权。保留独立许可和来源说明，不把所有第三方文件重标为 MIT。
