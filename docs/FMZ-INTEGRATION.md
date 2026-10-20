# fmz200 去广告接入明细

当前发布目标：**AD-20261020.5**。使用原 `config/stash.yaml`，无需新增覆写、换机场或重新安装证书。实际发布状态以 [PROGRESS](../PROGRESS.md) 为准。

这次重新读取了 [fmz200/wool_scripts](https://github.com/fmz200/wool_scripts) 的代码和 GPL-3.0 许可证。上游 HEAD 仍是 `5d5f63fcf98bc69d5f8f1b1bae6f86a01ee4bb97`，与之前采用的版本相同；本次主要补齐我们此前没有接入的分支，不是假称上游刚修好了所有开屏。上游 README 本身也注明部分规则可能失效。

## 手机怎么更新

1. 在 Stash 配置列表更新原公共配置，确认文本开头为 `AD-20261020.5`：

   ```text
   https://raw.githubusercontent.com/Panzm6111/Jimmy-s-Stash-rules/main/config/stash.yaml
   ```

2. 保留原私人机场覆写及自建证书；选中更新后的配置，断开再连接。仍用规则模式，广告拦截组选 REJECT，HTTP/MITM 保持开启。
3. 主配置会带来新主机、URL 匹配和带 `.5` 版本参数的脚本地址，脚本仍需联网加载。如果你使用的是无更新地址的本地副本，要从上述 URL 导入并关联已有私人覆写。
4. 可打开 [本机自检页](https://example.com/jimmy-stash-check)，确认页头 `.5`，开始一轮诊断后使用 App，再回页面刷新。各行显示的脚本版本才是该响应脚本实际执行版本。原生拒绝不写入响应计数。

不需要添加 fmz200 的 Quantumult X/Surge 链接，不需要另开 expanded。已有额外广告覆写应停用，避免与整合入口重复。

## 本次实际补充

以下源码行号均对应固定提交，不是会漂移的 main。完整 URL、SHA256 及协议变更模块清单见 [fmz-integration.json](../research/fmz-integration.json)。路径、正反例同时进入维护源和自动验证。

| App | 新增或补齐 | 来源与处理方式 | 业务边界 |
|---|---|---|---|
| 淘宝 | `acs.m.taobao.com/gw/mtop.alibaba.advertisementservice.getadv` | rewrite.snippet 第4427行，原生 `reject-dict`，限定API及可选数字版本段 | 不拦普通商品、搜索、订单、cloudvideo或poplayer；这是补充广告接口，不证明它是当前开屏主链 |
| 小红书 | `rec`、`www` 两个主机上的 `v6/homefeed`；`www` 的 `v*/ads/resource` | rewrite.snippet 第5521、5535行；xiaohongshu.js 第282–305行。首页只删非空 `ads_info` 项；独立资源接口返回空JSON | 保留直播、带货笔记、下载、水印、画质、用户信息和推荐；不把未知v7结构当v6处理 |
| 微博 | `api/mapi.weibo.cn`、`api/mapi.weibo.com`；热搜 `page/flowpage`、评论 `mix_comments/container_detail_comment/container_detail_mix` | weibo.snippet 第95–118行；weibo_ads.js 第35–49、162–169行。删除明确promotion、c_type:51、广告adType或非空commentAdType | 不清整个页头、普通trend、地区内容、导航或会员状态。空/未知结构放行。首页全部时间线仍不声称覆盖 |
| 百度网盘（核对后不重复添加） | `issuecdn.baidupcs.com/issue/netdisk/guanggao` 素材目录 | rewrite.snippet 第883行；现有域名扩展包已拒绝该主机 | 不额外MITM或挂载无效路径规则；网盘原ad/adx处理保留 |
| 网易云音乐 | 补齐 `interface1、2、4–9.music.163.com` 的 `api/ad`、`eapi/ad` | rewrite.snippet 第5188行；上游允许interface加一位数字。8个精确MITM主机及1条原生空JSON规则 | 原interface、interface3、ipv4保留；不通配任意主机，不拦播放、云贝、搜索。EAPI加密正文的兼容性仍待手机验证 |
| 知乎 | `commercial_api/answer或article/数字ID/bottom-v2` | rewrite.snippet 第6565行，原生空JSON | 仅商业广告接口，普通回答/文章正文不拦；不引入会员相关修改 |
| 美团 | `s3plus/flowplus.meituan.net/v*/目录/linglong/文件.mp4` | rewrite.snippet 第3180行。上游对该MP4使用reject-img，本项目改为原生reject-200空正文 | GIF/JPG继续用空图片；不给视频返回GIF。普通商品视频与goodsawardpic领券素材保留。空正文是否导致等待/重试须手机验收 |
| 已有fmz专项 | 根据已保存上游 `https?` 模式补齐 HTTP 匹配，包括淘宝、微博、小红书、美团及目录中相应模块 | 每个目录规则仍保留原来源摘录；HTTP正反例与原HTTPS路径一起验证 | 不扩大到所有URL，不修改仅有HTTPS依据的知乎等规则；没有证据认定此前缺HTTP就是开屏失败原因 |

总量从38条变为43条原生动作，11个响应handler和1个自检handler不增加；精确MITM主机从46个变为59个。数量只用于核对配置，不能当效果指标。MITM解密的是整个精确主机，广告处理仅匹配表内路径。

## 之前已采用并继续保留

原40个App维护模块全部保留，当前完整路径及范围见 [AD-MODULES](AD-MODULES.md) 和 [AD-ARCHITECTURE](AD-ARCHITECTURE.md)：

- 淘宝专用splash的展示控制及带明确 `tao_splash` 场景的请求。
- 微博实时/预载开屏原生空JSON、专用SDK/素材域名、话题/搜索明确广告项。
- 小红书启动配置splash、广告时间、广告素材域名、edith的v6赞助项。
- 美团外卖loadInfo已知广告数组、openscreen/startpicture和限定图片；京东已知start响应。
- 高德、拼多多、联通、移动、知乎等已有经审查的广告路径；其他来源的B站、贴吧等不替换为未经审核的fmz整包。

主配置仍使用原blackmatrix7扩展域名快照及真实RULE-SET引用。没有把整个fmz filter.list追加到前面，也没有复制其中终止规则、其他客户端策略或未审查整域封禁。原代理组、分流顺序、DNS和机场接入不变。

## 为什么没有把上游全部复制进来

| 上游部分 | 本次决定及具体原因 |
|---|---|
| 淘宝cloudvideo.video.query | 上游直接清通用视频资源、缓存及时间；缺少区分商品视频和开屏的样本，不整体启用。原splash中的广告视频URL仍会处理 |
| 淘宝poplayer JSON | 上游清整个活动素材并禁用，不能区分正常领券；不整体启用 |
| 小红书followfeed、搜索过滤、下载/画质/水印分支 | followfeed删推荐用户，不是已证实广告字段；搜索仅保留note可能删除普通搜索结果类型。下载等不属于本任务，完整正文日志和内容缓存也不引入 |
| 微博完整主脚本及详情净化 | 混合其他作者来源、皮肤/会员功能及广泛界面删除。本轮只提取fmz署名脚本中明确广告标记，保留导航和普通内容 |
| 瑞幸其他分支 | 上游还清商品推荐、兑换页响应，并匹配宽泛CDN图片。可能破坏正常点单/权益，保留原已审查adposNew，不扩大 |
| 京东其他functionId | 包含订单、物流、个人页服务和权益的精简，不能把界面精简当开屏修复；保留已知start处理 |
| 中国移动startInit、联通accountListData/getclientconfig | 混合启动和账号配置，整接口拒绝有业务风险；已有明确广告接口继续保留 |
| 美团goodsawardpic、waimai-alita ZIP、通用启动配置 | 无足够广告专用判据，不拦正常权益图或向ZIP返回JSON |
| 整份域名filter.list | 已阅读格式和相关App段落；包含业务/统计/关键词等多种规则，不能逐项证明适合当前白名单。现有域名扩展包保留，不将盲目叠加宣称为全面适配 |

以上是有选择的Stash适配，不是fmz全仓库的镜像或全功能承诺。没有加入会员解锁、自动签到、账号抓取或外部Cookie上传。

## 验证、更新与回退

本次检查包括配置引用/合并/优先级、生成一致性、原分流保留、新增URL正反例、HTTP与HTTPS、脚本正常/广告/未知/错误结构、只调用一次 `$done`、不记录业务数据，以及公开文件校验。模拟数据根据固定上游字段重建，**没有当前App的真实响应样本**；实际检查结果及发布提交见 [PROGRESS](../PROGRESS.md)。

手机验收仍需多次冷启动、后台返回、发生预加载后再次启动，并检查登录、搜索、消息、视频和正常领券。看到一次无广告或一次changed都不等于验收通过；记录为“本轮没有记录”也不能直接断定是HTTP/3。无需重新安装CA，优先用App自带清缓存，不默认卸载。

手机按24小时间隔尝试刷新本仓库规则集和JS；主配置每周手动更新一次，修复发布后立即更新。**上游更新不会未经审阅直接进入手机。** 现有本地 [维护工具](MAINTENANCE.md) 可每日检查上游变化，脚本变化仍需适配、验证并发布；本次新增不绕过此流程。

若更新后正常业务异常，先在Stash恢复更新前的本机配置备份并重连；JS是可变远程资源，单纯恢复旧配置不能保证所有旧JS字节也恢复。需要精确回退时按 [更新与回退](UPDATES.md) 使用固定提交资源，或先暂停HTTP/MITM再排查。“广告拦截→DIRECT”仅关闭域名规则，不是HTTP改写总开关。逐App开关已按用户要求取消，仍使用整合入口。
