# Stash 去广告：当前实现、修复证据与排查规格

当前配置与脚本：**AD-20261020.4**，仍用原 `config/stash.yaml` 整合入口。用户已确认AD-20261020.3恢复导入，但开屏广告仍出现，并确认规则模式、广告组REJECT；此前自建CA已完全信任。本轮共同字段与脚本保护审查没有找到可证实的全局失效根因，没有盲目删除保护、扩展拦截或声称广告已去除。修复的是排障必须复制配置且缺少执行证据的问题：在同一入口提供手动自检页和15分钟本机固定状态记录。原去广告转换、38条原生动作、分流、地区组、私人订阅接法与现有App解密主机保留；自动签到继续暂停。

## 1. 已修复问题与证据边界

| 历史问题或调整 | 当前实现 | 能确认到哪一层 |
|---|---|---|
| 主配置没有广告 RULE-SET，expanded 只换了不存在的 provider | `build_subscription.py` 保留并引用唯一“基础广告”provider；AD-20261020.2默认指向扩展快照，其他分流继续按原顺序展开 | 扩展包有实际引用；局域网、Apple推送、Microsoft登录例外与手动放行仍优先。规则集数量不等于开屏效果 |
| 配置用旧 `http.rewrite`，与用户核对的当前官方 `http.url-rewrite` 不同 | 修改真正的目录生成器与旧5款模块，统一生成 `url-rewrite` | 字段现与用户提供的当前官方调查一致；**旧 rewrite 是否仍为别名未验证，不能据此断言所有失败的根因** |
| 固定空响应绕到 JS；联通图片改成普通拒绝 | 原生 reject、reject-200、reject-dict、reject-img 分别保留；删除共享空响应脚本及对应 provider/request handler | 静态动作、端点正反例和无重复处理通过；真实状态码、头部与 App 回退须 Stash 验收 |
| 请求脚本依赖 `$response` 未定义；null/空对象会放行 | 固定响应不再经过请求 JS | 消除了该代码路径；**没有证明旧 Stash 真会传入 null/空对象** |
| 安装步骤过多，逐App开关需求已取消 | 原订阅入口整合现有专项；40份模块文件保留为构建源与旧安装兼容文件 | 已满足整合入口的结构要求；不再将逐App开关列为缺失功能。额外同名覆写仍须停用，避免重复挂载 |
| 脚本无版本、解析/结构问题难区分 | 原入口内置手动自检与限时本机状态；旧参数日志和隔离探针仅作维护兼容 | 默认不记录；开始排查后只存固定状态、时间、版本和计数。自检成功或无记录均不证明广告效果 |

官方能力核对的实际限制：最近一次常规和额外权限下请求官方站均得到云网络 403，**没有下载到当前正文**。`url-rewrite`、五种 reject 动作、Mock 和 HTTP/3 限制依据是用户此前提供的官方调查结论。`argument` 另有锁定版本 blackmatrix7 原生 Stash 模块声明作为参考。不能把这些说成已独立核实最低版本；目标为用户将更新的最新版，数字版本未提供。来源和未核实点见 [能力记录](STASH-CAPABILITIES.md)、[访问记录](../research/official-doc-access.json)。

## 2. 统一入口与日常使用

稳定主链接仍为：

```text
https://raw.githubusercontent.com/Panzm6111/Jimmy-s-Stash-rules/main/config/stash.yaml
```

主配置保留18个策略组、7个测速池、私人“机场”provider、原DNS与分流。**AD-20261020.4整合全部40款已有App专项、11份响应JS、1份手动自检JS及扩展域名规则集。** 唯一“基础广告”provider沿用名称，但其URL默认指向扩展快照，并有真实RULE-SET引用；无需再导入expanded。38条基础包仅保留作维护和旧分层安装兼容。扩展快照的规则数会随维护更新，实际数量见第9节自动生成的清单。扩展包可能误拦，也不能代替开屏接口处理；本次整合不代表效果已通过验收。

12份JS通过`script-providers.<name>.url`引用本仓库原路径，并带公开`?v=AD-20261020.4`版本参数以与旧资源缓存区分，`interval: 86400`。刷新主配置取得新URL、主机和handler，脚本正文仍由Stash联网加载；自检页及观察行显示实际运行版本，下载成功不能冒充执行成功。新主机/handler必须刷新主配置。恢复的非空URL声明继续保留，不回到content-only；精确版本URL也加入发布后下载和字节校验。本轮11份响应JS只增加限时观察hook，业务转换和已审阅URL范围未改。

首次更新：保留已能用的本机私人覆写和证书；停用额外App专项、旧整合“广告增强”、expanded及其同名副本；刷新**原主配置**并确认头部AD-20261020.4，再重建连接。未添加过这些额外覆写就跳过停用步骤。私人URL不写进公共配置，不需要重填已生效的私人接入。

**当前需求是整合入口，不设置逐App开关，也不另装expanded。** 主配置内的专项随主配置共同启用；额外覆写的启停不能撤销内置处理。“广告拦截→DIRECT”只控制域名路由，暂停HTTPS改写需关闭HTTP/MITM并重建连接。单App模块文件不是手机上的待安装清单。

历史兼容说明：原main.yaml、core和单App文件继续用于构建、来源审计及已有分层安装，原路径不删除。其覆写合并检查仅证明项目模型中的声明关系，不构成当前用户的额外安装步骤。设备私人精确白名单仍可优先放行确认误拦的主机，但不会停止HTTP处理。

整合生成时，专项域名规则放在LAN/关键直连例外之后、通用广告RULE-SET之前。扩展快照包含`flowplus.meituan.net`与`bootpreload.uve.weibo.com`的整域阻断，与本项目已有路径级处理冲突；主入口在广告位之前为两主机增加精确DIRECT例外，让已审阅URL处理接管，避免共享flowplus普通素材被整域拒绝。没有改上游快照、泛化白名单或声称已验证Stash原生执行顺序；这只是消除静态声明冲突。

本地ZIP保留基础主配置和可选广告增强合包、单App文件，各文件使用相同源逻辑。它仅保留作旧安装兼容及离线维护，不能重复叠加到整合订阅。离线expanded是含终止MATCH的整套有序路由快照，不能随意前插当普通广告列表。

## 3. 优先五款的广告链逐项核查

详细证据与每个分支的固定源码版本、行号、哈希见 [ad-repair-evidence.json](../research/ad-repair-evidence.json)。下面“实现”都指代码端，不等于当前 App 实测成功。已有测试样本为从固定源码重建的模拟结构；当前没有用户真实脱敏响应样本。

| App/环节 | 当前实现与匹配范围 | 来源、正常业务影响与验证 |
|---|---|---|
| 淘宝：实时开屏、预加载展示数据 | 保留 `guide-acs.m.taobao.com/gw/mtop.taobao.wireless.home.splash.awesome.get` 的已有响应分支；只改 `splash_home_base` 内 `taobao-splash` 条目的次数、等待、冷热启动、时间窗和图片/视频 URL | fmz200 `myBlockAds.js` 85–115行。MTOP失败不改；不删除普通首页、券、订单；兼容数字/布尔/字符串、补缺省字段、幂等与未知结构测试 |
| 淘宝：明确广告场景的补充请求 | 新增 `acs.m.taobao.com/gw/mtop.etao.noah.query/...` 且查询含独立 `tao_splash` 标记时原生空 JSON | fmz200合集4431行。没有这个广告标记的相同共享 API 不匹配；正例、普通场景、近似路径、伪域名测试 |
| 淘宝：cloudvideo 视频 | 已读 `cloudvideo.video.query` 上游63–83行，**未泛化启用** | 上游对整个响应清资源/时长，接口可能也用于商品视频；缺少当前开屏场景判别证据。当前不能证明视频开屏完整覆盖，不能改为整个视频 API 拒绝 |
| 淘宝：活动弹层/素材 | 已读 `poplayer.template.alibaba.com` 分支126–146行，**未泛化启用**；开屏主分支会清已识别广告条目的素材 URL | 上游只看通用活动结构，也可能清正常促销/领券；缺少广告专用判别。不封整域或整个活动 JSON |
| 微博：实时与预载 | `bootrealtime.../v*/ad/realtime`、`bootpreload.../v*/ad/preload` 改原生 reject-dict，支持结尾 `/` | fmz200 `weibo.snippet` 128–129行。不再等 JS 返回或依赖请求 `$response` 形态；近似路径不匹配 |
| 微博：SDK 广告/素材 | 新增精确广告主机 `sdkapp.uve.weibo.com`、`wbapp.uve.weibo.com`、`adimg.uve.weibo.com`、`adimg.vue.weibo.com` 的广告组路由 | 上游域名列表及 sdkad/wbpullad 路径旁证。SDK这两主机由上游列为广告专用，采用域名路由，**没有再重复添加相同主机 HTTP handler**；未拦通用微博 API/头像主机 |
| 微博：信息流 | `api.weibo.cn/2/searchall`、`statuses/container_timeline_topic`、`...topicpage` 的 `items` 中明确 `mblogtypename=广告`、`is_ad=1` 或 `ad_state=1` 项；搜索另处理一层子项 | fmz200 `weibo_ads.js` 当前锁定文件。保留正常项、账号信息、推荐、评论、导航；不复制清理页签、日志或关注项。**未声称覆盖首页 friends_timeline 的全部广告** |
| 小红书：开屏计划/预载 | 原 `system_service/splash_config`，推迟已识别 `ads_groups` 与子广告的时间 | fmz200小红书52–65行；数字/数字字符串/缺省字段测试，结构化未知时间不硬改 |
| 小红书：启动配置 | 新增 `system_service/config`，只删除已存在的 `data.splash` | 上游42–50行也删除 theme/loading/store，本项目不复制这些；保留主题、商城、加载图、普通业务配置。结尾 `/` 与 code数字字符串变体测试 |
| 小红书：广告素材 | 四个 `ads-img-{qc,al}.xhscdn.com`、`ads-video-{al,qc}.xhscdn.com` 精确广告组路由 | fmz200合集5507–5510行；不封图片/视频共享CDN，不MITM素材域名 |
| 小红书：信息流 | 仅 `/api/sns/v6/homefeed` 中 `ads_info` 为非空对象的明确赞助项 | 上游286–310行；保留普通笔记、直播、带货/商品属性、card_icon、空/null标记。不加入水印、下载、画质、用户信息修改；其他版本路径不猜测 |
| 美团：loadInfo | 保留 `wmapi.meituan.com/api/v*/loadInfo` 响应中已知 `data.startpicture.ad/mk` 广告数组处理 | blackmatrix7 startup外卖分支；保留其他启动业务字段，不把整个loadInfo空响应 |
| 美团：实时/预载专用接口 | 新增 `wmapi.meituan.com/api/v7/openscreen`、`startpicture` 原生空JSON | fmz200合集3179行；限定来源版本v7，不推断所有版本。**仍属外卖链路，不能称美团主App全部启动广告已覆盖** |
| 美团：素材 | 新增 `img.meituan.net/bizad/bizad_brandCpt_数字.jpg`；`s3plus/flowplus.meituan.net/v*/.../linglong/...gif或jpg` 原生空图片 | 上游3180–3181行；不拦商品图片/领券素材目录。MP4不是合法GIF，未把图片空响应泛化到视频，未导入ZIP/活动总配置规则 |
| 京东：启动与展示控制 | `api.m.jd.com/client.action` 查询中唯一 `functionId=start`；兼容二维广告列表与平铺广告记录；只改已知标量 showTimes/time、有效格式展示日期和 daily计数 | blackmatrix7 startup京东分支；fmz200京东258–266行仅作平铺结构线索。保留订单/券/倒计时，不采用上游 countdown=100。重复 functionId、未知字段类型、正常函数、幂等测试 |
| 京东：尚缺证据的变体 | 没有任意扫描所有 client.action POST 正文，未猜测其他 functionId/加密结构 | 已读来源都把start放在URL。本地解析不能证明最新版请求布局；若当前请求改为正文参数，需要脱敏命中元数据后补，不要求Cookie或正文 |

其余原有专项继续按已审阅路径提供，固定响应统一原生化；阿里云盘、菜鸟、瑞幸、微信公众号、B站、贴吧等响应分支也使用同一受保护运行模板。没有扩大其会员/下载/积分/正常券业务权限，没有拿“40个文件”替代实际效果结论。完整范围和实际动作在生成附录中逐项列出。

## 4. 原生固定响应与保留 JS 的边界

| 动作 | 预期意义 | 本项目使用边界 |
|---|---|---|
| reject | 原生拒绝请求，与合法空结果不同 | 只保留来源原本的专用广告拒绝路径；不能保证不重试、不留倒计时 |
| reject-200 | 200、空正文 | 来源要求空正文的专用广告/素材端点 |
| reject-dict | 200、JSON空对象 | 来源明确允许空广告JSON的专用端点；不是伪造支付/订单成功 |
| reject-array | 200、JSON空数组 | 校验器支持当前官方列出的动作；当前选用条目没有需要空数组的路径，不为凑数量新增 |
| reject-img | 原生空图片响应 | 恢复联通原意，并用于新增限定图片素材；不套给MP4 |
| Mock | 可以自定义固定响应时再采用 | 已评估；当前内置动作满足固定空结果，不需要自造头部/状态的Mock。瑞幸等要先判断真实成功响应，因此保留响应JS，不能在请求期直接Mock成功 |

这些预期依据用户提供的当前官方能力调查及来源动作意图；**本地不模拟一个HTTP服务来冒充Stash原生返回的状态/Content-Type/图片字节验证**。当前规则没有证据要求自定义响应头，因此不声称原生动作保留了旧JS的 Cache-Control:no-store。若手机证据显示需特定响应头，必须按正式Mock约定补测，不随意返回404当无广告结果。

## 5. 脚本 API、失败保护和日志

11个响应脚本各自独立执行，保留原许可，共同运行模板构建到各JS源文件，Stash按URL加载；用户不需要另加App覆写。只读 `$request.url/method`、`$response.body/status` 和临时 `$argument`；不读取Cookie/Authorization、不保存正文、不联网、不通知。未手动开始时只检查项目专用会话键，不写存储；有效排查窗口内才写固定状态、版本、时间和有上限的计数。探针只读URL用于内存匹配，**不读取请求或响应正文、头部**。

- 响应handler统一 `type: response`、`require-body: true`、`timeout: 5`。B站限GET，其他限GET/POST。缺失/null/空响应对象、正文非字符串或空正文均放行。没有把空对象响应当成功业务结构。
- 正文限 **2 MiB UTF-8编码长度**，不再把JS字符串码元数当网络字节数。二进制不猜测解码；不开启 binary-mode 或处理protobuf。
- 实际原生参考使用 `$response.status`。数字200和字符串"200"接受；错误、完整HTTP状态行或非预期形态不猜测放行修改。只有statusCode的形态输出unsupported-status；两者都不存在时沿用旧无状态字段保护分支，仍要求JSON与已知业务结构。具体原生对象形态待真机记录。
- 保留业务错误/MTOP错误，空修改对象 `$done({})` 保留原响应；产生修改只返回 `{body: JSON字符串}`，不手动伪造压缩/长度头。Stash自动重编码和头部处理仍是原生验收项。
- try/finally确保本地执行恰好调用一次`$done`。没有异步请求/重试。**原生5秒超时由Stash记录，JS被终止后不能自己补发timeout日志或保证回退**。
- 当前推荐诊断：使用下节内置自检页开始15分钟观察，无需副本、覆写或修改YAML。原`diagnostic=1`参数日志仅为维护兼容保留；主入口继续为0，避免日常控制台输出。

日志示例：`[JimmyAds][taobao][AD-20261020.4] changed`。状态仅为固定枚举：url-unmatched、unsupported-method、body-unavailable、body-too-large、http-error、unsupported-status、non-json、parse-error、unsupported-schema、unchanged、changed、exception。没有异常详情、账号值、完整URL/查询或正文。默认参数0不输出控制台日志；参数日志开启时每次调用最多一条。页面开启的观察独立于参数日志，最多持续15分钟，失效后不再写入；测试包含私人哨兵、损坏记录和故障存储。并发写入可能覆盖计数，因此只用于命中线索，不是精确流量统计。

<a id="6-临时只读诊断先确定请求有没有进入引擎"></a>

## 6. 手动自检：先取得真正的执行证据

在Stash运行时，用Safari打开 **https://example.com/jimmy-stash-check**。这个页面由本机请求脚本返回，没有远程后台、外部图片、统计或上传。HTTPS页面显示成功只证明这次example.com的HTTP引擎、请求脚本和MITM链工作；不代表淘宝/微博等App已解密、响应已被修改或广告已去除。页面显示实际http/https枚举，避免把Safari自动升级误当明文HTTP验证。

1. 刷新原公共配置至AD-20261020.4，私人覆写与证书沿用。打开上述地址，看到“Jimmy Stash 自检”与新版标记。
2. 点开始15分钟诊断，再进入结果页。正常使用淘宝、小红书等关注的App，包含冷启动、后台返回及预载后再次启动；不要求重装App。
3. 回到无查询参数的结果页刷新，仅反馈App名称与页面中文固定状态。不要再次刷新带start=1的地址，否则会开始新会话；页面提供固定返回链接。
4. 点停止或等15分钟到期。没有后台任务、定时联网或通知；观察只在已经匹配的响应脚本执行时记录。旧计数保留在设备专用键里、开启新会话后不会混用，不含私人请求内容。

存储契约：会话键`jimmy.ads.diag.session.v1`，值为数字id/until；每个响应模块键`jimmy.ads.diag.<模块ID>.v1`仅包含sessionId、脚本版本、last毫秒时间戳和固定状态计数，计数上限9999。白名单、数值与会话有效期均校验；损坏、未知字段或存储异常不进入页面，也不妨碍广告处理或单次$done。没有会话或会话过期不写入。

新增解密主机只有`example.com`，为精确主机，不是通配；其HTTPS均属于该MITM范围，但自检handler只处理`/jimmy-stash-check`以及固定start/stop参数，不处理普通主页或其他业务路径。原45个App主机不变。Stash原生request返回`$done({response:{status,headers,body}})`和persistentStore用法参考已锁定NobyDa IPA-Installer原生模块及脚本；本项目未复制安装业务。返回HTML设置no-store，不读请求头和正文。

空记录不能单独区分没发新请求、URL变更、缓存、HTTP/3、MITM未命中或脚本未取得新版。微博开屏等38条原生拒绝不经过响应JS，因此没有其响应记录也不能判为失败。原生动作仍需查看Stash本机HTTP/重写命中。旧`modules/diagnostics/ads.stoverride`只保留给维护时隔离观察，不作为当前用户的导入步骤，不叠加到正常HTTP动作。

| 观察到的证据 | 可以判断的方向 | 不能直接下的结论 |
|---|---|---|
| 主配置或自检页面不是AD-20261020.4，或者观察行显示其他脚本版本 | 检查选中配置和远程脚本加载；新主配置为JS URL添加公开v版本参数以区分旧缓存 | 只刷新机场不能更新本项目；HTTP200下载也不证明执行或App效果 |
| TCP443连接存在，但没有解密HTTP记录 | 检查实际主机/端口、HTTP/MITM适用范围、证书固定或其他加密；既有CA信任记录保留 | 不先要求重装证书；不关闭TLS验证 |
| 已解密，探针request-url-unmatched | 请求进入引擎，但不匹配目前专用广告端点，需核对当前App接口 | 不把同主机所有业务请求当广告 |
| request-url-matched后，正式响应日志body-unavailable/non-json/parse-error | handler进入，但没有可处理的JSON正文/解析失败 | 不自动删未知业务数据 |
| unsupported-schema | 已匹配URL且解析完成，当前业务结构不在支持范围 | 不能当作“没有广告” |
| unchanged | 识别了已支持结构，这次无需修改 | 不证明App没有缓存广告或备用广告请求 |
| changed | 这次JSON产生实际修改 | 不证明所有开屏、倒计时和业务都通过 |
| exception或Stash原生超时 | 执行发生异常，或被原生终止 | 不输出异常/完整配置寻找凭据，不保证所有层都fail-open |

