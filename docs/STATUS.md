# 实施与验收状态

新增实测：原版 WebUI 已能实时观察同一次 SDK 任务，最小探针及完整订单案例均通过。repair / verify 的 Session 身份、截图、原生归档和 PR #9 的恢复结果见 [原生 WebUI 验收](NATIVE-WEBUI-ACCEPTANCE.md)。此前各阶段证据继续保留。

2026-10-30。**环境、真实故障和工程交付链已经实际通过；真实模型接线、首条集成闭环和三次独立重置验收均已实际通过。** 没有模型替身，也没有把人工补丁验收记成 Agent 修复成功。

| 层次 | 当前结果 | 实际证据与边界 |
|---|---|---|
| 公开完整源码/脚本/学习文档 | 已发布 | `lelezi257/jiuwen-ops-lab`，公开且可用作模板；默认 main 保持正常业务源码 |
| 专用 Lima VM | 已运行 | ARM64、4 vCPU、10 GiB、60 GiB 按需磁盘；未复用其他 VM |
| 独立部署组件 | 已运行 | 自有 Web/API、独立原版 WebUI 只读观测服务、runner、取证、工程、probe、日志采集、PostgreSQL、Prometheus、Alertmanager、Loki、registry；订单容器由工程服务独立管理 |
| 九问源码与依赖 | 已安装/检查通过 | 官方固定 Swarm/Core/Protocol 源码；255个已安装包依赖兼容检查通过；未修改上游 Agent 实现 |
| 官方 SDK / CLI / Runtime | 实测通过（无模型） | protocol.capabilities、实际 Runtime mode.list 启动/退出、非法参数失败终态/退出码；[报告](evidence/sdk-runtime.json) |
| 正常业务基线 | 实测通过 | 连续两个60秒窗口，每窗口每条正常路径110次，金额、实际数据库记录、新旧订单与非法输入语义均通过；[报告](evidence/baseline.json) |
| 真实故障与自动告警 | 实测通过 | 无优惠码真实500，有效优惠码200/18000分；实际 Loki异常、Prometheus指标、Alertmanager创建排队事件；[报告](evidence/real-fault.json) |
| 真实候选、PR与CI | 实测通过（人工补丁工程验收） | [PR #1](https://github.com/lelezi257/jiuwen-ops-lab/pull/1)；[候选CI](https://github.com/lelezi257/jiuwen-ops-lab/actions/runs/40996229012)；真实代码、独立HTTP/DB合同与新增回归测试 |
| 合并后构建与发布 | 实测通过 | 控制中心自动合并到实验分支；[构建](https://github.com/lelezi257/jiuwen-ops-lab/actions/runs/40996327233) 在 AMD64/ARM64 都重查实际 merge SHA；导入 ARM64 制品后以真实 registry digest 发布 |
| 发布后业务恢复 | 实测通过 | 连续两个60秒窗口，每窗口每条路径109次且全部通过；数据库直接读取、旧订单与非法输入保持；[完整工程证据链](evidence/engineering-e2e.json) |
| 产品边界单测 | 本地15项通过 | 角色分离、路径/symlink、取消与重试身份、CI failure/neutral/skipped、过期 head/base 等；单元测试不是模型效果证明 |
| 真实模型/host tool/取消 | 实测通过 | 实际模型与 host tool、结构化结果、取消130和子进程清理；[报告](evidence/real-model-sdk.json) |
| 模型自主诊断与代码修复 E2E | 首条集成案例通过（含重试） | 真实模型生成修复/测试与 PR #3，CI、构建、发布、两个60秒业务窗口、新会话复核完成，终态 RESOLVED_FIXED；早期失败和重试保留；[完整摘要](evidence/real-model-integration-case.json) |
| 三次独立故障重置 | 3/3 实测通过，零人工重试 | 每轮修复/只读复核各一个新会话；PR #4/#5/#6、真实CI与双平台构建、独立两窗HTTP/DB合同全部通过；[完整结果](REAL-MODEL-ACCEPTANCE.md) · [证据](evidence/real-model-three-clean-trials.json) |
| 自动回滚保护 | 故障注入实测通过 | [PR #2](https://github.com/lelezi257/jiuwen-ops-lab/pull/2) 发布后停止真实订单容器，验证失败后自动回滚到上一已验证镜像；两个60秒窗口每路径106次全部通过；[证据](evidence/rollback-e2e.json)；不计修复成功 |

## 本次版本证据链

```text
事故 B: 297428371eb288ade09dfd5380f61b239d547ab5
候选 C: c2c03e7b9178b173af8d29e87da7dfd605a119e0
PR检查 test-merge: 0a61ab868307f5ec4dedbf1d89cc15d1242d7ea4
实际 merge M: 3e1e80e1aa3994b6f18e767c9a98647212691998
构建 run: 40996327233
ARM64 artifact: 12952050101
发布镜像: localhost:5000/jiuwen-order@sha256:eed0247991192fb5a437d51f7031a072a19b4337870740fb958551c3de414524
业务验证: verify-71517ae897d14e80
终态: DELIVERY_ACCEPTANCE_PASSED
人工补丁 / 模型调用0次 / 不计 Agent 成功
```

仍未证明所有异常重启/长期运行分支、Core Checkpoint 恢复或生产可靠性。

## 当前运行与复现

本次用户已在本地配置真实模型，`scripts/lab qualify` 实测通过。首条真实修复和 `scripts/lab agent-acceptance --trials 3` 的三轮独立故障复跑均已完成。真实模型异常如实进入需人工状态；早期结果接收失败和被拒绝的 bash 调用均保留，不自动退回脚本补丁。

最终运行现场和已完成事件见工作台及 [交接记录](evidence/handoff.json)。本地原始日志、订单探测、SDK回执、代码工作区与动作账本保存在专用VM及 `.local/evidence/`；公开的是脱敏摘要。其他人的操作系统/模型/网络组合需要自行按同一层次验收。

## 配置前交接现场（历史快照）

默认 `main` 保存平台实现和正常应用源码；`lab-live` 独立保存故障与修复历史，运行镜像以实际提交 SHA 和 digest 核对。当时真实告警事件 `case-812a384054014495` 已排队、尝试次数为0，Runner 等待模型。配置后该事件已完成真实修复；原始等待现场保留用于核对实施过程。

[配置前交接记录](evidence/handoff-before-model.json) · [配置前检查](evidence/verification-before-model.json) · [配置前截图](evidence/workbench-before-model.jpg)。匿名公开 clone 和本地空配置初始化已通过；未借用模型 Key。

## 完成审计

G0 独立部署、关闭工作台后后台继续推进；G1 官方SDK真实模型/host tool/取消/错误/清理；G2 实际故障和自动告警；G3 模型生成修复、新增测试与正确提交的CI；G4 合并后重新构建、制品哈希、digest发布与运行版本；G5/G6 两个60秒分路径HTTP/金额/数据库/旧订单/非法输入合同；G7 无人推进、取消与失败边界。三轮正常路径实际通过，另有发布失败后的真实回滚证据和15项产品边界测试。未覆盖的生产可靠性范围仍按上文边界保留。

[真实模型报告](REAL-MODEL-ACCEPTANCE.md) · [最终工作台](evidence/workbench-real-model-complete.jpg) · [最终核对](evidence/verification.json)。
