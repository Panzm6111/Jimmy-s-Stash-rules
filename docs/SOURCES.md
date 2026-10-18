# 来源、许可证与维护

核实日期 2026-10-18。未运行第三方签到代码；已读取的文件、完整 Git SHA、内容 SHA256 与仓库最新提交时间分别见 [projects.json](../research/projects.json) 和 [sources.lock.json](../research/sources.lock.json)。仓库有新提交不证明每个旧脚本仍然有效。

## 实际复用内容

| 来源 | 许可 | 本项目使用 | 维护/兼容证据 |
|---|---|---|---|
| [blackmatrix7/ios_rule_script](https://github.com/blackmatrix7/ios_rule_script) @ `7dd06b44f5093dd5404e1e5f3bca5452d97146ef` | GPL-2.0，原文 [licenses/blackmatrix7-GPL-2.0.txt](../licenses/blackmatrix7-GPL-2.0.txt) | Netflix、YouTube、Telegram、China 和 AdvertisingLite 数据。只转为 native 基本 classical 规则，不导入 Clash 配置/内核专用功能 | 仓库最后提交 2026-10-18 北京时间；各数据文件头的更新时间更早。全量读取后发现部分同名 `.yaml` 是拆分片段，优先使用 Classical；去掉 PROCESS-NAME/IP-ASN 等未核实项；精确遗漏列表在 lock 中 |
| [app2smile/rules](https://github.com/app2smile/rules) @ `df6366a7024e0b3f0aa3510c5b791eea6f3cba89` | MIT，原文 [licenses/app2smile-MIT.txt](../licenses/app2smile-MIT.txt) | 修改 `bilibili-json.js` 和 `tieba-json.js` 的明确广告处理；保留归属，自己保存无外联的缩小脚本 | 实际存在 `module/bilibili.stoverride`、`module/tieba.stoverride` 原生配置，含 HTTP/MITM/script-providers 字段。仓库提交 2026-03-04，不等于 JSON 处理在当前 App 实测有效 |
| 项目原创配置、教程、验证工具 | [MIT](../LICENSE) | 稳定组名、分层私人配置、较窄的 OpenAI/Apple/Microsoft 域名表、测试与工具 | 普通 YAML/脚本模型通过不等于 Stash 内核验收；完整能力限制另列 |

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

## 调查但未复用

24 平台的项目、许可、维护、实际代码和适配判断详见 [签到调查](CHECKIN-RESEARCH.md)。其中没有许可证的项目只用于发现实现线索，不复制脚本；Android Auto.js 不能当 Stash JS；Python/Node.js 需明确改写不能直接导入。外部签名/推送服务、抽奖/分享/购买/兑换等均不作为默认功能。

## 官方来源

Stash 官方文档入口：https://stash.wiki/ 。当前访问受云网络 CONNECT 403 阻塞；没有假称读过最新正文，也不编造最低版本号。已有原生公开模块仅作为辅助证据。具体未核实清单见 [STASH-CAPABILITIES.md](STASH-CAPABILITIES.md)。

## 2026-10-19 新增专项广告来源

[`fmz200/wool_scripts`](https://github.com/fmz200/wool_scripts) @ `5d5f63fcf98bc69d5f8f1b1bae6f86a01ee4bb97`，仓库 GPL-3.0；完整许可见 [fmz200-GPL-3.0.txt](../licenses/fmz200-GPL-3.0.txt)。新增淘宝/小红书/微博三个模块与脚本均显式标记 GPL-3.0-only，不以项目根 MIT 重新授权。

具体来源、文件日期、被删除的范围和端点见 [APP-SPLASH.md](APP-SPLASH.md)。淘宝与小红书仅提取明确开屏分支；微博只取专用端点与空字典策略，不复制配置引用的其他作者整包脚本。原来源为 QX 等客户端表达，已手工制作本项目原生 Stash 覆写和安全本地脚本；未使用第三方转换站。

旧两款MIT脚本、规则快照GPL-2.0及新增GPL-3.0派生文件分别保留许可。上游源 SHA、本地输出 SHA 和补充来源在 sources.lock.json；审核新版本时应保留许可、限制范围和失败放行逻辑。

## 图片135款调查与新增35款专项（2026-10-19）

完整逐款结论在 [APP-INVENTORY.md](APP-INVENTORY.md)，模块、精确主机及通用包重叠在 [AD-MODULES.md](AD-MODULES.md)。本轮不是整包导入来源；实际原文件、固定SHA、源哈希、各条取用片段和本地模块路径记录在 `research/ad-catalog.json`，脚本输出哈希仍统一放 `research/sources.lock.json`。

| 来源 | 许可与取用 | 维护/适配边界 |
|---|---|---|
| fmz200/wool_scripts，沿用前轮固定SHA | GPL-3.0-only；广告端点派生覆写及阿里云盘、菜鸟、瑞幸脚本；许可原文仍在 `licenses/fmz200-GPL-3.0.txt` | 合集文件头2026-09-10，阿里云盘/菜鸟/滴滴实际JS较旧。已阅读代码并去掉删领券、普通推荐、功能入口等逻辑。夸克JS混淆未运行；滴滴会删安全入口且部分端点与代码不符，暂缓 |
| blackmatrix7/ios_rule_script，沿用前轮固定SHA | GPL-2.0；京东、美团脚本仅改已知广告字段。`rewrite/Stash/Advertising/Advertising.stoverride` 仅作为原生 `http.rewrite` 格式证据 | 原生文件头2025-08-26；没有复制其中数百个MITM域名/规则。京东/美团模块与脚本显式标记GPL-2.0；项目根MIT不重新授权它们 |
| [NobyDa/Script](https://github.com/NobyDa/Script) @ `0b8d083d444f4476700cb9d5d059c07b42da85eb` | GPL-3.0-only，原文 `licenses/NobyDa-GPL-3.0.txt`；仅公众号文章广告数量/数组，保留原脚本会删除的appid | 现有浅克隆最近提交2026-08-13，不代表这份旧微信脚本当前有效。已另核对固定版本原文件和许可的HTTP/SHA；原QX/Surge写法重新制作成Stash响应覆写。无聊天、朋友圈、视频号处理 |
| [Maasea/sgmodule](https://github.com/Maasea/sgmodule) @ `65075cdb388fc5e3094afd7e7314c67b243f3525` | Apache-2.0；只审阅YouTube实际JS、模块、许可证和WeRead模块，**没有复制到运行代码** | README明确基于Surge；YouTube有Protobuf、请求/响应配套、动态视频域名和UI/后台播放修改，本轮未完成Stash广告专用裁剪与二进制回归。WeRead是阅读提示精简，不当成去广告 |
| app2smile/rules，沿用前轮固定SHA | MIT；既有B站/贴吧保留。Spotify模块只作调查，没有复制 | 实际Spotify模块修改Premium字段/权限；未作为广告专用模块导入。不把同样“有原生Stash模块”作为所有功能符合本项目范围的证据 |

本轮读取主要三个复用仓库HEAD均与锁定SHA相同。上游审计按URL去重，27个不同公开文件全部HTTP 200且哈希匹配；该结果与GitHub仓库活跃程度都不等于App当前广告实测有效。

原QX `reject-dict`、`reject-img`、`reject-200` 没有按同名字段套进Stash。本项目部分端点选择原生 `http.rewrite: 正则 - reject`；**拒绝的状态码/返回体与源动作不保证等价**，可能空白、等待或接口已改，必须逐款设备验收。只读来源，不请求真实业务接口，不保存账号响应。

本地下载包只改变承载方式：规则集展开为相同优先级的普通规则，11份独立脚本原文放入各自`script-providers.content`，不是拼成一个混合程序。content字段参考已有历史原生Stash示例，旧例注明仅推荐开发使用且不再维护；不视作当前官方版本证明。ZIP保留独立资源许可及完整可读源码，未复制该无许可示例的脚本或整份配置；实际手机兼容性待验收。

本轮生成的覆写按条目标记GPL-3.0-only或GPL-2.0，人工审核目录的源数据也按条目保留归属。原有MIT原创代码、GPL-2.0规则和独立GPL-3.0文件各自保留许可证，不能用根LICENSE覆盖。所有第三方代码的修改后的可读源码均与本项目一起提供；无混淆运行文件、未知外联、Cookie捕获或签到任务。
