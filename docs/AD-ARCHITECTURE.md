# Stash 去广告：当前实现、修复证据与排查规格

当前配置：**AD-20261020.2**；脚本：**AD-20261020.1**。用户已明确采用整合入口，并取消逐App独立开关要求。日常只使用原 `config/stash.yaml` 链接，刷新主配置即可取得全部已审阅专项和内嵌脚本，无需逐款安装。本次统一说明文字，不改变广告逻辑、分流、私人接入或上述版本。此前修复保留了路由/HKG改动，原生URL字段与脚本保护继续有效。**文件已发布，真实 iPhone 去广告效果仍未完成验收。** 用户已确认 HTTP/MITM 开启、自建 CA 完全信任，并表示会将 Stash、App 更新到最新版；不把未装证书当作统一解释。自动签到继续暂停。

## 1. 已修复问题与证据边界

| 历史问题或调整 | 当前实现 | 能确认到哪一层 |
|---|---|---|
| 主配置没有广告 RULE-SET，expanded 只换了不存在的 provider | `build_subscription.py` 保留并引用唯一“基础广告”provider；AD-20261020.2默认指向扩展快照，其他分流继续按原顺序展开 | 扩展包有实际引用；局域网、Apple推送、Microsoft登录例外与手动放行仍优先。规则集数量不等于开屏效果 |
| 配置用旧 `http.rewrite`，与用户核对的当前官方 `http.url-rewrite` 不同 | 修改真正的目录生成器与旧5款模块，统一生成 `url-rewrite` | 字段现与用户提供的当前官方调查一致；**旧 rewrite 是否仍为别名未验证，不能据此断言所有失败的根因** |
| 固定空响应绕到 JS；联通图片改成普通拒绝 | 原生 reject、reject-200、reject-dict、reject-img 分别保留；删除共享空响应脚本及对应 provider/request handler | 静态动作、端点正反例和无重复处理通过；真实状态码、头部与 App 回退须 Stash 验收 |
| 请求脚本依赖 `$response` 未定义；null/空对象会放行 | 固定响应不再经过请求 JS | 消除了该代码路径；**没有证明旧 Stash 真会传入 null/空对象** |
| 安装步骤过多，逐App开关需求已取消 | 原订阅入口整合现有专项；40份模块文件保留为构建源与旧安装兼容文件 | 已满足整合入口的结构要求；不再将逐App开关列为缺失功能。额外同名覆写仍须停用，避免重复挂载 |
| 脚本无版本、解析/结构问题难区分 | 统一自包含运行模板，临时参数诊断和独立只读探针 | 默认无日志；所有返回只调用一次 `$done`，固定状态不包含私人值。不是“没日志=没广告” |

官方能力核对的实际限制：最近一次常规和额外权限下请求官方站均得到云网络 403，**没有下载到当前正文**。`url-rewrite`、五种 reject 动作、Mock 和 HTTP/3 限制依据是用户此前提供的官方调查结论。`argument` 另有锁定版本 blackmatrix7 原生 Stash 模块声明作为参考。不能把这些说成已独立核实最低版本；目标为用户将更新的最新版，数字版本未提供。来源和未核实点见 [能力记录](STASH-CAPABILITIES.md)、[访问记录](../research/official-doc-access.json)。

## 2. 统一入口与日常使用

稳定主链接仍为：

```text
https://raw.githubusercontent.com/Panzm6111/Jimmy-s-Stash-rules/main/config/stash.yaml
```

主配置保留18个策略组、7个测速池、私人“机场”provider、原DNS与分流。**AD-20261020.2默认整合全部40款已有App专项、11份内嵌响应JS、扩展域名规则集。** 唯一“基础广告”provider沿用名称，但其URL默认指向38,066条已审阅扩展快照，并有真实RULE-SET引用；无需再导入expanded。38条基础包仅保留作维护和旧分层安装兼容。扩展包可能误拦，也不能代替开屏接口处理；本次整合不代表效果已通过验收。