## 7. HTTP/3、缓存、端口与更新

当前官方调查指出 HTTP/3 不进入改写引擎。当前没有真实连接证据，**未添加任何UDP阻断**，也不把`h3.open.taou.com`的名字当作QUIC证明。`force-http-engine`不能被宣传为解密HTTP/3。

如果在Stash本机确实观察到某广告主机UDP443，先记录该主机/端口/发生时间，再制作只针对该主机的UDP443对照规则，并验证是否回退TCP和正常业务；当前没有证据，因此没有发布未经确认语法/协议适用性的默认限制。不能全局禁UDP、通配MITM、泛解密银行支付域名或关闭TLS验证。显式非443端口、IP直连、证书固定、应用层加密均可能超出现有处理，不擅自宣称覆盖。

区分新广告与预加载：先使用已启用的整合配置一段时间，再冷启动、后台返回、再次启动进行多轮观察。已下载素材可在没有新网络请求时展示；网络规则不能删除App私有文件。优先用App自己的清缓存入口，保留登录/重要数据，不默认要求卸载重装。

| 层 | 更新操作 | 会不会带入新处理 |
|---|---|---|
| 公共主配置 | 建议每周手动刷新原URL一次；发布修复后立即刷新 | 主机、原生动作、handler和11份JS的来源声明一并更新；扩展provider默认引用也在这里。不承诺后台自动更新整份配置 |
| 旧App覆写（仅历史兼容） | 仅已有旧分层安装仍分别更新覆写 | 当前整合入口已包含这些声明，不新增或叠加；本地副本不会自动跟随远程声明 |
| 远程广告规则集 | 建议保持现有86400秒，即24小时自动尝试刷新；下载错误时手动刷新 | 整合入口默认引用扩展快照，存在真实RULE-SET；这是刷新间隔，不是每日北京时间零点执行保证 |
| 广告JS | 通过原URL读取，86400秒间隔尝试更新；需要立即取得JS修复时刷新脚本资源 | JS正文与主配置分开下载；新增主机/handler时仅刷新JS不够，不保证断网或iOS后台准点更新 |
| 本地静态包/私人节点快照 | 重新用当前源构建/导入，保留设备私人信息 | 静态规则和HTTP声明需重新构建；JS仍通过原URL获取，首次使用需联网；私人节点快照不自动更新机场 |
| 私人机场 | 建议保持现有86400秒，即24小时自动尝试刷新；节点异常或机场通知变更时手动刷新 | 不继承机场响应中的分流/DNS；机场更换URL时仍须本人在设备修改，不能自动发现新URL |

以上频率统一见[更新教程](UPDATES.md)。7个节点池的1800秒检查是30分钟测速，不是更新规则。规则集只下载本仓库已发布快照；建议电脑每天运行一次[本地维护工具](MAINTENANCE.md)检查上游。普通规则可在隔离生成和验证后更新本地文件，专项脚本、重写与MITM变化仍需审查适配；发布到原分支后手机才能取得更新。没有部署GitHub定时同步，也没有自动修复App接口或替代真机验收。

## 8. 验收、误伤与回退

验证分三层：静态配置/源与生成结果；源代码重建模拟样本；真实iPhone Stash解析、命中及广告效果。已有检查覆盖前两层，**第三层未运行**。官方站403、数字版本缺失、无真实脱敏响应都记录为限制，不用62个模拟测试或38,066条规则替代效果判断。精确运行记录见 [PROGRESS](../PROGRESS.md)。

手机最小验收顺序：整合入口已载入全部已有专项，先依次观察淘宝、微博、小红书，然后美团、京东及其他App；观察顺序不改变整合配置的已启用范围。每款分别检查冷启动、后台返回、正常使用触发预加载后再启动；记录广告是否消失、有无空白页/倒计时/更长加载，并检查登录、搜索、消息、视频、正常领券等业务。广告有频控，至少多次观察并结合命中记录；可与设备原来可用的备份配置对照；当前推荐命中取证使用上述自检页，不要求创建副本。单次没有广告不能判成功。

需要反馈时只提供：App名和广告位置、冷启动/后台/预载场景、是否空白/倒计时、对应固定版本/状态日志，以及仅包含主机、端口、协议、路径（**去掉整个查询**）的手工摘录。若更新后仍异常，再记录当时数字版本帮助复现。不要发送私人完整配置、原始日志、Cookie、token、证书私钥或响应正文。用户将全部更新，当前不再重复索取版本。

整合入口误伤时，先将广告组DIRECT判断域名拦截是否相关；它不会停止HTTP。需快速恢复时切换手机上原来可用的配置备份，保留私人覆写并核对关联/地区选择。没有备份且急需用该App时，可暂关Stash作对照，但会同时停止本项目代理分流和去广告。用户已取消逐App开关需求；当前恢复步骤以整体域名拦截、HTTP/MITM和可用配置备份为单位，不要求另建多份App覆写。代码基线`936fe45`可供维护者取历史公共文件，但回退到它会恢复本轮已确认的旧接入缺陷，不应作为长期方案。

<!-- GENERATED-AD-SPEC -->

## 9. 自动核对的当前完整清单

以下内容直接由现有配置和运行脚本生成。数量描述文件结构，不表示广告效果。

| 项目 | 实际值 |
|---|---|
| app_modules | 40 |
| public_main_rules | 5,287 |
| basic_ad_payload | 38 |
| expanded_ad_payload | 38,066 |
| app_domain_rules | 19 |
| native_url_rewrites | 38 |
| response_handlers | 11 |
| request_handlers | 1 |
| runtime_js_providers | 12 |
| remote_script_providers | 12 |
| inline_script_providers | 0 |
| mitm_exact_hosts | 46 |
| app_mitm_exact_hosts | 45 |
| manual_self_check_js | 1 |
| optional_probe_js | 1 |

公共主配置整合以下40款专项的11份响应JS，以及1份手动自检JS，按原路径附公开版本参数获取。自检不是新增App去广告。此表列出构建来源与处理范围，用户不需逐款导入；模块原路径保留作维护和旧安装兼容。逐App开关已取消需求，旧探针另列、默认不挂载。

| App专项 | 维护源路径 | 域名路由 | 原生URL动作 | 响应handler | 当前范围 |
|---|---|---|---|---|---|
| 58同城广告专项（维护源） | [58tongcheng](../modules/ads/58tongcheng.stoverride) | 0 | 1 | 0 | AD-20261020.1；仅 home/advertising 和 appadv；保留职位、联系与发布。已纳入整合入口，无需单独导入；需设备验收。 |
| 阿里云盘广告专项（维护源） | [alipan](../modules/ads/alipan.stoverride) | 0 | 0 | 1 | AD-20261020.1；仅 onboard_list 的4种推广banner；不宣称阿里云盘开屏或全界面去广告。已纳入整合入口，无需单独导入；需设备验收。 |
| 高德地图广告专项（维护源） | [amap](../modules/ads/amap.stoverride) | 2 | 2 | 0 | AD-20261020.1；两个独立启动广告接口及 optimus 广告域名；保留路线、定位和普通地图图片。已纳入整合入口，无需单独导入；需设备验收。 |
| 百度网盘广告专项（维护源） | [baidu-netdisk](../modules/ads/baidu-netdisk.stoverride) | 0 | 1 | 0 | AD-20261020.1；网盘独立 ad/adx 广告接口；不拦福利、会员、下载、分享。已纳入整合入口，无需单独导入；需设备验收。 |
| 哔哩哔哩广告处理（维护源） | [bilibili](../modules/ads/bilibili.stoverride) | 0 | 0 | 1 | AD-20261020.1；仅 JSON 开屏与推荐流广告；不处理会员权限、视频贴片或领券。已纳入整合入口，无需单独导入；需设备验收。 |
| 菜鸟广告专项（维护源） | [cainiao](../modules/ads/cainiao.stoverride) | 0 | 0 | 1 | AD-20261020.1；仅 ads.show 的明确 adItemDetail 广告项；不包含 mshow 或完整首页净化。已纳入整合入口，无需单独导入；需设备验收。 |
| 中国移动广告专项（维护源） | [cmcc](../modules/ads/cmcc.stoverride) | 0 | 1 | 0 | AD-20261020.1；仅 explorePage/getAdverList 候选广告接口；没有完整启动广告去除证据。已纳入整合入口，无需单独导入；需设备验收。 |
| 携程旅行广告专项（维护源） | [ctrip](../modules/ads/ctrip.stoverride) | 1 | 0 | 0 | AD-20261020.1；仅 ma-adx 主机的广告/统计请求；没有完整开屏去除证据。已纳入整合入口，无需单独导入；需设备验收。 |
| 大麦广告专项（维护源） | [damai](../modules/ads/damai.stoverride) | 0 | 1 | 0 | AD-20261020.1；专用 home.welcome 开屏；不屏蔽 HTTPDNS、票务或下单。已纳入整合入口，无需单独导入；需设备验收。 |
| 大众点评广告专项（维护源） | [dianping](../modules/ads/dianping.stoverride) | 0 | 1 | 0 | AD-20261020.1；仅 loadsplashconfig 开屏配置；不删普通首页、优惠或评价。已纳入整合入口，无需单独导入；需设备验收。 |
| 东方财富广告专项（维护源） | [eastmoney](../modules/ads/eastmoney.stoverride) | 1 | 0 | 0 | AD-20261020.1；仅 emdcadvertise 独立广告主机；不代表行情页面全部推广。已纳入整合入口，无需单独导入；需设备验收。 |
| 华住会广告专项（维护源） | [huazhu](../modules/ads/huazhu.stoverride) | 0 | 1 | 0 | AD-20261020.1；仅 getAppStartPage 开屏；保留酒店优惠、新客权益、更新和预订。已纳入整合入口，无需单独导入；需设备验收。 |
| 京东金融广告专项（维护源） | [jingdong-finance](../modules/ads/jingdong-finance.stoverride) | 2 | 0 | 0 | AD-20261020.1；仅 bdsp-x/dsp-x 广告主机候选；不包含金融网关或完整开屏。已纳入整合入口，无需单独导入；需设备验收。 |
| 京东广告专项（维护源） | [jingdong](../modules/ads/jingdong.stoverride) | 0 | 0 | 1 | AD-20261020.1；仅 URL 中 functionId=start 的历史开屏展示字段；不包含全部京东广告。已纳入整合入口，无需单独导入；需设备验收。 |
| 肯德基广告专项（维护源） | [kfc](../modules/ads/kfc.stoverride) | 0 | 1 | 0 | AD-20261020.1；仅 advertisement 路径广告素材候选；不包含完整开屏控制、菜单或优惠券。已纳入整合入口，无需单独导入；需设备验收。 |
| 猎聘广告专项（维护源） | [liepin](../modules/ads/liepin.stoverride) | 0 | 1 | 0 | AD-20261020.1；明确命名的 live.get-ad-cards；不拦职位推荐或投递。已纳入整合入口，无需单独导入；需设备验收。 |
| 瑞幸咖啡广告专项（维护源） | [luckin](../modules/ads/luckin.stoverride) | 0 | 0 | 1 | AD-20261020.1；仅 sys/app/adposNew 独立广告响应；保留点单、商品与优惠券。已纳入整合入口，无需单独导入；需设备验收。 |
| 脉脉广告专项（维护源） | [maimai](../modules/ads/maimai.stoverride) | 0 | 2 | 0 | AD-20261020.1；仅 adshow；保留礼物、消息和普通推荐。已纳入整合入口，无需单独导入；需设备验收。 |
| 麦当劳广告专项（维护源） | [mcdonalds](../modules/ads/mcdonalds.stoverride) | 0 | 1 | 0 | AD-20261020.1；专用 portal/home/splash；保留点餐、支付、领券。已纳入整合入口，无需单独导入；需设备验收。 |
| 美团广告专项（维护源） | [meituan](../modules/ads/meituan.stoverride) | 0 | 3 | 1 | AD-20261020.1；外卖loadInfo已知startpicture广告数组；v7 openscreen/startpicture专用接口与限定开屏图片素材；不是主App完整覆盖。已纳入整合入口，无需单独导入；需设备验收。 |
| 米家广告专项（维护源） | [mijia](../modules/ads/mijia.stoverride) | 0 | 1 | 0 | AD-20261020.1；仅 openingBanner 两个端点；保留设备控制、普通推荐和自动化。已纳入整合入口，无需单独导入；需设备验收。 |
| 网易邮箱大师广告专项（维护源） | [netease-mail](../modules/ads/netease-mail.stoverride) | 0 | 2 | 0 | AD-20261020.1；mmad 素材和 searchMultiAds/showAds；保留邮件、搜索和同步。已纳入整合入口，无需单独导入；需设备验收。 |
| 网易云音乐广告专项（维护源） | [netease-music](../modules/ads/netease-music.stoverride) | 0 | 3 | 0 | AD-20261020.1；仅3个精确主机的 api/ad 或 eapi/ad 路径候选；不解密 EAPI 正文。已纳入整合入口，无需单独导入；需设备验收。 |
| 拼多多广告专项（维护源） | [pinduoduo](../modules/ads/pinduoduo.stoverride) | 0 | 2 | 0 | AD-20261020.1；仅 cappuccino/splash；保留首页、买菜、红包和领券。已纳入整合入口，无需单独导入；需设备验收。 |
| 铁路12306广告专项（维护源） | [railway12306](../modules/ads/railway12306.stoverride) | 1 | 0 | 0 | AD-20261020.1；仅 ad.12306.cn 独立广告主机；不保证取消客户端缓存开屏。已纳入整合入口，无需单独导入；需设备验收。 |
| 淘宝开屏广告处理（维护源） | [taobao](../modules/ads/taobao.stoverride) | 0 | 1 | 1 | AD-20261020.1；专用开屏展示控制、明确tao_splash场景；通用视频/活动弹层未泛化屏蔽。已纳入整合入口，无需单独导入；待真机验收。 |
| 淘票票广告专项（维护源） | [taopiaopiao](../modules/ads/taopiaopiao.stoverride) | 0 | 1 | 0 | AD-20261020.1；仅 queryloadingbanner 启动广告；保留普通活动、选座和购票。已纳入整合入口，无需单独导入；需设备验收。 |
| 贴吧开屏广告处理（维护源） | [tieba](../modules/ads/tieba.stoverride) | 0 | 0 | 1 | AD-20261020.1；仅 JSON 开屏广告；不改帖子、登录、支付或券接口。已纳入整合入口，无需单独导入；需设备验收。 |
| UC浏览器广告专项（维护源） | [uc](../modules/ads/uc.stoverride) | 2 | 0 | 0 | AD-20261020.1；仅 ads.uc.cn、adslot.uc.cn 独立广告主机；不包含网页同域广告。已纳入整合入口，无需单独导入；需设备验收。 |
| 航旅纵横广告专项（维护源） | [umetrip](../modules/ads/umetrip.stoverride) | 0 | 1 | 0 | AD-20261020.1；仅 fs/advert/polite 广告素材候选；不包含开屏展示控制或航班业务。已纳入整合入口，无需单独导入；需设备验收。 |
| 中国联通广告专项（维护源） | [unicom](../modules/ads/unicom.stoverride) | 0 | 2 | 0 | AD-20261020.1；专用启动/广告接口；保留 accountListData、客户端配置和缴费。已纳入整合入口，无需单独导入；需设备验收。 |
| 云闪付广告专项（维护源） | [unionpay](../modules/ads/unionpay.stoverride) | 2 | 0 | 0 | AD-20261020.1；仅 ads.95516.com 和 ads.cup.com.cn 广告请求；不代表云闪付全界面去广告。已纳入整合入口，无需单独导入；需设备验收。 |
| 微信广告专项（维护源） | [wechat-articles](../modules/ads/wechat-articles.stoverride) | 0 | 0 | 1 | AD-20261020.1；仅历史公众号 getappmsgad 的广告字段；不包含朋友圈、视频号或聊天。已纳入整合入口，无需单独导入；需设备验收。 |
| 微博开屏广告处理（维护源） | [weibo](../modules/ads/weibo.stoverride) | 4 | 2 | 1 | AD-20261020.1；实时/预载空JSON、专用SDK与素材主机、话题/搜索明确广告项；不是首页全部信息流覆盖。已纳入整合入口，无需单独导入；待真机验收。 |
| WPS Office广告专项（维护源） | [wps](../modules/ads/wps.stoverride) | 0 | 2 | 0 | AD-20261020.1；仅广告统计请求与 feeds_ad 素材；没有完整开屏或文档内广告去除证据。已纳入整合入口，无需单独导入；需设备验收。 |
| 下厨房广告专项（维护源） | [xiachufang](../modules/ads/xiachufang.stoverride) | 0 | 1 | 0 | AD-20261020.1；仅 vN/ad/ 专用广告路径；保留菜谱、购物和内容图片。已纳入整合入口，无需单独导入；需设备验收。 |
| 闲鱼广告专项（维护源） | [xianyu](../modules/ads/xianyu.stoverride) | 0 | 1 | 0 | AD-20261020.1；仅 idlecommerce.splash.ads；保留聊天、交易、闲鱼币和搜索。已纳入整合入口，无需单独导入；需设备验收。 |
| 小红书开屏广告处理（维护源） | [xiaohongshu](../modules/ads/xiaohongshu.stoverride) | 4 | 0 | 1 | AD-20261020.1；开屏时间、启动配置splash、专用广告素材、v6首页明确赞助项；不改下载/水印/画质/用户信息。已纳入整合入口，无需单独导入；待真机验收。 |
| 小宇宙广告专项（维护源） | [xiaoyuzhou](../modules/ads/xiaoyuzhou.stoverride) | 0 | 1 | 0 | AD-20261020.1；仅 flash 开屏；保留节目推荐、AI总结、搜索和播客音频。已纳入整合入口，无需单独导入；需设备验收。 |
| 知乎广告专项（维护源） | [zhihu](../modules/ads/zhihu.stoverride) | 0 | 2 | 0 | AD-20261020.1；仅开屏、顶部横幅与 ad-style-service 候选；不包含全部回答和信息流广告。已纳入整合入口，无需单独导入；需设备验收。 |

## 10. 精确原生声明与基础规则原文

下列原生字段直接摘自主配置，省略完整分流，不能直接作为主配置导入。12份provider用url指向第12节的同名JS，均有非空来源。LAN/系统例外优先，然后精确路径接管例外、专项域名与广告RULE-SET，后面仍有完整分流与终止MATCH。

