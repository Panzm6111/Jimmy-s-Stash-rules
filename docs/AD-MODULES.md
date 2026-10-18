# 广告专项模块目录与开关

当前共41个独立覆写：40个App专项（含前轮贴吧，不在本次图片内），另有1个扩展域名包。图中135款中39款有专项文件。全部是**候选实现、待设备实测**。本页逐款文件用于按需模式，默认不额外导入。

推荐的[一体化订阅入口](SUBSCRIBE.md)已经组装40款专项，不要再叠加本页同款handler。需要逐款开关时改用core分层或本地包基础主配置；原文件和稳定名称持续维护，实际发布检查见[PROGRESS](../PROGRESS.md)。

## 添加和关闭

1. 先按[README](../README.md)完成主配置、私人订阅和公共分流。
2. 在下表找App，复制“远程覆写地址”，在Stash覆写管理中添加并关联主配置。先只启用一款。
3. “需MITM=是”时，按[证书教程](ADBLOCKING.md)在自己设备生成并信任CA；只使用该行列出的精确主机。域名级解密能看到同主机其他请求，广告处理本身仍限于表内路径；不愿接受此范围则保持关闭。
4. 重启目标App，分别检查广告和登录/支付/消息/播放/普通领券；原有缓存不会被脚本删除。广告无效、空白等待或业务异常就关闭该覆写并重建连接。
5. “广告拦截→DIRECT”只放行域名规则。要停止HTTP重写或响应脚本，必须关闭对应覆写；域名白名单不能停止它们。关闭域名专项后若扩展包仍含同一主机，也会继续被扩展包阻断。

## 本次新增35款

HTTP重写使用Stash原生 `http.rewrite` 的 `正则 - reject`，取自锁定的原生Stash参考。来源中的QX `reject-dict/reject-img/reject-200` **没有被直接导入，也不声称与reject等价**；返回形态、等待、错误提示均需逐款验收。不自动伪造成功业务响应。响应脚本则仅在已知结构上作窄化修改，异常放行。

