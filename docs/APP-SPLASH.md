# 淘宝、小红书、微博与天猫：当前专项范围

当前修订 **AD-20261020.1**，原路径更新。优先三款和后续美团/京东的逐环节、固定来源版本、正常业务保护及未实施原因完整见[详细技术规格第3部分](AD-ARCHITECTURE.md#3-优先五款的广告链逐项核查)和[证据JSON](../research/ad-repair-evidence.json)。这是代码实现清单，**没有手机效果通过记录**。

| App | 本轮实际处理 | 仍未证明覆盖 |
|---|---|---|
| 淘宝 | 原专用splash响应中的展示字段/素材URL；新增带明确tao_splash场景的noah.query空JSON | 通用cloudvideo视频无法单凭接口名区分商品视频，poplayer可能是正常活动/领券，未整域/整接口封禁 |
| 微博 | 实时/预载开屏原生空JSON；4个专用SDK/素材主机；话题/搜索的明确广告标记 | 首页friends_timeline全部信息流、国际版、所有备用链路 |
| 小红书 | 原开屏时间；启动配置splash；4个广告素材主机；v6首页非空ads_info赞助项 | 其他版本/私有结构；不改下载、水印、画质、用户信息，不删除普通带货/直播笔记 |
| 美团 | 原外卖loadInfo已知字段；v7 openscreen/startpicture；限定开屏GIF/JPG素材 | 美团主App所有启动链；不把MP4返回成空GIF，不拦正常领券/商品素材 |
| 京东 | 唯一查询functionId=start；二维/平铺已知广告展示控制与有效日期 | 只在POST正文或加密结构里的新接口/函数；保留原倒计时、订单和券 |
| 独立天猫 | 仍只有通用域名规则，未虚构专项 | 淘宝内共用接口不能代表独立天猫App已经适配 |

用户已有可信自建CA可沿用，保持HTTP/MITM开启。主入口不再嵌入专项：从[模块目录](AD-MODULES.md)启用需要的原App覆写，一款一份；不要叠加旧整合广告增强。关闭对应覆写并重建连接，撤销该专项；通用域名规则仍可能影响它，广告组DIRECT不是HTTP总开关。

原三款稳定地址：

```text
https://raw.githubusercontent.com/Panzm6111/Jimmy-s-Stash-rules/main/modules/ads/taobao.stoverride
https://raw.githubusercontent.com/Panzm6111/Jimmy-s-Stash-rules/main/modules/ads/xiaohongshu.stoverride
https://raw.githubusercontent.com/Panzm6111/Jimmy-s-Stash-rules/main/modules/ads/weibo.stoverride
```

本轮必须刷新原主配置、所选App覆写和JS。新增精确主机分别位于覆写中；MITM解密的是列出整个主机，即使脚本只匹配广告路径也须理解这个范围。不解密全域或银行支付，不安装他人CA、不关闭TLS验证。

预加载素材可保存在App私有目录，没有新请求也可能出现广告。先做多次冷启动、后台返回和使用后再启动的对照，优先App自带清缓存，网络规则不会删除本地文件。临时无敏感诊断、失败状态和最小反馈步骤见[去广告教程](ADBLOCKING.md)。自动签到继续暂停。
