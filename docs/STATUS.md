# 实施与验收状态

2026-10-30。**环境、真实故障和工程交付链已经实际通过；真实模型与 Agent 完整闭环仍等待用户配置。** 没有模型替身，也没有把人工补丁验收记成 Agent 修复成功。

| 层次 | 当前结果 | 实际证据与边界 |
|---|---|---|
| 公开完整源码/脚本/学习文档 | 已发布 | `lelezi257/jiuwen-ops-lab`，公开且可用作模板；默认 main 保持正常业务源码 |
| 专用 Lima VM | 已运行 | ARM64、4 vCPU、10 GiB、60 GiB 按需磁盘；未复用其他 VM |
| 独立部署组件 | 已运行 | 自有 Web/API、runner、取证、工程、probe、日志采集、PostgreSQL、Prometheus、Alertmanager、Loki、registry；订单容器由工程服务独立管理 |
| 九问源码与依赖 | 已安装/检查通过 | 官方固定 Swarm/Core/Protocol 源码；255个已安装包依赖兼容检查通过；未修改上游 Agent 实现 |
| 官方 SDK / CLI / Runtime | 实测通过（无模型） | protocol.capabilities、实际 Runtime mode.list 启动/退出、非法参数失败终态/退出码；[报告](evidence/sdk-runtime.json) |
| 正常业务基线 | 实测通过 | 连续两个60秒窗口，每窗口每条正常路径110次，金额、实际数据库记录、新旧订单与非法输入语义均通过；[报告](evidence/baseline.json) |
| 真实故障与自动告警 | 实测通过 | 无优惠码真实500，有效优惠码200/18000分；实际 Loki异常、Prometheus指标、Alertmanager创建排队事件；[报告](evidence/real-fault.json) |
| 真实候选、PR与CI | 实测通过（人工补丁工程验收） | [PR #1](https://github.com/lelezi257/jiuwen-ops-lab/pull/1)；[候选CI](https://github.com/lelezi257/jiuwen-ops-lab/actions/runs/40996229012)；真实代码、独立HTTP/DB合同与新增回归测试 |
| 合并后构建与发布 | 实测通过 | 控制中心自动合并到实验分支；[构建](https://github.com/lelezi257/jiuwen-ops-lab/actions/runs/40996327233) 在 AMD64/ARM64 都重查实际 merge SHA；导入 ARM64 制品后以真实 registry digest 发布 |
| 发布后业务恢复 | 实测通过 | 连续两个60秒窗口，每窗口每条路径109次且全部通过；数据库直接读取、旧订单与非法输入保持；[完整工程证据链](evidence/engineering-e2e.json) |
| 产品边界单测 | 本地10项通过 | 角色分离、路径/symlink、取消与重试身份、CI failure/neutral/skipped、过期 head/base 等；单元测试不是模型效果证明 |
| 真实模型/host tool/取消 | 待配置后实测 | 已提供 `scripts/lab qualify`；未发外部模型请求 |
| 模型自主诊断与代码修复 E2E | 尚未验收 | 人工补丁不是模型生成修复；尚无外部LLM成功率或三次干净重置结果 |
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

## 下一步

在 `.local/model.env` 配置真实供应商、API地址、模型和Key，运行 `scripts/lab configure-model`。单独的真实接线与取消检查使用 `scripts/lab qualify`；再观察排队的真实故障事件。真实模型异常会如实进入需人工状态，可在核对实际副作用后显式重新尝试，不自动退回脚本补丁。

最终运行现场和最新待处理事件见工作台及 `evidence/handoff.json`。本地原始日志、订单探测、SDK回执、代码工作区与动作账本保存在专用VM及 `.local/evidence/`；公开的是脱敏摘要。其他人的操作系统/模型/网络组合需要自行按同一层次验收。