| App | 仅处理的范围 | 需MITM / 精确主机 | 远程覆写地址 |
|---|---|---|---|
| 百度网盘 | 网盘独立 ad/adx 广告接口；不拦福利、会员、下载、分享 | 是：`pan.baidu.com` | [baidu-netdisk](https://raw.githubusercontent.com/Panzm6111/Jimmy-s-Stash-rules/main/modules/ads/baidu-netdisk.stoverride) |
| 大麦 | 专用 home.welcome 开屏；不屏蔽 HTTPDNS、票务或下单 | 是：`acs.m.taobao.com` | [damai](https://raw.githubusercontent.com/Panzm6111/Jimmy-s-Stash-rules/main/modules/ads/damai.stoverride) |
| 大众点评 | 仅 loadsplashconfig 开屏配置；不删普通首页、优惠或评价 | 是：`mapi.dianping.com` | [dianping](https://raw.githubusercontent.com/Panzm6111/Jimmy-s-Stash-rules/main/modules/ads/dianping.stoverride) |
| 高德地图 | 两个独立启动广告接口及 optimus 广告域名；保留路线、定位和普通地图图片 | 是：`m5.amap.com`、`amap-aos-info-nogw.amap.com` | [amap](https://raw.githubusercontent.com/Panzm6111/Jimmy-s-Stash-rules/main/modules/ads/amap.stoverride) |
| 航旅纵横 | 仅 fs/advert/polite 广告素材；未改原生 gateway 或航班业务 | 是：`oss.umetrip.com` | [umetrip](https://raw.githubusercontent.com/Panzm6111/Jimmy-s-Stash-rules/main/modules/ads/umetrip.stoverride) |
| 华住会 | 仅 getAppStartPage 开屏；保留酒店优惠、新客权益、更新和预订 | 是：`appapi.huazhu.com` | [huazhu](https://raw.githubusercontent.com/Panzm6111/Jimmy-s-Stash-rules/main/modules/ads/huazhu.stoverride) |
| 肯德基 | 仅 advertisement 路径素材；保留 apphome 配置、菜单和优惠券 | 是：`res.kfc.com.cn` | [kfc](https://raw.githubusercontent.com/Panzm6111/Jimmy-s-Stash-rules/main/modules/ads/kfc.stoverride) |
| 麦当劳 | 专用 portal/home/splash；保留点餐、支付、领券 | 是：`api.mcd.cn` | [mcdonalds](https://raw.githubusercontent.com/Panzm6111/Jimmy-s-Stash-rules/main/modules/ads/mcdonalds.stoverride) |
| 脉脉 | 仅 adshow；保留礼物、消息和普通推荐 | 是：`open.taou.com`、`h3.open.taou.com` | [maimai](https://raw.githubusercontent.com/Panzm6111/Jimmy-s-Stash-rules/main/modules/ads/maimai.stoverride) |
| 猎聘 | 明确命名的 live.get-ad-cards；不拦职位推荐或投递 | 是：`api-ac.liepin.com` | [liepin](https://raw.githubusercontent.com/Panzm6111/Jimmy-s-Stash-rules/main/modules/ads/liepin.stoverride) |
| 米家 | 仅 openingBanner 两个端点；保留设备控制、普通推荐和自动化 | 是：`home.mi.com` | [mijia](https://raw.githubusercontent.com/Panzm6111/Jimmy-s-Stash-rules/main/modules/ads/mijia.stoverride) |
| 拼多多 | 仅 cappuccino/splash；保留首页、买菜、红包和领券 | 是：`api.pinduoduo.com`、`api.yangkeduo.com` | [pinduoduo](https://raw.githubusercontent.com/Panzm6111/Jimmy-s-Stash-rules/main/modules/ads/pinduoduo.stoverride) |
| 淘票票 | 仅 queryloadingbanner 启动广告；保留普通活动、选座和购票 | 是：`acs.m.taobao.com` | [taopiaopiao](https://raw.githubusercontent.com/Panzm6111/Jimmy-s-Stash-rules/main/modules/ads/taopiaopiao.stoverride) |
| 网易邮箱大师 | mmad 素材和 searchMultiAds/showAds；保留邮件、搜索和同步 | 是：`appconf.mail.163.com`、`client.mail.163.com` | [netease-mail](https://raw.githubusercontent.com/Panzm6111/Jimmy-s-Stash-rules/main/modules/ads/netease-mail.stoverride) |
| 网易云音乐 | 仅 api/ad 或 eapi/ad 广告子路径；保留歌曲、评论、云贝、会员真实状态 | 是：`interface.music.163.com`、`interface3.music.163.com`、`ipv4.music.163.com` | [netease-music](https://raw.githubusercontent.com/Panzm6111/Jimmy-s-Stash-rules/main/modules/ads/netease-music.stoverride) |
| 下厨房 | 仅 vN/ad/ 专用广告路径；保留菜谱、购物和内容图片 | 是：`api.xiachufang.com` | [xiachufang](https://raw.githubusercontent.com/Panzm6111/Jimmy-s-Stash-rules/main/modules/ads/xiachufang.stoverride) |
| 闲鱼 | 仅 idlecommerce.splash.ads；保留聊天、交易、闲鱼币和搜索 | 是：`acs.m.goofish.com` | [xianyu](https://raw.githubusercontent.com/Panzm6111/Jimmy-s-Stash-rules/main/modules/ads/xianyu.stoverride) |
| 小宇宙 | 仅 flash 开屏；保留节目推荐、AI总结、搜索和播客音频 | 是：`api.xiaoyuzhoufm.com` | [xiaoyuzhou](https://raw.githubusercontent.com/Panzm6111/Jimmy-s-Stash-rules/main/modules/ads/xiaoyuzhou.stoverride) |
| WPS Office | 广告统计及 feeds_ad 图片；不改会员、文档、云同步 | 是：`ios.wps.cn`、`mobile-pic.cache.iciba.com` | [wps](https://raw.githubusercontent.com/Panzm6111/Jimmy-s-Stash-rules/main/modules/ads/wps.stoverride) |
| 58同城 | 仅 home/advertising 和 appadv；保留职位、联系与发布 | 是：`app.58.com` | [58tongcheng](https://raw.githubusercontent.com/Panzm6111/Jimmy-s-Stash-rules/main/modules/ads/58tongcheng.stoverride) |
| 中国移动 | 仅 explorePage/getAdverList；保留 startInit、账号、缴费和权益 | 是：`client.app.coc.10086.cn` | [cmcc](https://raw.githubusercontent.com/Panzm6111/Jimmy-s-Stash-rules/main/modules/ads/cmcc.stoverride) |
| 中国联通 | 专用启动/广告接口；保留 accountListData、客户端配置和缴费 | 是：`m.client.10010.com` | [unicom](https://raw.githubusercontent.com/Panzm6111/Jimmy-s-Stash-rules/main/modules/ads/unicom.stoverride) |
| 东方财富 | 仅 emdcadvertise 广告主机；不解密行情、交易或登录 | 否；仅独立广告域名 | [eastmoney](https://raw.githubusercontent.com/Panzm6111/Jimmy-s-Stash-rules/main/modules/ads/eastmoney.stoverride) |
| 携程旅行 | 仅 ma-adx 广告主机；不解密预订或支付，不拦易误杀图片的 tripAds | 否；仅独立广告域名 | [ctrip](https://raw.githubusercontent.com/Panzm6111/Jimmy-s-Stash-rules/main/modules/ads/ctrip.stoverride) |
| 铁路12306 | 仅 ad.12306.cn 广告主机；不解密车票、身份信息或支付 | 否；仅独立广告域名 | [railway12306](https://raw.githubusercontent.com/Panzm6111/Jimmy-s-Stash-rules/main/modules/ads/railway12306.stoverride) |
| 云闪付 | 仅 ads.95516.com 和 ads.cup.com.cn；不屏蔽推送/安全SDK，不解密支付 | 否；仅独立广告域名 | [unionpay](https://raw.githubusercontent.com/Panzm6111/Jimmy-s-Stash-rules/main/modules/ads/unionpay.stoverride) |
| UC浏览器 | 仅 ads.uc.cn、adslot.uc.cn；保留反诈、安全、语音和网页正文 | 否；仅独立广告域名 | [uc](https://raw.githubusercontent.com/Panzm6111/Jimmy-s-Stash-rules/main/modules/ads/uc.stoverride) |
| 京东金融 | 仅 bdsp-x/dsp-x 独立广告主机；不解密金融或支付 | 否；仅独立广告域名 | [jingdong-finance](https://raw.githubusercontent.com/Panzm6111/Jimmy-s-Stash-rules/main/modules/ads/jingdong-finance.stoverride) |
| 知乎 | 仅独立开屏、顶部横幅和 ad-style-service；保留回答、搜索和普通推荐 | 是：`api.zhihu.com` | [zhihu](https://raw.githubusercontent.com/Panzm6111/Jimmy-s-Stash-rules/main/modules/ads/zhihu.stoverride) |
| 阿里云盘 | 仅 onboard_list 的4种推广banner；保留备份、更新、签到/权益入口 | 是：`member.alipan.com` | [alipan](https://raw.githubusercontent.com/Panzm6111/Jimmy-s-Stash-rules/main/modules/ads/alipan.stoverride) |
| 菜鸟 | 仅 ads.show 返回中带明确 adItemDetail 的广告项；保留积分/券/消息/包裹 | 是：`cn-acs.m.cainiao.com` | [cainiao](https://raw.githubusercontent.com/Panzm6111/Jimmy-s-Stash-rules/main/modules/ads/cainiao.stoverride) |
| 京东 | 仅 functionId=start 中展示次数/时长字段；保留订单/商品/京豆/优惠 | 是：`api.m.jd.com` | [jingdong](https://raw.githubusercontent.com/Panzm6111/Jimmy-s-Stash-rules/main/modules/ads/jingdong.stoverride) |
| 美团 | 仅外卖 loadInfo.startpicture.ad/mk 广告数组；保留其他启动数据与券 | 是：`wmapi.meituan.com` | [meituan](https://raw.githubusercontent.com/Panzm6111/Jimmy-s-Stash-rules/main/modules/ads/meituan.stoverride) |
| 瑞幸咖啡 | 仅 sys/app/adposNew 独立广告响应；保留点单、商品与优惠券 | 是：`capi.lkcoffee.com` | [luckin](https://raw.githubusercontent.com/Panzm6111/Jimmy-s-Stash-rules/main/modules/ads/luckin.stoverride) |
| 微信 | 仅公众号 getappmsgad 的广告数组/数量；不改朋友圈、视频号、好友聊天或安全链接 | 是：`mp.weixin.qq.com` | [wechat-articles](https://raw.githubusercontent.com/Panzm6111/Jimmy-s-Stash-rules/main/modules/ads/wechat-articles.stoverride) |

既有5款：[B站](../modules/ads/bilibili.stoverride)、[贴吧](../modules/ads/tieba.stoverride)、[淘宝](../modules/ads/taobao.stoverride)、[小红书](../modules/ads/xiaohongshu.stoverride)、[微博](../modules/ads/weibo.stoverride)。淘宝/小红书/微博的细节见[原专项说明](APP-SPLASH.md)。[扩展域名包](../modules/ads/expanded.stoverride)不需证书，替换基础广告provider而不叠加整包。

## 与原通用包是否重叠

以下按**目标主机**实际匹配现有基本域名/关键词规则；不推断该App全部流量，IP规则没有在此推演。通用包已命中时，专项可能只是提供较小范围/独立入口，并不额外增加一次拦截。基础和扩展二选一；同一请求按首条规则处理。

| App | 目标主机 | 基础21条 | 扩展38,066条 |
|---|---|---|---|
| 百度网盘 | `pan.baidu.com` | 未命中 | 未命中 |
| 大麦 | `acs.m.taobao.com` | 未命中 | 未命中 |
| 大众点评 | `mapi.dianping.com` | 未命中 | 未命中 |
| 高德地图 | `amap-aos-info-nogw.amap.com` | 未命中 | 未命中 |
| 高德地图 | `m5.amap.com` | 未命中 | 未命中 |
| 高德地图 | `optimus-ads.amap.com` | 未命中 | 有命中：`DOMAIN-SUFFIX,optimus-ads.amap.com` |
| 高德地图 | `optimus-ads.amap.com.w.alikunlun.com` | 未命中 | 有命中：`DOMAIN-SUFFIX,optimus-ads.amap.com.w.alikunlun.com` |
| 航旅纵横 | `oss.umetrip.com` | 未命中 | 未命中 |
| 华住会 | `appapi.huazhu.com` | 未命中 | 未命中 |
| 肯德基 | `res.kfc.com.cn` | 未命中 | 未命中 |
| 麦当劳 | `api.mcd.cn` | 未命中 | 未命中 |
| 脉脉 | `h3.open.taou.com` | 未命中 | 未命中 |
| 脉脉 | `open.taou.com` | 未命中 | 未命中 |
| 猎聘 | `api-ac.liepin.com` | 未命中 | 未命中 |
| 米家 | `home.mi.com` | 未命中 | 未命中 |
| 拼多多 | `api.pinduoduo.com` | 未命中 | 未命中 |
| 拼多多 | `api.yangkeduo.com` | 未命中 | 未命中 |
| 淘票票 | `acs.m.taobao.com` | 未命中 | 未命中 |
| 网易邮箱大师 | `appconf.mail.163.com` | 未命中 | 未命中 |
| 网易邮箱大师 | `client.mail.163.com` | 未命中 | 未命中 |
| 网易云音乐 | `interface.music.163.com` | 未命中 | 未命中 |
| 网易云音乐 | `interface3.music.163.com` | 未命中 | 未命中 |
| 网易云音乐 | `ipv4.music.163.com` | 未命中 | 未命中 |
| 下厨房 | `api.xiachufang.com` | 未命中 | 未命中 |
| 闲鱼 | `acs.m.goofish.com` | 未命中 | 未命中 |
| 小宇宙 | `api.xiaoyuzhoufm.com` | 未命中 | 未命中 |
| WPS Office | `ios.wps.cn` | 未命中 | 未命中 |
| WPS Office | `mobile-pic.cache.iciba.com` | 未命中 | 未命中 |
| 58同城 | `app.58.com` | 未命中 | 未命中 |
| 中国移动 | `client.app.coc.10086.cn` | 未命中 | 未命中 |
| 中国联通 | `m.client.10010.com` | 未命中 | 未命中 |
| 东方财富 | `emdcadvertise.eastmoney.com` | 未命中 | 有命中：`DOMAIN-SUFFIX,emdcadvertise.eastmoney.com` |
| 携程旅行 | `ma-adx.ctrip.com` | 未命中 | 未命中 |
| 铁路12306 | `ad.12306.cn` | 未命中 | 有命中：`DOMAIN-SUFFIX,ad.12306.cn` |
| 云闪付 | `ads.95516.com` | 未命中 | 有命中：`DOMAIN,ads.95516.com` |
| 云闪付 | `ads.cup.com.cn` | 未命中 | 有命中：`DOMAIN,ads.cup.com.cn` |
| UC浏览器 | `ads.uc.cn` | 未命中 | 有命中：`DOMAIN-SUFFIX,ads.uc.cn` |
| UC浏览器 | `adslot.uc.cn` | 未命中 | 有命中：`DOMAIN-SUFFIX,adslot.uc.cn` |
| 京东金融 | `bdsp-x.jd.com` | 未命中 | 未命中 |
| 京东金融 | `dsp-x.jd.com` | 未命中 | 未命中 |
| 知乎 | `api.zhihu.com` | 未命中 | 未命中 |
| 阿里云盘 | `member.alipan.com` | 未命中 | 未命中 |
| 菜鸟 | `cn-acs.m.cainiao.com` | 未命中 | 未命中 |
| 京东 | `api.m.jd.com` | 未命中 | 未命中 |
| 美团 | `wmapi.meituan.com` | 未命中 | 未命中 |
| 瑞幸咖啡 | `capi.lkcoffee.com` | 未命中 | 未命中 |
| 微信 | `mp.weixin.qq.com` | 未命中 | 未命中 |

这张表也解释了为什么通用包不能代替所有App专项：共享业务网关若整域拦截会伤到正常功能，而路径处理只选广告端点。反过来，已被扩展包阻断的独立广告域名不必再叠加同一作用模块。

## 合并、优先级与验收

如果仅为检查而把全部模块合并，预期有 **12条响应handler、32条HTTP拒绝重写、41个去重后的精确MITM主机**。这不是建议全部启用；不同模块共享主机可能在原生预览重复出现，不同路径互不重叠。当前官方数组合并语义仍待复核，必须确认没有只保留最后一款。

离线验证覆盖每个单模块、全部模块的正序/反序、每个有序模块对和所有端点的正反例；检查没有跨App业务URL误匹配。它不能证明HTTP/3、证书固定、私有协议、原生合并或当前App版本可用。

模块内部规则已去重；跨模块共享MITM域名是独立启停带来的重复声明，不重复运行同一路径handler。不要安装另一整包重写与这些端点竞争；未知第三方模块优先级不在项目验证范围。

## 更新和维护

新增模块从人工审核的 `research/ad-catalog.json` 生成；修改原条目后运行 `python tools/generate_ad_modules.py --write`，再运行 `python tools/validate.py`。不要直接编辑生成文件造成下次回写丢失。清单文字由 `python tools/render_app_research.py --write` 同步。旧5款保持原路径维护。

新增/调整端点前重读源代码、许可、正常权益影响和设备反馈；固定SHA更新，保留脚本失败放行和无外联约束。公共更新不改设备私人订阅；覆写手动刷新、provider间隔更新等区别见[更新教程](UPDATES.md)。
