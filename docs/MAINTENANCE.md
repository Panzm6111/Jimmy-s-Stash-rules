# 在电脑上检查和更新上游规则

这个工具帮你完成重复劳动：检查别人维护的公开资源有没有变化，更新普通规则，生成配置，执行项目验证，再保存到你的本地项目。你不用逐条复制广告域名。

**它需要在电脑上运行。** iPhone里的Stash不会运行Python维护程序。手机继续使用原有公共配置链接和私人机场覆写；本地更新后，还要发布到GitHub，手机才能取得新内容。你无需提供机场订阅、Cookie或证书。

## 先分清三个步骤

| 步骤 | 谁执行 | 得到什么 |
|---|---|---|
| 检查上游 | 电脑运行`check` | 哪些公开文件有变化的中文报告 |
| 更新本地项目 | 电脑运行`update` | 经过生成和验证的普通规则更新；本地备份 |
| 发布更新 | 每日auto_update.py在核准范围及验证通过后自动提交、推送GitHub | 原有订阅链接取得新的公开文件 |

没有变化时无需更新；上游改了与本项目无关的内容，也不必重写配置。App专项脚本、URL重写及MITM主机的变化需要审查；工具不会把整包上游脚本直接覆盖进来。

2026-10-29自动同步范围扩展为12份blackmatrix7输入（增加Apple、Microsoft、GitHub）和10份MetaCubeX/Sukka完整社区分类，包含TikTok功能/广告、AI、常用社交与通用海外规则。只做格式转换和去重，退出原人工精选AI生成链；只改注释时不提交。来源清单、许可和兼容遗漏见[社区规则说明](COMMUNITY-SOURCES.md)。本地白名单、私人接入、策略组与HTTP专项保持原样。

## 一次性准备

2026-10-29审查后新增第11份社区输入：MetaCubeX完整基础广告category-ads，仅用于新的Clash自动订阅，Stash现行规则保持不变。`config/clash-verge-auto.yaml`已加入生成器和自动发布白名单；原中午任务同时维护Stash与Clash公开产物，无需新增计划任务。Clash客户端须启用主订阅360分钟自动更新，才会取得策略组等结构变化。来源审查证据见[审查记录](../research/source-health-review-20261029.json)。

电脑安装以下软件，使用各软件官方网站的安装包：

