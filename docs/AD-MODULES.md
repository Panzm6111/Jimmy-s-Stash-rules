# 广告专项实现范围与来源目录

当前保留41份维护源文件：40个App专项（含贴吧，不在本次图片内），另有1个扩展域名包。图中135款中39款有专项实现。已采用的专项全部纳入整合入口，**实际效果待设备实测**。此页用于查实现范围和来源，无需逐款导入。

当前需求已统一为[整合入口](SUBSCRIBE.md)，不再要求逐App开关。原config/stash.yaml包含全部40款已有专项、11份响应JS的URL声明和扩展域名包引用；刷新主配置即可取得当前处理。已有额外App/广告增强/expanded覆写应停用以免重复，私人订阅覆写继续保留。源文件路径不变，供生成器维护及旧安装兼容使用。

## 当前接入约定

日常只刷新整合主配置，不把下表链接当作安装清单。HTTP去广告沿用设备上已信任的自建CA；只有首次配置时才按[证书教程](ADBLOCKING.md)安装。域名级解密可涉及同主机其他请求，实际改写仍限于表内路径；不解密支付或银行主域。

“广告拦截→DIRECT”只放行域名规则，HTTP/MITM需单独关闭才能暂停HTTPS改写。广告无效或业务异常时，按[恢复与诊断教程](ADBLOCKING.md)处理；当前不提供逐App启停操作。

旧main.yaml＋core及单独覆写文件保留用于已有安装兼容，不属于当前日常安装要求，不与整合主配置叠加。

## 目录生成的35项实现

2026-10-20修订：固定响应使用`http.url-rewrite`原生动作，区分reject、reject-200、reject-dict、reject-img；联通图片语义恢复。共享空响应JS已移除。11个响应handler只处理已知广告结构，默认无日志；在Safari打开整合入口内置的`https://example.com/jimmy-stash-check`并开始15分钟排查后，仅在本机保存版本、时间与固定状态计数。自检请求handler不处理App广告；当前用户无需复制配置或另装探针。详见[排查教程](ADBLOCKING.md)。