<!-- CONFIG:ad-core -->
```yaml
proxy-groups:
- name: 广告拦截
  type: select
  proxies:
  - REJECT
  - DIRECT
rule-providers:
  基础广告:
    type: http
    behavior: classical
    url: https://raw.githubusercontent.com/Panzm6111/Jimmy-s-Stash-rules/main/rules/vendor/ads-expanded.yaml
    interval: 86400
rules:
- DOMAIN,flowplus.meituan.net,DIRECT
- DOMAIN,bootpreload.uve.weibo.com,DIRECT
- DOMAIN,optimus-ads.amap.com,广告拦截
- DOMAIN,optimus-ads.amap.com.w.alikunlun.com,广告拦截
- DOMAIN,ma-adx.ctrip.com,广告拦截
- DOMAIN,emdcadvertise.eastmoney.com,广告拦截
- DOMAIN,bdsp-x.jd.com,广告拦截
- DOMAIN,dsp-x.jd.com,广告拦截
- DOMAIN,ad.12306.cn,广告拦截
- DOMAIN,ads.uc.cn,广告拦截
- DOMAIN,adslot.uc.cn,广告拦截
- DOMAIN,ads.95516.com,广告拦截
- DOMAIN,ads.cup.com.cn,广告拦截
- DOMAIN,sdkapp.uve.weibo.com,广告拦截
- DOMAIN,wbapp.uve.weibo.com,广告拦截
- DOMAIN,adimg.uve.weibo.com,广告拦截
- DOMAIN,adimg.vue.weibo.com,广告拦截
- DOMAIN,ads-img-qc.xhscdn.com,广告拦截
- DOMAIN,ads-img-al.xhscdn.com,广告拦截
- DOMAIN,ads-video-al.xhscdn.com,广告拦截
- DOMAIN,ads-video-qc.xhscdn.com,广告拦截
- RULE-SET,基础广告,广告拦截
http:
  mitm:
  - example.com
  - api.zhihu.com
  - api.xiaoyuzhoufm.com
  - edith.xiaohongshu.com
  - acs.m.goofish.com
  - api.xiachufang.com
  - ios.wps.cn
  - mobile-pic.cache.iciba.com
  - bootrealtime.uve.weibo.com
  - bootpreload.uve.weibo.com
  - api.weibo.cn
  - mp.weixin.qq.com
  - m.client.10010.com
  - oss.umetrip.com
  - tiebac.baidu.com
  - acs.m.taobao.com
  - guide-acs.m.taobao.com
  - api.pinduoduo.com
  - api.yangkeduo.com
  - interface.music.163.com
  - interface3.music.163.com
  - ipv4.music.163.com
  - appconf.mail.163.com
  - client.mail.163.com
  - home.mi.com
  - wmapi.meituan.com
  - img.meituan.net
  - s3plus.meituan.net
  - flowplus.meituan.net
  - api.mcd.cn
  - open.taou.com
  - h3.open.taou.com
  - capi.lkcoffee.com
  - api-ac.liepin.com
  - res.kfc.com.cn
  - api.m.jd.com
  - appapi.huazhu.com
  - mapi.dianping.com
  - client.app.coc.10086.cn
  - cn-acs.m.cainiao.com
  - app.bilibili.com
  - pan.baidu.com
  - m5.amap.com
  - amap-aos-info-nogw.amap.com
  - member.alipan.com
  - app.58.com
  url-rewrite:
  - ^https://api\.zhihu\.com/commercial_api/(?:launch_v2|real_time_launch_v2|banners_v3/app_topstory_banner)/?(?:\?|$) - reject-dict
  - ^https://api\.zhihu\.com/ad-style-service/request/?(?:\?|$) - reject-dict
  - ^https://api\.xiaoyuzhoufm\.com/v\d+/flash/?(?:\?|$) - reject-dict
  - ^https://acs\.m\.goofish\.com/gw/mtop\.taobao\.idlecommerce\.splash\.ads(?:/[0-9]+(?:\.[0-9]+)*)?/?(?:\?|$) - reject-dict
  - ^https://api\.xiachufang\.com/v\d+/ad/[^?#]*(?:\?|$) - reject
  - ^https://ios\.wps\.cn/ad-statistics-service(?:/[^?#]*)?(?:\?|$) - reject
  - ^https://mobile\-pic\.cache\.iciba\.com/feeds_ad/[^?#]*(?:\?|$) - reject-200
  - ^https://bootrealtime\.uve\.weibo\.com/v\d+/ad/realtime/?(?:\?|$) - reject-dict
  - ^https://bootpreload\.uve\.weibo\.com/v\d+/ad/preload/?(?:\?|$) - reject-dict
  - ^https://m\.client\.10010\.com/mobileService/(?:activity|customer)/(?:get_client_adv|get_startadv)(?:\.htm)?/?(?:\?|$)
    - reject-img
  - ^https://m\.client\.10010\.com/uniAdmsInterface/(?:getHomePageAd|getWelcomeAd)/?(?:\?|$) - reject-img
  - ^https://oss\.umetrip\.com/fs/advert/polite(?:/[^?#]*)?(?:\?|$) - reject
  - ^https://acs\.m\.taobao\.com/gw/mtop\.film\.mtopadvertiseapi\.queryloadingbanner(?:/[0-9]+(?:\.[0-9]+)*)?/?(?:\?|$) -
    reject
  - ^https://acs\.m\.taobao\.com/gw/mtop\.etao\.noah\.query/(?:[0-9.]+/?)?\?[^#]*(?:%22|%27|[^A-Za-z0-9_])tao_splash(?:%22|%27|[^A-Za-z0-9_]|$)[^#]*$
    - reject-dict
  - ^https://api\.pinduoduo\.com/api/cappuccino/splash/?(?:\?|$) - reject
  - ^https://api\.yangkeduo\.com/api/cappuccino/splash/?(?:\?|$) - reject
  - ^https://interface\.music\.163\.com/e?api/ad(?:/[^?#]*)?(?:\?|$) - reject-dict
  - ^https://interface3\.music\.163\.com/e?api/ad(?:/[^?#]*)?(?:\?|$) - reject-dict
  - ^https://ipv4\.music\.163\.com/e?api/ad(?:/[^?#]*)?(?:\?|$) - reject-dict
  - ^https://appconf\.mail\.163\.com/mmad/[^?#]*(?:\?|$) - reject-200
  - ^https://client\.mail\.163\.com/apptrack/confinfo/(?:searchMultiAds|showAds)/?(?:\?|$) - reject
  - ^https://home\.mi\.com/cgi-op/api/v1/(?:recommendation|resource/realtime)/openingBanner/?(?:\?|$) - reject-dict
  - ^https://wmapi\.meituan\.com/api/v7/(?:openscreen|startpicture)/?(?:\?|$) - reject-dict
  - ^https://img\.meituan\.net/bizad/bizad_brandCpt_\d+\.jpg(?:\?|$) - reject-img
  - ^https://(?:s3plus|flowplus)\.meituan\.net/v\d+/\w+/linglong/\w+\.(?:gif|jpg)(?:\?|$) - reject-img
  - ^https://api\.mcd\.cn/bff/portal/home/splash/?(?:\?|$) - reject-200
  - ^https://open\.taou\.com/maimai/adshow/?(?:\?|$) - reject-dict
  - ^https://h3\.open\.taou\.com/maimai/adshow/?(?:\?|$) - reject-dict
  - ^https://api\-ac\.liepin\.com/api/com\.liepin\.cyclops\.live\.get-ad-cards/?(?:\?|$) - reject-dict
  - ^https://res\.kfc\.com\.cn/advertisement/[^?#]*(?:\?|$) - reject
  - ^https://appapi\.huazhu\.com(?::\d+)?/client/app/getAppStartPage/(?:\?|$) - reject
  - ^https://mapi\.dianping\.com/mapi/operating/loadsplashconfig/?(?:\?|$) - reject
  - ^https://acs\.m\.taobao\.com/gw/mtop\.damai\.wireless\.home\.welcome(?:/[0-9]+(?:\.[0-9]+)*)?/?(?:\?|$) - reject-200
  - ^https://client\.app\.coc\.10086\.cn/biz-orange/DN/explorePage/getAdverList/?(?:\?|$) - reject
  - ^https://pan\.baidu\.com/rest/\d+\.\d+/pcs/(?:adx|ad)(?:/[^?#]*)?(?:\?|$) - reject
  - ^https://m5\.amap\.com/ws/shield/dsp/app/startup/init/?(?:\?|$) - reject-dict
  - ^https://amap\-aos\-info\-nogw\.amap\.com/ws/aos/alimama/splash_screen_rt/?(?:\?|$) - reject
  - ^https://app\.58\.com/api/home/(?:advertising|appadv)/[^?#]*(?:\?|$) - reject
  script:
  - match: ^https?://example\.com(?::(?:80|443))?/jimmy-stash-check/?(?:\?[^#]*)?$
    name: jimmy_ads_self_check
    type: request
    require-body: false
    timeout: 5
  - match: ^https://edith\.xiaohongshu\.com/api/sns/(?:v\d+/system_service/(?:splash_config|config)|v6/homefeed)/?(?:\?|$)
    name: jimmy_xiaohongshu_ads
    type: response
    require-body: true
    timeout: 5
    argument: diagnostic=0
  - match: ^https://api\.weibo\.cn/2/(?:searchall|statuses/container_timeline_topic(?:page)?)/?(?:\?|$)
    name: jimmy_weibo_ads
    type: response
    require-body: true
    timeout: 5
    argument: diagnostic=0
  - match: ^https://mp\.weixin\.qq\.com/mp/getappmsgad/?(?:\?|$)
    name: jimmy_wechat_articles_ads
    type: response
    require-body: true
    timeout: 5
    argument: diagnostic=0
  - match: ^https:\/\/tiebac\.baidu\.com\/c\/f\/ad\/getSplashAd(\?|$)
    name: jimmy_tieba_ads
    type: response
    require-body: true
    timeout: 5
    argument: diagnostic=0
  - match: ^https:\/\/guide-acs\.m\.taobao\.com\/gw\/mtop\.taobao\.wireless\.home\.splash\.awesome\.get(\/\d+(\.\d+)*\/?)?(\?|$)
    name: jimmy_taobao_ads
    type: response
    require-body: true
    timeout: 5
    argument: diagnostic=0
  - match: ^https://wmapi\.meituan\.com/api/v\d+/loadInfo/?(?:\?|$)
    name: jimmy_meituan_ads
    type: response
    require-body: true
    timeout: 5
    argument: diagnostic=0
  - match: ^https://capi\.lkcoffee\.com/resource/m/sys/app/adposNew/?(?:\?|$)
    name: jimmy_luckin_ads
    type: response
    require-body: true
    timeout: 5
    argument: diagnostic=0
  - match: ^https://api\.m\.jd\.com/client\.action\?(?:[^#&]*&)*functionId=start(?:&|$)
    name: jimmy_jingdong_ads
    type: response
    require-body: true
    timeout: 5
    argument: diagnostic=0
  - match: ^https://cn-acs\.m\.cainiao\.com/gw/mtop\.cainiao\.guoguo\.nbnetflow\.ads\.show\.cn(?:/[0-9]+(?:\.[0-9]+)*)?/?(?:\?|$)
    name: jimmy_cainiao_ads
    type: response
    require-body: true
    timeout: 5
    argument: diagnostic=0
  - match: ^https:\/\/app\.bilibili\.com\/x\/v2\/(splash\/(list|show)|feed\/index)(\?|$)
    name: jimmy_bilibili_ads
    type: response
    require-body: true
    timeout: 5
    argument: diagnostic=0
  - match: ^https://member\.alipan\.com/v1/users/onboard_list/?(?:\?|$)
    name: jimmy_alipan_ads
    type: response
    require-body: true
    timeout: 5
    argument: diagnostic=0
script-providers:
  jimmy_alipan_ads:
    url: https://raw.githubusercontent.com/Panzm6111/Jimmy-s-Stash-rules/main/scripts/ads/alipan.js?v=AD-20261020.4
    interval: 86400
  jimmy_bilibili_ads:
    url: https://raw.githubusercontent.com/Panzm6111/Jimmy-s-Stash-rules/main/scripts/ads/bilibili.js?v=AD-20261020.4
    interval: 86400
  jimmy_cainiao_ads:
    url: https://raw.githubusercontent.com/Panzm6111/Jimmy-s-Stash-rules/main/scripts/ads/cainiao.js?v=AD-20261020.4
    interval: 86400
  jimmy_jingdong_ads:
    url: https://raw.githubusercontent.com/Panzm6111/Jimmy-s-Stash-rules/main/scripts/ads/jingdong.js?v=AD-20261020.4
    interval: 86400
  jimmy_luckin_ads:
    url: https://raw.githubusercontent.com/Panzm6111/Jimmy-s-Stash-rules/main/scripts/ads/luckin.js?v=AD-20261020.4
    interval: 86400
  jimmy_meituan_ads:
    url: https://raw.githubusercontent.com/Panzm6111/Jimmy-s-Stash-rules/main/scripts/ads/meituan.js?v=AD-20261020.4
    interval: 86400
  jimmy_taobao_ads:
    url: https://raw.githubusercontent.com/Panzm6111/Jimmy-s-Stash-rules/main/scripts/ads/taobao.js?v=AD-20261020.4
    interval: 86400
  jimmy_tieba_ads:
    url: https://raw.githubusercontent.com/Panzm6111/Jimmy-s-Stash-rules/main/scripts/ads/tieba.js?v=AD-20261020.4
    interval: 86400
  jimmy_wechat_articles_ads:
    url: https://raw.githubusercontent.com/Panzm6111/Jimmy-s-Stash-rules/main/scripts/ads/wechat-articles.js?v=AD-20261020.4
    interval: 86400
  jimmy_weibo_ads:
    url: https://raw.githubusercontent.com/Panzm6111/Jimmy-s-Stash-rules/main/scripts/ads/weibo.js?v=AD-20261020.4
    interval: 86400
  jimmy_xiaohongshu_ads:
    url: https://raw.githubusercontent.com/Panzm6111/Jimmy-s-Stash-rules/main/scripts/ads/xiaohongshu.js?v=AD-20261020.4
    interval: 86400
  jimmy_ads_self_check:
    url: https://raw.githubusercontent.com/Panzm6111/Jimmy-s-Stash-rules/main/scripts/ads/self-check.js?v=AD-20261020.4
    interval: 86400
```

旧分层安装保留的基础payload（无需MITM）；当前整合入口默认使用上方provider指向的扩展快照，以下38条仅供维护对照，不同时叠加：

```yaml
payload:
- DOMAIN-SUFFIX,pangle.io
- DOMAIN-SUFFIX,pangolin.snssdk.com
- DOMAIN-SUFFIX,mobads-logs.baidu.cn
- DOMAIN-SUFFIX,mobads-logs.baidu.com
- DOMAIN-SUFFIX,mobads.baidu.cn
- DOMAIN-SUFFIX,c.gdt.qq.com
- DOMAIN-SUFFIX,d.gdt.qq.com
- DOMAIN-SUFFIX,mi.gdt.qq.com
- DOMAIN-SUFFIX,nc.gdt.qq.com
- DOMAIN-SUFFIX,s.gdt.qq.com
- DOMAIN-SUFFIX,t.gdt.qq.com
- DOMAIN-SUFFIX,v.gdt.qq.com
- DOMAIN-SUFFIX,win.gdt.qq.com
- DOMAIN-SUFFIX,xc.gdt.qq.com
- DOMAIN,mobads-pre-config.cdn.bcebos.com
- DOMAIN-SUFFIX,doubleclick.net
- DOMAIN-SUFFIX,googlesyndication.com
- DOMAIN-SUFFIX,admob.com
- DOMAIN-SUFFIX,adsrvr.org
- DOMAIN-SUFFIX,adnxs.com
- DOMAIN-SUFFIX,adkwai.com
- DOMAIN-KEYWORD,pangolin-sdk-toutiao
- DOMAIN-KEYWORD,pglstatp-toutiao
- DOMAIN-KEYWORD,mobads.baidu.com
- DOMAIN,v2.gdt.qq.com
- DOMAIN,vr.gdt.qq.com
- DOMAIN,xs.gdt.qq.com
- DOMAIN,adsmind.gdtimg.com
- DOMAIN,qzs.gdtimg.com
- DOMAIN-SUFFIX,canvas.gdt.qq.com
- DOMAIN-SUFFIX,pgdt.gtimg.cn
- DOMAIN-SUFFIX,pgdt.gtimg.com
- DOMAIN-SUFFIX,q.i.gdt.qq.com
- DOMAIN-SUFFIX,rm.gdt.qq.com
- DOMAIN-SUFFIX,ugdtimg.com
- DOMAIN-SUFFIX,unityads.unity3d.com
- DOMAIN,unityads.unitychina.cn
- DOMAIN,config.unityads.unitychina.cn
```

## 11. 关键输入校验值

这些哈希用于核对公开源与生成结果，不包含手机私人配置。运行文件及发布提交另看PROGRESS和发布审计。

| 文件 | SHA256 |
|---|---|
| [config/stash.yaml](../config/stash.yaml) | `abd7c0f211a7e2dd358acf4c5909430f36b5919bdecceca98c437120ba890a0b` |
| [config/core.stoverride](../config/core.stoverride) | `e64bfa01488b4579e03accb239e5688f004bcfab8c2ccd40d12a21fa6a715b94` |
| [tools/build_ad_scripts.py](../tools/build_ad_scripts.py) | `0ecfcadd2e11c9d2ed472b5fb8f73a2984d2f22e3dccf82f406584a4a819675a` |
| [scripts/ads/alipan.js](../scripts/ads/alipan.js) | `eda94445f28f293e4949b7776a6d98e6016c6a8e163015fd6b15d3470f921998` |
| [scripts/ads/bilibili.js](../scripts/ads/bilibili.js) | `b5543bbaf454e4b5d73a90338b93267f8ff27cbed9a4f4c9d1fd5147083d92c1` |
| [scripts/ads/cainiao.js](../scripts/ads/cainiao.js) | `364c5a371c2d7e5cfeb01b3aed6f6e416e3b6582fde726b39ba13036924579ea` |
| [scripts/ads/jingdong.js](../scripts/ads/jingdong.js) | `16344ef61ba2d4c38d42c22324e57b15ff31554843e81971b58a47cd1a4f85c3` |
| [scripts/ads/luckin.js](../scripts/ads/luckin.js) | `96a62a0f673040e5b185638a9492a4d236e21a8c9d076c5834a800d8ee7e7a08` |
| [scripts/ads/meituan.js](../scripts/ads/meituan.js) | `6749b93c9675085c3a7c1c230ce9b97089641158cdb073cb99b514c22925c459` |
| [scripts/ads/probe.js](../scripts/ads/probe.js) | `2c8563da324513322b5a0612aa113be760daea86e41ebe4c28108002527c14e4` |
| [scripts/ads/self-check.js](../scripts/ads/self-check.js) | `0147c71d7e026e6d7adddacd60ae9abc8862d4470339230449c39fb3d1845789` |
| [scripts/ads/taobao.js](../scripts/ads/taobao.js) | `ade17f384d15c5e0d2c1e5d61ba368efd25bae07e359dfdbcbb244972bbdbce6` |
| [scripts/ads/tieba.js](../scripts/ads/tieba.js) | `ee3d48ca94d71c6171b02c82ad62c2e78855abf81feed1dfbe35540a3728ca3a` |
| [scripts/ads/wechat-articles.js](../scripts/ads/wechat-articles.js) | `ea41e4eef48babdfec1d4cd6ef4569b84eac8a0872baa87c383e90aa7c00facb` |
| [scripts/ads/weibo.js](../scripts/ads/weibo.js) | `6bc6ffd19e687c6c4764e4a2f73d082e9656a2367b207e16040f1448275ddfaa` |
| [scripts/ads/xiaohongshu.js](../scripts/ads/xiaohongshu.js) | `bd1e3f15382950bbbc0abe9c787cfab86e26e56582896e89ca0605aefb8537f1` |

完整输入哈希和结构计数见 [ad-architecture-audit.json](../research/ad-architecture-audit.json)。

## 12. 当前全部运行JS原文

其中11份是整合入口按URL加载的响应处理，1份self-check只供手动访问自检；这里展示完整源代码供审查，不是可粘贴进content字段的配置。另有probe可选诊断，不参与正常去广告。每份代码独立保留许可；下列正文与稳定脚本文件逐字相同。

### alipan.js

源文件：[scripts/ads/alipan.js](../scripts/ads/alipan.js)。

