# 一次完整案例怎样操作、怎样观察

工作台：http://127.0.0.1:18780/ 。持续观测页：http://127.0.0.1:18781/ops-observe.html 。直接的九问原版页面与 `/chat/SESSION_ID` 路径继续保留。

## 自己跑一轮

1. 在工作台填操作令牌，点击“记住本次会话”。终端在仓库中执行 `scripts/lab token` 可取得令牌；模型 Key 仍只配在 `.local/model.env`。
2. 点击“1. 验证正常基线”。结果卡先显示正在验证，给出真实轮次、下单次数和失败数；通过后显示实际金额、订单读回与 PostgreSQL 检查结果。
3. 点击“2. 制造真实故障”。先看到“正在发布故障版本”。只有采到该故障版本普通下单的实际 500 响应，才显示“故障已复现”。发布成功和修复成功是两件事。
4. 点击一次“持续观察本轮事件”。可以在告警事件尚未创建时就打开，它会等待真实事件和 SDK Session，并自动接上后续执行。
5. 工作台看业务状态、PR、交付和恢复；观测页看同一事件中的真实模型/工具轨迹。观测页在 CI、构建、发布时显示等待项；新的复核 Session 开始后会自动切换。
6. 最终工作台应显示“业务已恢复”和 `RESOLVED_FIXED`。下方“正常 → 故障 → 恢复”保留本轮证据，即使修复很快也能回看。

原始操作返回、事件完整数据和逐条执行记录都在默认折叠的技术详情里，展开后内部滚动。默认界面不展示展开的发布账本 JSON。

## 业务状态与处理进度分别来自哪里

| 展示 | 实际依据 |
|---|---|
| 业务正常 / 异常 / 待确认 | probe 持续发真实普通/优惠码下单请求，读取订单，并用只读数据库账号 SELECT 核对金额和数量；采样前后版本必须相同，过期或取不到结果显示待确认 |
| 正常基线通过 | 原有独立业务合同的 2×60 秒验证；进度来自验证器实际计数，不能由按钮点击或容器状态推断 |
| 故障已复现 | 发布后该 release/source 的实际普通下单 HTTP 500 采样，带观察时间和 observation_id |
| 业务已恢复 | 新版本的真实业务采样正常，且本轮独立恢复合同通过；Agent 的发布后复核仍可继续运行 |
| Agent / CI / 构建 / 发布进度 | 原有控制中心的真实持久化状态，与业务健康分开 |
| RESOLVED_FIXED | 原有真实 SDK、PR/CI/发布、独立验证及新 Session 复核门槛全部通过 |

业务采样会保留健康状态/发布版本变化时的第一条证据；完整轮次引用基线报告、故障采样和恢复报告。故障确认只观察事实，不暂停、排队阻挡或刻意延迟 Agent 来留展示时间。当前采样正常也不会删除已经保存的故障证据。

## 持续观测扩展的准确边界

上方“事件跟随栏”是本项目新增的自有页面；下方 iframe 是固定官方源码构建的完整九问原版 WebUI。没有改原版前端源文件，也没有自绘一份轨迹来替代它。

扩展复用现有 `/chat/SESSION_ID` 路由、原生轨迹分析组件、原生 SQLite/OTel 读取和 `trace.updated` 增量。跟随栏读取控制中心的真实 case/attempt/Session 映射，选择相应原生路由；自动打开原版已有的轨迹分析开关、展开成员、折叠输入框。按钮选择器固定在当前官方提交的 `data-testid`/ARIA 接口上，构建脚本包含该适配文件，可复现。

修复和复核**始终是两个真实 Session**，阶段按钮、页面身份栏、原生 iframe URL 和事件里的 `sdk_runs` 均保留各自原始编号。平台等待项只出现在自有跟随栏，不生成 Core Span。

查看历史阶段会暂停自动切换；点“继续跟随最新阶段”恢复。新事件只增加提示与选择入口，用户选中的历史事件不会被抢走。在原生 iframe 内主动切换到其他会话，也会暂停自动跟随。

### 为什么没有直接让原生会话列表完成这一切

已核查固定官方版本：

- [项目会话列表查询](https://github.com/openJiuwen-ai/jiuwenswarm/blob/32d75d7d3a0b466412ee64d77c29460297515119/jiuwenswarm/server/control/store/project_queries.py#L259) 明确筛选 `channel_id == web`；Process SDK 会话保留真实的 `process_cli` 通道身份。本项目没有把它们改标为 web 会话。
- [原生路由](https://github.com/openJiuwen-ai/jiuwenswarm/blob/32d75d7d3a0b466412ee64d77c29460297515119/jiuwenswarm/channels/web/frontend/src/multi-session/routing/route.ts) 支持按真实 Session 打开，没有按运维 case 自动跨 Session 跟随的路由。
- [原生轨迹增量订阅](https://github.com/openJiuwen-ai/jiuwenswarm/blob/32d75d7d3a0b466412ee64d77c29460297515119/jiuwenswarm/channels/web/frontend/src/features/trajectory/TrajectoryPanel.tsx#L1106) 用于同一 Session 的轨迹更新，不能代替运维事件阶段编排。
- [原版轨迹开关与输入框开关](https://github.com/openJiuwen-ai/jiuwenswarm/blob/32d75d7d3a0b466412ee64d77c29460297515119/jiuwenswarm/channels/web/frontend/src/components/ChatPanel/index.tsx#L2652) 是跟随页使用的现有 UI 控件。

因此这里提供的是“自有事件跟随栏 + 原版九问轨迹”，不声称官方原生产品已有 case 连续观测能力。原版界面中的聊天/设置/删除等写操作仍未接入，后端保持只读。

## 实现与升级

- `lab/experience.py`：持久化操作、实验轮次、真实证据引用和精简状态投影；与模型循环分离。
- `lab/probe.py`：持续业务采样、版本绑定、健康变化证据和独立验证进度，复用已有真实流量与合同。
- `lab/control.py`：接入后台操作、概览和恢复记录；原 SDK 执行、交付门槛保留。
- `web/workbench.*`：人能理解的操作卡、独立业务状态、轮次证据、折叠技术详情。
- `web/observe.html`：明确标注的事件跟随栏及原版 iframe。
- `lab/native_observer.py`：增加只读状态投影/Session 就绪查询；原轨迹读取与执行隔离保持。

新增操作接口 `POST /api/operations` 接受 baseline/fault 并立即返回 operation_id；`GET /api/operations/ID` 查询进度，`?details=true` 读取原始结果。旧 `/api/experiment/baseline` 和 `/fault` 同步入口兼容保留，CLI 脚本仍可运行。

部署使用原 VM 与数据卷，增加通用对象存储里的 operation/experiment/采样记录，无需重建或清空。先确认没有 Agent、交付或操作任务在运行，再同步、构建、启动更新的控制、probe 和 native-web 服务。重启发现未完成的操作会标记中断并保留事实，不自动重放故障发布。

旧事件照常保留。升级前没有采集过的本轮业务证据不会被补造。

## 验收采集

```bash
python3 scripts/verify_experience.py EXPERIMENT_ID
python3 scripts/observe_native_trace.py CASE_ID
```

这两个脚本只读取实际状态/原生数据，不写补丁、不构造模型结果，也不代替浏览器验收。最终还需实际检查同一观测页的路由接续、历史不抢占、默认 JSON 折叠，并保留截图、真实 PR/CI、镜像和业务验证回执。
