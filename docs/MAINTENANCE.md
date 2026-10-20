# 在电脑上检查和更新上游规则

这个工具帮你完成重复劳动：检查别人维护的公开资源有没有变化，更新普通规则，生成配置，执行项目验证，再保存到你的本地项目。你不用逐条复制广告域名。

**它需要在电脑上运行。** iPhone里的Stash不会运行Python维护程序。手机继续使用原有公共配置链接和私人机场覆写；本地更新后，还要发布到GitHub，手机才能取得新内容。你无需提供机场订阅、Cookie或证书。

## 先分清三个步骤

| 步骤 | 谁执行 | 得到什么 |
|---|---|---|
| 检查上游 | 电脑运行`check` | 哪些公开文件有变化的中文报告 |
| 更新本地项目 | 电脑运行`update` | 经过生成和验证的普通规则更新；本地备份 |
| 发布更新 | 你审阅差异后提交、推送GitHub | 原有订阅链接取得新的公开文件 |

没有变化时无需更新；上游改了与本项目无关的内容，也不必重写配置。App专项脚本、URL重写及MITM主机的变化需要审查；工具不会把整包上游脚本直接覆盖进来。

本轮自动同步范围是blackmatrix7来源的6份规则输出：Netflix、YouTube、Telegram、国内域名、扩展广告包和基础广告子集。AI精选规则、App专项与其他参考来源会检查并提示变化，不自动改写。本地白名单与私人接入保持原样，生成的主配置仍用原稳定路径，地区组保留。

## 一次性准备

电脑安装以下软件，使用各软件官方网站的安装包：

- [Python](https://www.python.org/downloads/)：建议3.12；Windows安装时勾选添加到PATH。
- [Git](https://git-scm.com/downloads)：用于下载仓库、检查本地状态和发布。
- [Node.js](https://nodejs.org/en/download)：建议22 LTS，用于执行现有JavaScript检查。仅安装Python不能完成更新后的全部验证。

本轮在Linux环境验证。下面提供Windows与macOS的操作方式，但尚未在这两个系统实际运行验证。

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

工具不会自动提交、推送或修改仓库可见性。更新完成后先运行：

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

发布后，手机保留原私人覆写和证书，在Stash里刷新原主配置链接并重连；需要立即更新广告域名包时，手动刷新远程规则集“基础广告”。主配置里的脚本随主配置刷新，域名包平时按24小时间隔尝试刷新。详细步骤见[更新教程](UPDATES.md)。

## 建议多久检查

**每天检查一次即可，有变化才处理。** 不需要每几分钟拉取。建议先手动成功运行一次，再把`check`加入电脑定时任务；暂不建议定时直接发布变化。

本项目没有替你安装定时任务，也没有部署GitHub定时同步。电脑休眠、关机或断网会影响本地任务，聊天结束后也不会有助手替你后台运行。若希望不依赖电脑开机，可另外部署GitHub Actions定时检查；当前仓库的验证工作流不等于这个同步服务。

### Windows每天检查

1. 在终端取得仓库完整路径，确认`.venv\Scripts\python.exe`存在。
2. 打开Windows“任务计划程序”，选择“创建基本任务”，名称填写“Stash上游检查”。
3. 触发器选“每天”，选择你通常开着电脑的时间，例如20:00。
4. 操作选“启动程序”。程序填写虚拟环境Python的完整路径，例如`C:\Users\你的用户名\Jimmy-s-Stash-rules\.venv\Scripts\python.exe`。
5. 参数填写`tools\maintain.py check`；“起始于”填写仓库目录的完整路径，不加引号。
6. 保存后手动“运行”一次，查看`.local\maintenance\`中的报告时间是否更新。

路径要换成你电脑的实际位置。该时间使用Windows本地时区；希望北京时间20:00执行，先确认系统时区为北京时间。任务没有弹窗不等于成功，仍需查看报告。

### macOS与Linux

macOS日常手动运行上面的命令即可。需要定时检查的macOS/Linux用户，可用`crontab -e`加入一行；先把下列两处路径换成自己的仓库绝对路径：

```cron
0 20 * * * cd "/绝对路径/Jimmy-s-Stash-rules" && "/绝对路径/Jimmy-s-Stash-rules/.venv/bin/python" tools/maintain.py check
```

这表示每天本机时区20:00检查；macOS不保证休眠时执行。保存后在终端手动运行同一条`cd ... && ... check`命令验证路径，再查看报告。定时环境通常不加载终端配置；Git需要能被该环境找到，不要把私人凭据写进任务命令。

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