<!-- SOURCE:scripts/ads/alipan.js -->
```javascript
/* SPDX-License-Identifier: GPL-3.0-only
 * Advertising-only transformation adapted from fmz200/wool_scripts Scripts/adrive/adrive.js.
 * Source revisions, hashes and modifications: research/sources.lock.json and
 * research/ad-repair-evidence.json; license texts: licenses/.
 * Runtime and optional fixed-code diagnostics generated by build_ad_scripts.py.
 */
// Generated by tools/build_ad_scripts.py; version AD-20261020.4

(() => {
  let result = {}, state = 'url-unmatched';
  const version = "AD-20261020.4", id = "alipan";
  const debug = typeof $argument === 'string' && /(?:^|&)diagnostic=1(?:&|$)/.test($argument);
  /* SPDX-License-Identifier: MIT
   * Optional device-only observation. No request values, headers or bodies.
   * Concurrent script runs can overwrite counters: these are diagnostic hints,
   * not exact traffic statistics. Observation never changes an ad result.
   */
  function observeAdState(id, version, state) {
    try {
      const modules = ['alipan', 'bilibili', 'cainiao', 'jingdong', 'luckin',
        'meituan', 'taobao', 'tieba', 'wechat-articles', 'weibo', 'xiaohongshu'];
      const states = ['url-unmatched', 'unsupported-method', 'body-unavailable',
        'body-too-large', 'http-error', 'unsupported-status', 'non-json',
        'parse-error', 'unsupported-schema', 'unchanged', 'changed', 'exception'];
      if (!modules.includes(id) || !states.includes(state) ||
          typeof version !== 'string' || !/^AD-\d{8}\.\d+$/.test(version)) return;
      if (typeof $persistentStore === 'undefined' || !$persistentStore) return;
      const store = $persistentStore;
      if (typeof store.read !== 'function' || typeof store.write !== 'function') return;
      const sessionText = store.read('jimmy.ads.diag.session.v1');
      if (typeof sessionText !== 'string' || sessionText.length > 2048) return;
      const session = JSON.parse(sessionText);
      const now = Date.now(), limit = 15 * 60 * 1000;
      if (!session || typeof session !== 'object' || Array.isArray(session) ||
          !Number.isSafeInteger(now) ||
          !Number.isSafeInteger(session.id) || session.id <= 0 || session.id > now ||
          !Number.isSafeInteger(session.until) || now >= session.until ||
          session.until > now + limit || session.until - session.id > limit) return;
      const key = 'jimmy.ads.diag.' + id + '.v1';
      const counts = {};
      const previousText = store.read(key);
      if (typeof previousText === 'string' && previousText.length <= 8192) {
        // Corrupted old counters should not stop the current session recording.
        let previous;
        try { previous = JSON.parse(previousText); } catch (_) {}
        if (previous && !Array.isArray(previous) &&
            previous.sessionId === session.id && previous.version === version &&
            previous.counts && typeof previous.counts === 'object' &&
            !Array.isArray(previous.counts)) {
          for (const known of states) {
            if (!Object.prototype.hasOwnProperty.call(previous.counts, known)) continue;
            const count = previous.counts[known];
            if (Number.isSafeInteger(count) && count >= 0 && count <= 9999) counts[known] = count;
          }
        }
      }
      counts[state] = Math.min(9999, (counts[state] || 0) + 1);
      store.write(JSON.stringify({sessionId: session.id, version, last: now, counts}), key);
    } catch (_) {
      // Missing/failed storage must not affect the response or $done.
    }
  }
  function record(x) { return !!x && typeof x === 'object' && !Array.isArray(x); }
  function successful(x, codes = [0, '0']) {
    return record(x) && x.success !== false && !x.error && !x.error_code &&
      (!Object.prototype.hasOwnProperty.call(x,'code') || codes.includes(x.code));
  }
  function mtopSuccess(x) {
    return !Object.prototype.hasOwnProperty.call(x,'ret') || (Array.isArray(x.ret) && x.ret.length > 0 && x.ret.every(v => typeof v === 'string' && /^SUCCESS(?:::|$)/.test(v)));
  }
  // Count UTF-8 bytes, not UTF-16 code units; no binary decoder assumptions.
  function oversized(s) {
    let n = 0;
    for (let i=0; i<s.length; i++) {
      const c = s.charCodeAt(i);
      if (c < 128) n++; else if (c < 2048) n += 2;
      else if (c >= 0xd800 && c <= 0xdbff && i+1 < s.length && s.charCodeAt(i+1) >= 0xdc00 && s.charCodeAt(i+1) <= 0xdfff) { n += 4; i++; }
      else n += 3;
      if (n > 2*1024*1024) return true;
    }
    return false;
  }
  try {
    const req = typeof $request === 'object' && $request ? $request : {};
    const resp = typeof $response === 'object' && $response ? $response : {};
    const url = String(req.url || '');
    if (!["^https://member\\.alipan\\.com/v1/users/onboard_list/?(?:\\?|$)"].some(p => new RegExp(p).test(url))) return;
    state = 'unsupported-method';
    if (!["GET", "POST"].includes(req.method)) return;
    state = 'body-unavailable';
    if (typeof resp.body !== 'string' || !resp.body.length) return;
    state = 'body-too-large'; if (oversized(resp.body)) return;
    state = 'http-error';
    // Stash native examples use status. Do not silently accept malformed status
    // or guess that a response with statusCode alone is a successful response.
    if (resp.status !== undefined && !/^2\d\d$/.test(String(resp.status))) return;
    if (resp.status === undefined && resp.statusCode !== undefined) { state = 'unsupported-status'; return; }
    state = 'non-json';
    if (!/^[\s]*[\[{]/.test(resp.body)) return;
    state = 'parse-error'; const obj = JSON.parse(resp.body);
    state = 'unsupported-schema'; if (!record(obj)) return;
    const before = JSON.stringify(obj);
    function transform(obj) {
      // Maintained transformation fragment; runtime and diagnostics are generated.
      if (!successful(obj, [0, '0', 200, '200', 'Success']) || !Array.isArray(obj.result)) return false;
      obj.result = obj.result.filter(item => !item || !['backup_top_banner','home_top_banner','resource_top_banner','video_top_banner'].includes(item.anchor));
      return true;
    }
    if (!transform(obj)) return;
    const body = JSON.stringify(obj);
    state = body === before ? 'unchanged' : 'changed';
    if (state === 'changed') result = {body};
  } catch (_) {
    if (state !== 'parse-error') state = 'exception';
  } finally {
    observeAdState(id, version, state);
    if (debug) { try { console.log('[JimmyAds][' + id + '][' + version + '] ' + state); } catch (_) {} }
    $done(result);
  }
})();
```

### bilibili.js

源文件：[scripts/ads/bilibili.js](../scripts/ads/bilibili.js)。

<!-- SOURCE:scripts/ads/bilibili.js -->
```javascript
/* SPDX-License-Identifier: MIT
 * Advertising-only transformation adapted from app2smile/rules js/bilibili-json.js.
 * Source revisions, hashes and modifications: research/sources.lock.json and
 * research/ad-repair-evidence.json; license texts: licenses/.
 * Copyright (c) 2023 app2smile.
 * Runtime and optional fixed-code diagnostics generated by build_ad_scripts.py.
 */
// Generated by tools/build_ad_scripts.py; version AD-20261020.4

(() => {
  let result = {}, state = 'url-unmatched';
  const version = "AD-20261020.4", id = "bilibili";
  const debug = typeof $argument === 'string' && /(?:^|&)diagnostic=1(?:&|$)/.test($argument);
  /* SPDX-License-Identifier: MIT
   * Optional device-only observation. No request values, headers or bodies.
   * Concurrent script runs can overwrite counters: these are diagnostic hints,
   * not exact traffic statistics. Observation never changes an ad result.
   */
  function observeAdState(id, version, state) {
    try {
      const modules = ['alipan', 'bilibili', 'cainiao', 'jingdong', 'luckin',
        'meituan', 'taobao', 'tieba', 'wechat-articles', 'weibo', 'xiaohongshu'];
      const states = ['url-unmatched', 'unsupported-method', 'body-unavailable',
        'body-too-large', 'http-error', 'unsupported-status', 'non-json',
        'parse-error', 'unsupported-schema', 'unchanged', 'changed', 'exception'];
      if (!modules.includes(id) || !states.includes(state) ||
          typeof version !== 'string' || !/^AD-\d{8}\.\d+$/.test(version)) return;
      if (typeof $persistentStore === 'undefined' || !$persistentStore) return;
      const store = $persistentStore;
      if (typeof store.read !== 'function' || typeof store.write !== 'function') return;
      const sessionText = store.read('jimmy.ads.diag.session.v1');
      if (typeof sessionText !== 'string' || sessionText.length > 2048) return;
      const session = JSON.parse(sessionText);
      const now = Date.now(), limit = 15 * 60 * 1000;
      if (!session || typeof session !== 'object' || Array.isArray(session) ||
          !Number.isSafeInteger(now) ||
          !Number.isSafeInteger(session.id) || session.id <= 0 || session.id > now ||
          !Number.isSafeInteger(session.until) || now >= session.until ||
          session.until > now + limit || session.until - session.id > limit) return;
      const key = 'jimmy.ads.diag.' + id + '.v1';
      const counts = {};
      const previousText = store.read(key);
      if (typeof previousText === 'string' && previousText.length <= 8192) {
        // Corrupted old counters should not stop the current session recording.
        let previous;
        try { previous = JSON.parse(previousText); } catch (_) {}
        if (previous && !Array.isArray(previous) &&
            previous.sessionId === session.id && previous.version === version &&
            previous.counts && typeof previous.counts === 'object' &&
            !Array.isArray(previous.counts)) {
          for (const known of states) {
            if (!Object.prototype.hasOwnProperty.call(previous.counts, known)) continue;
            const count = previous.counts[known];
            if (Number.isSafeInteger(count) && count >= 0 && count <= 9999) counts[known] = count;
          }
        }
      }
      counts[state] = Math.min(9999, (counts[state] || 0) + 1);
      store.write(JSON.stringify({sessionId: session.id, version, last: now, counts}), key);
    } catch (_) {
      // Missing/failed storage must not affect the response or $done.
    }
  }
  function record(x) { return !!x && typeof x === 'object' && !Array.isArray(x); }
  function successful(x, codes = [0, '0']) {
    return record(x) && x.success !== false && !x.error && !x.error_code &&
      (!Object.prototype.hasOwnProperty.call(x,'code') || codes.includes(x.code));
  }
  function mtopSuccess(x) {
    return !Object.prototype.hasOwnProperty.call(x,'ret') || (Array.isArray(x.ret) && x.ret.length > 0 && x.ret.every(v => typeof v === 'string' && /^SUCCESS(?:::|$)/.test(v)));
  }
  // Count UTF-8 bytes, not UTF-16 code units; no binary decoder assumptions.
  function oversized(s) {
    let n = 0;
    for (let i=0; i<s.length; i++) {
      const c = s.charCodeAt(i);
      if (c < 128) n++; else if (c < 2048) n += 2;
      else if (c >= 0xd800 && c <= 0xdbff && i+1 < s.length && s.charCodeAt(i+1) >= 0xdc00 && s.charCodeAt(i+1) <= 0xdfff) { n += 4; i++; }
      else n += 3;
      if (n > 2*1024*1024) return true;
    }
    return false;
  }
  try {
    const req = typeof $request === 'object' && $request ? $request : {};
    const resp = typeof $response === 'object' && $response ? $response : {};
    const url = String(req.url || '');
    if (!["^https:\\/\\/app\\.bilibili\\.com\\/x\\/v2\\/(splash\\/(list|show)|feed\\/index)(\\?|$)"].some(p => new RegExp(p).test(url))) return;
    state = 'unsupported-method';
    if (!["GET"].includes(req.method)) return;
    state = 'body-unavailable';
    if (typeof resp.body !== 'string' || !resp.body.length) return;
    state = 'body-too-large'; if (oversized(resp.body)) return;
    state = 'http-error';
    // Stash native examples use status. Do not silently accept malformed status
    // or guess that a response with statusCode alone is a successful response.
    if (resp.status !== undefined && !/^2\d\d$/.test(String(resp.status))) return;
    if (resp.status === undefined && resp.statusCode !== undefined) { state = 'unsupported-status'; return; }
    state = 'non-json';
    if (!/^[\s]*[\[{]/.test(resp.body)) return;
    state = 'parse-error'; const obj = JSON.parse(resp.body);
    state = 'unsupported-schema'; if (!record(obj)) return;
    const before = JSON.stringify(obj);
    function transform(obj) {
      // Maintained transformation fragment; runtime and diagnostics are generated.
      if (!successful(obj) || obj.code !== 0 || !record(obj.data)) return false;
      if (/\/splash\//.test(url)) {
        if (!Object.prototype.hasOwnProperty.call(obj.data,'show')) return false;
        delete obj.data.show; return true;
      }
      if (!Array.isArray(obj.data.items)) return false;
      const adTypes = ['ad_web_s','ad_av','ad_web_gif','ad_player','ad_inline_3d','ad_inline_eggs'];
      obj.data.items = obj.data.items.filter(item => {
        if (!record(item)) return true;
        if (item.card_type === 'cm_v2' && adTypes.includes(item.card_goto)) return false;
        if (item.card_type === 'cm_double_v9' && item.card_goto === 'ad_inline_av') return false;
        if (item.card_type === 'banner_v8' && item.card_goto === 'banner' && Array.isArray(item.banner_item)) item.banner_item = item.banner_item.filter(v => !v || v.type !== 'ad');
        return true;
      });
      return true;
    }
    if (!transform(obj)) return;
    const body = JSON.stringify(obj);
    state = body === before ? 'unchanged' : 'changed';
    if (state === 'changed') result = {body};
  } catch (_) {
    if (state !== 'parse-error') state = 'exception';
  } finally {
    observeAdState(id, version, state);
    if (debug) { try { console.log('[JimmyAds][' + id + '][' + version + '] ' + state); } catch (_) {} }
    $done(result);
  }
})();
```

### cainiao.js

源文件：[scripts/ads/cainiao.js](../scripts/ads/cainiao.js)。

<!-- SOURCE:scripts/ads/cainiao.js -->
```javascript
/* SPDX-License-Identifier: GPL-3.0-only
 * Advertising-only transformation adapted from fmz200/wool_scripts Scripts/cainiao/cainiao.js.
 * Source revisions, hashes and modifications: research/sources.lock.json and
 * research/ad-repair-evidence.json; license texts: licenses/.
 * Runtime and optional fixed-code diagnostics generated by build_ad_scripts.py.
 */
// Generated by tools/build_ad_scripts.py; version AD-20261020.4

(() => {
  let result = {}, state = 'url-unmatched';
  const version = "AD-20261020.4", id = "cainiao";
  const debug = typeof $argument === 'string' && /(?:^|&)diagnostic=1(?:&|$)/.test($argument);
  /* SPDX-License-Identifier: MIT
   * Optional device-only observation. No request values, headers or bodies.
   * Concurrent script runs can overwrite counters: these are diagnostic hints,
   * not exact traffic statistics. Observation never changes an ad result.
   */
  function observeAdState(id, version, state) {
    try {
      const modules = ['alipan', 'bilibili', 'cainiao', 'jingdong', 'luckin',
        'meituan', 'taobao', 'tieba', 'wechat-articles', 'weibo', 'xiaohongshu'];
      const states = ['url-unmatched', 'unsupported-method', 'body-unavailable',
        'body-too-large', 'http-error', 'unsupported-status', 'non-json',
        'parse-error', 'unsupported-schema', 'unchanged', 'changed', 'exception'];
      if (!modules.includes(id) || !states.includes(state) ||
          typeof version !== 'string' || !/^AD-\d{8}\.\d+$/.test(version)) return;
      if (typeof $persistentStore === 'undefined' || !$persistentStore) return;
      const store = $persistentStore;
      if (typeof store.read !== 'function' || typeof store.write !== 'function') return;
      const sessionText = store.read('jimmy.ads.diag.session.v1');
      if (typeof sessionText !== 'string' || sessionText.length > 2048) return;
      const session = JSON.parse(sessionText);
      const now = Date.now(), limit = 15 * 60 * 1000;
      if (!session || typeof session !== 'object' || Array.isArray(session) ||
          !Number.isSafeInteger(now) ||
          !Number.isSafeInteger(session.id) || session.id <= 0 || session.id > now ||
          !Number.isSafeInteger(session.until) || now >= session.until ||
          session.until > now + limit || session.until - session.id > limit) return;
      const key = 'jimmy.ads.diag.' + id + '.v1';
      const counts = {};
      const previousText = store.read(key);
      if (typeof previousText === 'string' && previousText.length <= 8192) {
        // Corrupted old counters should not stop the current session recording.
        let previous;
        try { previous = JSON.parse(previousText); } catch (_) {}
        if (previous && !Array.isArray(previous) &&
            previous.sessionId === session.id && previous.version === version &&
            previous.counts && typeof previous.counts === 'object' &&
            !Array.isArray(previous.counts)) {
          for (const known of states) {
            if (!Object.prototype.hasOwnProperty.call(previous.counts, known)) continue;
            const count = previous.counts[known];
            if (Number.isSafeInteger(count) && count >= 0 && count <= 9999) counts[known] = count;
          }
        }
      }
      counts[state] = Math.min(9999, (counts[state] || 0) + 1);
      store.write(JSON.stringify({sessionId: session.id, version, last: now, counts}), key);
    } catch (_) {
      // Missing/failed storage must not affect the response or $done.
    }
  }
  function record(x) { return !!x && typeof x === 'object' && !Array.isArray(x); }
  function successful(x, codes = [0, '0']) {
    return record(x) && x.success !== false && !x.error && !x.error_code &&
      (!Object.prototype.hasOwnProperty.call(x,'code') || codes.includes(x.code));
  }
  function mtopSuccess(x) {
    return !Object.prototype.hasOwnProperty.call(x,'ret') || (Array.isArray(x.ret) && x.ret.length > 0 && x.ret.every(v => typeof v === 'string' && /^SUCCESS(?:::|$)/.test(v)));
  }
  // Count UTF-8 bytes, not UTF-16 code units; no binary decoder assumptions.
  function oversized(s) {
    let n = 0;
    for (let i=0; i<s.length; i++) {
      const c = s.charCodeAt(i);
      if (c < 128) n++; else if (c < 2048) n += 2;
      else if (c >= 0xd800 && c <= 0xdbff && i+1 < s.length && s.charCodeAt(i+1) >= 0xdc00 && s.charCodeAt(i+1) <= 0xdfff) { n += 4; i++; }
      else n += 3;
      if (n > 2*1024*1024) return true;
    }
    return false;
  }
  try {
    const req = typeof $request === 'object' && $request ? $request : {};
    const resp = typeof $response === 'object' && $response ? $response : {};
    const url = String(req.url || '');
    if (!["^https://cn-acs\\.m\\.cainiao\\.com/gw/mtop\\.cainiao\\.guoguo\\.nbnetflow\\.ads\\.show\\.cn(?:/[0-9]+(?:\\.[0-9]+)*)?/?(?:\\?|$)"].some(p => new RegExp(p).test(url))) return;
    state = 'unsupported-method';
    if (!["GET", "POST"].includes(req.method)) return;
    state = 'body-unavailable';
    if (typeof resp.body !== 'string' || !resp.body.length) return;
    state = 'body-too-large'; if (oversized(resp.body)) return;
    state = 'http-error';
    // Stash native examples use status. Do not silently accept malformed status
    // or guess that a response with statusCode alone is a successful response.
    if (resp.status !== undefined && !/^2\d\d$/.test(String(resp.status))) return;
    if (resp.status === undefined && resp.statusCode !== undefined) { state = 'unsupported-status'; return; }
    state = 'non-json';
    if (!/^[\s]*[\[{]/.test(resp.body)) return;
    state = 'parse-error'; const obj = JSON.parse(resp.body);
    state = 'unsupported-schema'; if (!record(obj)) return;
    const before = JSON.stringify(obj);
    function transform(obj) {
      // Maintained transformation fragment; runtime and diagnostics are generated.
      if (!successful(obj) || !mtopSuccess(obj) || !obj.data || !Array.isArray(obj.data.result)) return false;
      obj.data.result = obj.data.result.filter(item => !(item && item.materialContentMapper && item.materialContentMapper.adItemDetail));
      return true;
    }
    if (!transform(obj)) return;
    const body = JSON.stringify(obj);
    state = body === before ? 'unchanged' : 'changed';
    if (state === 'changed') result = {body};
  } catch (_) {
    if (state !== 'parse-error') state = 'exception';
  } finally {
    observeAdState(id, version, state);
    if (debug) { try { console.log('[JimmyAds][' + id + '][' + version + '] ' + state); } catch (_) {} }
    $done(result);
  }
})();
```

