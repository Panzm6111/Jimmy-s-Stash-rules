# Stash 能力、证据等级与版本门槛

核实日期：2026-10-20。客户端限定 iPhone Stash，未使用其他内核代替验收。

## 当前重要阻塞

**当前云网络策略拒绝访问 Stash 官方文档站 [stash.wiki](https://stash.wiki/)**：HTTPS CONNECT 返回 403，页面内容未下载。所保存的域名放行草稿尚未应用到本机（运行配置 revision=1，custom allowed_hosts 为空）。这不是 Stash 网站返回的业务错误，也不是已获官方支持的证明。

最近一次官方HTTP文档访问记录仍为403，未读到正文；没有把旧访问记录当成新核实，也没有通过代理/镜像规避策略。按用户给出的当前官方调查，采用`http.url-rewrite`和原生空响应动作；旧`rewrite`别名是否仍兼容未知。`.3`根据provider错误恢复URL声明后，用户确认导入可用，但开屏仍在；本轮依据已读原生Stash示例添加手动自检，不把诊断实现当作广告效果已通过。

因此，当前配置是**已有原生格式参考与离线验证的候选交付**，未声称官方最低版本、真实合并、url-test 的空池细节已经核实。用户已反馈节点正常、HTTP/MITM开启且自建证书完全信任，并确认规则模式和广告组REJECT；仍反馈开屏没有效果。此次没有找到可确证全部失效的共同代码根因。更新后仍需完成 [手机验收](PHONE-CHECKLIST.md)。

## 已有来源与仍需确认的能力

| 能力 | 本项目采用的方式与证据 | 官方来源/版本要求状态 |
|---|---|---|
| 主配置 | `config/stash.yaml` 为当前统一整合入口；`config/main.yaml` 仅保留作维护和旧分层安装兼容模板。不放真实 URL，不假设任意 YAML 环境变量展开 | 官方入口 https://stash.wiki/；下载/编辑/更新行为仍待读取当前正文；不编造最低版本 |
| 覆写与深层映射 | 整合主配置 + 仅设备保存的私人 provider URL覆写；广告模块保留为构建源，有app2smile原生Stash源码参考 | 原生参考 `module/bilibili.stoverride`、`module/tieba.stoverride` 在锁定版本中实际存在。真实 map/list/rules 合并与覆写顺序需官方文档和合并预览复核 |
| 代理集 | `proxy-providers`，固定名称“机场”，更新间隔 86400 秒；真实订阅仅设备填写 | `proxies:` 节点文件为本项目明确采用的目标结构；全配置/Base64/URI/不同 VLESS 传输的原生支持不能在本云机断言；须看当前官方代理集/协议文档 |
| 软件选择地区池 | 软件 `select` 引用美国、日本、香港、新加坡、台湾5个 `url-test` 组；“自动节点”“其他地区”同样自动测速，“手动节点”保留select，共18组。海外AI默认美国，Apple默认DIRECT | select/use/filter/url-test 的当前官方语义和最低版本待复核。未使用未证实的exclude-filter或负向前瞻；公共“其他地区”是常见国家正向匹配，非严格补集。地区组的REJECT哨兵及正则已做结构检查，**真实空池/全失效行为仍需手机测试** |
| 自动测速 | 7池采用原生 `url-test`，HTTPS 204地址、1800秒检查间隔，选择测试延迟最低的可用候选；没有添加未经证实的tolerance/lazy字段 | [历史原生示例](https://github.com/jinzaizhichi/stash-example/blob/c0f273b8539b0aa648e0cab90cae7e5b4922a098/config.yaml#L434) 实际注释说明url-test选择最短URL测试延迟，fallback按顺序选可用候选。示例停止维护，仅参考字段，不复制无许可代码。当前默认容差、缓存、测试和切换时机未实测；不将其他内核行为当作Stash证明 |
| 规则集 | HTTP classical payload；只留下 DOMAIN/SUFFIX/KEYWORD/IP-CIDR/IP-CIDR6；每24小时尝试刷新公共快照 | 规则数据与完整来源已实际读取；native 格式参考与普通结构测试不等于真实 Stash 核心校验。IP-ASN/PROCESS-NAME 等未核实项已剔除 |
| MITM | 仅 `http.mitm` 中的精确域名，设备生成证书，不含 CA 私钥 | app2smile Stash 原生覆写直接使用 `http.mitm`；当前证书菜单与最低版本待官方和设备确认；不设置泛域名或关闭 TLS 校验 |
| HTTP原生URL重写 | `http.url-rewrite`；保留reject/reject-200/reject-dict/reject-img语义，校验器也接受reject-array | 依据用户此前提供的当前官方文档调查。旧blackmatrix7原生文件使用rewrite，别名兼容仍未证实；当前官文正文下载失败，最低Stash版本未知。用户将全部更新到最新版；没有编造版本号 |
| 响应脚本 | `http.script` + `script-providers`；response、require-body:true、timeout:5；默认无控制台日志。自检页手动开启15分钟固定状态记录 | app2smile原生覆写、blackmatrix7锁定`AdvertisingScript.stoverride`中的argument声明已实际读取并哈希锁定；不是当前官方或手机执行证明。没有证据时不盲改`$response.status`、method、body类型保护；自动长度/压缩处理需真机验收 |
| 固定空响应与Mock | 已移除原共享请求JS；原生URL动作直接处理固定空结果。需要先识别真实成功结构的业务仍用响应JS | 用户提供当前官方列出五种reject和Mock；当前固定结果不需自定义Mock。没有把普通拒绝与合法无广告结果视为相同，没有声称验证了原生返回字节/头部 |
| 整合专项与恢复 | 统一入口内置40个原专项，用户已取消逐App开关要求；域名拦截用广告组控制，HTTP处理通过HTTP/MITM设置暂停 | 入口结构符合新需求，真实效果仍待手机验收。旧分层文件只保留兼容；关闭额外同名覆写不能撤销内置动作，不可混装 |
| 临时诊断探针 | 仅已审阅45个精确主机的request handler，require-body:false；只记录URL是否命中预期，不改请求 | 字段形态有既有原生request参考；诊断覆写默认关闭，应与正式App专项隔离对照。没日志不能单独证明没进MITM |
| 手动自检页与本机临时记录 | 整合入口增加example.com精确MITM及单独路径request handler，`$done({response:{status,headers,body}})`返回本机页面。`$persistentStore.read/write`仅存15分钟内的固定状态、计数和时间 | 已核对NobyDa锁定原生Stash IPA-Installer模块及其JS：request响应包装和read/write调用均存在；仅作API用法依据，不复制安装器业务。来源哈希见[SOURCES](SOURCES.md)。没有新增真机成功结论；HTTPS页只证明测试主机的执行，不证明App命中 |
| HTTP/3 | 当前HTTP/3不进改写引擎，不能靠force-http-engine宣称解密 | 依据用户提供官方调查；当前无真实QUIC证据，未添加UDP阻断。不根据h3域名猜传输协议 |
| 整合入口与本地包的脚本来源 | `script-providers.<name>.url` 指向本仓库原JS文件，`interval: 86400`；不再生成仅含content的provider | 用户实机报`provider: url,payload, path are all empty`；出错的旧配置中11个content-only脚本声明没有这些来源字段。恢复项目既有app2smile原生Stash覆写使用的URL写法；不据报错猜测payload正文类型或最低版本 |
| 脚本更新 | 整合主入口包含URL声明，Stash联网加载JS；新增主机/handler须刷新主配置，不能只刷新JS。原路径加`?v=AD-20261020.4`区分新版资源请求 | URL/interval来自既有原生覆写；实际刷新和缓存时机待手机验证，不保证断网更新。配置和脚本当前均AD-20261020.4；版本参数不是Git固定提交或不可变快照 |
| 策略选择保留 | 固定配置名称、策略组名、provider 名；不写未经核实的 profile.store-selected | native 持久化行为未验证。普通 YAML 合并不能保存 UI 的运行时选择；更新前记下选择，更新后核对，必要时重选 |
| 定时签到（已暂停，仅备忘） | **不生成 cron**，用户已暂停此项 | 官方当前 cron 字段、时区、前后台语义、错过补跑及最低版本尚未查实；不能把 Surge cron 原样复制，也不承诺后台准点 |
| 原生持久化/通知（签到备忘） | 日后用户明确恢复才继续，不作为当前交付前提 | N 携程脚本源码列出 Stash，但兼容声明不是本项目实机证明；当前未创建凭据存储脚本 |

## 必须复核的官方文档项目

从官方首页进入：配置/覆写、代理集与节点协议、策略组、规则集、HTTP/MITM、JavaScript API、版本更新记录（定时任务只作未来签到备忘）。记录每页最终 URL、获取日期、适用 Stash 版本和关键原文摘要。尚未成功读取的页面不伪造深层链接。

特别核实：

1. 多覆写的规则是前插还是覆盖，http.script 与 http.mitm 是否合并；不同版本 UI 的排序如何对应优先级。
2. `filter` 是否同时作用于静态 proxies 和 use；`url-test` 对REJECT、静态节点与provider的测试处理、缓存、空集与全部失败行为。拒绝连接不能被视作“成功且0毫秒”的最快节点。若设备表现不符，必须先修配置；不能暗中允许DIRECT或其他地区。
3. 订阅解析格式、VLESS/Reality/XTLS/WS/gRPC 等逐项支持。不能把一个基础 VLESS 示例推广为支持所有机场 VLESS。
4. provider 更新失败/节点改名对缓存和选择的处理；软件组选择的持久化边界。
5. 自动签到已暂停，cron及账号凭据存储留待用户以后明确恢复时重新调查；当前仅使用无凭据的诊断状态存储，不实现签到。

[research/projects.json](../research/projects.json) 与 [sources.lock.json](../research/sources.lock.json) 可以复查已读原生模块和脚本，而不是用另一个代理客户端代替 Stash。

配置及脚本AD-20261020.4：真实实现、官方访问限制、脚本约定与待真机项统一见[详细规格](AD-ARCHITECTURE.md)。广告规则集、机场和远程JS均配置24小时尝试刷新，主配置每周手动刷新一次、修复发布后立即刷新；新主机或handler不能只刷新JS。测速30分钟不是规则更新。具体机制以[更新教程](UPDATES.md)为准，不承诺断网或iOS后台下准点执行。本轮增加自检和临时观察，地区策略、私人订阅机制和广告转换逻辑保留，自动签到暂停。
