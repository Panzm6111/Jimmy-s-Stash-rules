# 海外 AI 分流覆盖

2026-10-29起，两端的 `海外AI` 直接使用社区维护的完整分类：MetaCubeX 的 `category-ai-!cn` 与 Sukka 的 `Source/non_ip/ai.conf`，只做兼容格式转换和去重。当前两份来源分别213条、55条，合并为231条；原 [rules/openai.yaml](../rules/openai.yaml) 地址保持不变。来源、提交、许可和逐文件哈希见 [community-sources.json](../research/community-sources.json)。

海外AI 的 ai 池为新加坡 A、荷兰、英国 B（250 ms）；TikTok 的 AI最速池另含日本 A/B、美国 C/D（100 ms）；总代理默认最速节点，为 HKG A/B/C/I/J/M、日本 A/B、荷兰、新加坡 A、英国 B（50 ms）。Stash 前两项分别经「GPT 服务优选」「TikTok 服务优选」，Clash 直接选对应池。 AI 分流无需 MITM。Clash 组名带 Jimmy · 前缀。

当前手机验收按[独立服务检测与截图指南](ROUTING.md#iphone-service-health)操作。以下保留 11 月 8 日的 DNS 排查依据；当时的成员及容差已由当前设置替代。

## Stash AI DNS 与地区报错（2026-11-08）

`ROUTE-20261108.1 / AI-DNS-20261108.1` 使用 Stash iOS 3.6+ 的原生 DNS 功能。维护源为 [stash_ai_guard.py](../tools/stash_ai_guard.py)，由整合入口生成器调用；Clash生成时明确移除这层Stash专用配置，Clash入口维持原内容。

- ChatGPT的 `chatgpt.com`、`openai.com`、`oaistatic.com`、`oaiusercontent.com` 及子域名有本地路由保护，位于原系统/LAN例外之后、广告与国内总分类之前；即使远程AI规则集未加载，也不会因该缺失落入国内IP直连。其他AI服务仍使用完整上游分类。
- 上述四类域名及两份AI集合的**本地真实DNS解析**指定Cloudflare/Google的IP地址DoH，启用 `follow-rule`，对应两个解析器IP在规则首部固定走 `海外AI`。不与国内DNS并发争抢结果，不为AI增加国内回退。`海外AI` 仍须选代理出口；人为选择DIRECT、其他覆写或直连模式可以改变结果。
- 普通域名保留阿里/腾讯DoH；为两个DNS主机增加固定DIRECT路由。bootstrap和代理节点域名使用独立的、直接连接的国内IP地址DoH，避免“连接代理需要DNS、DNS又需要代理”的循环。国内解析商仍会看到这些bootstrap/节点及普通域名查询，不能把此方案称作全设备零DNS泄露。通过代理按域名建连时，最终解析仍可能由节点侧完成。
- 当时通过通用延迟判断健康，不能验证 ChatGPT 地区、登录或出口信誉；现在的服务入口检查也不验证账号或模型回复。节点名称也不是出口所在地的证明。

依据：[Stash内置DNS](https://stash.wiki/features/dns-server)、[Stash策略组](https://stash.wiki/proxy-protocols/proxy-groups)。本地生成、路由模型和回归通过不等同于iPhone原生DNS或ChatGPT实测通过。

手机更新后需这样验收：

1. 刷新**原主配置**，确认版本标记；规则集刷新不能取得DNS、内联规则等结构变化。检查个人覆写是否覆盖 `dns` 或核心规则，并保持规则模式。
2. 先将 `海外AI` 选到 `手动节点`，再在手动节点中选一条美国节点。关闭ChatGPT后重启Stash连接、再打开App；固定节点用于把自动切换与规则问题分开。不要清除私人订阅、证书或账号数据。
3. 在Stash连接记录中核对实际 `chatgpt.com` / `auth.openai.com` / `ws.chatgpt.com` 等请求命中 `海外AI`；如产生本地DoH连接，`1.1.1.1:443` / `8.8.8.8:443` 也应走该组。记录时间、规则、最终节点、错误文字即可，不导出聊天、令牌或完整日志。
4. 同一固定节点分别在Wi-Fi/蜂窝复测，再换另一条固定节点对照。固定某节点持续报地区限制、换节点消失，才支持该出口问题；切回 `ai` 后复现时记录当时最终节点。普通DNS检测网站出现国内解析商不能单独证明ChatGPT请求直连。

如果仍报地区限制，不能仅靠公共域名规则确认根因或保证修复；还需上述手机实际出口与请求命中证据。无手机日志时，不将间歇性报错直接归因于DNS泄露，也不把服务端地区判断当作规则已能控制的条件。

## 覆盖与边界

覆盖由上游分类决定，包括ChatGPT、Claude、Gemini、Copilot、Perplexity、Grok、Cursor等服务及上游收录的依赖。本项目不再手工选择25类服务或逐条维护域名；旧 [ai-sources.json](../research/ai-sources.json) 明确标为历史资料，退出当前生成链。

`!cn` 是上游分类名，不等于厂商国籍证明；其中可能包含中国厂商面向海外的服务。共享依赖 `host.livekit.cloud` 本轮按上游分类进入AI组，因此其他使用相同主机的业务也可能走AI出口。此处遵循完整维护集，不再本地挑选排除项。

Sukka源中的一条Gemini跳转 `URL-REGEX` 需要URL层语义，不能等价转换成两端通用域名规则；转换器显式记录该条未采用，保留其余完整域名规则。新增未知规则类型会使维护停止。没有增加Google全域MITM。

AI在普通Microsoft、GitHub及通用海外分类之前。`api.github.com` 按当前AI上游走海外AI，普通GitHub走总代理；`google.com` 由通用海外集走总代理，`microsoft.com` 仍走Microsoft。原系统通知、更新与特定登录直连例外保持更高优先级。

## 更新与检查

GitHub每日北京时间12:17计划检查6份必要转换，平台可能延迟；可直接使用的分类由客户端直订上游。验证通过且有实际变化才提交并推送，电脑旧维护任务已退役。客户端 `海外AI` 规则集每24小时尝试下载；新增provider或顺序变化仍需刷新主配置，见 [更新教程](UPDATES.md)。

```sh
python tools/community_rules.py
python tools/build_ads.py
```

以上验证来源哈希、完整集合合并与生成一致性；不访问真实AI账号。出现地区限制或登录循环时，核对实际选中节点和连接记录中的命中策略。反馈域名、策略与错误文字即可，不发送聊天、Cookie、令牌或完整请求URL。手机逐服务登录及解锁效果仍待验收。