### jingdong.js

源文件：[scripts/ads/jingdong.js](../scripts/ads/jingdong.js)。

<!-- SOURCE:scripts/ads/jingdong.js -->
```javascript
/* SPDX-License-Identifier: GPL-2.0
 * Advertising-only transformation adapted from blackmatrix7/ios_rule_script script/startup/startup.js; fmz200 branch reviewed only.
 * Source revisions, hashes and modifications: research/sources.lock.json and
 * research/ad-repair-evidence.json; license texts: licenses/.
 * Runtime and optional fixed-code diagnostics generated by build_ad_scripts.py.
 */
// Generated by tools/build_ad_scripts.py; version AD-20261020.4

(() => {
  let result = {}, state = 'url-unmatched';
  const version = "AD-20261020.4", id = "jingdong";
  const debug = typeof $argument === 'string' && /(?:^|&)diagnostic=1(?:&|$)/.test($argument);
  /* SPDX-License-Identifier: MIT
   * Optional device-only observation. No request values, headers or bodies.
   * Concurrent script runs can overwrite counters: these are diagnostic hints,
   * not exact traffic statistics. Observation never changes an ad result.
   */
  function observeAdState(id, version, state) {
    try {
      const modules = ['alipan', 'bilibili', 'cainiao', 'jingdong', 'luckin',
        'meituan', 'taobao', 'tieba', 'wechat-articles', 'weibo', 'xiaohongshu'];
      const states = ['url-unmatched', 'unsupported-method', 'body-unavailable',
        'body-too-large', 'http-error', 'unsupported-status', 'non-json',
        'parse-error', 'unsupported-schema', 'unchanged', 'changed', 'exception'];
      if (!modules.includes(id) || !states.includes(state) ||
          typeof version !== 'string' || !/^AD-\d{8}\.\d+$/.test(version)) return;
      if (typeof $persistentStore === 'undefined' || !$persistentStore) return;
      const store = $persistentStore;
      if (typeof store.read !== 'function' || typeof store.write !== 'function') return;
      const sessionText = store.read('jimmy.ads.diag.session.v1');
      if (typeof sessionText !== 'string' || sessionText.length > 2048) return;
      const session = JSON.parse(sessionText);
      const now = Date.now(), limit = 15 * 60 * 1000;
      if (!session || typeof session !== 'object' || Array.isArray(session) ||
          !Number.isSafeInteger(now) ||
          !Number.isSafeInteger(session.id) || session.id <= 0 || session.id > now ||
          !Number.isSafeInteger(session.until) || now >= session.until ||
          session.until > now + limit || session.until - session.id > limit) return;
      const key = 'jimmy.ads.diag.' + id + '.v1';
      const counts = {};
      const previousText = store.read(key);
      if (typeof previousText === 'string' && previousText.length <= 8192) {
        // Corrupted old counters should not stop the current session recording.
        let previous;
        try { previous = JSON.parse(previousText); } catch (_) {}
        if (previous && !Array.isArray(previous) &&
            previous.sessionId === session.id && previous.version === version &&
            previous.counts && typeof previous.counts === 'object' &&
            !Array.isArray(previous.counts)) {
          for (const known of states) {
            if (!Object.prototype.hasOwnProperty.call(previous.counts, known)) continue;
            const count = previous.counts[known];
            if (Number.isSafeInteger(count) && count >= 0 && count <= 9999) counts[known] = count;
          }
        }
      }
      counts[state] = Math.min(9999, (counts[state] || 0) + 1);
      store.write(JSON.stringify({sessionId: session.id, version, last: now, counts}), key);
    } catch (_) {
      // Missing/failed storage must not affect the response or $done.
    }
  }
  function record(x) { return !!x && typeof x === 'object' && !Array.isArray(x); }
  function successful(x, codes = [0, '0']) {
    return record(x) && x.success !== false && !x.error && !x.error_code &&
      (!Object.prototype.hasOwnProperty.call(x,'code') || codes.includes(x.code));
  }
  function mtopSuccess(x) {
    return !Object.prototype.hasOwnProperty.call(x,'ret') || (Array.isArray(x.ret) && x.ret.length > 0 && x.ret.every(v => typeof v === 'string' && /^SUCCESS(?:::|$)/.test(v)));
  }
  // Count UTF-8 bytes, not UTF-16 code units; no binary decoder assumptions.
  function oversized(s) {
    let n = 0;
    for (let i=0; i<s.length; i++) {
      const c = s.charCodeAt(i);
      if (c < 128) n++; else if (c < 2048) n += 2;
      else if (c >= 0xd800 && c <= 0xdbff && i+1 < s.length && s.charCodeAt(i+1) >= 0xdc00 && s.charCodeAt(i+1) <= 0xdfff) { n += 4; i++; }
      else n += 3;
      if (n > 2*1024*1024) return true;
    }
    return false;
  }
  try {
    const req = typeof $request === 'object' && $request ? $request : {};
    const resp = typeof $response === 'object' && $response ? $response : {};
    const url = String(req.url || '');
    if (!["^https://api\\.m\\.jd\\.com/client\\.action\\?(?:[^#&]*&)*functionId=start(?:&|$)"].some(p => new RegExp(p).test(url))) return;
    state = 'unsupported-method';
    if (!["GET", "POST"].includes(req.method)) return;
    state = 'body-unavailable';
    if (typeof resp.body !== 'string' || !resp.body.length) return;
    state = 'body-too-large'; if (oversized(resp.body)) return;
    state = 'http-error';
    // Stash native examples use status. Do not silently accept malformed status
    // or guess that a response with statusCode alone is a successful response.
    if (resp.status !== undefined && !/^2\d\d$/.test(String(resp.status))) return;
    if (resp.status === undefined && resp.statusCode !== undefined) { state = 'unsupported-status'; return; }
    state = 'non-json';
    if (!/^[\s]*[\[{]/.test(resp.body)) return;
    state = 'parse-error'; const obj = JSON.parse(resp.body);
    state = 'unsupported-schema'; if (!record(obj)) return;
    const before = JSON.stringify(obj);
    function transform(obj) {
      // Maintained transformation fragment; runtime and diagnostics are generated.
      // Both reviewed sources use functionId=start in the URL. Do not infer an
      // unseen POST-body function or touch other client.action business functions.
      const query = url.split('?')[1] || '';
      const ids = query.split('&').filter(p => p.split('=')[0] === 'functionId');
      if (ids.length !== 1 || ids[0] !== 'functionId=start' || !successful(obj) || !Array.isArray(obj.images)) return false;
      if (!obj.images.every(x => Array.isArray(x) || record(x))) return false;
      const rows = obj.images.flat();
      // A flat list is an upstream-supported variant. Only known ad control fields
      // are modified; empty objects and normal product records remain unchanged.
      let supported = rows.length === 0;
      function zero(item,key) {
        if (typeof item[key] === 'number' && Number.isFinite(item[key])) item[key] = 0;
        else if (typeof item[key] === 'string' && /^\d+$/.test(item[key])) item[key] = '0';
      }
      for (const ad of rows) {
        if (!record(ad) || !(typeof ad.showTimes === 'number' && Number.isFinite(ad.showTimes) || typeof ad.showTimes === 'string' && /^\d+$/.test(ad.showTimes))) continue;
        supported = true; zero(ad,'showTimes'); zero(ad,'time');
        for (const key of ['onlineTime','referralsTime']) if (typeof ad[key] === 'string' && /^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$/.test(ad[key])) ad[key] = '2090-12-31 00:00:00';
      }
      if (supported) zero(obj,'showTimesDaily');
      return supported;
    }
    if (!transform(obj)) return;
    const body = JSON.stringify(obj);
    state = body === before ? 'unchanged' : 'changed';
    if (state === 'changed') result = {body};
  } catch (_) {
    if (state !== 'parse-error') state = 'exception';
  } finally {
    observeAdState(id, version, state);
    if (debug) { try { console.log('[JimmyAds][' + id + '][' + version + '] ' + state); } catch (_) {} }
    $done(result);
  }
})();
```

### luckin.js

源文件：[scripts/ads/luckin.js](../scripts/ads/luckin.js)。

<!-- SOURCE:scripts/ads/luckin.js -->
```javascript
/* SPDX-License-Identifier: GPL-3.0-only
 * Advertising-only transformation adapted from fmz200/wool_scripts QuantumultX/rewrite/rewrite.snippet.
 * Source revisions, hashes and modifications: research/sources.lock.json and
 * research/ad-repair-evidence.json; license texts: licenses/.
 * Runtime and optional fixed-code diagnostics generated by build_ad_scripts.py.
 */
// Generated by tools/build_ad_scripts.py; version AD-20261020.4

(() => {
  let result = {}, state = 'url-unmatched';
  const version = "AD-20261020.4", id = "luckin";
  const debug = typeof $argument === 'string' && /(?:^|&)diagnostic=1(?:&|$)/.test($argument);
  /* SPDX-License-Identifier: MIT
   * Optional device-only observation. No request values, headers or bodies.
   * Concurrent script runs can overwrite counters: these are diagnostic hints,
   * not exact traffic statistics. Observation never changes an ad result.
   */
  function observeAdState(id, version, state) {
    try {
      const modules = ['alipan', 'bilibili', 'cainiao', 'jingdong', 'luckin',
        'meituan', 'taobao', 'tieba', 'wechat-articles', 'weibo', 'xiaohongshu'];
      const states = ['url-unmatched', 'unsupported-method', 'body-unavailable',
        'body-too-large', 'http-error', 'unsupported-status', 'non-json',
        'parse-error', 'unsupported-schema', 'unchanged', 'changed', 'exception'];
      if (!modules.includes(id) || !states.includes(state) ||
          typeof version !== 'string' || !/^AD-\d{8}\.\d+$/.test(version)) return;
      if (typeof $persistentStore === 'undefined' || !$persistentStore) return;
      const store = $persistentStore;
      if (typeof store.read !== 'function' || typeof store.write !== 'function') return;
      const sessionText = store.read('jimmy.ads.diag.session.v1');
      if (typeof sessionText !== 'string' || sessionText.length > 2048) return;
      const session = JSON.parse(sessionText);
      const now = Date.now(), limit = 15 * 60 * 1000;
      if (!session || typeof session !== 'object' || Array.isArray(session) ||
          !Number.isSafeInteger(now) ||
          !Number.isSafeInteger(session.id) || session.id <= 0 || session.id > now ||
          !Number.isSafeInteger(session.until) || now >= session.until ||
          session.until > now + limit || session.until - session.id > limit) return;
      const key = 'jimmy.ads.diag.' + id + '.v1';
      const counts = {};
      const previousText = store.read(key);
      if (typeof previousText === 'string' && previousText.length <= 8192) {
        // Corrupted old counters should not stop the current session recording.
        let previous;
        try { previous = JSON.parse(previousText); } catch (_) {}
        if (previous && !Array.isArray(previous) &&
            previous.sessionId === session.id && previous.version === version &&
            previous.counts && typeof previous.counts === 'object' &&
            !Array.isArray(previous.counts)) {
          for (const known of states) {
            if (!Object.prototype.hasOwnProperty.call(previous.counts, known)) continue;
            const count = previous.counts[known];
            if (Number.isSafeInteger(count) && count >= 0 && count <= 9999) counts[known] = count;
          }
        }
      }
      counts[state] = Math.min(9999, (counts[state] || 0) + 1);
      store.write(JSON.stringify({sessionId: session.id, version, last: now, counts}), key);
    } catch (_) {
      // Missing/failed storage must not affect the response or $done.
    }
  }
  function record(x) { return !!x && typeof x === 'object' && !Array.isArray(x); }
  function successful(x, codes = [0, '0']) {
    return record(x) && x.success !== false && !x.error && !x.error_code &&
      (!Object.prototype.hasOwnProperty.call(x,'code') || codes.includes(x.code));
  }
  function mtopSuccess(x) {
    return !Object.prototype.hasOwnProperty.call(x,'ret') || (Array.isArray(x.ret) && x.ret.length > 0 && x.ret.every(v => typeof v === 'string' && /^SUCCESS(?:::|$)/.test(v)));
  }
  // Count UTF-8 bytes, not UTF-16 code units; no binary decoder assumptions.
  function oversized(s) {
    let n = 0;
    for (let i=0; i<s.length; i++) {
      const c = s.charCodeAt(i);
      if (c < 128) n++; else if (c < 2048) n += 2;
      else if (c >= 0xd800 && c <= 0xdbff && i+1 < s.length && s.charCodeAt(i+1) >= 0xdc00 && s.charCodeAt(i+1) <= 0xdfff) { n += 4; i++; }
      else n += 3;
      if (n > 2*1024*1024) return true;
    }
    return false;
  }
  try {
    const req = typeof $request === 'object' && $request ? $request : {};
    const resp = typeof $response === 'object' && $response ? $response : {};
    const url = String(req.url || '');
    if (!["^https://capi\\.lkcoffee\\.com/resource/m/sys/app/adposNew/?(?:\\?|$)"].some(p => new RegExp(p).test(url))) return;
    state = 'unsupported-method';
    if (!["GET", "POST"].includes(req.method)) return;
    state = 'body-unavailable';
    if (typeof resp.body !== 'string' || !resp.body.length) return;
    state = 'body-too-large'; if (oversized(resp.body)) return;
    state = 'http-error';
    // Stash native examples use status. Do not silently accept malformed status
    // or guess that a response with statusCode alone is a successful response.
    if (resp.status !== undefined && !/^2\d\d$/.test(String(resp.status))) return;
    if (resp.status === undefined && resp.statusCode !== undefined) { state = 'unsupported-status'; return; }
    state = 'non-json';
    if (!/^[\s]*[\[{]/.test(resp.body)) return;
    state = 'parse-error'; const obj = JSON.parse(resp.body);
    state = 'unsupported-schema'; if (!record(obj)) return;
    const before = JSON.stringify(obj);
    function transform(obj) {
      // Maintained transformation fragment; runtime and diagnostics are generated.
      if (!successful(obj, [0, '0', 200, '200']) || obj.status !== 'SUCCESS') return false;
      for (const key of Object.keys(obj)) if (key !== 'status') delete obj[key];
      return true;
    }
    if (!transform(obj)) return;
    const body = JSON.stringify(obj);
    state = body === before ? 'unchanged' : 'changed';
    if (state === 'changed') result = {body};
  } catch (_) {
    if (state !== 'parse-error') state = 'exception';
  } finally {
    observeAdState(id, version, state);
    if (debug) { try { console.log('[JimmyAds][' + id + '][' + version + '] ' + state); } catch (_) {} }
    $done(result);
  }
})();
```

### meituan.js

源文件：[scripts/ads/meituan.js](../scripts/ads/meituan.js)。

<!-- SOURCE:scripts/ads/meituan.js -->
```javascript
/* SPDX-License-Identifier: GPL-2.0
 * Advertising-only transformation adapted from blackmatrix7/ios_rule_script script/startup/startup.js.
 * Source revisions, hashes and modifications: research/sources.lock.json and
 * research/ad-repair-evidence.json; license texts: licenses/.
 * Runtime and optional fixed-code diagnostics generated by build_ad_scripts.py.
 */
// Generated by tools/build_ad_scripts.py; version AD-20261020.4

(() => {
  let result = {}, state = 'url-unmatched';
  const version = "AD-20261020.4", id = "meituan";
  const debug = typeof $argument === 'string' && /(?:^|&)diagnostic=1(?:&|$)/.test($argument);
  /* SPDX-License-Identifier: MIT
   * Optional device-only observation. No request values, headers or bodies.
   * Concurrent script runs can overwrite counters: these are diagnostic hints,
   * not exact traffic statistics. Observation never changes an ad result.
   */
  function observeAdState(id, version, state) {
    try {
      const modules = ['alipan', 'bilibili', 'cainiao', 'jingdong', 'luckin',
        'meituan', 'taobao', 'tieba', 'wechat-articles', 'weibo', 'xiaohongshu'];
      const states = ['url-unmatched', 'unsupported-method', 'body-unavailable',
        'body-too-large', 'http-error', 'unsupported-status', 'non-json',
        'parse-error', 'unsupported-schema', 'unchanged', 'changed', 'exception'];
      if (!modules.includes(id) || !states.includes(state) ||
          typeof version !== 'string' || !/^AD-\d{8}\.\d+$/.test(version)) return;
      if (typeof $persistentStore === 'undefined' || !$persistentStore) return;
      const store = $persistentStore;
      if (typeof store.read !== 'function' || typeof store.write !== 'function') return;
      const sessionText = store.read('jimmy.ads.diag.session.v1');
      if (typeof sessionText !== 'string' || sessionText.length > 2048) return;
      const session = JSON.parse(sessionText);
      const now = Date.now(), limit = 15 * 60 * 1000;
      if (!session || typeof session !== 'object' || Array.isArray(session) ||
          !Number.isSafeInteger(now) ||
          !Number.isSafeInteger(session.id) || session.id <= 0 || session.id > now ||
          !Number.isSafeInteger(session.until) || now >= session.until ||
          session.until > now + limit || session.until - session.id > limit) return;
      const key = 'jimmy.ads.diag.' + id + '.v1';
      const counts = {};
      const previousText = store.read(key);
      if (typeof previousText === 'string' && previousText.length <= 8192) {
        // Corrupted old counters should not stop the current session recording.
        let previous;
        try { previous = JSON.parse(previousText); } catch (_) {}
        if (previous && !Array.isArray(previous) &&
            previous.sessionId === session.id && previous.version === version &&
            previous.counts && typeof previous.counts === 'object' &&
            !Array.isArray(previous.counts)) {
          for (const known of states) {
            if (!Object.prototype.hasOwnProperty.call(previous.counts, known)) continue;
            const count = previous.counts[known];
            if (Number.isSafeInteger(count) && count >= 0 && count <= 9999) counts[known] = count;
          }
        }
      }
      counts[state] = Math.min(9999, (counts[state] || 0) + 1);
      store.write(JSON.stringify({sessionId: session.id, version, last: now, counts}), key);
    } catch (_) {
      // Missing/failed storage must not affect the response or $done.
    }
  }
  function record(x) { return !!x && typeof x === 'object' && !Array.isArray(x); }
  function successful(x, codes = [0, '0']) {
    return record(x) && x.success !== false && !x.error && !x.error_code &&
      (!Object.prototype.hasOwnProperty.call(x,'code') || codes.includes(x.code));
  }
  function mtopSuccess(x) {
    return !Object.prototype.hasOwnProperty.call(x,'ret') || (Array.isArray(x.ret) && x.ret.length > 0 && x.ret.every(v => typeof v === 'string' && /^SUCCESS(?:::|$)/.test(v)));
  }
  // Count UTF-8 bytes, not UTF-16 code units; no binary decoder assumptions.
  function oversized(s) {
    let n = 0;
    for (let i=0; i<s.length; i++) {
      const c = s.charCodeAt(i);
      if (c < 128) n++; else if (c < 2048) n += 2;
      else if (c >= 0xd800 && c <= 0xdbff && i+1 < s.length && s.charCodeAt(i+1) >= 0xdc00 && s.charCodeAt(i+1) <= 0xdfff) { n += 4; i++; }
      else n += 3;
      if (n > 2*1024*1024) return true;
    }
    return false;
  }
  try {
    const req = typeof $request === 'object' && $request ? $request : {};
    const resp = typeof $response === 'object' && $response ? $response : {};
    const url = String(req.url || '');
    if (!["^https://wmapi\\.meituan\\.com/api/v\\d+/loadInfo/?(?:\\?|$)"].some(p => new RegExp(p).test(url))) return;
    state = 'unsupported-method';
    if (!["GET", "POST"].includes(req.method)) return;
    state = 'body-unavailable';
    if (typeof resp.body !== 'string' || !resp.body.length) return;
    state = 'body-too-large'; if (oversized(resp.body)) return;
    state = 'http-error';
    // Stash native examples use status. Do not silently accept malformed status
    // or guess that a response with statusCode alone is a successful response.
    if (resp.status !== undefined && !/^2\d\d$/.test(String(resp.status))) return;
    if (resp.status === undefined && resp.statusCode !== undefined) { state = 'unsupported-status'; return; }
    state = 'non-json';
    if (!/^[\s]*[\[{]/.test(resp.body)) return;
    state = 'parse-error'; const obj = JSON.parse(resp.body);
    state = 'unsupported-schema'; if (!record(obj)) return;
    const before = JSON.stringify(obj);
    function transform(obj) {
      // Maintained transformation fragment; runtime and diagnostics are generated.
      if (!successful(obj)) return false;
      const splash = obj.data && obj.data.startpicture;
      if (!record(splash)) return false;
      let supported = false;
      for (const key of ['ad','mk']) if (Array.isArray(splash[key])) { splash[key] = []; supported = true; }
      return supported;
    }
    if (!transform(obj)) return;
    const body = JSON.stringify(obj);
    state = body === before ? 'unchanged' : 'changed';
    if (state === 'changed') result = {body};
  } catch (_) {
    if (state !== 'parse-error') state = 'exception';
  } finally {
    observeAdState(id, version, state);
    if (debug) { try { console.log('[JimmyAds][' + id + '][' + version + '] ' + state); } catch (_) {} }
    $done(result);
  }
})();
```

