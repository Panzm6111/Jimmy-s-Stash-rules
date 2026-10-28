# Clash Verge 远程订阅使用方法

当前推荐使用完整远程配置，规则内容与策略组结构均可跟随项目更新；保留全部20个策略组、海外AI的日本+美国池及统一TikTok社交组。Clash只做域名去广告，Stash继续保留HTTP层。

## 首次迁移到远程配置

1. 在“订阅”中从URL导入：

   https://raw.githubusercontent.com/Panzm6111/Jimmy-s-Stash-rules/main/config/clash-verge.yaml

2. 右键这张新订阅卡片，打开“编辑信息”，开启自动更新，将更新间隔设为一天（界面单位为分钟时填1440）。GitHub Raw不提供自定义的profile-update-interval响应头，不能假定导入后默认已启用。
3. 右键这张卡片的“编辑扩展配置”，只在本机填写机场URL：

```yaml
proxy-providers:
  机场:
    url: "在本机粘贴你自己的Clash格式机场订阅URL"
```

4. 保存并激活这张订阅。停用此前给原机场订阅粘贴的Jimmy扩展脚本，避免两套主配置混用；原机场订阅保留作备份。私人URL不写入GitHub。
5. 使用“规则”模式，首次将“总代理”从REJECT改为所需地区或自动节点。“海外AI”可选美国、日本、日本+美国或具体节点；TikTok组统一管理TikTok/Instagram/X，默认美国。

日常无需再次复制代码：14个远程规则集按86400秒尝试更新，机场代理集按自身间隔更新。主配置的自动更新用于取得策略组、匹配顺序、DNS及provider声明等结构变化。客户端关闭、断网或下载失败会影响更新，不能保证每天固定时刻成功。

## 更新链路与能力边界

| 内容 | 更新入口 |
|---|---|
| AI、社交、Netflix/YouTube/Telegram、Apple/Microsoft、国内分流、全部域名广告和例外 | 14个HTTP rule-providers，各自24小时尝试刷新；每个有独立缓存路径 |
| 策略组结构、国家组合、规则集顺序、DNS、provider声明 | 上方远程主配置订阅的自动更新；不由机场节点刷新替代 |
| 机场节点 | 本机私人机场proxy-provider；URL更换时需本人修改本机覆写 |
| Stash HTTP改写/响应JS/自检 | Clash不执行；Stash用自己的主配置及script-providers更新 |

扩展脚本不能直接执行网络/文件IO，复制到本机的脚本不会因为刷新机场订阅而更新自身。为满足持续更新，推荐切换到上面的远程主配置。

## 原机场扩展脚本：兼容方式

[config/clash-verge.js](../config/clash-verge.js)仍保留，供必须在原机场订阅上转换的用户使用。**需先复制一次新版脚本**：新版不再展开规则正文，改为引用14个远程规则集，所以规则集内容之后可以自动刷新。但这个本地脚本里的策略组、provider清单和顺序仍是固定版本；将来结构变更时需重新复制脚本。它不能替代完整远程主配置的结构更新。

如节点名与本项目策略组冲突，转换会明确停止，不静默丢节点。其他全局/订阅扩展可能再次覆盖规则，应检查最终生效配置。

## 恢复与验证

切回原机场订阅可恢复原用法；将广告拦截切DIRECT可对照域名误伤。日常保留能用的私人配置备份。真实节点连通、TikTok地区可用性、AI解锁和实际广告效果仍需设备验证。

已在独立Mihomo v1.19.32进程验证14个HTTP规则集，并通过本地HTTP刷新让AI测试条目数由126变为127，主配置不重载、策略组保持；测试未使用私人机场，未修改系统代理。完整展开的43,421条有序规则与迁移前逐条相同。

依据：[Clash扩展规则](https://www.clashverge.dev/guide/extend.html)、[脚本能力](https://www.clashverge.dev/guide/script.html)、[订阅响应头](https://www.clashverge.dev/guide/url_schemes.html)、[Mihomo远程规则集](https://wiki.metacubex.one/config/rule-providers/)。进度与发布结果见[PROGRESS](../PROGRESS.md)。