| App | 仅处理的范围 | 需MITM / 精确主机 | 维护源链接 |
|---|---|---|---|
| 百度网盘 | 网盘独立 ad/adx 广告接口；不拦福利、会员、下载、分享 | 是：`pan.baidu.com` | [baidu-netdisk](https://raw.githubusercontent.com/Panzm6111/Jimmy-s-Stash-rules/main/modules/ads/baidu-netdisk.stoverride) |
| 大麦 | 专用 home.welcome 开屏；不屏蔽 HTTPDNS、票务或下单 | 是：`acs.m.taobao.com` | [damai](https://raw.githubusercontent.com/Panzm6111/Jimmy-s-Stash-rules/main/modules/ads/damai.stoverride) |
| 大众点评 | 仅 loadsplashconfig 开屏配置；不删普通首页、优惠或评价 | 是：`mapi.dianping.com` | [dianping](https://raw.githubusercontent.com/Panzm6111/Jimmy-s-Stash-rules/main/modules/ads/dianping.stoverride) |
| 高德地图 | 两个独立启动广告接口及 optimus 广告域名；保留路线、定位和普通地图图片 | 是：`m5.amap.com`、`amap-aos-info-nogw.amap.com` | [amap](https://raw.githubusercontent.com/Panzm6111/Jimmy-s-Stash-rules/main/modules/ads/amap.stoverride) |
| 航旅纵横 | 仅 fs/advert/polite 广告素材候选；不包含开屏展示控制或航班业务 | 是：`oss.umetrip.com` | [umetrip](https://raw.githubusercontent.com/Panzm6111/Jimmy-s-Stash-rules/main/modules/ads/umetrip.stoverride) |
| 华住会 | 仅 getAppStartPage 开屏；保留酒店优惠、新客权益、更新和预订 | 是：`appapi.huazhu.com` | [huazhu](https://raw.githubusercontent.com/Panzm6111/Jimmy-s-Stash-rules/main/modules/ads/huazhu.stoverride) |
| 肯德基 | 仅 advertisement 路径广告素材候选；不包含完整开屏控制、菜单或优惠券 | 是：`res.kfc.com.cn` | [kfc](https://raw.githubusercontent.com/Panzm6111/Jimmy-s-Stash-rules/main/modules/ads/kfc.stoverride) |
| 麦当劳 | 专用 portal/home/splash；保留点餐、支付、领券 | 是：`api.mcd.cn` | [mcdonalds](https://raw.githubusercontent.com/Panzm6111/Jimmy-s-Stash-rules/main/modules/ads/mcdonalds.stoverride) |
| 脉脉 | 仅 adshow；保留礼物、消息和普通推荐 | 是：`open.taou.com`、`h3.open.taou.com` | [maimai](https://raw.githubusercontent.com/Panzm6111/Jimmy-s-Stash-rules/main/modules/ads/maimai.stoverride) |
| 猎聘 | 明确命名的 live.get-ad-cards；不拦职位推荐或投递 | 是：`api-ac.liepin.com` | [liepin](https://raw.githubusercontent.com/Panzm6111/Jimmy-s-Stash-rules/main/modules/ads/liepin.stoverride) |
| 米家 | 仅 openingBanner 两个端点；保留设备控制、普通推荐和自动化 | 是：`home.mi.com` | [mijia](https://raw.githubusercontent.com/Panzm6111/Jimmy-s-Stash-rules/main/modules/ads/mijia.stoverride) |
| 拼多多 | 仅 cappuccino/splash；保留首页、买菜、红包和领券 | 是：`api.pinduoduo.com`、`api.yangkeduo.com` | [pinduoduo](https://raw.githubusercontent.com/Panzm6111/Jimmy-s-Stash-rules/main/modules/ads/pinduoduo.stoverride) |
| 淘票票 | 仅 queryloadingbanner 启动广告；保留普通活动、选座和购票 | 是：`acs.m.taobao.com` | [taopiaopiao](https://raw.githubusercontent.com/Panzm6111/Jimmy-s-Stash-rules/main/modules/ads/taopiaopiao.stoverride) |
| 网易邮箱大师 | mmad 素材和 searchMultiAds/showAds；保留邮件、搜索和同步 | 是：`appconf.mail.163.com`、`client.mail.163.com` | [netease-mail](https://raw.githubusercontent.com/Panzm6111/Jimmy-s-Stash-rules/main/modules/ads/netease-mail.stoverride) |
| 网易云音乐 | 仅3个精确主机的 api/ad 或 eapi/ad 路径候选；不解密 EAPI 正文 | 是：`interface.music.163.com`、`interface3.music.163.com`、`ipv4.music.163.com` | [netease-music](https://raw.githubusercontent.com/Panzm6111/Jimmy-s-Stash-rules/main/modules/ads/netease-music.stoverride) |
| 下厨房 | 仅 vN/ad/ 专用广告路径；保留菜谱、购物和内容图片 | 是：`api.xiachufang.com` | [xiachufang](https://raw.githubusercontent.com/Panzm6111/Jimmy-s-Stash-rules/main/modules/ads/xiachufang.stoverride) |
| 闲鱼 | 仅 idlecommerce.splash.ads；保留聊天、交易、闲鱼币和搜索 | 是：`acs.m.goofish.com` | [xianyu](https://raw.githubusercontent.com/Panzm6111/Jimmy-s-Stash-rules/main/modules/ads/xianyu.stoverride) |
| 小宇宙 | 仅 flash 开屏；保留节目推荐、AI总结、搜索和播客音频 | 是：`api.xiaoyuzhoufm.com` | [xiaoyuzhou](https://raw.githubusercontent.com/Panzm6111/Jimmy-s-Stash-rules/main/modules/ads/xiaoyuzhou.stoverride) |
| WPS Office | 仅广告统计请求与 feeds_ad 素材；没有完整开屏或文档内广告去除证据 | 是：`ios.wps.cn`、`mobile-pic.cache.iciba.com` | [wps](https://raw.githubusercontent.com/Panzm6111/Jimmy-s-Stash-rules/main/modules/ads/wps.stoverride) |
| 58同城 | 仅 home/advertising 和 appadv；保留职位、联系与发布 | 是：`app.58.com` | [58tongcheng](https://raw.githubusercontent.com/Panzm6111/Jimmy-s-Stash-rules/main/modules/ads/58tongcheng.stoverride) |
| 中国移动 | 仅 explorePage/getAdverList 候选广告接口；没有完整启动广告去除证据 | 是：`client.app.coc.10086.cn` | [cmcc](https://raw.githubusercontent.com/Panzm6111/Jimmy-s-Stash-rules/main/modules/ads/cmcc.stoverride) |
| 中国联通 | 专用启动/广告接口；保留 accountListData、客户端配置和缴费 | 是：`m.client.10010.com` | [unicom](https://raw.githubusercontent.com/Panzm6111/Jimmy-s-Stash-rules/main/modules/ads/unicom.stoverride) |
| 东方财富 | 仅 emdcadvertise 独立广告主机；不代表行情页面全部推广 | 否；仅独立广告域名 | [eastmoney](https://raw.githubusercontent.com/Panzm6111/Jimmy-s-Stash-rules/main/modules/ads/eastmoney.stoverride) |
| 携程旅行 | 仅 ma-adx 主机的广告/统计请求；没有完整开屏去除证据 | 否；仅独立广告域名 | [ctrip](https://raw.githubusercontent.com/Panzm6111/Jimmy-s-Stash-rules/main/modules/ads/ctrip.stoverride) |
| 铁路12306 | 仅 ad.12306.cn 独立广告主机；不保证取消客户端缓存开屏 | 否；仅独立广告域名 | [railway12306](https://raw.githubusercontent.com/Panzm6111/Jimmy-s-Stash-rules/main/modules/ads/railway12306.stoverride) |
| 云闪付 | 仅 ads.95516.com 和 ads.cup.com.cn 广告请求；不代表云闪付全界面去广告 | 否；仅独立广告域名 | [unionpay](https://raw.githubusercontent.com/Panzm6111/Jimmy-s-Stash-rules/main/modules/ads/unionpay.stoverride) |
| UC浏览器 | 仅 ads.uc.cn、adslot.uc.cn 独立广告主机；不包含网页同域广告 | 否；仅独立广告域名 | [uc](https://raw.githubusercontent.com/Panzm6111/Jimmy-s-Stash-rules/main/modules/ads/uc.stoverride) |
| 京东金融 | 仅 bdsp-x/dsp-x 广告主机候选；不包含金融网关或完整开屏 | 否；仅独立广告域名 | [jingdong-finance](https://raw.githubusercontent.com/Panzm6111/Jimmy-s-Stash-rules/main/modules/ads/jingdong-finance.stoverride) |
| 知乎 | 仅开屏、顶部横幅与 ad-style-service 候选；不包含全部回答和信息流广告 | 是：`api.zhihu.com` | [zhihu](https://raw.githubusercontent.com/Panzm6111/Jimmy-s-Stash-rules/main/modules/ads/zhihu.stoverride) |
| 阿里云盘 | 仅 onboard_list 的4种推广banner；不宣称阿里云盘开屏或全界面去广告 | 是：`member.alipan.com` | [alipan](https://raw.githubusercontent.com/Panzm6111/Jimmy-s-Stash-rules/main/modules/ads/alipan.stoverride) |
| 菜鸟 | 仅 ads.show 的明确 adItemDetail 广告项；不包含 mshow 或完整首页净化 | 是：`cn-acs.m.cainiao.com` | [cainiao](https://raw.githubusercontent.com/Panzm6111/Jimmy-s-Stash-rules/main/modules/ads/cainiao.stoverride) |
| 京东 | 仅 URL 中 functionId=start 的历史开屏展示字段；不包含全部京东广告 | 是：`api.m.jd.com` | [jingdong](https://raw.githubusercontent.com/Panzm6111/Jimmy-s-Stash-rules/main/modules/ads/jingdong.stoverride) |
| 美团 | 外卖loadInfo已知startpicture广告数组；v7 openscreen/startpicture专用接口与限定开屏图片素材；不是主App完整覆盖 | 是：`wmapi.meituan.com`、`img.meituan.net`、`s3plus.meituan.net`、`flowplus.meituan.net` | [meituan](https://raw.githubusercontent.com/Panzm6111/Jimmy-s-Stash-rules/main/modules/ads/meituan.stoverride) |
| 瑞幸咖啡 | 仅 sys/app/adposNew 独立广告响应；保留点单、商品与优惠券 | 是：`capi.lkcoffee.com` | [luckin](https://raw.githubusercontent.com/Panzm6111/Jimmy-s-Stash-rules/main/modules/ads/luckin.stoverride) |
| 微信 | 仅历史公众号 getappmsgad 的广告字段；不包含朋友圈、视频号或聊天 | 是：`mp.weixin.qq.com` | [wechat-articles](https://raw.githubusercontent.com/Panzm6111/Jimmy-s-Stash-rules/main/modules/ads/wechat-articles.stoverride) |

另有5项既有实现：[B站](../modules/ads/bilibili.stoverride)、[贴吧](../modules/ads/tieba.stoverride)、[淘宝](../modules/ads/taobao.stoverride)、[小红书](../modules/ads/xiaohongshu.stoverride)、[微博](../modules/ads/weibo.stoverride)，同样已纳入整合入口。淘宝/小红书/微博的细节见[专项范围说明](APP-SPLASH.md)。[扩展域名维护源](../modules/ads/expanded.stoverride)不需证书，整合主配置已默认引用扩展快照，无需额外开启expanded；基础包仅保留给旧分层安装，二者不同时叠加。完整关系见[去广告技术总览](AD-ARCHITECTURE.md)。

## 与原通用包是否重叠

以下按**目标主机**实际匹配现有基本域名/关键词规则；不推断该App全部流量，IP规则没有在此推演。通用包已命中时，专项可能只是提供较小范围/独立入口，并不额外增加一次拦截。基础和扩展二选一；同一请求按首条规则处理。

| App | 目标主机 | 基础规则 | 扩展规则 |
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
| 美团 | `flowplus.meituan.net` | 未命中 | 有命中：`DOMAIN,flowplus.meituan.net` |
| 美团 | `img.meituan.net` | 未命中 | 未命中 |
| 美团 | `s3plus.meituan.net` | 未命中 | 未命中 |
| 美团 | `wmapi.meituan.com` | 未命中 | 未命中 |
| 瑞幸咖啡 | `capi.lkcoffee.com` | 未命中 | 未命中 |
| 微信 | `mp.weixin.qq.com` | 未命中 | 未命中 |

这张表也解释了为什么通用包不能代替所有App专项：共享业务网关若整域拦截会伤到正常功能，而路径处理只选广告端点。反过来，已被扩展包阻断的独立广告域名不必再叠加同一作用模块。

## 合并、优先级与验收

基础维护快照38条，整合入口默认引用的扩展快照38,066条。全部专项在构建时合并为 **11条脚本handler（全部响应阶段）、38条原生URL重写、45个去重后的精确MITM主机**。这些计数不代表实测有效。整合入口已在生成时去重MITM主机，原生解析、动作最低版本和实际处理仍待设备验收。

离线验证覆盖每个单模块、全部模块的正序/反序、每个有序模块对和所有端点的正反例；检查没有跨App业务URL误匹配。它不能证明HTTP/3、证书固定、私有协议、原生合并或当前App版本可用。

各维护源可引用相同MITM主机，整合生成器会去重，不重复挂载同一路径handler。不要再叠加另一整包重写或同款覆写；未知第三方模块优先级不在项目验证范围。

## 更新和维护

新增模块从人工审核的 `research/ad-catalog.json` 生成；修改原条目后运行 `python tools/generate_ad_modules.py --write`，再运行 `python tools/validate.py`。不要直接编辑生成文件造成下次回写丢失。清单文字由 `python tools/render_app_research.py --write` 同步。旧5款保持原模块路径维护；所有JS由`tools/ad_transforms/`和`tools/build_ad_scripts.py`生成，再构建入口与本地包。

新增/调整端点前重读源代码、许可、正常权益影响和设备反馈；固定SHA更新，保留脚本失败放行和无外联约束。公共更新不改设备私人订阅。规则集与机场代理集按现有24小时间隔尝试刷新；建议主配置每周手动刷新一次，发布修复时及时刷新，JS由Stash按原URL获取并按24小时间隔尝试更新；新增主机或handler仍须更新主配置。间隔并非北京时间固定时刻，也不保证断网更新；完整机制见[更新教程](UPDATES.md)。