### probe.js

源文件：[scripts/ads/probe.js](../scripts/ads/probe.js)。

<!-- SOURCE:scripts/ads/probe.js -->
```javascript
/* SPDX-License-Identifier: MIT
 * Generated metadata-only observer. Match references retain their source notices
 * in modules/ads and research/ad-catalog.json. Never logs request values.
 */
(() => {
  try {
    const req = typeof $request === 'object' && $request ? $request : {};
    const url = String(req.url || '');
    const routes = [{"id": "58tongcheng", "match": "^https://app\\.58\\.com/api/home/(?:advertising|appadv)/[^?#]*(?:\\?|$)"}, {"id": "alipan", "match": "^https://member\\.alipan\\.com/v1/users/onboard_list/?(?:\\?|$)"}, {"id": "amap", "match": "^https://m5\\.amap\\.com/ws/shield/dsp/app/startup/init/?(?:\\?|$)"}, {"id": "amap", "match": "^https://amap\\-aos\\-info\\-nogw\\.amap\\.com/ws/aos/alimama/splash_screen_rt/?(?:\\?|$)"}, {"id": "baidu-netdisk", "match": "^https://pan\\.baidu\\.com/rest/\\d+\\.\\d+/pcs/(?:adx|ad)(?:/[^?#]*)?(?:\\?|$)"}, {"id": "bilibili", "match": "^https:\\/\\/app\\.bilibili\\.com\\/x\\/v2\\/(splash\\/(list|show)|feed\\/index)(\\?|$)"}, {"id": "cainiao", "match": "^https://cn-acs\\.m\\.cainiao\\.com/gw/mtop\\.cainiao\\.guoguo\\.nbnetflow\\.ads\\.show\\.cn(?:/[0-9]+(?:\\.[0-9]+)*)?/?(?:\\?|$)"}, {"id": "cmcc", "match": "^https://client\\.app\\.coc\\.10086\\.cn/biz-orange/DN/explorePage/getAdverList/?(?:\\?|$)"}, {"id": "damai", "match": "^https://acs\\.m\\.taobao\\.com/gw/mtop\\.damai\\.wireless\\.home\\.welcome(?:/[0-9]+(?:\\.[0-9]+)*)?/?(?:\\?|$)"}, {"id": "dianping", "match": "^https://mapi\\.dianping\\.com/mapi/operating/loadsplashconfig/?(?:\\?|$)"}, {"id": "huazhu", "match": "^https://appapi\\.huazhu\\.com(?::\\d+)?/client/app/getAppStartPage/(?:\\?|$)"}, {"id": "jingdong", "match": "^https://api\\.m\\.jd\\.com/client\\.action\\?(?:[^#&]*&)*functionId=start(?:&|$)"}, {"id": "kfc", "match": "^https://res\\.kfc\\.com\\.cn/advertisement/[^?#]*(?:\\?|$)"}, {"id": "liepin", "match": "^https://api\\-ac\\.liepin\\.com/api/com\\.liepin\\.cyclops\\.live\\.get-ad-cards/?(?:\\?|$)"}, {"id": "luckin", "match": "^https://capi\\.lkcoffee\\.com/resource/m/sys/app/adposNew/?(?:\\?|$)"}, {"id": "maimai", "match": "^https://open\\.taou\\.com/maimai/adshow/?(?:\\?|$)"}, {"id": "maimai", "match": "^https://h3\\.open\\.taou\\.com/maimai/adshow/?(?:\\?|$)"}, {"id": "mcdonalds", "match": "^https://api\\.mcd\\.cn/bff/portal/home/splash/?(?:\\?|$)"}, {"id": "meituan", "match": "^https://wmapi\\.meituan\\.com/api/v7/(?:openscreen|startpicture)/?(?:\\?|$)"}, {"id": "meituan", "match": "^https://img\\.meituan\\.net/bizad/bizad_brandCpt_\\d+\\.jpg(?:\\?|$)"}, {"id": "meituan", "match": "^https://(?:s3plus|flowplus)\\.meituan\\.net/v\\d+/\\w+/linglong/\\w+\\.(?:gif|jpg)(?:\\?|$)"}, {"id": "meituan", "match": "^https://wmapi\\.meituan\\.com/api/v\\d+/loadInfo/?(?:\\?|$)"}, {"id": "mijia", "match": "^https://home\\.mi\\.com/cgi-op/api/v1/(?:recommendation|resource/realtime)/openingBanner/?(?:\\?|$)"}, {"id": "netease-mail", "match": "^https://appconf\\.mail\\.163\\.com/mmad/[^?#]*(?:\\?|$)"}, {"id": "netease-mail", "match": "^https://client\\.mail\\.163\\.com/apptrack/confinfo/(?:searchMultiAds|showAds)/?(?:\\?|$)"}, {"id": "netease-music", "match": "^https://interface\\.music\\.163\\.com/e?api/ad(?:/[^?#]*)?(?:\\?|$)"}, {"id": "netease-music", "match": "^https://interface3\\.music\\.163\\.com/e?api/ad(?:/[^?#]*)?(?:\\?|$)"}, {"id": "netease-music", "match": "^https://ipv4\\.music\\.163\\.com/e?api/ad(?:/[^?#]*)?(?:\\?|$)"}, {"id": "pinduoduo", "match": "^https://api\\.pinduoduo\\.com/api/cappuccino/splash/?(?:\\?|$)"}, {"id": "pinduoduo", "match": "^https://api\\.yangkeduo\\.com/api/cappuccino/splash/?(?:\\?|$)"}, {"id": "taobao", "match": "^https://acs\\.m\\.taobao\\.com/gw/mtop\\.etao\\.noah\\.query/(?:[0-9.]+/?)?\\?[^#]*(?:%22|%27|[^A-Za-z0-9_])tao_splash(?:%22|%27|[^A-Za-z0-9_]|$)[^#]*$"}, {"id": "taobao", "match": "^https:\\/\\/guide-acs\\.m\\.taobao\\.com\\/gw\\/mtop\\.taobao\\.wireless\\.home\\.splash\\.awesome\\.get(\\/\\d+(\\.\\d+)*\\/?)?(\\?|$)"}, {"id": "taopiaopiao", "match": "^https://acs\\.m\\.taobao\\.com/gw/mtop\\.film\\.mtopadvertiseapi\\.queryloadingbanner(?:/[0-9]+(?:\\.[0-9]+)*)?/?(?:\\?|$)"}, {"id": "tieba", "match": "^https:\\/\\/tiebac\\.baidu\\.com\\/c\\/f\\/ad\\/getSplashAd(\\?|$)"}, {"id": "umetrip", "match": "^https://oss\\.umetrip\\.com/fs/advert/polite(?:/[^?#]*)?(?:\\?|$)"}, {"id": "unicom", "match": "^https://m\\.client\\.10010\\.com/mobileService/(?:activity|customer)/(?:get_client_adv|get_startadv)(?:\\.htm)?/?(?:\\?|$)"}, {"id": "unicom", "match": "^https://m\\.client\\.10010\\.com/uniAdmsInterface/(?:getHomePageAd|getWelcomeAd)/?(?:\\?|$)"}, {"id": "wechat-articles", "match": "^https://mp\\.weixin\\.qq\\.com/mp/getappmsgad/?(?:\\?|$)"}, {"id": "weibo", "match": "^https://bootrealtime\\.uve\\.weibo\\.com/v\\d+/ad/realtime/?(?:\\?|$)"}, {"id": "weibo", "match": "^https://bootpreload\\.uve\\.weibo\\.com/v\\d+/ad/preload/?(?:\\?|$)"}, {"id": "weibo", "match": "^https://api\\.weibo\\.cn/2/(?:searchall|statuses/container_timeline_topic(?:page)?)/?(?:\\?|$)"}, {"id": "wps", "match": "^https://ios\\.wps\\.cn/ad-statistics-service(?:/[^?#]*)?(?:\\?|$)"}, {"id": "wps", "match": "^https://mobile\\-pic\\.cache\\.iciba\\.com/feeds_ad/[^?#]*(?:\\?|$)"}, {"id": "xiachufang", "match": "^https://api\\.xiachufang\\.com/v\\d+/ad/[^?#]*(?:\\?|$)"}, {"id": "xianyu", "match": "^https://acs\\.m\\.goofish\\.com/gw/mtop\\.taobao\\.idlecommerce\\.splash\\.ads(?:/[0-9]+(?:\\.[0-9]+)*)?/?(?:\\?|$)"}, {"id": "xiaohongshu", "match": "^https://edith\\.xiaohongshu\\.com/api/sns/(?:v\\d+/system_service/(?:splash_config|config)|v6/homefeed)/?(?:\\?|$)"}, {"id": "xiaoyuzhou", "match": "^https://api\\.xiaoyuzhoufm\\.com/v\\d+/flash/?(?:\\?|$)"}, {"id": "zhihu", "match": "^https://api\\.zhihu\\.com/commercial_api/(?:launch_v2|real_time_launch_v2|banners_v3/app_topstory_banner)/?(?:\\?|$)"}, {"id": "zhihu", "match": "^https://api\\.zhihu\\.com/ad-style-service/request/?(?:\\?|$)"}];
    const hit = routes.find(r => new RegExp(r.match).test(url));
    console.log('[JimmyAds][' + (hit ? hit.id : 'probe') + '][AD-20261020.4] ' + (hit ? 'request-url-matched' : 'request-url-unmatched'));
  } catch (_) { try { console.log('[JimmyAds][probe][AD-20261020.4] exception'); } catch (_) {} }
  finally { $done({}); }
})();
```

### self-check.js

源文件：[scripts/ads/self-check.js](../scripts/ads/self-check.js)。

<!-- SOURCE:scripts/ads/self-check.js -->
```javascript
/* SPDX-License-Identifier: MIT
 * Generated manual self-check, not an advertisement transformation.
 * Native request response envelope and persistentStore API reviewed in:
 * NobyDa/Script@0b8d083d444f4476700cb9d5d059c07b42da85eb
 * Stash/IPA-Installer.stoverride + IPA-Installer/IPA-Installer.js L70,76,112-116,142-146.
 * JS SHA256 c7b2887cafcbe563f022488e04a7fafed9160465fc939f5d0cfa048232216499.
 * Only API conventions are used; no installer business code is copied or run.
 * No request headers/body, account data, URL query values or remote requests.
 */
(() => {
  let output = {};
  const version = 'AD-20261020.4', key = 'jimmy.ads.diag.session.v1';
  const modules = [{"id": "alipan", "name": "阿里云盘广告专项"}, {"id": "bilibili", "name": "哔哩哔哩广告处理"}, {"id": "cainiao", "name": "菜鸟广告专项"}, {"id": "jingdong", "name": "京东广告专项"}, {"id": "luckin", "name": "瑞幸咖啡广告专项"}, {"id": "meituan", "name": "美团广告专项"}, {"id": "taobao", "name": "淘宝开屏广告处理"}, {"id": "tieba", "name": "贴吧开屏广告处理"}, {"id": "wechat-articles", "name": "微信广告专项"}, {"id": "weibo", "name": "微博开屏广告处理"}, {"id": "xiaohongshu", "name": "小红书开屏广告处理"}];
  const labels = {
    'url-unmatched':'脚本已进入，但URL未匹配',
    'unsupported-method':'请求方法不支持',
    'body-unavailable':'响应正文不可用',
    'body-too-large':'响应正文超出处理上限',
    'http-error':'HTTP状态非成功',
    'unsupported-status':'HTTP状态格式不支持',
    'non-json':'正文不是JSON',
    'parse-error':'JSON解析失败',
    'unsupported-schema':'响应结构未支持',
    'unchanged':'已识别，无需修改',
    'changed':'实际产生修改',
    'exception':'脚本执行异常'
  };
  const own = (o, k) => Object.prototype.hasOwnProperty.call(o, k);
  const record = x => !!x && typeof x === 'object' && !Array.isArray(x);
  const integer = x => Number.isSafeInteger(x) && x >= 0;
  const escape = x => String(x).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  function parsed(raw) {
    if (typeof raw !== 'string' || raw.length > 8192) throw Error('invalid-storage');
    const value = JSON.parse(raw);
    if (!record(value)) throw Error('invalid-storage');
    return value;
  }
  function sessionValid(s, now) {
    return record(s) && integer(s.id) && s.id > 0 && s.id <= now && integer(s.until) &&
      (s.until === 0 || (s.until >= s.id && s.until - s.id <= 900000));
  }
  function stamp(value) {
    return new Date(value + 8 * 3600000).toISOString().slice(0, 19).replace('T', ' ') + ' 北京时间';
  }
  try {
    const req = typeof $request === 'object' && $request ? $request : {};
    if (req.method !== 'GET' || typeof req.url !== 'string') return;
    const match = /^http(s?):\/\/example\.com(?::(?:80|443))?\/jimmy-stash-check\/?(?:\?(start=1|stop=1))?$/.exec(req.url);
    if (!match) return;
    const protocol = match[1] ? 'https' : 'http', action = match[2] || '';
    const now = Date.now();
    let store = null, session = null, unavailable = false, damaged = false, command = '';
    try {
      if (typeof $persistentStore === 'undefined' || !$persistentStore ||
          typeof $persistentStore.read !== 'function' || typeof $persistentStore.write !== 'function') throw Error('no-storage');
      store = $persistentStore;
      const raw = store.read(key);
      if (raw !== null && raw !== undefined && raw !== '') {
        session = parsed(raw);
        if (!sessionValid(session, now)) throw Error('invalid-session');
      }
    } catch (_) {
      unavailable = true;
      session = null;
    }
    if (action && store) {
      try {
        function saveSession(next) {
          if (!sessionValid(next, now) || store.write(JSON.stringify(next), key) !== true) throw Error('write-failed');
          const saved = parsed(store.read(key));
          if (!sessionValid(saved, now) || saved.id !== next.id || saved.until !== next.until) throw Error('readback-failed');
        }
        if (action === 'start=1') {
          const next = {id: now, until: now + 900000};
          saveSession(next);
          session = next;
          unavailable = false;
          command = '已开始15分钟诊断。请先返回结果页，再打开需要检查的App。';
        } else if (session) {
          const next = {id: session.id, until: 0};
          saveSession(next);
          session = next;
          command = '已停止记录；本轮已有结果仍保留在设备。';
        } else {
          command = '没有可停止的有效诊断会话。';
        }
      } catch (_) {
        unavailable = true;
        command = '本机存储写入失败或读回核对失败，无法确认诊断已开始或停止。';
      }
    } else if (action) {
      command = '本机存储不可用，无法开始或停止诊断。';
    }
    const active = !unavailable && session && session.until > now;
    let total = 0;
    const rows = modules.map(module => {
      let value = null, trouble = false;
      if (session && store && !unavailable) {
        try {
          const raw = store.read('jimmy.ads.diag.' + module.id + '.v1');
          if (raw !== null && raw !== undefined && raw !== '') {
            const candidate = parsed(raw);
            if (!integer(candidate.sessionId)) throw Error('invalid-record');
            if (candidate.sessionId === session.id) {
              if (typeof candidate.version !== 'string' || !/^AD-\d{8}\.\d{1,4}$/.test(candidate.version) ||
                  !integer(candidate.last) || candidate.last < session.id || candidate.last > now ||
                  !record(candidate.counts) || Object.keys(candidate.counts).some(k => !own(labels,k) || !integer(candidate.counts[k]) || candidate.counts[k] > 9999)) {
                throw Error('invalid-record');
              }
              value = candidate;
            }
          }
        } catch (_) {
          trouble = damaged = true;
        }
      }
      const counts = value ? Object.keys(labels).filter(k => value.counts[k] > 0)
        .map(k => { total += value.counts[k]; return escape(labels[k]) + '：' + value.counts[k]; }).join('<br>') : '';
      const detail = trouble ? '本机记录损坏或读取失败；无法记录/读取该模块状态。' :
        value ? '脚本 ' + escape(value.version) + '<br>最后记录：' + stamp(value.last) + '<br>' + (counts || '本轮尚无有效命中计数') :
        '本轮没有记录';
      return '<tr><th scope="row">' + escape(module.name) + '</th><td>' + detail + '</td></tr>';
    }).join('');
    const sessionText = unavailable ? '本机诊断存储不可用或数据损坏，当前无法可靠记录。自检页仍可显示。' :
      !session ? '尚未开始诊断，默认不记录。' :
      active ? '记录中，将于 ' + stamp(session.until) + ' 自动停止新增记录。' :
      session.until === 0 ? '已手动停止；不再新增记录。' : '15分钟已结束；不再新增记录。';
    const empty = total === 0 ? '<p>目前没有本轮处理记录。这不能直接证明MITM失败：可能尚未发出新请求、URL未匹配、脚本资源未更新、使用缓存或流量没有进入HTTP引擎。</p>' : '';
    const body = '<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">' +
      '<meta name="referrer" content="no-referrer"><title>Jimmy Stash 去广告自检</title>' +
      '<style>body{font:16px/1.65 system-ui,sans-serif;max-width:760px;margin:24px auto;padding:0 18px;color:#202124;background:#fff}' +
      'a{display:inline-block;margin:6px 12px 6px 0}table{width:100%;border-collapse:collapse}th,td{border:1px solid #ddd;padding:10px;text-align:left;vertical-align:top}' +
      '.notice{background:#eef4ff;padding:12px;border-radius:8px}small{color:#555}</style></head><body>' +
      '<h1>Jimmy Stash 去广告自检</h1><p>页面版本：' + version + '；实际请求协议：<strong>' + protocol + '</strong>。</p>' +
      '<div class="notice">看到此页面，说明本次自检请求已执行Stash请求脚本。' +
      (protocol === 'https' ? '本次HTTPS请求也通过了example.com的解密处理。' : '本次是HTTP请求，尚不能证明HTTPS解密有效。') +
      '这不证明淘宝等App已命中，也不证明开屏广告已去除。</div>' +
      '<h2>检查步骤</h2><ol><li>点“开始15分钟诊断”。</li><li>返回结果页，然后冷启动淘宝、小红书等需要检查的App，等待出现广告或进入首页。</li>' +
      '<li>回到Safari的结果页，点“刷新结果”；不要重复点开始，否则会开始新一轮。</li></ol>' +
      '<p><a href="/jimmy-stash-check?start=1">开始15分钟诊断</a><a href="/jimmy-stash-check">返回结果页 / 刷新结果</a>' +
      '<a href="/jimmy-stash-check?stop=1">停止记录</a></p>' +
      (command ? '<p class="notice">' + command + '</p>' : '') + '<p>' + sessionText + '</p>' +
      (action ? '<p><strong>请点“返回结果页 / 刷新结果”后再切换App，避免刷新带开始参数的页面重置本轮。</strong></p>' : '') +
      (damaged ? '<p>部分模块记录不可读取；页面没有显示其中的内容，请重新开始一轮诊断。</p>' : '') + empty +
      '<h2>响应脚本状态</h2><table><thead><tr><th>模块</th><th>本轮结果</th></tr></thead><tbody>' + rows + '</tbody></table>' +
      '<p>这里仅统计响应脚本；原生URL拒绝和域名拦截不经过这些脚本，所以不会显示在表内。计数说明执行状态，不能单凭次数判断广告效果。</p>' +
      '<p>仅在设备保存模块、版本、时间及固定状态计数；不保存或上传Cookie、账号、请求地址、请求头或正文。到期或手动停止后，已有结果保留，但不再新增。</p>' +
      '<p>本自检只新增example.com这个精确解密主机；该主机HTTPS连接可进入解密，脚本只处理本自检路径，不改变任何App的数据处理策略。</p>' +
      '<p><small>Safari可能自动将HTTP升级HTTPS，请以上面的“实际请求协议”为准。此页面没有外部资源或上传功能。</small></p></body></html>';
    output = {response: {status: 200, headers: {'Content-Type':'text/html; charset=utf-8','Cache-Control':'no-store'}, body}};
  } catch (_) {
    // Do not log an exception: host errors can contain private request data.
  } finally {
    $done(output);
  }
})();
```