11份JS通过`script-providers.<name>.content`内嵌，刷新主配置时同时取得脚本正文、主机、原生动作和handler，不再要求整合模式单独刷新JS。content只有历史原生示例作为参考，原注释仅推荐开发使用且示例已停止维护；当前官方正文不可访问，未核实当前原生执行或最低版本，完整证据见[能力记录](STASH-CAPABILITIES.md)。脚本逻辑未改，诊断仍显示AD-20261020.1；配置头部AD-20261020.2标识的是新的承载方式。

首次更新：保留已能用的本机私人覆写和证书；停用额外App专项、旧整合“广告增强”、expanded及其同名副本；刷新**原主配置**并确认头部AD-20261020.2，再重建连接。未添加过这些额外覆写就跳过停用步骤。私人URL不写进公共配置，不需要重填已生效的私人接入。

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

11个响应脚本各自独立执行，保留原许可，运行模板构建时内嵌，不要求手机加载模块。只读 `$request.url/method`、`$response.body/status` 和临时 `$argument`；不读取Cookie/Authorization、不保存正文、不联网、不写存储、不通知。探针只读URL用于内存匹配，**不读取请求或响应正文、头部**。

- 响应handler统一 `type: response`、`require-body: true`、`timeout: 5`。B站限GET，其他限GET/POST。缺失/null/空响应对象、正文非字符串或空正文均放行。没有把空对象响应当成功业务结构。
- 正文限 **2 MiB UTF-8编码长度**，不再把JS字符串码元数当网络字节数。二进制不猜测解码；不开启 binary-mode 或处理protobuf。
- 实际原生参考使用 `$response.status`。数字200和字符串"200"接受；错误、完整HTTP状态行或非预期形态不猜测放行修改。只有statusCode的形态输出unsupported-status；两者都不存在时沿用旧无状态字段保护分支，仍要求JSON与已知业务结构。具体原生对象形态待真机记录。
- 保留业务错误/MTOP错误，空修改对象 `$done({})` 保留原响应；产生修改只返回 `{body: JSON字符串}`，不手动伪造压缩/长度头。Stash自动重编码和头部处理仍是原生验收项。
- try/finally确保本地执行恰好调用一次`$done`。没有异步请求/重试。**原生5秒超时由Stash记录，JS被终止后不能自己补发timeout日志或保证回退**。
- 临时诊断：整合模式在设备创建主配置的**临时诊断副本**，仅将目标HTTP脚本条目的`argument: diagnostic=0`改为1，选中副本并保持私人层关联。完成后删除/停用临时副本，切回原远程主配置；不要把副本当长期更新入口。旧分层安装的诊断才涉及单独覆写，当前日常使用无需进行这种操作。

日志示例：`[JimmyAds][taobao][AD-20261020.1] changed`。状态仅为固定枚举：url-unmatched、unsupported-method、body-unavailable、body-too-large、http-error、unsupported-status、non-json、parse-error、unsupported-schema、unchanged、changed、exception。没有异常详情、账号值、完整URL/查询或正文。默认参数0完全不记录，开启时每次调用最多一条；测试包含注入私人哨兵及故障日志设施。

<a id="6-临时只读诊断先确定请求有没有进入引擎"></a>

## 6. 临时只读诊断：先确定请求有没有进入引擎

独立诊断覆写，**默认不导入、不启用**：

```text
https://raw.githubusercontent.com/Panzm6111/Jimmy-s-Stash-rules/main/modules/diagnostics/ads.stoverride
```