- [Python](https://www.python.org/downloads/)：建议3.12；Windows安装时勾选添加到PATH。
- [Git](https://git-scm.com/downloads)：用于下载仓库、检查本地状态和发布。
- [Node.js](https://nodejs.org/en/download)：建议22 LTS，用于执行现有JavaScript检查。仅安装Python不能完成更新后的全部验证。

原维护逻辑曾在Linux模拟验证；2026-10-28已在Windows实际检查来源并运行计划任务。自动提交推送已用临时裸仓库验证；真实公开上游无内容差量时不伪造事务，macOS尚未实机验证。

已经有本仓库的Git工作副本时，进入原目录继续使用，不再克隆第二份。只有ZIP解压目录时，建议按下面的命令克隆一次；更新工具依赖Git状态和历史。

macOS打开“终端”，Windows打开PowerShell。先执行：

```sh
git clone https://github.com/Panzm6111/Jimmy-s-Stash-rules.git
cd Jimmy-s-Stash-rules
```

macOS：

```sh
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/python tools/maintain.py check
```

如果安装后的命令是`python3`，先用`python3 --version`确认版本，再用它替换第一行的`python3.12`。

Windows PowerShell：

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe tools\maintain.py check
```

不用激活虚拟环境，也不用修改PowerShell执行策略。后文的`python`表示上面的虚拟环境解释器：macOS用`.venv/bin/python`，Windows用`.\.venv\Scripts\python.exe`。

## 平时运行

先进入这个仓库目录，检查有没有上游变化：

```sh
python tools/maintain.py check
```

不写`check`也会执行检查。中文报告保存在`.local/maintenance/latest.md`，机器可读结果是同目录下的`latest.json`；每次检查覆盖这两个最新报告。该目录被Git忽略，不属于公开订阅文件。

报告提示普通规则有变化时，运行：

```sh
python tools/maintain.py update
```

更新要求Git工作区干净。若有你尚未保存为提交的修改，工具会停止；先用`git status`查看并处理自己的修改，**不要为了通过检查直接丢弃文件**。如果其他设备已更新GitHub，也应在干净工作区先用`git pull --ff-only`取得新版本，再运行维护工具；发生分叉时停止并处理原因。

更新会先在临时副本中获取新规则、生成配置并执行验证。任一来源检查失败都会停止整次更新，包括暂时无法下载的参考来源；不会按“其余来源成功”继续写入。待同步普通规则的许可证改变、规则内容异常或验证失败，也会停止写入；其他专项或参考来源的许可证变化只记录为待审查，不自动采用。

普通规则还有变化量保护：删除超过原条目的10%、增删合计超过原条目的25%或5000条，以及新增顶级域后缀匹配时，停止自动采用并要求审查。命中保护不等于上游有错；它表示变化已经超出无人值守同步的范围。成功后按报告查看本地变更和备份位置。

完整生成和验证可能需要几分钟，终端会显示当前验证步骤；不要在正常验证期间强制结束。私人配置合成回归只用模拟数据，并预留10分钟超时以适应较慢的电脑。

Clash全局Merge现由tools/build_clash.py与另两份Clash入口一起生成，正式文件为config/clash-verge-merge.yaml；已纳入隔离更新和精确发布白名单，无需增加任务。它从同一分流源生成，不读取.local临时版本或机场凭据。客户端已粘贴的Merge仅自动更新规则集正文，结构仍需手动换入新版文件。

这些检查能够发现格式、引用和部分路由回归；**不能代替iPhone上的Stash执行和去广告效果验收**。

## 报告应该怎么看

| 报告情况 | 你的处理 |
|---|---|
| 引用的文件没有变化 | 不用做事；仓库提交号变化不一定代表所用文件变化 |
| 普通规则变化 | 可以执行`update`，成功后审阅差异并发布 |
| App脚本、重写、许可证等需要审查 | 保留当前版本，把报告中的公开来源和变化范围交给维护者分析 |
| 仅供参考的来源变化 | 不等于已启用模块失效；不要直接导入该上游整包 |
| 网络或来源检查失败 | 保留现有规则，恢复网络后重试；不能把失败当作没有更新 |

专项脚本不会自动获得新的广告接口。域名规则更新得更勤，也不能替代缺失的开屏处理逻辑。

供定时任务判断的退出码：`0`表示本次检查或操作成功，仍可能有“需要审查”的变化；`1`表示网络、验证或保护条件导致失败；`2`表示命令参数错误。`0`不是“上游没有变化”，也不是“手机去广告成功”。

## 发布到GitHub，手机才会得到变化

兼容命令update只更新本地；已授权的publish模式会在必要验证通过后自动提交并推送。手工发布时，更新完成后先运行：

```sh
git status --short
git diff --stat
git diff
```

只提交报告列出的公开配置、规则、生成文档和来源记录。不要使用`git add .`把其他文件一起加入；不要上传`.local`、私人订阅、导出的最终配置或证书。第一次在电脑上推送需要登录你自己的GitHub账号，可以使用[GitHub Desktop](https://desktop.github.com/)审阅、选择公开变更文件并提交、推送；工具不会索取或保存GitHub登录信息。

命令行用户可逐项执行`git add -- 路径`，检查`git diff --cached`后再提交：

```sh
git commit -m "同步公开上游规则并重新生成配置"
git push origin HEAD:main
```

不要添加强制推送参数。推送被拒绝时先核对远程变化；本地文件保存成功不等于已经上传。

发布后，手机保留原私人覆写和证书，在Stash里刷新原主配置链接并重连；需要立即更新广告域名包时，手动刷新远程规则集“基础广告”。主配置更新脚本URL、主机及handler声明；脚本和域名包分别按24小时间隔尝试刷新。仅刷新JS不能替代新增主机/handler后的主配置更新。详细步骤见[更新教程](UPDATES.md)。

## 本机每天中午12点检查

2026-10-28已在本机注册 Windows 任务 Jimmy-Stash-Rules-Noon-Check，每天北京时间12:00检查；本机时区为China Standard Time。使用当前用户登录会话，锁屏可运行，关机/休眠时不唤醒；错过后在可用时或中午之后登录补检，同一天成功后不重复。电脑未登录、关机或断网时不能保证准点执行。

任务动作现为Run-Maintenance.ps1 -Mode publish -Scheduled，由auto_update.py执行检查、隔离更新、验证、提交与推送。仅当普通规则确有内容变化才改受控文件并产生提交；无变化只更新.local日志。公开上游下载失败时整轮重试一次，仍失败返回非零结果，保留原规则。运行日志位于.local/maintenance/run-*.log，latest.md为中文报告。

重新安装或迁移任务（须先在新位置准备Python环境及Git/Node）：

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\tools\Install-MaintenanceTask.ps1
```

安装器捕获当前Git/Node路径到被忽略的.local配置。任务名称沿用Jimmy-Stash-Rules-Noon-Check，避免重复注册。只在该进程使用Bypass，不修改全机执行策略；不保存账号密码。若同名任务指向其他程序会停止，避免覆盖无关任务。移动仓库后重新安装。

立即手动检查或更新：

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\tools\Run-Maintenance.ps1
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\tools\Run-Maintenance.ps1 -Mode update
```

update是仅更新本地的兼容命令；-Mode publish才执行获授权的日常发布。两者均要求干净工作区。专项脚本、MITM、许可及陌生规则类型需审阅；已接入的完整AI分类可机械同步。完整配置构建会同步生成Stash和Clash文件。

查看或删除任务（删除不影响仓库文件）：

```powershell
Get-ScheduledTaskInfo -TaskName Jimmy-Stash-Rules-Noon-Check
Unregister-ScheduledTask -TaskName Jimmy-Stash-Rules-Noon-Check -Confirm:$false
```

2026-10-28原任务已升级为publish模式，23:14:32真实执行退出0；54项来源读取成功，结果为无相关差量、无提交、无推送，1项上游变化保留待审查。下一次计划时间为2026-10-29 12:00。这不是广告效果验收。macOS/Linux尚未安装调度。

## 自动发布边界

默认入口为 powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\tools\Run-Maintenance.ps1 -Mode publish；任务每天12点执行同一入口，并保留登录后补执行、每日成功去重、互斥、日志与失败非零退出。

只允许原origin地址和main分支。任务启动时若有其他会话的暂存、未提交或未跟踪内容会停止；不stash、reset、清理或上传它们。远端前进只允许快进，本地未知提交或分叉停止。仅临时生成、校验并应用白名单文件；提交前复核HEAD、文件集合、内容哈希与暂存内容。私人订阅、证书、.local、.venv及缓存不进入提交。

网络/许可变化、异常变化量、任何必要验证失败都不发布。无法安全自动适配的HTTP脚本、MITM、陌生规则类型和参考来源保留明确待审查状态，不能记为已经更新。Apple/Microsoft/GitHub直接采用社区维护源；规则和源锁分别跟踪实际内容与提交，Meta数据分支和许可分支独立检查。

若推送失败，只记录本程序刚创建提交的SHA/父提交/文件哈希。以后仅能重试这个已核验提交；不会替其他本地提交推送，也不会强制推送。GitHub已接收但确认网络失败时可识别为已收到，不重复提交。进程在提交之前被中止或用户编辑造成冲突时保持失败与现状，需要先核对日志，避免覆盖个人修改。

日志：.local/maintenance/latest.md（来源与待审查）、publication-latest.json（本轮发布状态）、pending-publication.json（仅本程序待确认提交）、run-*.log（任务输出）。发布前的生成回归会核验Stash、Clash、脚本、私人合成及维护/自动发布事务。已存在的CI仍在推送后运行，不是电脑调度的替代品。

## 回退与失败处理

成功更新会保存本地备份：`.local/maintenance/backups/备份编号/`。回退最近一次成功更新：

```sh
python tools/maintain.py rollback
```

需要指定备份时，复制工具输出或备份目录中的编号：

```sh
python tools/maintain.py rollback --backup 备份编号
```

回退也只在本地生效，已经发布到GitHub的更新需要另行发布回退结果。工具会核对待恢复文件是否仍与该次更新后的内容一致，避免覆盖你后来做的修改；保留`.local/maintenance/`，否则无法使用其中的本地备份。

如果提示存在后续修改，先保留自己的文件并检查差异，不使用强制重置。也可以请维护者依据备份和Git差异合并恢复。手机暂时恢复的方法见[更新与回退](UPDATES.md#暂停处理与回退)。

如果电脑断电或进程被强制结束，文件替换只能保证单个文件完整，不能保证整批文件同时完成。残留的`.local/maintenance/run.lock`会阻止再次运行。先确认原维护进程已经退出，备份当前工作目录，再查看`.local/maintenance/backups/`中对应备份的`manifest.json`：状态为`prepared`或`recovery_required`时，可能需要恢复未完成的写入。

确认进程已退出后才删除残留`run.lock`，然后用`rollback --backup 对应编号`恢复该次更新；不要直接用不带编号的回退，因为默认记录可能仍指向更早的成功更新。不要删除备份目录。工具若发现文件又被修改会停止，保留现状并请维护者协助合并。

没有真实设备证据时，不把一次更新成功写成某款App已去广告。出现广告时仍应按[诊断教程](ADBLOCKING.md)核对实际命中、协议和缓存。