### taobao.js

源文件：[scripts/ads/taobao.js](../scripts/ads/taobao.js)。

<!-- SOURCE:scripts/ads/taobao.js -->
```javascript
/* SPDX-License-Identifier: GPL-3.0-only
 * Advertising-only transformation adapted from fmz200/wool_scripts Scripts/myBlockAds.js.
 * Source revisions, hashes and modifications: research/sources.lock.json and
 * research/ad-repair-evidence.json; license texts: licenses/.
 * Runtime and optional fixed-code diagnostics generated by build_ad_scripts.py.
 */
// Generated by tools/build_ad_scripts.py; version AD-20261020.4

(() => {
  let result = {}, state = 'url-unmatched';
  const version = "AD-20261020.4", id = "taobao";
  const debug = typeof $argument === 'string' && /(?:^|&)diagnostic=1(?:&|$)/.test($argument);
  /* SPDX-License-Identifier: MIT
   * Optional device-only observation. No request values, headers or bodies.
   * Concurrent script runs can overwrite counters: these are diagnostic hints,
   * not exact traffic statistics. Observation never changes an ad result.
   */
  function observeAdState(id, version, state) {
    try {
      const modules = ['alipan', 'bilibili', 'cainiao', 'jingdong', 'luckin',
        'meituan', 'taobao', 'tieba', 'wechat-articles', 'weibo', 'xiaohongshu'];
      const states = ['url-unmatched', 'unsupported-method', 'body-unavailable',
        'body-too-large', 'http-error', 'unsupported-status', 'non-json',
        'parse-error', 'unsupported-schema', 'unchanged', 'changed', 'exception'];
      if (!modules.includes(id) || !states.includes(state) ||
          typeof version !== 'string' || !/^AD-\d{8}\.\d+$/.test(version)) return;
      if (typeof $persistentStore === 'undefined' || !$persistentStore) return;
      const store = $persistentStore;
      if (typeof store.read !== 'function' || typeof store.write !== 'function') return;
      const sessionText = store.read('jimmy.ads.diag.session.v1');
      if (typeof sessionText !== 'string' || sessionText.length > 2048) return;
      const session = JSON.parse(sessionText);
      const now = Date.now(), limit = 15 * 60 * 1000;
      if (!session || typeof session !== 'object' || Array.isArray(session) ||
          !Number.isSafeInteger(now) ||
          !Number.isSafeInteger(session.id) || session.id <= 0 || session.id > now ||
          !Number.isSafeInteger(session.until) || now >= session.until ||
          session.until > now + limit || session.until - session.id > limit) return;
      const key = 'jimmy.ads.diag.' + id + '.v1';
      const counts = {};
      const previousText = store.read(key);
      if (typeof previousText === 'string' && previousText.length <= 8192) {
        // Corrupted old counters should not stop the current session recording.
        let previous;
        try { previous = JSON.parse(previousText); } catch (_) {}
        if (previous && !Array.isArray(previous) &&
            previous.sessionId === session.id && previous.version === version &&
            previous.counts && typeof previous.counts === 'object' &&
            !Array.isArray(previous.counts)) {
          for (const known of states) {
            if (!Object.prototype.hasOwnProperty.call(previous.counts, known)) continue;
            const count = previous.counts[known];
            if (Number.isSafeInteger(count) && count >= 0 && count <= 9999) counts[known] = count;
          }
        }
      }
      counts[state] = Math.min(9999, (counts[state] || 0) + 1);
      store.write(JSON.stringify({sessionId: session.id, version, last: now, counts}), key);
    } catch (_) {
      // Missing/failed storage must not affect the response or $done.
    }
  }
  function record(x) { return !!x && typeof x === 'object' && !Array.isArray(x); }
  function successful(x, codes = [0, '0']) {
    return record(x) && x.success !== false && !x.error && !x.error_code &&
      (!Object.prototype.hasOwnProperty.call(x,'code') || codes.includes(x.code));
  }
  function mtopSuccess(x) {
    return !Object.prototype.hasOwnProperty.call(x,'ret') || (Array.isArray(x.ret) && x.ret.length > 0 && x.ret.every(v => typeof v === 'string' && /^SUCCESS(?:::|$)/.test(v)));
  }
  // Count UTF-8 bytes, not UTF-16 code units; no binary decoder assumptions.
  function oversized(s) {
    let n = 0;
    for (let i=0; i<s.length; i++) {
      const c = s.charCodeAt(i);
      if (c < 128) n++; else if (c < 2048) n += 2;
      else if (c >= 0xd800 && c <= 0xdbff && i+1 < s.length && s.charCodeAt(i+1) >= 0xdc00 && s.charCodeAt(i+1) <= 0xdfff) { n += 4; i++; }
      else n += 3;
      if (n > 2*1024*1024) return true;
    }
    return false;
  }
  try {
    const req = typeof $request === 'object' && $request ? $request : {};
    const resp = typeof $response === 'object' && $response ? $response : {};
    const url = String(req.url || '');
    if (!["^https:\\/\\/guide-acs\\.m\\.taobao\\.com\\/gw\\/mtop\\.taobao\\.wireless\\.home\\.splash\\.awesome\\.get(\\/\\d+(\\.\\d+)*\\/?)?(\\?|$)"].some(p => new RegExp(p).test(url))) return;
    state = 'unsupported-method';
    if (!["GET", "POST"].includes(req.method)) return;
    state = 'body-unavailable';
    if (typeof resp.body !== 'string' || !resp.body.length) return;
    state = 'body-too-large'; if (oversized(resp.body)) return;
    state = 'http-error';
    // Stash native examples use status. Do not silently accept malformed status
    // or guess that a response with statusCode alone is a successful response.
    if (resp.status !== undefined && !/^2\d\d$/.test(String(resp.status))) return;
    if (resp.status === undefined && resp.statusCode !== undefined) { state = 'unsupported-status'; return; }
    state = 'non-json';
    if (!/^[\s]*[\[{]/.test(resp.body)) return;
    state = 'parse-error'; const obj = JSON.parse(resp.body);
    state = 'unsupported-schema'; if (!record(obj)) return;
    const before = JSON.stringify(obj);
    function transform(obj) {
      if (!successful(obj) || !mtopSuccess(obj)) return false;
      if (typeof obj.api === 'string' && obj.api.toLowerCase() !== 'mtop.taobao.wireless.home.splash.awesome.get') return false;
      const sections = obj.data && obj.data.containers && obj.data.containers.splash_home_base && obj.data.containers.splash_home_base.base && obj.data.containers.splash_home_base.base.sections;
          if (!Array.isArray(sections)) return;
          let supported = sections.length === 0;
          for (const section of sections) {
            const splash = section && section.bizData && section.bizData['taobao-splash'];
            if (!splash || !Array.isArray(splash.data)) continue;
            supported = true;
            for (const item of splash.data) {
              if (!item || typeof item !== 'object' || Array.isArray(item) || !Object.keys(item).length) continue;
              // Only the fields documented by the reviewed upstream splash handler.
              const changes = {waitTime:'0', times:'0', hotStart:'false', coldStart:'false',
                startTime:'3818332800000', endTime:'3818419199000',
                gmtStart:'2090-12-31 00:00:00', gmtEnd:'2090-12-31 23:59:59',
                gmtStartMs:'3818332800000', gmtEndMs:'3818419199000', imgUrl:'', videoUrl:''};
              for (const [key, value] of Object.entries(changes)) {
                const before = item[key];
                // These controls belong to a confirmed taobao-splash entry. Leaving
                // absent controls unset lets the app apply its normal display defaults.
                if (!Object.prototype.hasOwnProperty.call(item, key) || typeof before === 'string') item[key] = value;
                else if (typeof before === 'number' && Number.isFinite(before) && /^\d+$/.test(value)) item[key] = Number(value);
                else if (typeof before === 'boolean' && /^(true|false)$/.test(value)) item[key] = value === 'true';
              }
            }
          }
      return supported;
    }
    if (!transform(obj)) return;
    const body = JSON.stringify(obj);
    state = body === before ? 'unchanged' : 'changed';
    if (state === 'changed') result = {body};
  } catch (_) {
    if (state !== 'parse-error') state = 'exception';
  } finally {
    observeAdState(id, version, state);
    if (debug) { try { console.log('[JimmyAds][' + id + '][' + version + '] ' + state); } catch (_) {} }
    $done(result);
  }
})();
```

### tieba.js

源文件：[scripts/ads/tieba.js](../scripts/ads/tieba.js)。

<!-- SOURCE:scripts/ads/tieba.js -->
```javascript
/* SPDX-License-Identifier: MIT
 * Advertising-only transformation adapted from app2smile/rules js/tieba-json.js.
 * Source revisions, hashes and modifications: research/sources.lock.json and
 * research/ad-repair-evidence.json; license texts: licenses/.
 * Copyright (c) 2023 app2smile.
 * Runtime and optional fixed-code diagnostics generated by build_ad_scripts.py.
 */
// Generated by tools/build_ad_scripts.py; version AD-20261020.4

(() => {
  let result = {}, state = 'url-unmatched';
  const version = "AD-20261020.4", id = "tieba";
  const debug = typeof $argument === 'string' && /(?:^|&)diagnostic=1(?:&|$)/.test($argument);
  /* SPDX-License-Identifier: MIT
   * Optional device-only observation. No request values, headers or bodies.
   * Concurrent script runs can overwrite counters: these are diagnostic hints,
   * not exact traffic statistics. Observation never changes an ad result.
   */
  function observeAdState(id, version, state) {
    try {
      const modules = ['alipan', 'bilibili', 'cainiao', 'jingdong', 'luckin',
        'meituan', 'taobao', 'tieba', 'wechat-articles', 'weibo', 'xiaohongshu'];
      const states = ['url-unmatched', 'unsupported-method', 'body-unavailable',
        'body-too-large', 'http-error', 'unsupported-status', 'non-json',
        'parse-error', 'unsupported-schema', 'unchanged', 'changed', 'exception'];
      if (!modules.includes(id) || !states.includes(state) ||
          typeof version !== 'string' || !/^AD-\d{8}\.\d+$/.test(version)) return;
      if (typeof $persistentStore === 'undefined' || !$persistentStore) return;
      const store = $persistentStore;
      if (typeof store.read !== 'function' || typeof store.write !== 'function') return;
      const sessionText = store.read('jimmy.ads.diag.session.v1');
      if (typeof sessionText !== 'string' || sessionText.length > 2048) return;
      const session = JSON.parse(sessionText);
      const now = Date.now(), limit = 15 * 60 * 1000;
      if (!session || typeof session !== 'object' || Array.isArray(session) ||
          !Number.isSafeInteger(now) ||
          !Number.isSafeInteger(session.id) || session.id <= 0 || session.id > now ||
          !Number.isSafeInteger(session.until) || now >= session.until ||
          session.until > now + limit || session.until - session.id > limit) return;
      const key = 'jimmy.ads.diag.' + id + '.v1';
      const counts = {};
      const previousText = store.read(key);
      if (typeof previousText === 'string' && previousText.length <= 8192) {
        // Corrupted old counters should not stop the current session recording.
        let previous;
        try { previous = JSON.parse(previousText); } catch (_) {}
        if (previous && !Array.isArray(previous) &&
            previous.sessionId === session.id && previous.version === version &&
            previous.counts && typeof previous.counts === 'object' &&
            !Array.isArray(previous.counts)) {
          for (const known of states) {
            if (!Object.prototype.hasOwnProperty.call(previous.counts, known)) continue;
            const count = previous.counts[known];
            if (Number.isSafeInteger(count) && count >= 0 && count <= 9999) counts[known] = count;
          }
        }
      }
      counts[state] = Math.min(9999, (counts[state] || 0) + 1);
      store.write(JSON.stringify({sessionId: session.id, version, last: now, counts}), key);
    } catch (_) {
      // Missing/failed storage must not affect the response or $done.
    }
  }
  function record(x) { return !!x && typeof x === 'object' && !Array.isArray(x); }
  function successful(x, codes = [0, '0']) {
    return record(x) && x.success !== false && !x.error && !x.error_code &&
      (!Object.prototype.hasOwnProperty.call(x,'code') || codes.includes(x.code));
  }
  function mtopSuccess(x) {
    return !Object.prototype.hasOwnProperty.call(x,'ret') || (Array.isArray(x.ret) && x.ret.length > 0 && x.ret.every(v => typeof v === 'string' && /^SUCCESS(?:::|$)/.test(v)));
  }
  // Count UTF-8 bytes, not UTF-16 code units; no binary decoder assumptions.
  function oversized(s) {
    let n = 0;
    for (let i=0; i<s.length; i++) {
      const c = s.charCodeAt(i);
      if (c < 128) n++; else if (c < 2048) n += 2;
      else if (c >= 0xd800 && c <= 0xdbff && i+1 < s.length && s.charCodeAt(i+1) >= 0xdc00 && s.charCodeAt(i+1) <= 0xdfff) { n += 4; i++; }
      else n += 3;
      if (n > 2*1024*1024) return true;
    }
    return false;
  }
  try {
    const req = typeof $request === 'object' && $request ? $request : {};
    const resp = typeof $response === 'object' && $response ? $response : {};
    const url = String(req.url || '');
    if (!["^https:\\/\\/tiebac\\.baidu\\.com\\/c\\/f\\/ad\\/getSplashAd(\\?|$)"].some(p => new RegExp(p).test(url))) return;
    state = 'unsupported-method';
    if (!["GET", "POST"].includes(req.method)) return;
    state = 'body-unavailable';
    if (typeof resp.body !== 'string' || !resp.body.length) return;
    state = 'body-too-large'; if (oversized(resp.body)) return;
    state = 'http-error';
    // Stash native examples use status. Do not silently accept malformed status
    // or guess that a response with statusCode alone is a successful response.
    if (resp.status !== undefined && !/^2\d\d$/.test(String(resp.status))) return;
    if (resp.status === undefined && resp.statusCode !== undefined) { state = 'unsupported-status'; return; }
    state = 'non-json';
    if (!/^[\s]*[\[{]/.test(resp.body)) return;
    state = 'parse-error'; const obj = JSON.parse(resp.body);
    state = 'unsupported-schema'; if (!record(obj)) return;
    const before = JSON.stringify(obj);
    function transform(obj) {
      // Maintained transformation fragment; runtime and diagnostics are generated.
      if (obj.error_code === 2230209 && obj.data === null) return true;
      if (obj.error_code !== 0 || !Object.prototype.hasOwnProperty.call(obj,'data')) return false;
      obj.error_code = 2230209; obj.data = null; return true;
    }
    if (!transform(obj)) return;
    const body = JSON.stringify(obj);
    state = body === before ? 'unchanged' : 'changed';
    if (state === 'changed') result = {body};
  } catch (_) {
    if (state !== 'parse-error') state = 'exception';
  } finally {
    observeAdState(id, version, state);
    if (debug) { try { console.log('[JimmyAds][' + id + '][' + version + '] ' + state); } catch (_) {} }
    $done(result);
  }
})();
```

### wechat-articles.js

源文件：[scripts/ads/wechat-articles.js](../scripts/ads/wechat-articles.js)。