1. 整合入口需在设备创建临时本地诊断副本，清空其`http.url-rewrite`和`http.script`数组，广告组暂选DIRECT，并停用额外广告覆写；保留分流、私人接入和HTTP/MITM。仅关闭同名覆写不能隔离内置处理。旧分层安装可通过暂停原广告覆写隔离处理；这不是当前整合入口的操作步骤。探针只观察已审阅45个精确主机，不解密全域名。
2. 启用诊断覆写，刷新其`jimmy_ads_probe`脚本，重建连接，冷启动目标App；诊断会输出固定 `request-url-matched` 或 `request-url-unmatched`，不改变请求。记录广告位置、时间及模块/版本/状态。
3. 在Stash本机连接/HTTP记录中查看目标主机、端口、TCP或UDP、是否已解密；**不要分享完整记录**。没有探针日志可能是资源未下载、脚本未挂载、没发新请求、未进HTTP、缓存或不在当前主机列表，不能单凭无日志判定原因。
4. 关闭探针，恢复原配置中的正式处理与广告组选择；如需响应日志，按上节另做仅目标handler参数为1的临时副本。旧分层安装才恢复其原广告覆写。探针不与正式改写竞争；不能假定Stash不同改写步骤必定按同一顺序执行。
5. 原生固定动作不运行响应JS，在Stash本机看其重写命中；响应handler看下面决策表。排查完成关闭探针和临时诊断。

| 观察到的证据 | 可以判断的方向 | 不能直接下的结论 |
|---|---|---|
| 整合主配置头部不是AD-20261020.2，或响应JS日志不是AD-20261020.1 | 检查当前选中配置及更新；整合模式只刷新原主配置后重建连接 | 配置和脚本版本不同是本次设计；脚本.1不代表配置未更新 |
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
| 公共主配置 | 建议每周手动刷新原URL一次；发布修复后立即刷新 | 主机、原生动作、handler和11份内嵌JS一并更新；扩展provider默认引用也在这里。不承诺后台自动更新整份配置 |
| 旧App覆写（仅历史兼容） | 仅已有旧分层安装仍分别更新覆写 | 当前整合入口已包含这些声明，不新增或叠加；本地副本不会自动跟随远程声明 |
| 远程广告规则集 | 建议保持现有86400秒，即24小时自动尝试刷新；下载错误时手动刷新 | 整合入口默认引用扩展快照，存在真实RULE-SET；这是刷新间隔，不是每日北京时间零点执行保证 |
| 广告JS | 随整合主配置一起更新，无需独立刷新 | 内嵌JS不会独立后台更新；旧分层远程JS的86400秒刷新机制仅用于历史兼容 |
| 本地静态包/私人节点快照 | 重新用当前源构建/导入，保留设备私人信息 | 静态规则/内嵌JS不是远程自动更新；私人节点快照不自动更新机场 |
| 私人机场 | 建议保持现有86400秒，即24小时自动尝试刷新；节点异常或机场通知变更时手动刷新 | 不继承机场响应中的分流/DNS；机场更换URL时仍须本人在设备修改，不能自动发现新URL |

以上频率统一见[更新教程](UPDATES.md)。7个节点池的1800秒检查是30分钟测速，不是更新规则。规则集只下载本仓库已发布快照；建议维护者每周人工检查上游一次，有已确认失效时及时检查，审核许可与代码后再发布。当前没有自动审查并同步上游的定时任务。

## 8. 验收、误伤与回退

验证分三层：静态配置/源与生成结果；源代码重建模拟样本；真实iPhone Stash解析、命中及广告效果。已有检查覆盖前两层，**第三层未运行**。官方站403、数字版本缺失、无真实脱敏响应都记录为限制，不用62个模拟测试或38,066条规则替代效果判断。精确运行记录见 [PROGRESS](../PROGRESS.md)。

手机最小验收顺序：整合入口已载入全部已有专项，先依次观察淘宝、微博、小红书，然后美团、京东及其他App；观察顺序不改变整合配置的已启用范围。每款分别检查冷启动、后台返回、正常使用触发预加载后再启动；记录广告是否消失、有无空白页/倒计时/更长加载，并检查登录、搜索、消息、视频、正常领券等业务。广告有频控，至少多次观察并结合命中记录；可用已隔离处理的临时诊断副本或原来可用的备份配置对照。单次没有广告不能判成功。

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
| request_handlers | 0 |
| runtime_js_providers | 11 |
| mitm_exact_hosts | 45 |
| optional_probe_js | 1 |

