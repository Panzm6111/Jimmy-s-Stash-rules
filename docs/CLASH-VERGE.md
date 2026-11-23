# Clash Verge 使用方法

本机连续3–5天记录实际使用节点、AI组切换与分时段表现，见[实际使用观察](CLASH-MONITOR.md)。这是可选的本地监控工具，不是新的订阅入口。

## 完整自动订阅（推荐）

这是唯一的Clash发布入口：

```text
https://raw.githubusercontent.com/Panzm6111/Jimmy-s-Stash-rules/main/config/clash-verge-auto.yaml
```

主订阅包含 24 个 Stash 对应组、1 个隐藏下载回退组和 33 个规则集。海外AI 默认 AI组，Gemini 和 Claude 由 GeminiClaude 自动选线。TikTok 保留独立自动组。四组各八条，名单和默认分流见[当前分流](ROUTING.md)。

总代理和手动节点中可直接选择机场节点。手动节点的新配置默认从 HKG A 起步。刷新原主订阅后，仍有效的旧手选可能保留。可在代理页核对业务出口，并解除自动池旧图钉。

电脑精选池保留每 60 秒主动检查，机场每 60 秒检查通用 204。AI组探测 ChatGPT HTTP 200，GeminiClaude 和 TikTok 用通用 204 验证传输。AI组和 GeminiClaude 容差 200 ms，其余测速池 50 ms。

小红书、抖音和东方财富使用上游直连分类。抖音与 TikTok 同时明确收录的域名优先走 `Jimmy · TikTok`，目前为 `snssdk.com` 及其子域。抖音也可能通过该出口访问共享接口。抖音专用主机继续直连，TikTok 专属广告继续走广告拦截。[分流说明](ROUTING.md)

### 已使用“Jimmy 全自动”

保留原卡片与私人Merge，更新原主订阅即可。自动更新开启，间隔1440分钟；机场和规则集按86400秒尝试更新。仅更新规则集不能取得新的策略组结构。

### 首次接入

1. 导入上面的URL，并开启1440分钟自动更新。保留原可用配置作为设备备份。
2. 在这张卡片的私人Merge中保留原机场URL、私人节点启动后备、DNS及个人设置。私人Merge不放Jimmy的rules、proxy-groups、rule-providers。
3. 全局Merge中不再粘贴旧Jimmy路由；已有其他个人设置时只移除旧Jimmy结构，不清空无关设置。
4. 由用户选择何时应用，避免切换影响当前网络。查看“代理集 → 机场”的节点数及成功时间，再核对软件出口。

若机场必须经代理才能下载，可在可信本机用原机场配置生成私人启动后备：

```text
python -X utf8 tools/prepare_clash_bootstrap.py --airport <原机场本地YAML> --merge <私人Merge> --output <新的本地私人文件>
```

输出包含节点凭据，只留本机，不上传GitHub或第三方转换站。工具保留节点和个人设置，移除旧固定下载代理；公共配置使用隐藏fallback组自动选择可用出口，60秒通用健康检查，不固定依赖某一个日本节点。

下载失败时，首次无缓存需要先有本机后备。已有后备和缓存的保留行为已做Mihomo模拟，真实机场是否可用仍取决于网络、节点与账号。代理组的HTTPS测速不代表TikTok/AI一定可用。

## 已退役入口

旧独立Clash配置、全局Merge文件和扩展脚本已删除，不再提供第二套配置或兼容下载地址。历史讨论与验收证据保留在[PROGRESS](../PROGRESS.md)和[research](../research/)，其中旧路径与旧节点数按当时日期解读。

来源与更新边界见[社区来源](COMMUNITY-SOURCES.md)及[更新说明](UPDATES.md)。