<!-- SOURCE:scripts/ads/wechat-articles.js -->
```javascript
/* SPDX-License-Identifier: GPL-3.0-only
 * Advertising-only transformation adapted from NobyDa/Script QuantumultX/File/Wechat.js.
 * Source revisions, hashes and modifications: research/sources.lock.json and
 * research/ad-repair-evidence.json; license texts: licenses/.
 * Runtime and optional fixed-code diagnostics generated by build_ad_scripts.py.
 */
// Generated by tools/build_ad_scripts.py; version AD-20261020.4

(() => {
  let result = {}, state = 'url-unmatched';
  const version = "AD-20261020.4", id = "wechat-articles";
  const debug = typeof $argument === 'string' && /(?:^|&)diagnostic=1(?:&|$)/.test($argument);
  /* SPDX-License-Identifier: MIT
   * Optional device-only observation. No request values, headers or bodies.
   * Concurrent script runs can overwrite counters: these are diagnostic hints,
   * not exact traffic statistics. Observation never changes an ad result.
   */
  function observeAdState(id, version, state) {
    try {
      const modules = ['alipan', 'bilibili', 'cainiao', 'jingdong', 'luckin',
        'meituan', 'taobao', 'tieba', 'wechat-articles', 'weibo', 'xiaohongshu'];
      const states = ['url-unmatched', 'unsupported-method', 'body-unavailable',
        'body-too-large', 'http-error', 'unsupported-status', 'non-json',
        'parse-error', 'unsupported-schema', 'unchanged', 'changed', 'exception'];
      if (!modules.includes(id) || !states.includes(state) ||
          typeof version !== 'string' || !/^AD-\d{8}\.\d+$/.test(version)) return;
      if (typeof $persistentStore === 'undefined' || !$persistentStore) return;
      const store = $persistentStore;
      if (typeof store.read !== 'function' || typeof store.write !== 'function') return;
      const sessionText = store.read('jimmy.ads.diag.session.v1');
      if (typeof sessionText !== 'string' || sessionText.length > 2048) return;
      const session = JSON.parse(sessionText);
      const now = Date.now(), limit = 15 * 60 * 1000;
      if (!session || typeof session !== 'object' || Array.isArray(session) ||
          !Number.isSafeInteger(now) ||
          !Number.isSafeInteger(session.id) || session.id <= 0 || session.id > now ||
          !Number.isSafeInteger(session.until) || now >= session.until ||
          session.until > now + limit || session.until - session.id > limit) return;
      const key = 'jimmy.ads.diag.' + id + '.v1';
      const counts = {};
      const previousText = store.read(key);
      if (typeof previousText === 'string' && previousText.length <= 8192) {
        // Corrupted old counters should not stop the current session recording.
        let previous;
        try { previous = JSON.parse(previousText); } catch (_) {}
        if (previous && !Array.isArray(previous) &&
            previous.sessionId === session.id && previous.version === version &&
            previous.counts && typeof previous.counts === 'object' &&
            !Array.isArray(previous.counts)) {
          for (const known of states) {
            if (!Object.prototype.hasOwnProperty.call(previous.counts, known)) continue;
            const count = previous.counts[known];
            if (Number.isSafeInteger(count) && count >= 0 && count <= 9999) counts[known] = count;
          }
        }
      }
      counts[state] = Math.min(9999, (counts[state] || 0) + 1);
      store.write(JSON.stringify({sessionId: session.id, version, last: now, counts}), key);
    } catch (_) {
      // Missing/failed storage must not affect the response or $done.
    }
  }
  function record(x) { return !!x && typeof x === 'object' && !Array.isArray(x); }
  function successful(x, codes = [0, '0']) {
    return record(x) && x.success !== false && !x.error && !x.error_code &&
      (!Object.prototype.hasOwnProperty.call(x,'code') || codes.includes(x.code));
  }
  function mtopSuccess(x) {
    return !Object.prototype.hasOwnProperty.call(x,'ret') || (Array.isArray(x.ret) && x.ret.length > 0 && x.ret.every(v => typeof v === 'string' && /^SUCCESS(?:::|$)/.test(v)));
  }
  // Count UTF-8 bytes, not UTF-16 code units; no binary decoder assumptions.
  function oversized(s) {
    let n = 0;
    for (let i=0; i<s.length; i++) {
      const c = s.charCodeAt(i);
      if (c < 128) n++; else if (c < 2048) n += 2;
      else if (c >= 0xd800 && c <= 0xdbff && i+1 < s.length && s.charCodeAt(i+1) >= 0xdc00 && s.charCodeAt(i+1) <= 0xdfff) { n += 4; i++; }
      else n += 3;
      if (n > 2*1024*1024) return true;
    }
    return false;
  }
  try {
    const req = typeof $request === 'object' && $request ? $request : {};
    const resp = typeof $response === 'object' && $response ? $response : {};
    const url = String(req.url || '');
    if (!["^https://mp\\.weixin\\.qq\\.com/mp/getappmsgad/?(?:\\?|$)"].some(p => new RegExp(p).test(url))) return;
    state = 'unsupported-method';
    if (!["GET", "POST"].includes(req.method)) return;
    state = 'body-unavailable';
    if (typeof resp.body !== 'string' || !resp.body.length) return;
    state = 'body-too-large'; if (oversized(resp.body)) return;
    state = 'http-error';
    // Stash native examples use status. Do not silently accept malformed status
    // or guess that a response with statusCode alone is a successful response.
    if (resp.status !== undefined && !/^2\d\d$/.test(String(resp.status))) return;
    if (resp.status === undefined && resp.statusCode !== undefined) { state = 'unsupported-status'; return; }
    state = 'non-json';
    if (!/^[\s]*[\[{]/.test(resp.body)) return;
    state = 'parse-error'; const obj = JSON.parse(resp.body);
    state = 'unsupported-schema'; if (!record(obj)) return;
    const before = JSON.stringify(obj);
    function transform(obj) {
      // Maintained transformation fragment; runtime and diagnostics are generated.
      if (!successful(obj) || (obj.base_resp && obj.base_resp.ret !== 0) || !Array.isArray(obj.advertisement_info) || typeof obj.advertisement_num !== 'number') return false;
      obj.advertisement_info = []; obj.advertisement_num = 0;
      return true;
    }
    if (!transform(obj)) return;
    const body = JSON.stringify(obj);
    state = body === before ? 'unchanged' : 'changed';
    if (state === 'changed') result = {body};
  } catch (_) {
    if (state !== 'parse-error') state = 'exception';
  } finally {
    observeAdState(id, version, state);
    if (debug) { try { console.log('[JimmyAds][' + id + '][' + version + '] ' + state); } catch (_) {} }
    $done(result);
  }
})();
```

### weibo.js

源文件：[scripts/ads/weibo.js](../scripts/ads/weibo.js)。

<!-- SOURCE:scripts/ads/weibo.js -->
```javascript
/* SPDX-License-Identifier: GPL-3.0-only
 * Advertising-only transformation adapted from fmz200/wool_scripts Scripts/weibo/weibo_ads.js.
 * Source revisions, hashes and modifications: research/sources.lock.json and
 * research/ad-repair-evidence.json; license texts: licenses/.
 * Runtime and optional fixed-code diagnostics generated by build_ad_scripts.py.
 */
// Generated by tools/build_ad_scripts.py; version AD-20261020.4

(() => {
  let result = {}, state = 'url-unmatched';
  const version = "AD-20261020.4", id = "weibo";
  const debug = typeof $argument === 'string' && /(?:^|&)diagnostic=1(?:&|$)/.test($argument);
  /* SPDX-License-Identifier: MIT
   * Optional device-only observation. No request values, headers or bodies.
   * Concurrent script runs can overwrite counters: these are diagnostic hints,
   * not exact traffic statistics. Observation never changes an ad result.
   */
  function observeAdState(id, version, state) {
    try {
      const modules = ['alipan', 'bilibili', 'cainiao', 'jingdong', 'luckin',
        'meituan', 'taobao', 'tieba', 'wechat-articles', 'weibo', 'xiaohongshu'];
      const states = ['url-unmatched', 'unsupported-method', 'body-unavailable',
        'body-too-large', 'http-error', 'unsupported-status', 'non-json',
        'parse-error', 'unsupported-schema', 'unchanged', 'changed', 'exception'];
      if (!modules.includes(id) || !states.includes(state) ||
          typeof version !== 'string' || !/^AD-\d{8}\.\d+$/.test(version)) return;
      if (typeof $persistentStore === 'undefined' || !$persistentStore) return;
      const store = $persistentStore;
      if (typeof store.read !== 'function' || typeof store.write !== 'function') return;
      const sessionText = store.read('jimmy.ads.diag.session.v1');
      if (typeof sessionText !== 'string' || sessionText.length > 2048) return;
      const session = JSON.parse(sessionText);
      const now = Date.now(), limit = 15 * 60 * 1000;
      if (!session || typeof session !== 'object' || Array.isArray(session) ||
          !Number.isSafeInteger(now) ||
          !Number.isSafeInteger(session.id) || session.id <= 0 || session.id > now ||
          !Number.isSafeInteger(session.until) || now >= session.until ||
          session.until > now + limit || session.until - session.id > limit) return;
      const key = 'jimmy.ads.diag.' + id + '.v1';
      const counts = {};
      const previousText = store.read(key);
      if (typeof previousText === 'string' && previousText.length <= 8192) {
        // Corrupted old counters should not stop the current session recording.
        let previous;
        try { previous = JSON.parse(previousText); } catch (_) {}
        if (previous && !Array.isArray(previous) &&
            previous.sessionId === session.id && previous.version === version &&
            previous.counts && typeof previous.counts === 'object' &&
            !Array.isArray(previous.counts)) {
          for (const known of states) {
            if (!Object.prototype.hasOwnProperty.call(previous.counts, known)) continue;
            const count = previous.counts[known];
            if (Number.isSafeInteger(count) && count >= 0 && count <= 9999) counts[known] = count;
          }
        }
      }
      counts[state] = Math.min(9999, (counts[state] || 0) + 1);
      store.write(JSON.stringify({sessionId: session.id, version, last: now, counts}), key);
    } catch (_) {
      // Missing/failed storage must not affect the response or $done.
    }
  }
  function record(x) { return !!x && typeof x === 'object' && !Array.isArray(x); }
  function successful(x, codes = [0, '0']) {
    return record(x) && x.success !== false && !x.error && !x.error_code &&
      (!Object.prototype.hasOwnProperty.call(x,'code') || codes.includes(x.code));
  }
  function mtopSuccess(x) {
    return !Object.prototype.hasOwnProperty.call(x,'ret') || (Array.isArray(x.ret) && x.ret.length > 0 && x.ret.every(v => typeof v === 'string' && /^SUCCESS(?:::|$)/.test(v)));
  }
  // Count UTF-8 bytes, not UTF-16 code units; no binary decoder assumptions.
  function oversized(s) {
    let n = 0;
    for (let i=0; i<s.length; i++) {
      const c = s.charCodeAt(i);
      if (c < 128) n++; else if (c < 2048) n += 2;
      else if (c >= 0xd800 && c <= 0xdbff && i+1 < s.length && s.charCodeAt(i+1) >= 0xdc00 && s.charCodeAt(i+1) <= 0xdfff) { n += 4; i++; }
      else n += 3;
      if (n > 2*1024*1024) return true;
    }
    return false;
  }
  try {
    const req = typeof $request === 'object' && $request ? $request : {};
    const resp = typeof $response === 'object' && $response ? $response : {};
    const url = String(req.url || '');
    if (!["^https://api\\.weibo\\.cn/2/(?:searchall|statuses/container_timeline_topic(?:page)?)/?(?:\\?|$)"].some(p => new RegExp(p).test(url))) return;
    state = 'unsupported-method';
    if (!["GET", "POST"].includes(req.method)) return;
    state = 'body-unavailable';
    if (typeof resp.body !== 'string' || !resp.body.length) return;
    state = 'body-too-large'; if (oversized(resp.body)) return;
    state = 'http-error';
    // Stash native examples use status. Do not silently accept malformed status
    // or guess that a response with statusCode alone is a successful response.
    if (resp.status !== undefined && !/^2\d\d$/.test(String(resp.status))) return;
    if (resp.status === undefined && resp.statusCode !== undefined) { state = 'unsupported-status'; return; }
    state = 'non-json';
    if (!/^[\s]*[\[{]/.test(resp.body)) return;
    state = 'parse-error'; const obj = JSON.parse(resp.body);
    state = 'unsupported-schema'; if (!record(obj)) return;
    const before = JSON.stringify(obj);
    function transform(obj) {
      // Maintained transformation fragment; runtime and diagnostics are generated.
      if (!successful(obj) || !Array.isArray(obj.items)) return false;
      // fmz200 weibo_ads.js: only explicit advertising markers in known topic/search
      // lists. Keep recommendations, navigation, profile and comment semantics.
      const ad = item => record(item) && record(item.data) && (item.data.mblogtypename === '广告' || item.data.ad_state === 1 || item.data.is_ad === 1);
      obj.items = obj.items.filter(item => !ad(item));
      if (/\/searchall\/?(?:\?|$)/.test(url)) for (const item of obj.items) if (record(item) && Array.isArray(item.items)) item.items = item.items.filter(v => !ad(v));
      return true;
    }
    if (!transform(obj)) return;
    const body = JSON.stringify(obj);
    state = body === before ? 'unchanged' : 'changed';
    if (state === 'changed') result = {body};
  } catch (_) {
    if (state !== 'parse-error') state = 'exception';
  } finally {
    observeAdState(id, version, state);
    if (debug) { try { console.log('[JimmyAds][' + id + '][' + version + '] ' + state); } catch (_) {} }
    $done(result);
  }
})();
```

### xiaohongshu.js

源文件：[scripts/ads/xiaohongshu.js](../scripts/ads/xiaohongshu.js)。

<!-- SOURCE:scripts/ads/xiaohongshu.js -->
```javascript
/* SPDX-License-Identifier: GPL-3.0-only
 * Advertising-only transformation adapted from fmz200/wool_scripts Scripts/xiaohongshu/xiaohongshu.js.
 * Source revisions, hashes and modifications: research/sources.lock.json and
 * research/ad-repair-evidence.json; license texts: licenses/.
 * Runtime and optional fixed-code diagnostics generated by build_ad_scripts.py.
 */
// Generated by tools/build_ad_scripts.py; version AD-20261020.4

(() => {
  let result = {}, state = 'url-unmatched';
  const version = "AD-20261020.4", id = "xiaohongshu";
  const debug = typeof $argument === 'string' && /(?:^|&)diagnostic=1(?:&|$)/.test($argument);
  /* SPDX-License-Identifier: MIT
   * Optional device-only observation. No request values, headers or bodies.
   * Concurrent script runs can overwrite counters: these are diagnostic hints,
   * not exact traffic statistics. Observation never changes an ad result.
   */
  function observeAdState(id, version, state) {
    try {
      const modules = ['alipan', 'bilibili', 'cainiao', 'jingdong', 'luckin',
        'meituan', 'taobao', 'tieba', 'wechat-articles', 'weibo', 'xiaohongshu'];
      const states = ['url-unmatched', 'unsupported-method', 'body-unavailable',
        'body-too-large', 'http-error', 'unsupported-status', 'non-json',
        'parse-error', 'unsupported-schema', 'unchanged', 'changed', 'exception'];
      if (!modules.includes(id) || !states.includes(state) ||
          typeof version !== 'string' || !/^AD-\d{8}\.\d+$/.test(version)) return;
      if (typeof $persistentStore === 'undefined' || !$persistentStore) return;
      const store = $persistentStore;
      if (typeof store.read !== 'function' || typeof store.write !== 'function') return;
      const sessionText = store.read('jimmy.ads.diag.session.v1');
      if (typeof sessionText !== 'string' || sessionText.length > 2048) return;
      const session = JSON.parse(sessionText);
      const now = Date.now(), limit = 15 * 60 * 1000;
      if (!session || typeof session !== 'object' || Array.isArray(session) ||
          !Number.isSafeInteger(now) ||
          !Number.isSafeInteger(session.id) || session.id <= 0 || session.id > now ||
          !Number.isSafeInteger(session.until) || now >= session.until ||
          session.until > now + limit || session.until - session.id > limit) return;
      const key = 'jimmy.ads.diag.' + id + '.v1';
      const counts = {};
      const previousText = store.read(key);
      if (typeof previousText === 'string' && previousText.length <= 8192) {
        // Corrupted old counters should not stop the current session recording.
        let previous;
        try { previous = JSON.parse(previousText); } catch (_) {}
        if (previous && !Array.isArray(previous) &&
            previous.sessionId === session.id && previous.version === version &&
            previous.counts && typeof previous.counts === 'object' &&
            !Array.isArray(previous.counts)) {
          for (const known of states) {
            if (!Object.prototype.hasOwnProperty.call(previous.counts, known)) continue;
            const count = previous.counts[known];
            if (Number.isSafeInteger(count) && count >= 0 && count <= 9999) counts[known] = count;
          }
        }
      }
      counts[state] = Math.min(9999, (counts[state] || 0) + 1);
      store.write(JSON.stringify({sessionId: session.id, version, last: now, counts}), key);
    } catch (_) {
      // Missing/failed storage must not affect the response or $done.
    }
  }
  function record(x) { return !!x && typeof x === 'object' && !Array.isArray(x); }
  function successful(x, codes = [0, '0']) {
    return record(x) && x.success !== false && !x.error && !x.error_code &&
      (!Object.prototype.hasOwnProperty.call(x,'code') || codes.includes(x.code));
  }
  function mtopSuccess(x) {
    return !Object.prototype.hasOwnProperty.call(x,'ret') || (Array.isArray(x.ret) && x.ret.length > 0 && x.ret.every(v => typeof v === 'string' && /^SUCCESS(?:::|$)/.test(v)));
  }
  // Count UTF-8 bytes, not UTF-16 code units; no binary decoder assumptions.
  function oversized(s) {
    let n = 0;
    for (let i=0; i<s.length; i++) {
      const c = s.charCodeAt(i);
      if (c < 128) n++; else if (c < 2048) n += 2;
      else if (c >= 0xd800 && c <= 0xdbff && i+1 < s.length && s.charCodeAt(i+1) >= 0xdc00 && s.charCodeAt(i+1) <= 0xdfff) { n += 4; i++; }
      else n += 3;
      if (n > 2*1024*1024) return true;
    }
    return false;
  }
  try {
    const req = typeof $request === 'object' && $request ? $request : {};
    const resp = typeof $response === 'object' && $response ? $response : {};
    const url = String(req.url || '');
    if (!["^https://edith\\.xiaohongshu\\.com/api/sns/(?:v\\d+/system_service/(?:splash_config|config)|v6/homefeed)/?(?:\\?|$)"].some(p => new RegExp(p).test(url))) return;
    state = 'unsupported-method';
    if (!["GET", "POST"].includes(req.method)) return;
    state = 'body-unavailable';
    if (typeof resp.body !== 'string' || !resp.body.length) return;
    state = 'body-too-large'; if (oversized(resp.body)) return;
    state = 'http-error';
    // Stash native examples use status. Do not silently accept malformed status
    // or guess that a response with statusCode alone is a successful response.
    if (resp.status !== undefined && !/^2\d\d$/.test(String(resp.status))) return;
    if (resp.status === undefined && resp.statusCode !== undefined) { state = 'unsupported-status'; return; }
    state = 'non-json';
    if (!/^[\s]*[\[{]/.test(resp.body)) return;
    state = 'parse-error'; const obj = JSON.parse(resp.body);
    state = 'unsupported-schema'; if (!record(obj)) return;
    const before = JSON.stringify(obj);
    function transform(obj) {
      // Maintained transformation fragment; runtime and diagnostics are generated.
      if (!successful(obj) || !record(obj.data) && !Array.isArray(obj.data)) return false;
      if (/\/system_service\/config\/?(?:\?|$)/.test(url)) {
        if (!record(obj.data)) return false;
        // Only splash is unambiguously advertising. Keep app_theme/store/loading_img.
        if (!Object.prototype.hasOwnProperty.call(obj.data,'splash')) return false;
        delete obj.data.splash; return true;
      }
      if (/\/v6\/homefeed\/?(?:\?|$)/.test(url)) {
        if (!Array.isArray(obj.data)) return false;
        // Do not remove live streams, shopping notes, card icons or related questions.
        obj.data = obj.data.filter(item => !(record(item) && record(item.ads_info) && Object.keys(item.ads_info).length));
        return true;
      }
      const groups = obj.data.ads_groups;
      if (!Array.isArray(groups)) return false;
      let supported = groups.length === 0;
      function postpone(item) {
        if (!record(item) || !Object.keys(item).length) return;
        for (const key of ['start_time','end_time']) {
          if (!Object.prototype.hasOwnProperty.call(item,key)) continue;
          if (!(typeof item[key] === 'number' && Number.isFinite(item[key])) && !(typeof item[key] === 'string' && /^\d+$/.test(item[key]))) return;
        }
        supported = true;
        for (const [key,value] of [['start_time',3818332800],['end_time',3818419199]]) item[key] = typeof item[key] === 'string' ? String(value) : value;
      }
      for (const group of groups) { postpone(group); if (group && Array.isArray(group.ads)) group.ads.forEach(postpone); }
      return supported;
    }
    if (!transform(obj)) return;
    const body = JSON.stringify(obj);
    state = body === before ? 'unchanged' : 'changed';
    if (state === 'changed') result = {body};
  } catch (_) {
    if (state !== 'parse-error') state = 'exception';
  } finally {
    observeAdState(id, version, state);
    if (debug) { try { console.log('[JimmyAds][' + id + '][' + version + '] ' + state); } catch (_) {} }
    $done(result);
  }
})();
```