公共主配置已整合以下全部40款专项，11份响应JS通过content内嵌。此表列出构建来源与处理范围，用户不需逐款导入；模块原路径保留作维护和旧安装兼容。逐App开关已取消需求，探针另列、默认关闭。

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

下列原生字段直接摘自主配置，省略完整分流与script-providers正文，不能直接作为主配置导入。11份provider的content与第12节同名JS逐字对应。LAN/系统例外优先，然后精确路径接管例外、专项域名与广告RULE-SET，后面仍有完整分流与终止MATCH。

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
| [config/stash.yaml](../config/stash.yaml) | `6a57834a0512f3b89a3644980568f4708920664ae464456f3147514e7ac99afc` |
| [config/core.stoverride](../config/core.stoverride) | `e64bfa01488b4579e03accb239e5688f004bcfab8c2ccd40d12a21fa6a715b94` |
| [tools/build_ad_scripts.py](../tools/build_ad_scripts.py) | `0af78f79d83532318c23c3a442c31927e16dad43163640178aa8b737b3ae3a79` |
| [scripts/ads/alipan.js](../scripts/ads/alipan.js) | `729a277242f2bbbe626c34716e4eddff031c161d3011b8f39e7e346799991aa8` |
| [scripts/ads/bilibili.js](../scripts/ads/bilibili.js) | `54b416c99de3dd6d401cac10481883bafcebf677e18981383338384a007bc43e` |
| [scripts/ads/cainiao.js](../scripts/ads/cainiao.js) | `4d0f186e786bb281b6e9e5bff468867a43c0ca05e446fd49f2db07e3f74adae7` |
| [scripts/ads/jingdong.js](../scripts/ads/jingdong.js) | `432e156d6e7cfc9d720a0a232c8b108fa1cc983640de516bccbe92de26cf32f6` |
| [scripts/ads/luckin.js](../scripts/ads/luckin.js) | `109b19679e9a43c0d69b5168ad9b05d1494a88df0f7a74f1b041a93c1414997b` |
| [scripts/ads/meituan.js](../scripts/ads/meituan.js) | `71f1c46a1230f684b5f58b94e8b306325a17eaa964d51dbc870efa8f1f492798` |
| [scripts/ads/probe.js](../scripts/ads/probe.js) | `a6f98eb006a8fd72be69fa7d068c93e817f318ccc7b61b55ee6d73a3a8e958d2` |
| [scripts/ads/taobao.js](../scripts/ads/taobao.js) | `05b71cbaa7950ce569b98ddcce59eca448b29db4ec650e99ee6a3f1f2551b57a` |
| [scripts/ads/tieba.js](../scripts/ads/tieba.js) | `6c39725a2cf24c51bdccc5ee6d470feeea2c637d9714e3b7767632407b7cf6c3` |
| [scripts/ads/wechat-articles.js](../scripts/ads/wechat-articles.js) | `831411fb29e910a29a288c8fd77b1a4579ecf9074ae4a9e7ee6b29fe52e0c2f0` |
| [scripts/ads/weibo.js](../scripts/ads/weibo.js) | `db34ab8f1236362feaac08a4bbebdaaab422cb3d60aff5e9f68f20a88b65a7ca` |
| [scripts/ads/xiaohongshu.js](../scripts/ads/xiaohongshu.js) | `f5f79fdf840a88e6c46e6786386c1243b247721b612699fe133aa9fecd48988d` |

完整输入哈希和结构计数见 [ad-architecture-audit.json](../research/ad-architecture-audit.json)。

## 12. 当前全部运行JS原文

其中11份是整合入口内嵌的响应处理；模块中的远程加载声明仅保留作旧安装兼容。另有probe可选诊断，不参与正常去广告。每份代码独立保留许可；下列正文与稳定脚本文件逐字相同。

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
// Generated by tools/build_ad_scripts.py; version AD-20261020.1

