# Stash 能力、证据等级与版本门槛

核实日期：2026-10-19。客户端限定 iPhone Stash，未使用其他内核代替验收。

## 当前重要阻塞

**当前云网络策略拒绝访问 Stash 官方文档站 [stash.wiki](https://stash.wiki/)**：HTTPS CONNECT 返回 403，页面内容未下载。所保存的域名放行草稿尚未应用到本机（运行配置 revision=1，custom allowed_hosts 为空）。这不是 Stash 网站返回的业务错误，也不是已获官方支持的证明。

需要环境所有者在环境设置审核并保存网络新增域名 `stash.wiki`、`www.stash.wiki`（以及为后续元数据研究申请的 `api.github.com`），按界面要求发布。随后重试官方文档，补全本文件与配置。草稿保存不等于权限已生效，不会假称已读到官方最新正文。

因此，这轮配置是**已有原生格式参考与离线验证的候选交付**，未声称官方最低版本、真实合并、fallback 的空池细节已经核实。使用前先完成官方文档复核与 [手机验收](PHONE-CHECKLIST.md)。不要仅因离线检查通过就把它当作保证地区出口的生产配置。

## 已有来源与仍需确认的能力

| 能力 | 本项目采用的方式与证据 | 官方来源/版本要求状态 |
|---|---|---|
| 主配置 | `config/main.yaml` 为本地启动模板；不放真实 URL，不假设任意 YAML 环境变量展开 | 官方入口 https://stash.wiki/；下载/编辑/更新行为仍待读取当前正文；不编造最低版本 |
| 覆写与深层映射 | 公共 `.stoverride` + 仅设备保存的私人 provider URL；广告模块有 app2smile 原生 Stash 源码参考 | 原生参考 `module/bilibili.stoverride`、`module/tieba.stoverride` 在锁定版本中实际存在。真实 map/list/rules 合并与覆写顺序需官方文档和合并预览复核 |
| 代理集 | `proxy-providers`，固定名称“机场”，更新间隔 86400 秒；真实订阅仅设备填写 | `proxies:` 节点文件为本项目明确采用的目标结构；全配置/Base64/URI/不同 VLESS 传输的原生支持不能在本云机断言；须看当前官方代理集/协议文档 |
| 软件选择地区池 | 软件 `select` 引用5个地区 `fallback` 组；另有全部节点、常见其他地区手选及旧手动入口，共18组；不含Meta专用include-all等键 | select/use/filter/fallback 的确切官方语义和最低版本待复核。未使用未证实的exclude-filter或负向前瞻；其他地区是常见国家正向匹配，非严格补集。地区组的REJECT哨兵及正则已做结构检查，**真实空池/全失效行为是必测门槛** |
| 自动测速/故障切换 | 优先故障切换，健康检查 30 分钟；不选择每次最低延迟 | 本项目没有启用 url-test 最低延迟模式。官方 fallback 与 url-test 的具体判定、缓存和版本需复核；不假定 REJECT 的健康判定等同其他内核 |
| 规则集 | HTTP classical payload；只留下 DOMAIN/SUFFIX/KEYWORD/IP-CIDR/IP-CIDR6；每日检查公共快照 | 规则数据与完整来源已实际读取；native 格式参考与普通结构测试不等于真实 Stash 核心校验。IP-ASN/PROCESS-NAME 等未核实项已剔除 |
| MITM | 仅 `http.mitm` 中的精确域名，设备生成证书，不含 CA 私钥 | app2smile Stash 原生覆写直接使用 `http.mitm`；当前证书菜单与最低版本待官方和设备确认；不设置泛域名或关闭 TLS 校验 |
| HTTP拒绝重写 | `http.rewrite` 的 `正则 - reject`；仅独立广告路径 | 已读取 blackmatrix7 固定SHA的原生 `rewrite/Stash/Advertising/Advertising.stoverride`；该文件头2025-08-26。不是直接套用QX重写；不假设reject等于reject-dict/img/200，具体返回、合并和版本仍待官方/手机核对 |
| 响应脚本 | `http.script` + `script-providers`，response、require-body、timeout；只用 `$request/$response/$done`；推荐公开入口使用与已读原生模块相同的url/interval声明 | 源码原生覆写已读；上游模块标 iOS≥15。**这不是 Stash 最低版本的官方证明**，本项目不凭此编造版本号；也不能把URL替代content说成用户本次DNS/节点错误的根因修复 |
| 请求空响应 | `http.script`的request、require-body:false；`$done({response:{status:200,headers,body}})`，只用于严格匹配的广告路径 | NobyDa固定SHA的原生Stash模块与对应JS调用链已读并校验，链接见[SOURCES](SOURCES.md#广告失效复审与原生请求响应证据2026-10-19)。不是复制QX动作名；最低版本及设备执行待确认 |
| 本地包的内嵌脚本 | `script-providers.<name>.content` 保存原JS正文，不加自造type字段；rule-providers按原优先级展开为普通规则 | 历史 `jinzaizhichi/stash-example@c0f273b8539b0aa648e0cab90cae7e5b4922a098/config.yaml` 实际存在content模式，原注释“仅推荐作为开发使用”，文件亦已停止维护。只参考原生字段，不复制无许可示例代码；当前官方/最低版本和iPhone导入仍未验证 |
| 脚本更新 | `script-providers.interval: 86400`，稳定脚本 URL；源脚本已窄化并固定本仓库路径 | interval 字段来自原生覆写；何时刷新/离线缓存失效行为仍待文档与手机验证，不保证断网更新 |
| 策略选择保留 | 固定配置名称、策略组名、provider 名；不写未经核实的 profile.store-selected | native 持久化行为未验证。普通 YAML 合并不能保存 UI 的运行时选择；更新前记下选择，更新后核对，必要时重选 |
| 定时签到（已暂停，仅备忘） | **不生成 cron**，用户已暂停此项 | 官方当前 cron 字段、时区、前后台语义、错过补跑及最低版本尚未查实；不能把 Surge cron 原样复制，也不承诺后台准点 |
| 原生持久化/通知（签到备忘） | 日后用户明确恢复才继续，不作为本轮交付前提 | N 携程脚本源码列出 Stash，但兼容声明不是本项目实机证明；当前未创建凭据存储脚本 |

## 必须复核的官方文档项目

从官方首页进入：配置/覆写、代理集与节点协议、策略组、规则集、HTTP/MITM、JavaScript API、版本更新记录（定时任务只作未来签到备忘）。记录每页最终 URL、获取日期、适用 Stash 版本和关键原文摘要。尚未成功读取的页面不伪造深层链接。

特别核实：

1. 多覆写的规则是前插还是覆盖，http.script 与 http.mitm 是否合并；不同版本 UI 的排序如何对应优先级。
2. `filter` 是否同时作用于静态 proxies 和 use；`fallback` 的静态节点与 provider 顺序、空集与全部失败是否保留 REJECT。若不符，必须先修配置；不能暗中允许 DIRECT。
3. 订阅解析格式、VLESS/Reality/XTLS/WS/gRPC 等逐项支持。不能把一个基础 VLESS 示例推广为支持所有机场 VLESS。
4. provider 更新失败/节点改名对缓存和选择的处理；软件组选择的持久化边界。
5. 自动签到已暂停，cron/设备存储等内容留待用户以后明确恢复时重新调查，不阻塞当前非签到功能。

[research/projects.json](../research/projects.json) 与 [sources.lock.json](../research/sources.lock.json) 可以复查已读原生模块和脚本，而不是用另一个代理客户端代替 Stash。

2026-10-19 补充：淘宝、小红书保留响应handler并修正字段兼容；微博改请求handler、脚本兼容旧响应式配置，详情见 [APP-SPLASH.md](APP-SPLASH.md)。新增固定console诊断仅含模块和状态，不含请求数据。精确域名不构成全域解密；不把原QX配置直接导入，不使用外部转换网站。当前官方文档访问阻塞仍未解除，设备验收仍独立进行。