(() => {
  let result = {}, state = 'url-unmatched';
  const version = "AD-20261020.1", id = "alipan";
  const debug = typeof $argument === 'string' && /(?:^|&)diagnostic=1(?:&|$)/.test($argument);
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
// Generated by tools/build_ad_scripts.py; version AD-20261020.1

(() => {
  let result = {}, state = 'url-unmatched';
  const version = "AD-20261020.1", id = "bilibili";
  const debug = typeof $argument === 'string' && /(?:^|&)diagnostic=1(?:&|$)/.test($argument);
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
// Generated by tools/build_ad_scripts.py; version AD-20261020.1

(() => {
  let result = {}, state = 'url-unmatched';
  const version = "AD-20261020.1", id = "cainiao";
  const debug = typeof $argument === 'string' && /(?:^|&)diagnostic=1(?:&|$)/.test($argument);
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
// Generated by tools/build_ad_scripts.py; version AD-20261020.1

(() => {
  let result = {}, state = 'url-unmatched';
  const version = "AD-20261020.1", id = "jingdong";
  const debug = typeof $argument === 'string' && /(?:^|&)diagnostic=1(?:&|$)/.test($argument);
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
// Generated by tools/build_ad_scripts.py; version AD-20261020.1

(() => {
  let result = {}, state = 'url-unmatched';
  const version = "AD-20261020.1", id = "luckin";
  const debug = typeof $argument === 'string' && /(?:^|&)diagnostic=1(?:&|$)/.test($argument);
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
// Generated by tools/build_ad_scripts.py; version AD-20261020.1

(() => {
  let result = {}, state = 'url-unmatched';
  const version = "AD-20261020.1", id = "meituan";
  const debug = typeof $argument === 'string' && /(?:^|&)diagnostic=1(?:&|$)/.test($argument);
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
    console.log('[JimmyAds][' + (hit ? hit.id : 'probe') + '][AD-20261020.1] ' + (hit ? 'request-url-matched' : 'request-url-unmatched'));
  } catch (_) { try { console.log('[JimmyAds][probe][AD-20261020.1] exception'); } catch (_) {} }
  finally { $done({}); }
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
// Generated by tools/build_ad_scripts.py; version AD-20261020.1

(() => {
  let result = {}, state = 'url-unmatched';
  const version = "AD-20261020.1", id = "taobao";
  const debug = typeof $argument === 'string' && /(?:^|&)diagnostic=1(?:&|$)/.test($argument);
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
// Generated by tools/build_ad_scripts.py; version AD-20261020.1

(() => {
  let result = {}, state = 'url-unmatched';
  const version = "AD-20261020.1", id = "tieba";
  const debug = typeof $argument === 'string' && /(?:^|&)diagnostic=1(?:&|$)/.test($argument);
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
// Generated by tools/build_ad_scripts.py; version AD-20261020.1

(() => {
  let result = {}, state = 'url-unmatched';
  const version = "AD-20261020.1", id = "wechat-articles";
  const debug = typeof $argument === 'string' && /(?:^|&)diagnostic=1(?:&|$)/.test($argument);
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
// Generated by tools/build_ad_scripts.py; version AD-20261020.1

(() => {
  let result = {}, state = 'url-unmatched';
  const version = "AD-20261020.1", id = "weibo";
  const debug = typeof $argument === 'string' && /(?:^|&)diagnostic=1(?:&|$)/.test($argument);
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
// Generated by tools/build_ad_scripts.py; version AD-20261020.1

(() => {
  let result = {}, state = 'url-unmatched';
  const version = "AD-20261020.1", id = "xiaohongshu";
  const debug = typeof $argument === 'string' && /(?:^|&)diagnostic=1(?:&|$)/.test($argument);
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
    if (debug) { try { console.log('[JimmyAds][' + id + '][' + version + '] ' + state); } catch (_) {} }
    $done(result);
  }
})();
```
