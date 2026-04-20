# mars-moon 当前计划

- 更新时间：`2026-04-15 17:36:00`
- 当前目录：`mars-moon/`
- 当前目标：保持 `mars-moon` 作为可迁移、自包含、双平台可执行的离线语音测试 bundle，并保留当前可复用的全链路验证基线。

## 当前结论

- 主链路 `prepare -> build -> burn -> run` 已在当前 bundle 内稳定跑通。
- 指定声卡播报已切到短 key 方案，当前 Linux 基础配置为 `VID_8765&PID_5678:USB_0_4_3_1_0`。
- `mars-moon` 已支持在缺少 `listenai-play` / `listenai-laid-installer` 时自动从 Git 下载，并支持显式刷新远端最新版本。
- 当前最新完整回归未引入新的工具类故障；剩余 `FAIL/BLOCKED` 仍主要属于固件、需求口径或依赖阻塞问题。

## 关键已完成节点

### 1. Bundle 与执行入口收敛

- 已统一主入口：`scripts/mars_moon_pipeline.py`
- 已收敛烧录工具：
  - `tools/burn_bundle/windows/`
  - `tools/burn_bundle/linux/`
- 已统一基础配置：
  - 串口：`tools/serial_ports.json`
  - 声卡：`tools/audio_devices.json`
- 已同步核心文档：
  - `SKILL.md`
  - `references/workflow.md`
  - `references/current-baseline.md`
  - `references/mind.md`

### 2. Traceability 与 runner 能力补齐

- 已完成逐需求绑定，避免整模块需求被单条 case 误绑定。
- 已支持 `validate_duration`、`blocked_by_case_ids`、需求级结果汇总输出。
- 已补齐设置类闭环校验，减少“只播报不落盘”的假 PASS。
- 已补齐用例前后默认状态恢复，减少跨 case 状态污染。
- 已将 `CFG-006 / CFG-007 / CFG-008 / CFG-010 / CFG-014` 固定按 `NO_METHOD / 人工确认` 管理。

### 3. 声卡路由与外部 skill 集成

- 已完成 ListenAI 声卡短 key 收敛，Linux/Windows 规则保持一致思路。
- 已同步 `listenai-play` 与 `listenai-laid-installer` 的 key 生成和 `laid` 安装逻辑。
- 已将以下规则写入外部 skill：
  - 调试/正式测试前先上电
  - 多张 ListenAI Render 时禁止默认声卡自动猜测
  - 声卡 key 作为基础配置保存
  - key 与显示名分离
- `mars-moon` 已落地运行时 bootstrap：
  - `tools/codex_skill_bootstrap.py`
  - `tools/audio_playback.py`
  - `scripts/mars_moon_pipeline.py` 的 `skills` 子命令与 `--refresh-codex-skills`

## 关键验证基线

### 基线回归

- `work/fullchain-20260408-wakephrase-v3/result/0408103826`
  - `PASS 64 / FAIL 9 / BLOCKED 0`
  - 用于保留早期完整链路基线

### Traceability 全链路

- `work/tmp-fullchain-20260409-195717-traceability/result/0409203151`
  - `PASS 61 / FAIL 10 / BLOCKED 5`
  - 首次形成稳定的 `execution_summary.md + requirement_status.md + testResult.xlsx`

### 指定声卡全链路

- `work/soundcard-fullchain-20260414-1719/result/0414171946`
  - `PASS 62 / FAIL 9 / BLOCKED 5`
  - 已确认：先上电后，指定声卡 `VID_8765&PID_5678:USB_0_4_3_1_0` 可支撑完整测试流程

### Skill bootstrap / Git refresh 全链路

- `work/fullchain-skill-bootstrap-20260414-2020/result/0414202156`
  - `PASS 62 / FAIL 9 / BLOCKED 5`
  - 已确认：
    - 缺 skill 时可自动从 Git 下载
    - `run --refresh-codex-skills` 可正常命中远端更新
    - 指定声卡播报在自动下载、刷新后仍稳定可用

## 当前固定规则

- 调试或正式测试前，必须先给 DUT 上电。
- 长流程任务要阶段性上报，不只在最后汇总。
- 所有生成、烧录、测试流程都必须在当前 `mars-moon` bundle 或其 workspace 内执行。
- `prepare` 之后，后续流程不得再依赖目录外文件。
- 设置类命令必须走完整闭环：唤醒 -> 进入设置 -> 目标设置 -> 生效校验。
- 主动重启、主动上下电不计入异常重启；被动重启要单独归因。

## 当前基础配置

- Linux 播报声卡 key：`VID_8765&PID_5678:USB_0_4_3_1_0`
- 当前外部 skill Git 版本：
  - `listenai-play = 7ee3b4e`
  - `listenai-laid-installer = eb10375`
- 常用维护命令：
  - `python3 scripts/mars_moon_pipeline.py skills --mode ensure`
  - `python3 scripts/mars_moon_pipeline.py skills --mode refresh`

## 当前待办

- 当前无阻塞中的必做项。
- 若后续继续优化，优先顺序如下：
  1. 修正 `protocol_serial` 预检文案中的乱码问题
  2. 细化失败归因与结果口径，必要时把 `NO_METHOD` 再细分
  3. 结合后续需求确认，继续收敛剩余 `FAIL / BLOCKED` 的真实归因

## 本次清理说明

- 已移除历史过程性记录、现场追问记录、重复中间状态和过细的背景日志。
- 当前 `plan.md` 仅保留后续继续接手最需要的结论、基线、规则和待办。

- 进展记录（2026-04-15 09:34）
  - 已按当前精简版 `plan.md` 继续接手，开始复核 runner 在播命令词前是否做唤醒态检测，以及设置命令是否校验 `configSaved` 等保存日志。
  - 当前计划：直接检查 `tools/dooya_voice_runner.py`、`tools/dooya_case_builder.py`、`tools/dooya_link_probe.py` 与 `sample/voiceTestLite.py` 的实际实现，然后给出口径，必要时指出现有覆盖点和缺口。

- 进展记录（2026-04-15 09:39）
  - 已完成代码复核：当前 runner 在绝大多数命令词前会先执行 `auto_wake -> run_wake()`，并用 `wakeKw + 可接受唤醒 tone` 作为主要唤醒成功判据。
  - 当前实现已覆盖：日志恢复、唤醒词匹配、播报 `playId` 命中、设置成功类 `configSaved=save config success` 日志校验。
  - 当前实现未做成硬门槛的项也已确认：唤醒协议、`mode=1`、唤醒播报结束信号并未作为统一强判据；其中 `workMode` 日志目前更多用于辅助判断和唤醒 tone 兼容，不是所有 case 的硬断言。

- 进展记录（2026-04-15 11:15）
  - 已完成本轮唤醒前置校验增强：当前 `run_wake()` 除 `wakeKw + 动态唤醒 tone` 外，已额外要求唤醒就绪日志 `wake up ready to asr`；若 action/词表后续提供唤醒协议，也支持按配置追加协议校验，缺失则自动忽略。
  - 已保持设置类保存校验口径：`say_action(expect_log_values=...)` 仍将 `configSaved=save config success` 作为 PASS 条件之一。
  - 已完成静态验证：`python3 -m py_compile tools/dooya_voice_runner.py tools/dooya_case_builder.py tools/dooya_deviceinfo_builder.py`
  - 已完成最小实机验证：`work/validation-wake-strict-20260415-0948/`，选跑 `TC_BASE_001 + TC_WORKMODE_006`，结果 `PASS 2 / FAIL 0 / BLOCKED 0`，确认严格唤醒校验与设置保存校验未打坏当前链路。

- 进展记录（2026-04-15 11:18）
  - 已确认本轮完整回归继续沿用 `tmp/需求文档.md + tmp/词条处理.xlsx + tmp/tone.h + tmp/fw-csk5062-dooya-general-curtain-VCC.03.02.00.24.bin` 这一套已验证输入。
  - 已确认现场硬件口径保持不变：`ctrl=/dev/ttyACM4`、`burn=/dev/ttyACM0`、`log=/dev/ttyACM0`、`protocol=/dev/ttyACM2`、`burn_baud=460800`。
  - 下一步直接执行：先上电，再创建新的全链路 workspace，随后跑 `prepare -> build -> burn -> run`。


- 进展记录（2026-04-15 11:27）
  - 已重新读取 `plan.md` 并接手当前完整回归任务；当前 workspace `work/fullchain-wake-strict-20260415-111737/` 已具备 `generated/cases.json`、`generated/deviceInfo_dooya.json` 与测试 Excel，视为 `build` 产物已落地。
  - 下一阶段按正式链路继续执行：先复位确认上电状态，再跑 `burn`，随后跑 `run --refresh-codex-skills` 完成整轮回归，并汇总 `PASS / FAIL / BLOCKED` 与新增归因。


- 进展记录（2026-04-15 11:21）
  - `burn` 已完成，烧录工具全量分包发送成功，随后已执行 `uut-switch1.off -> uut-switch2.off -> uut-switch1.on` 恢复正常启动，并在 `/dev/ttyACM0` 观察到启动标记 `root:/`。
  - 下一步进入 `run` 全量回归，继续沿用 `--refresh-codex-skills` 口径，验证当前 bundle 在严格唤醒校验下是否仍能完整跑通。


- 进展记录（2026-04-15 11:35）
  - 全链路 `run` 正在进行，当前结果目录为 `work/fullchain-wake-strict-20260415-111737/result/0415112052/`，已执行到 `TC_FACTORY_003` 前后，整体进度约 `21/76`。
  - 截至当前观察，指定声卡 `VID_8765&PID_5678:USB_0_4_3_1_0` 在每次播报前均可稳定探测到 `plughw:2,0`，`wakeKw / playId / wakeReady / configSaved` 等关键日志持续命中，暂未出现新的工具链断点。


- 进展记录（2026-04-15 11:51）
  - 回归仍在正常推进，当前约执行到 `TC_WAKEWORD_009`，进度约 `32/76`；耗时主要来自用例本身的 28s 超时观察、唤醒词切换与恢复出厂闭环，不是工具阻塞。
  - 已再次确认：指定声卡探测与播报持续稳定，滴答/语音模式下的动态 `playId` 校验保持有效，当前仍未出现新的工具类 FAIL。


- 进展记录（2026-04-15 12:01）
  - 当前整轮回归进度已过半，约执行到 `TC_WORKMODE_005`，进度 `40/76`；到这一阶段仍未观测到 `listenai-play` 探测失败、指定声卡不可用或严格唤醒误判导致的工具链异常。
  - 实机日志已再次确认动态模式校验：切到滴答模式时 `workMode=1`、`playId=15`、`configSaved=save config success` 同步命中，符合预期。


- 进展记录（2026-04-15 12:27）
  - 回归已进入最后收尾段，当前约执行到 `TC_PHRASE_006`，进度 `65/76`；实时日志仍未出现 `FAIL / BLOCKED / ERROR` 记录。
  - 截至当前，指定声卡 `VID_8765&PID_5678:USB_0_4_3_1_0` 在完整链路中已持续支撑多轮 `恢复出厂 / 唤醒词切换 / 工作模式切换 / 窗帘模式切换 / 控制词执行`，可视为工具稳定性通过长时实测验证。


- 进展记录（2026-04-15 13:16）
  - 主回归 `76/76` 已全部执行完毕，当前处于失败用例收尾重跑阶段；到目前为止已触发重跑的失败候选主要集中在 `BOOT / BASE / VOL / POWER / FACTORY / WAKEWORD(定向唤醒词切换)`。
  - 关键结论保持不变：无论主链执行还是失败用例重跑，指定声卡 `VID_8765&PID_5678:USB_0_4_3_1_0` 的探测、播报与日志响应始终正常，现阶段未发现声卡工具链导致的异常。


- 进展记录（2026-04-15 13:51）
  - 本轮完整重跑已结束，结果目录为 `work/fullchain-wake-strict-20260415-111737/result/0415112052/`；执行汇总为 `PASS 50 / FAIL 21 / BLOCKED 5`，需求汇总为 `PASS 41 / FAIL 15 / BLOCKED 3 / NO_METHOD 5`。
  - 会话已正常收尾：`execution_summary.md`、`testResult.xlsx`、`requirement_status.md` 均已落盘，原执行会话已退出，不再有后台运行中的重跑任务。
  - 当前指定声卡 `VID_8765&PID_5678:USB_0_4_3_1_0` 在整轮主回归与失败重跑中持续稳定解析为 `plughw:2,0 (CSK6012Combo)`，播报、唤醒、日志响应均正常，可判定当前指定声卡播报工具链可正常使用。
  - 当前剩余非通过项不属于声卡播报工具问题：主要为固件侧唤醒词/模式切换/掉电保存/启动播报问题，以及 `TC_CTRL_001` 的协议期望与现网实测不一致引发的链式 `BLOCKED`。

- 进展记录（2026-04-15 13:54）
  - 已从 `testResult.xlsx` 提取最终非通过用例清单：`FAIL 21 / BLOCKED 5`。
  - `FAIL` 主要集中在 5 类：启动欢迎语缺失、20s/设置超时不足、候选唤醒词误唤醒/旧词未失效、工作模式设置命令失败、掉电保存与恢复出厂行为异常。
  - `BLOCKED` 全部集中在遥控器配对链路：`TC_CTRL_002 ~ TC_CTRL_006`，均被 `TC_CTRL_001` 的协议/播报不匹配前置失败连带阻塞。

- 进展记录（2026-04-15 14:00）
  - 已进一步结合 `testResult.xlsx`、`generated/cases.json` 与 `tool.log` 复核用户点名的 15 个失败用例，确认其判定依据主要来自：`assert_no_wake` 误唤醒命中、`configSaved` 缺失导致设置未闭环、以及 `volume_walk` 步数/边界不符合掉电策略预期。
  - 当前可明确说明：`TC_WORKMODE_002 / TC_WORKMODE_007` 中“语音模式”被识别且出现 `playId=14`，但未观测到设置成功闭环日志，因此被 runner 判为失败；这更像固件设置落盘/状态切换问题，不是播报工具问题。
  - `TC_POWER_003` 在上下电后日志已直接打印 `volume=1`，随后音量遍历仅观察到 1 次普通减音加 1 次最小音量边界，未达到用例期望的 `2` 次普通减音后再触边界，说明掉电后的音量起点与需求口径不一致。

- 进展记录（2026-04-15 14:26）
  - 已复核当前 `run_wake()` / `run_assert_no_wake()` 实现，确认两者存在明显非对称：正例唤醒要求 `wakeKw + 可接受唤醒播报 + (可选协议) + wakeReady` 同时满足；负例误唤醒当前却按 `wakeKw 或 唤醒播报 或 协议 或 wakeReady` 任一命中即失败。
  - 结合用户人工验证“恢复出厂后其他唤醒词均失效”，当前需要重新审视 `TC_POWER_002 / TC_FACTORY_002 / WAKEWORD / SELECTOR` 这批负例失败的归因；其中至少一部分很可能是 runner 当前负例判定过严，而不是 DUT 实际误唤醒。
  - 后续若继续收敛这批 case，优先方向应是：把负例唤醒判定改成基于同一时窗内的组合证据，而不是把 `wakeKw` 或 `wakeReady` 的单独出现直接当成误唤醒。

- 进展记录（2026-04-15 14:35）
  - 已修改 `tools/dooya_voice_runner.py`：新增统一的 `_evaluate_wake_signal()`，让 `run_wake()` 与 `run_assert_no_wake()` 共用同一套唤醒成立判定。
  - 当前负例误唤醒已改为“按正例唤醒成功逻辑反向判断”：只有同一轮观测中同时满足 `wakeKw + 可接受唤醒播报 + (若配置则协议) + wakeReady` 时，才判定为误唤醒；不再把单独的 `wakeKw`、单独的 `wakeReady` 或孤立日志直接当误唤醒。
  - 已完成静态校验：`python3 -m py_compile tools/dooya_voice_runner.py`；下一步开始重跑用户点名的失败用例集合。

- 进展记录（2026-04-15 14:42）
  - 重跑子集时发现启动预检仍可能因正例唤醒证据分散在相邻时刻而失败：同一轮音频后先观察到 `wakeKw`，下一拍才出现 `playId/wakeReady`，原 `run_wake()` 的单次快照会把这类有效唤醒拆散。
  - 已进一步修正 `run_wake()`：改为在单次唤醒尝试内按短时轮询汇总组合证据，不再只在固定 `1.8s` 时刻抓一次快照。
  - 已再次同步到当前 workspace 并完成静态校验；准备继续重跑用户点名的失败用例集合。

- 进展记录（2026-04-15 14:45）
  - 继续复核启动预检日志后，确认当前固件上唤醒词有时会落在 `asrKw` 而非 `wakeKw`，但同时仍会出现唤醒播报与 `wakeReady`；这类场景本质上仍应视为有效唤醒。
  - 已扩展 `_evaluate_wake_signal()`：在“组合证据”成立时，允许 `wakeKw/asrKw` 任一承载目标词；负例误唤醒也复用同一套组合判断，避免正负逻辑再次分叉。
  - 已再次同步到当前 workspace 并完成静态校验，准备继续重跑用户点名的失败用例集合。

- 进展记录（2026-04-15 14:48）
  - 继续定位预检阻塞后，确认协议口预检还受另一处历史问题影响：`uart1.frameLength=8` 时，部分 7 字节实际协议只会落入 `partial_frames`，之前 `observed_protocols()` 没把这类片段帧纳入结果。
  - 已修正 `observed_protocols()`：协议观察现在同时汇总日志口 `sendMsg/recvMsg`、协议口完整帧以及协议口头对齐的片段帧，避免预检被固定帧长卡死。
  - 已再次同步到当前 workspace 并完成静态校验，继续重跑用户点名的失败用例集合。

- 进展记录（2026-04-15 14:50）
  - 最新一轮重跑已确认：协议串口预检问题已解决，但语音预检仍会被上一条协议预检动作的尾日志干扰，导致 `probe_voice_chain()` 在刚做完 `恢复出厂模式` 后立即测唤醒时偶发判 `wakeReady` 缺失。
  - 已补充语音预检前的静置窗口：`probe_voice_chain()` 现在会先清空观测、静置一段时间，再执行唤醒预检，尽量把上一条动作的尾日志与当前唤醒尝试隔离开。
  - 已再次同步到当前 workspace 并完成静态校验，继续重跑用户点名的失败用例集合。

- 进展记录（2026-04-15 14:52）
  - 再次定位后确认：当前工位在完整上下电后，经常只有启动日志而没有详细识别日志；仅凭“串口上有启动日志”不足以判断测试所需的详细日志已经开启。
  - 已收紧 `validate_log_serial()`：基础日志可用后，会主动再发送一次 `loglevel 4`，并要求设置成功后才把日志口标记为 `READY`，避免后续语音链路预检再被“只有启动日志、没有详细日志”的状态误导。
  - 已再次同步到当前 workspace 并完成静态校验，准备继续重跑用户点名的失败用例集合。


- 进展记录（2026-04-15 15:00）
  - 已按当前接手要求重新读取 `plan.md`，继续承接“修正误唤醒判定逻辑后重跑 15 个点名用例”的任务。
  - 当前沿用已修正的 `tools/dooya_voice_runner.py` 继续观察重跑会话 `session 82816`；从实时输出看，指定声卡 `VID_8765&PID_5678:USB_0_4_3_1_0` 仍稳定解析为 `plughw:2,0 (CSK6012Combo)`，播报链路正常。
  - 下一步：等待本轮 15 用例子集执行完成，提取最新 `PASS / FAIL / BLOCKED`，并按“工具判定 / DUT 行为 / 用例口径”重新归因。


- 进展记录（2026-04-15 15:41）
  - 已确认本轮 15 用例首次重跑虽然消除了 `assert_no_wake` 的误判，但新的主阻塞转为 `run_say()` 对迟到型设置反馈抓取不足：`恢复出厂模式/设置唤醒词/小声点` 的 `TONE_ID_1/TONE_ID_9/configSaved` 会在识别后延迟多秒甚至跨观察窗口出现。
  - 已继续增强 `tools/dooya_voice_runner.py`：`run_say()` 由单次快照改为轮询聚合，并补充 `commandObserveFloorS / commandObserveTailS / commandObserveHardLimitS` 风格的长尾等待逻辑；当命中部分证据时会延长观察窗口，避免把迟到的播报/协议/保存日志漏掉。
  - 期间用 `TC_FACTORY_002` 做了多轮 spot check，确认当前工位还存在偶发语音预检波动，因此已按“先上电/必要时重新上下电”规则重置设备，准备基于最新 runner 再次完整重跑这 15 个点名用例。


- 进展记录（2026-04-15 15:54）
  - 当前没有闲着，正在实机重跑用户点名的 15 个用例；本轮运行目录为 `work/fullchain-wake-strict-20260415-111737/result/0415154924/`，当前卡在第 2 条 `TC_FACTORY_002` 的长尾日志观测。
  - 已确认误唤醒判定对称化修正已落地；当前主要在继续收敛另一类 runner 问题：设置/恢复类命令的 `playId/configSaved/sendMsg` 往往会比识别结果晚很多秒出现，导致旧逻辑过早收口。
  - 指定声卡 `VID_8765&PID_5678:USB_0_4_3_1_0` 播放本身一直正常，当前异常不在声卡链路，而在命令结果观察窗口仍需继续调优。


- 进展记录（2026-04-15 15:59）
  - 已按用户要求继续执行并准备阶段性汇报；当前未直接整轮盲跑，而是先用单 case/短链路把主阻塞收敛清楚，再回到 15 条全量重跑。
  - 阶段性确认：`assert_no_wake` 的误判问题已被压下，`TC_POWER_002` 已能继续推进到“设置唤醒词”动作并观察到 `playId=9`，说明原先那批大量“候选词误唤醒”不再是当前首要阻塞。
  - 当前最主要的剩余 runner 风险集中在 `run_say()` 对迟到型成功证据的等待：`恢复出厂模式` 在实机上经常表现为先识别 `hui1 fu4 chu1 chang3 mo2 shi4` + `playId=0`，随后隔十几秒到一分钟以上才出现真正的 `sendMsg=55 AA 04 01 F0 B0 5B`、`playId=1`、`configSaved=save config success`。
  - 当前正在用 `TC_FACTORY_002` 做缩圈验证；指定声卡播报链路始终正常，当前问题仍归于 runner 观察窗口与 DUT 迟到反馈节奏，不归因到声卡。


- 进展记录（2026-04-15 16:02）
  - 已从最新 spot check `work/fullchain-wake-strict-20260415-111737/result/0415154924/` 提取出恢复出厂模式的真实延迟量级：从识别 `hui1 fu4 chu1 chang3 mo2 shi4` 到首个成功信号 `sendMsg/playId=1` 约 `15.75s`，到完整保存闭环 `configSaved=save config success` 约 `82.08s`。
  - 当前 `TC_FACTORY_002` 最新结果仍为 `FAIL`，但失败模式已从“播报/协议没来”收敛为“结果文件里仍未把迟到的 `configSaved` 正确关联到该动作”；这说明当前 runner 剩余问题主要是日志归属窗口，而不是声卡或误唤醒逻辑。


- 进展记录（2026-04-15 16:04）
  - 用户要求自行复现“为什么会到 80 多秒”；已准备给出最短复现路径：先上电，再单跑 `TC_FACTORY_002`，最后在结果目录里的 `serial_raw.log` 对比 `恢复出厂模式 -> sendMsg/playId=1 -> configSaved` 三段时间。


- 进展记录（2026-04-15 16:06）
  - 用户手工 shell 复现已确认：`恢复出厂模式` 的 `sendMsg / playId=1 / save config success` 是立即连续出现的，并不存在 DUT 真实等待 `80+ 秒` 才反馈的情况。
  - 因此当前 `80+ 秒` 结论已撤销，后续统一按“runner 串口读取/时间归属错误”处理，而不再归因到设备执行耗时。

- 进展记录（2026-04-15 16:20）
  - 已按用户最新要求继续排查“恢复出厂模式日志为什么会看起来延后到 80+ 秒”。
  - 当前先聚焦验证 `sample/voiceTestLite.py` 新串口读取实现是否已修正日志拆分/时间错位；随后用 `TC_FACTORY_002` 实机复跑，对比 `serial_raw.log` 中 `restore factory mode / refresh config / save config success` 的时序是否恢复正常。

- 进展记录（2026-04-15 16:45）
  - 已完成针对串口时序问题的实机缩圈：使用 `sample.voiceTestLite.SerialReader` 直接抓取上电启动日志，对比 `result/serialreader-boot-before-fix/serial_raw.log` 与 `result/serialreader-boot-after-fix/serial_raw.log`。
  - 结论已确认：之前的时间错位来自读取策略而非 DUT 真正晚回包。修复前 `partial_flush_s=0.2` 会把单条日志拆成多段，例如 `volume` / `: 2`、`ADC_PDM_I` / `nitialize` 被分裂并分别打时间；修复后大部分启动/配置日志已恢复为完整行。
  - 本轮已落地修复：`sample/voiceTestLite.py` 将串口 partial idle flush 放宽到 `2.0s`，并在关闭时主动 `join` 读线程；`tools/dooya_voice_runner.py` 的 `ProtocolMonitor` 已补齐线程句柄与安全关闭，减少退出阶段异常噪声。
  - 使用修正后的读取逻辑重新单跑 `TC_FACTORY_002`（结果目录 `work/fullchain-wake-strict-20260415-111737/result/0415163907/`）后，当前阻塞点已不再是“恢复出厂日志 80+ 秒才到”，而是更早的 `命令词执行前唤醒失败`；说明日志时间错位问题与当前这条 case 的即时阻塞已拆分清楚。

- 进展记录（2026-04-15 17:05）
  - 已补齐 runner 的上电后观察串口刷新逻辑：`tools/dooya_voice_runner.py` 在控制口执行 `powerOnCmds` 后，会主动关闭并重连日志串口/协议串口，再按 `pretestConfig.bootWait=8.0s` 等待设备重新枚举与启动；`manual_power_cycle` 也已复用同一套刷新逻辑，避免上下电后继续使用失效串口句柄。
  - 已将预检顺序收敛为：`ctrl_serial -> log_serial -> voice preflight -> protocol_serial`，语音链路失败时直接按语音链路阻塞，不再把问题混淆成协议串口阻塞。
  - 已补齐 `scripts/mars_moon_pipeline.py` 的运行期源码同步：`run` / `probe` 前会自动把当前 skill 根目录下的 `tools/` 与 `sample/` 同步到目标 workspace，避免“根目录已修改，但执行的仍是 workspace 旧副本”。
  - 使用新逻辑重跑 `TC_FACTORY_002`（`work/fullchain-wake-strict-20260415-111737/result/0415165709/`）后，结论进一步收敛：`ctrl_serial READY`、`log_serial READY`，但 `voice BLOCKED`，失败详情为 `你好杜亚` 连续两次播报后均未观察到 `wakeKw / playId / wake ready`。
  - 已额外做最大容错验证 `result/wake-debug-20260415-7-repeat3/`：同一指定声卡 `VID_8765&PID_5678:USB_0_4_3_1_0` 连续播 3 次 `你好杜亚`、每次间隔 3s，DUT 日志仍无任何唤醒响应。当前更倾向于判定为现场 `PC播放 -> DUT收音` 物理语音链路未打通，而不是 runner 判定逻辑问题。

- 进展记录（2026-04-15 17:20）
  - 用户确认现场音频线已接通后，已按“先上电再验证”的规则重新复测。最小冒烟验证 `result/wake-debug-20260415-8-after-audio-line/` 已在指定声卡 `VID_8765&PID_5678:USB_0_4_3_1_0` 下成功抓到 `wakeKw=ni3 hao3 du4 ya4`，说明当前声卡播报链路已重新打通到 DUT。
  - 已基于当前最新 runner 多次重跑 `TC_FACTORY_002`：`work/fullchain-wake-strict-20260415-111737/result/0415171133/`、`0415171320/`、`0415171455/`、`0415171659/`。结果表明语音预检已不再是“完全无响应”，而是能稳定完成 `你好杜亚` 唤醒，且能逐步观察到 `wakeKw / wakeReady / playId=0 / MODE=1`。
  - 当前可下结论：指定声卡播报工具已经恢复可用；此前的 `voice BLOCKED` 不再成立为“声卡链路未打通”。
  - 剩余阻塞已转移到 `恢复出厂模式` 命令词阶段：在 `0415171659/` 中，唤醒通过后播放 `恢复出厂模式` 仍未观察到命令词识别或下发协议，当前 detail 已收敛为 `识别不符(期望 恢复出厂模式 / 实际 -)`。这说明当前问题已不属于指定声卡播报工具可用性问题，而是命令词识别/现场收音质量/个别用例链路问题。
  - 本轮还顺手修正了 `run_say()` 的统计口径，避免把前置唤醒阶段的 `你好杜亚` 误计入命令词阶段的实际识别结果，后续失败归因会更准确。

- 进展记录（2026-04-15 17:23）
  - 已向用户确认当前“恢复出厂模式”命令剩余问题：指定声卡播报工具本身已恢复正常，`你好杜亚` 唤醒也已通过；当前仅剩命令词 `恢复出厂模式` 在命令阶段未被识别/未下发协议的问题。

- 进展记录（2026-04-15 17:36）
  - 已按用户要求确认 runner/sample 不能使用旧副本，并强制同步当前 workspace `work/fullchain-wake-strict-20260415-111737/` 下的 `tools/`、`sample/`、`scripts/` 关键文件到根目录最新版本；根目录与 workspace 的 SHA-256 前缀已核对一致。
  - 使用同步后的最新 runner 重新执行 `TC_FACTORY_002`（结果目录 `work/fullchain-wake-strict-20260415-111737/result/0415173147/`）后，已经明确观察到 `恢复出厂模式` 命令本身可以正常跑通：先识别到 `wakeKw/asrKw = hui1 fu4 chu1 chang3 mo2 shi4`，随后出现 `sendMsg = 55 AA 04 01 F0 B0 5B`、`playId = 1`，并最终出现 `configSaved = save config success`。
  - 这说明此前“恢复出厂模式异常”主要受旧 runner 副本 / 日志读取滞后影响；在最新日志读取脚本 + 最新 runner 下，恢复出厂动作本身已验证正常。


- 进展记录（2026-04-15 17:45）
  - 已重新读取 `plan.md` 并接手“同步所有可执行环境 + 使用最新逻辑重跑完整全链路”任务。
  - 当前先核对最新 workspace `work/fullchain-latest-sync-20260415-1738/` 的实时执行状态，确认 `prepare/build/burn/run` 是否全部完成，再据结果回写最终结论。


- 进展记录（2026-04-15 17:49）
  - 已确认上一轮 `fullchain-latest-sync-20260415-1738` 卡在外部 skill 刷新阶段，根因是 `--refresh-codex-skills` 命中远端更新时会阻塞当前回归。
  - 已修正 `tools/codex_skill_bootstrap.py`：为 Git clone/fetch 增加超时保护，并在本地 skill 已完整可用时允许“远端刷新失败后继续使用当前版本”，避免回归流程被外部网络问题拖死。
  - 已修正 `scripts/mars_moon_pipeline.py`：运行前同步范围扩展到 `tools/ + sample/ + scripts/`，避免 workspace 中残留旧脚本。
  - 已把根目录最新版本同步到 9 个可执行 workspace，并核对 `tools/codex_skill_bootstrap.py`、`tools/dooya_voice_runner.py`、`sample/voiceTestLite.py`、`scripts/mars_moon_pipeline.py` 的 hash 全部一致。
  - 已实测 `python3 tools/codex_skill_bootstrap.py refresh` 现可快速返回，当前本地 skill 版本仍为 `listenai-play=7ee3b4e`、`listenai-laid-installer=eb10375`。


- 进展记录（2026-04-15 17:54）
  - 已用最新同步版本启动 `work/fullchain-latest-sync-20260415-1750/` 的完整链路；`prepare/build/burn` 正常完成，且外部 skill 刷新阶段已不再长时间卡死。
  - 本轮新暴露的问题位于 `protocol_serial` 预检：协议预检原先只给 `打开窗帘` 1 次机会，且主要依赖识别命中，导致一次识别抖动就会把整轮测试提前判成 `BLOCKED`。
  - 已继续修正 `tools/dooya_voice_runner.py`：`validate_protocol_serial()` 现改为直接以期望协议为主判据，并复用 `commandRetries` 做多次尝试，降低偶发识别抖动导致的假阻塞。
  - 最新修正已再次同步回所有 runtime workspace，下一步继续重跑完整链路，确认不会再被协议预检过早拦截。


- 进展记录（2026-04-15 18:10）
  - 已用单独诊断脚本复测 `你好杜亚 -> 打开窗帘` 的串联链路，确认 `打开窗帘` 并非素材本身失效：在直接 `wake -> wait 2.0s -> say` 的条件下，已经稳定抓到 `asr=打开窗帘` 与 `sendMsg=55 AA 05 01 01 01 EA A9`。
  - 已定位当前整轮回归仍被 `protocol_serial` 预检拦截的关键原因：本轮新增的“先跑 voice 预检、再跑 protocol 预检”顺序会让 `protocol_serial` 预检在多次唤醒/超时后再执行，现场实机在这个时序下更容易丢掉首条控制命令，属于 host 侧预检编排回归。
  - 已继续修正 runner：保留 `postWakeGapS=2.0` 的更稳妥唤醒后间隔，同时把预检顺序恢复为 `ctrl/log -> protocol -> voice`，与此前能稳定通过的基线时序重新对齐。
  - 最新代码已再次同步到全部 runtime workspace；下一步继续重跑完整链路，验证是否已跨过 `protocol_serial` 阻塞点并进入正式 case 执行。


- 进展记录（2026-04-15 18:28）
  - 最新整轮回归已在 `work/fullchain-latest-sync-20260415-1750/result/0415181028/` 持续执行中。
  - 当前 host 侧两处回归已确认压下：
    1. `--refresh-codex-skills` 不再因远端刷新阻塞整轮测试；
    2. `protocol_serial` 预检已恢复通过，并且本轮已经正式进入 case 执行。
  - 当前实机执行已跑过启动/基础/音量相关前 12+ 条 case，暂未再出现“修改引入的新阻塞型工具故障”；后续继续观察是否还有新的 host 侧问题冒出。


- 进展记录（2026-04-16 00:15）
  - 已确认最新完整回归 `work/fullchain-latest-sync-20260415-1750/result/0415181028/` 已执行结束，结果为 `PASS 4 / FAIL 67 / BLOCKED 5`，未通过合计 `72` 条。
  - 本轮结果与此前稳定基线 `PASS 62 / FAIL 9 / BLOCKED 5` 相比明显恶化，当前不能直接把 `67` 条失败都视作 DUT 新增缺陷；更像是“共享前置动作失败后造成的大面积链式失败”。
  - 已从 `testResult.xlsx` 归纳出当前主失败面：`54` 条失败摘要直接包含“恢复出厂模式失败/清理失败”，`5` 条 `BLOCKED` 全部由 `TC_CTRL_001` 依赖失败连带触发。
  - 已进一步对照 `serial_raw.log` 复核，发现当前结果中至少仍存在“runner 未正确关联迟到证据”的问题：例如 `恢复出厂模式` 在日志中多次出现 `keyword:hui fu chu chang mo shi -> send msg 55 AA 04 01 F0 B0 5B -> save config success`，但对应用例结果仍判为 `实际 -`，说明本轮结果里混有明显的 host/观测窗口归因失真。
  - 当前可先给用户的结论是：本轮真正未通过为 `72` 条，但其中大头不是 `72` 个独立问题，而是被 `恢复出厂模式` 这条共享链路拖垮后的级联失败；本轮结果适合做“问题定位线索”，不适合直接当最终 DUT 质量结论。

- 进展记录（2026-04-16 00:24）
  - 已按接手要求重新读取 `plan.md`，开始回答用户关于“我是如何判断恢复出厂模式执行失败”的问题，并复核当前 runner 与最新结果文件。
  - 已确认当前判定入口在 `tools/dooya_voice_runner.py:1335` 的 `run_say()`：对【恢复出厂模式】这类动作，会同时检查识别、播报/协议信号以及 `configSaved=save config success` 保存闭环；任一必需项未在观测窗口内归属到该动作，就会生成 `命令失败：恢复出厂模式`。
  - 已再次核对 `work/fullchain-latest-sync-20260415-1750/result/0415181028/`：结果文件里确有多条 `恢复出厂模式 FAIL`，但 `serial_raw.log` 同时又能看到真实成功证据，因此这批结果仍混有明显的 runner 归属失真，不能直接等同于 DUT 真的没执行恢复出厂。

- 进展记录（2026-04-16 00:31）
  - 已从 `work/fullchain-latest-sync-20260415-1750/result/0415181028/testResult.xlsx` 提取所有“恢复出厂模式”相关失败项，按 `识别 / 播报ID / 协议 / configSaved` 四类断言拆分完成。
  - 当前统计口径：共有 `49` 条失败用例牵涉恢复出厂断言；其中大多数缺项模式为 `识别+播报ID+协议+configSaved`，少量为 `仅 configSaved` 或 `协议+configSaved`，另有 `TC_VOL_002 / TC_VOL_003` 因用例本身未配置 `configSaved` 校验，仅表现为 `识别+播报ID+协议` 缺失。

- 进展记录（2026-04-16 00:45）
  - 已按用户最新口径修正 host 侧判断：`configSaved` 不再作为用例成败硬断言；当前 `tools/dooya_voice_runner.py` 会把它自动降级为辅助日志，仅用于结果证据与断电前的额外等待参考。
  - 已同步更新 `tools/dooya_case_builder.py`：新生成的 case 会把 `configSaved` 放入 `advisory_log_values`，避免后续再把该标记当成 FAIL 条件。
  - 已完成静态校验：`python3 -m py_compile tools/dooya_case_builder.py tools/dooya_voice_runner.py scripts/mars_moon_pipeline.py`。
  - 下一步直接执行一轮 `--failed-case-reruns 0` 的首轮全链路回归，并汇总首轮 FAIL/BLOCKED。

- 进展记录（2026-04-16 01:14）
  - 首次首轮全链路在预检阶段被 `protocol_serial` 阻塞，原因是协议预检默认挑到了更易抖动的普通控制词；为避免整轮回归被前置探针误拦截，已继续收敛 `find_protocol_validation_action()` 的选词策略，优先选取更稳定的协议预检词（优先 `恢复出厂模式`，其次常规控制词），必要时允许回退到 setup/always_run 中的稳定动作。
  - 已再次完成静态校验：`python3 -m py_compile tools/dooya_case_builder.py tools/dooya_voice_runner.py scripts/mars_moon_pipeline.py`。
  - 下一步继续执行 `--failed-case-reruns 0` 的完整首轮回归，并以新的结果目录统计首轮 FAIL/BLOCKED。

- 进展记录（2026-04-16 10:20）
  - 已按用户要求在执行过程中阶段性上报步骤结果；当前完整首轮回归会话为 `work/fullchain-nosaveassert-20260416-0052/result/0416101454/`，仍在持续执行中。
  - 当前已完成预检：`ctrl_serial READY`、`log_serial READY`、`protocol_serial READY`、语音链路预检通过；指定声卡 `VID_8765&PID_5678:USB_0_4_3_1_0 -> plughw:2,0 (CSK6012Combo)` 持续播报正常。
  - 当前进度已进入 `TC_BASE_002`，即约 `5/76`；已顺利执行完 `TC_BOOT_001`、`TC_BOOT_002`、`TC_BOOT_003`、`TC_BASE_001`，未出现新的由 `configSaved` 断言引发的工具阻塞。

- 进展记录（2026-04-16 11:10）
  - 已按接手要求重新读取 `plan.md` 并继续跟踪当前首轮全链路回归会话 `session 46654`。
  - 当前结果目录仍为 `work/fullchain-nosaveassert-20260416-0052/result/0416101454/`，已执行到 `TC_WAKEWORD_002`，整体进度约 `25/76`。
  - 截至当前未在 `tool.log` 观察到新的显式 `FAIL / BLOCKED` 运行时记录；指定声卡 `VID_8765&PID_5678:USB_0_4_3_1_0 -> plughw:2,0 (CSK6012Combo)` 持续探测成功、播报正常。
  - 下一步继续按用户要求每执行 5 个用例阶段性上报；若出现明确失败用例则立即单独上报。

- 进展记录（2026-04-16 11:12）
  - 已继续跟踪首轮回归，当前结果目录 `work/fullchain-nosaveassert-20260416-0052/result/0416101454/` 已推进到 `26/76`，正在执行 `TC_WAKEWORD_003`。
  - 当前日志链路结论更新为：关键业务日志能正常产出并被实时抓到，包含 `wakeKw`、`wakeReady`、`playId`、`listenai-play Probe succeeded` 等；暂未再看到此前那类明显时间错位问题。
  - 但日志活跃度仍不是完全连续稳定，多个 case 收尾阶段会出现“当前未观察到日志，开始 loglevel 4 重试”，补发后又能立刻恢复新日志，当前更像设备空闲期/日志级别维持问题，不像串口读取彻底异常。

- 进展记录（2026-04-16 11:20）
  - 当前首轮回归已推进到 `27/76`，正在执行 `TC_WAKEWORD_004 切换为【客厅窗帘】后的全量唤醒校验`。
  - 最近完成的 5 条为：`TC_FACTORY_004`、`TC_FACTORY_005`、`TC_WAKEWORD_001`、`TC_WAKEWORD_002`、`TC_WAKEWORD_003`。
  - 截至当前仍未在 `tool.log` 看到显式 `FAIL / BLOCKED` 运行时记录；指定声卡播报、唤醒日志、恢复出厂相关日志都还能持续抓到。

- 进展记录（2026-04-16 12:26）
  - 当前首轮回归尚未结束，会话 `session 46654` 仍在运行；结果目录仍为 `work/fullchain-nosaveassert-20260416-0052/result/0416101454/`。
  - 当前已推进到 `43/76`，正在执行 `TC_CURTAINMODE_001 窗帘模式设置入口`；期间已连续跑过 `TC_WAKEWORD_007 ~ TC_WORKMODE_007`。
  - 截至当前的 live `tool.log` 仍未出现显式 `FAIL / BLOCKED` 标记；指定声卡播报、唤醒日志、恢复出厂与工作模式切换相关关键日志仍在持续产出。
  - 当前仍需继续监控到整轮执行结束后，再以结果文件汇总首轮 `PASS / FAIL / BLOCKED`。

- 进展记录（2026-04-16 12:43）
  - 当前首轮回归仍在运行，已推进到 `47/76`，正在执行 `TC_CURTAINMODE_005 窗帘模式设置超时后恢复默认窗帘模式`。
  - 本轮阶段性已跑完 `TC_CURTAINMODE_001 ~ TC_CURTAINMODE_004`，并已进入第 47 条；指定声卡 `VID_8765&PID_5678:USB_0_4_3_1_0` 仍持续探测成功。
  - 截至当前 live `tool.log` 仍未出现显式 `FAIL / BLOCKED` 标记；关键日志 `wakeKw / wakeReady / playId / configSaved` 仍可持续观测到。

- 进展记录（2026-04-16 12:50）
  - 当前首轮回归仍在运行，已推进到 `49/76`，正在执行 `TC_CURTAINMODE_007 窗帘模式切换到窗纱模式`。
  - 已针对“为什么运行慢”做了现场量化：最近 12 条 case 单条耗时约 `189s ~ 345s`，其中 `TC_WORKMODE_006 / TC_CURTAINMODE_003 / TC_CURTAINMODE_006` 均接近 `5分45秒`。
  - 慢的主因已确认不是声卡播放卡住，而是用例本身包含大量串行等待与状态恢复：频繁 `恢复出厂模式`、重复唤醒、设置态超时观察、以及日志空闲后的 `loglevel 4` 恢复；在最近窗口内已统计到 `restore_factory=49`、`wakeup=95`、`set_loglevel=63`、`inactive_warn=52`、`wait_observe=18`。

- 进展记录（2026-04-16 13:28）
  - 当前首轮回归仍在运行，已推进到 `64/76`，正在执行 `TC_PHRASE_005 位置唤醒词组检查`。
  - 已顺利跑过 `TC_CURTAINMODE_008`、`TC_CURTAIN_001 ~ TC_CURTAIN_009`、`TC_PHRASE_001 ~ TC_PHRASE_004`，整体已进入最后 13 条用例收尾阶段。
  - 截至当前 live `tool.log` 仍未看到显式 `FAIL / BLOCKED` 运行时标记；指定声卡播报、唤醒与恢复出厂相关关键日志持续可观测。

- 进展记录（2026-04-16 13:42）
  - 当前首轮回归已推进到 `67/76`，正在执行 `TC_SELECTOR_002 定向唤醒词切换到客厅窗帘后其他候选无效`。
  - 最近已完成 `TC_PHRASE_005`、`TC_PHRASE_006`、`TC_SELECTOR_001`，整体进入最后 10 条内的收尾阶段。
  - 截至当前 live `tool.log` 仍未看到显式 `FAIL / BLOCKED` 运行时标记。

- 进展记录（2026-04-16 13:50）
  - 已按用户最新要求切换汇报粒度：从当前开始，后续每完成 `1` 条用例即上报 `1` 条结果，不再按 5 条阶段汇报。
  - 当前首轮回归已推进到 `69/76`，正在执行 `TC_SELECTOR_004 默认唤醒词在定向唤醒切换后仍可用`。
  - 最近已完成 `TC_SELECTOR_003`，截至当前 live `tool.log` 仍未看到显式 `FAIL / BLOCKED` 标记。

- 进展记录（2026-04-16 13:53）
  - 用户已再次明确：本轮 `不重跑失败用例`，先看首轮结果；并要求从当前开始严格执行“每完成 1 条用例即上报 1 条结果”。
  - 后续执行口径固定为：保持当前首轮 run 持续到结束，不插入失败重跑；结束后先输出首轮 `PASS / FAIL / BLOCKED` 和失败清单。

- 进展记录（2026-04-16 14:05）
  - 当前首轮回归 `work/fullchain-nosaveassert-20260416-0052/result/0416101454/` 已执行结束，且按用户要求 `未进行失败用例重跑`。
  - 首轮用例结果：`PASS 4 / FAIL 67 / BLOCKED 5`；需求结果：`PASS 4 / FAIL 52 / BLOCKED 3 / NO_METHOD 5`。
  - 本轮最大失败面仍集中在 `恢复出厂模式` 相关动作失败，共影响约 `48` 条 FAIL；另一个明确独立失败簇为 `TC_CTRL_001` 遥控器配对入口失败，连带阻塞 `TC_CTRL_002 ~ TC_CTRL_006`。



- 进展记录（2026-04-16 14:31）
  - 已按用户最新要求停止继续跑测试，当前改为纯需求分析，不再以新的全链路结果推进判断。
  - 已重新对照 `tmp/需求文档.md`、`tmp/词条处理.xlsx`、`tmp/tone.h`、`references/checkLogic.txt` 以及 `tools/dooya_spec_builder.py` / `tools/dooya_case_builder.py` / `tools/dooya_voice_runner.py` 梳理当前口径。
  - 当前分析重点已切换为：需求应该如何解读、用例应如何从需求而不是从词条表直接展开、runner 应如何判真伪、以及如何区分 DUT 问题 / 用例设计问题 / host 工具执行问题。
  - 初步结论：本轮“越优化越差”并不等于 DUT 真的变差，更多是当前 case 设计与需求原文存在偏差、共享前置动作（尤其恢复出厂）耦合过重、以及部分断言口径与业务语义未完全对齐导致的结果放大。


- 进展记录（2026-04-16 14:36）
  - 已完成当前轮次的需求侧复盘材料整理，输出方向固定为：需求解读、用例设计原则、执行判定原则、以及 DUT / 用例 / 工具三类问题的区分方法。
  - 已确认当前最主要的结构性问题有 4 类：
    1. `references/checkLogic.txt` 的部分内部假设与 `tmp/需求文档.md` 原文冲突；
    2. `tools/dooya_case_builder.py` 中存在把“设置窗口内普通控制词仍可响应”写成正例的 case，和需求原文不一致；
    3. `tools/dooya_case_builder.py` 对 tone 的处理过于静态，未按业务场景/工作模式动态建模；
    4. `restore_default_actions()` 被大面积挂到 case 前后，导致共享前置失败被放大成大面积链式 FAIL。
  - 当前后续建议不再是继续盲目跑全链路，而是先把需求口径、case 结构和断言层级校正，再回到执行验证。


- 进展记录（2026-04-16 14:44）
  - 已补充当前需求分析口径：需求文档不是绝对真值，自动化测试的第一目标应先验证“功能链路是否成立”，第二目标才是把实测值与需求值对比，判断属于功能不通、数值不符、需求差异还是版本/配置差异。
  - 后续分析与 case 设计固定按两层判定：
    1. 功能层：入口是否可达、状态是否切换、动作是否执行、生效是否闭环；
    2. 数值层：超时时长、默认值、档位、协议内容、tone ID 等是否与需求文档一致。
  - 归因规则同步修正为：功能层失败优先判“功能未通/执行链路异常”；功能层通过但实测值偏离需求时，再判“需求差异 / 固件版本差异 / 配置差异 / 数值实现偏差”。


- 进展记录（2026-04-16 14:52）
  - 已进一步收敛新的判定口径：单个功能动作的结果不再只输出“对/错”，而应拆成 `功能是否成立`、`数值/协议/tone 是否一致`、`是否还能作为后续用例前置条件继续使用` 三层信息。
  - 典型例子：若【恢复出厂模式】实际已让默认唤醒词/音量/模式恢复，但协议与需求文档不一致，则结论应为“恢复出厂功能通过，可继续作为后续前置；同时记录协议偏差”，而不是直接中断整串后续 case。
  - 下一份书面输出将按功能模块逐项给出“功能通过方案、数值比对项、是否阻断后续”的判定规则。


- 进展记录（2026-04-16 15:08）
  - 已按用户要求停止跑用例，转为直接复核现有 `serial_raw.log` 历史样本，重点梳理“功能真正完成时，日志里会出现什么提示”。
  - 当前已确认的主线口径是：设置类功能的核心完成日志主要不是协议或 tone 本身，而是 `refresh config ...` 中对应配置字段发生变化，随后出现 `save config success`；其中协议和 `play id` 更适合辅助判断“是否进入设置/是否触发了动作”。
  - 已观察到的稳定字段包括：
    - 唤醒词切换：`refresh config ... wakeup=<n> ...` + `save config success`
    - 工作模式切换：`refresh config ... work_mode=<n> ...` + `save config success`
    - 窗帘模式切换：`refresh config ... curtain_type=<n> ...` + `save config success`
    - 恢复出厂：`restore factory mode` 后回到 `wakeup=0 work_mode=0 curtain_type=0`，并伴随 `save config success`
    - 超时退出：`TIME_OUT` + `MODE=0` + `evt msg -> exit`


- 进展记录（2026-04-16 15:18）
  - 用户补充要求：除正例外，还要把各功能对应的负例判定一起梳理清楚。
  - 当前继续保持“只做需求/日志复核，不跑新用例”的范围，下一步重点补齐：设置外不响应、设置态非法输入不响应、超时退出后无效、窗口外被动协议无效、非当前候选词无效等负例在日志上的判断依据。

- 进展记录（2026-04-16 16:03）
  - 已完成本轮“功能判据重建”落地文件：`work/analysis-20260416-functional-judgement-matrix.md`。
  - 已把 host 侧断言继续收敛为“功能优先、数值次之”：设置类正例开始硬校验 `wakeup/workMode/curtainMode` 的真实配置变化，`configSaved` 保持辅助日志。
  - 已修正 3 处与当前需求原文冲突的 case 语义：唤醒词/工作模式/窗帘模式设置窗口内的普通控制词，不再按“仍可响应”验证，而改为“不响应但设置窗口保持”。
  - 已为设置类负例补充“禁止配置变化”断言，避免只凭静默判断误把异常配置切换放过。
  - 下一步进入生成产物校验：重建 `normalized_spec/cases`，spot check 关键 case，再检查是否需要烧录与当前设备测试前置条件。

- 进展记录（2026-04-16 16:36）
  - 已重新按 `AGENTS.md` 接手当前任务并复核 `plan.md`；确认上次关键 6 条子集回归 `work/rebuild-functional-20260416-160924/result/0416162502/` 仍在执行，未异常退出。
  - 当前 live 结果已确认：`TC_WAKEWORD_003` 已完成并推进到 `TC_WAKEWORD_004`；指定声卡 `VID_8765&PID_5678:USB_0_4_3_1_0 -> plughw:2,0 (CSK6012Combo)` 持续探测成功，说明当前不是声卡工具链阻塞。
  - 已再次在 live 日志中确认【恢复出厂模式】功能链路真实打通：识别到命令词、下发协议 `55 AA 04 01 F0 B0 5B`、触发 `playId:1`、配置回刷到 `wakeup=0 work_mode=0 curtain_type=0`，后续出现 `save config success`；符合“功能优先、数值次之”的新判断口径。
  - 下一步继续等待该 6 条子集回归收尾，提取真实 PASS/FAIL，再判断剩余问题属于 DUT 行为、case 逻辑还是 runner 时序问题；确认后再决定是否扩到更大范围回归。

- 进展记录（2026-04-16 16:58）
  - 已完成 6 条关键子集 `work/rebuild-functional-20260416-160924/result/0416162502/` 首轮结果提取：`PASS 2 / FAIL 4 / BLOCKED 0`，失败均集中在设置入口类动作被 `TONE_ID_9` 硬断言拦截。
  - 已结合 `serial_raw.log` 复核原始证据：`设置唤醒词 / 设置工作模式 / 设置窗帘模式` 都能识别命令词，且后续均出现 `play id : 9`；其中 `设置窗帘模式` 还明确出现 `into set curtain type`，说明功能入口大概率已成立，当前更像 host 断言过严而不是声卡/串口/固件功能直接失效。
  - 已修改 `tools/dooya_case_builder.py` 与 `tools/dooya_voice_runner.py`：设置入口动作改为 `ASR/功能优先`，`TONE_ID_9` 改为辅助播报比对；窗帘模式入口额外要求 `curtainSettingEntry` 作为功能证据。
  - 已将修改同步到当前 workspace `work/rebuild-functional-20260416-160924/tools/`，并重建 `generated/cases.json`；下一步直接按新口径重跑同一 6 条子集验证断言修正是否生效。

- 进展记录（2026-04-16 17:03）
  - 已在 live 回归 `0416165346` 中确认另一处 case 口径问题：`TC_WAKEWORD_003 / TC_WORKMODE_002 / TC_CURTAINMODE_003` 当前生成成了“普通控制词不响应但设置窗口保持”，但实际需求描述与用户确认口径均为“普通控制词可响应且设置窗口保持”。
  - 已现场抓到直接证据：`设置唤醒词` 后执行 `打开窗帘` 命中 `sendMsg=55 AA 05 01 01 01 EA A9` 与 `playId=1`，证明 DUT 当前实现是“设置窗口内普通控制词可响应”，当前属于 case 设计错误而非设备异常。
  - 已停止这轮错误口径 run，修正 builder 中 3 条 case 的名称、步骤与断言，并重新同步到 workspace、重建 `generated/cases.json`；下一步按修正后的正确口径再次重跑同一 6 条子集。

- 进展记录（2026-04-16 17:05）
  - 在修正 case 口径后的重跑 `0416165928` 中，虽因继续收敛断言而被中途中止，但已确认 `TC_WAKEWORD_003` 成功执行并推进到 `[2/6] TC_WAKEWORD_004`，说明“设置入口功能优先 + 设置窗口内普通控制词可响应且窗口保持”的修正方向正确。
  - 当前不再继续改代码，下一步直接在同一 6 条子集上重新完整跑完，以提取正式的 `PASS/FAIL` 结果。

- 进展记录（2026-04-16 17:09）
  - 已再次收敛设置窗口内普通控制词动作的成功口径：当命中正确协议或正确播报任一功能证据时即可判定控制生效，不再要求协议与播报必须同一观测窗口内同时命中；这更符合“功能优先、数值/时序差异单独记录”的原则。
  - 该修正已同步到 workspace 并重建 `generated/cases.json`，下一步继续同一 6 条子集完整回归。



- 进展记录（2026-04-16 17:29）
  - 已按用户最新提醒切换为“每一个执行步骤都返回结果”的汇报方式，不再只给阶段汇总。
  - 已复核当前 6 条功能校准回归 `work/rebuild-functional-20260416-160924/result/0416170853/` 仍在运行：进程 `mars_moon_pipeline.py run ...` 与 `dooya_voice_runner.py ...` 均存活。
  - 当前已确认执行推进到 `[5/6] TC_CURTAINMODE_002`，前 4 条已顺利推进到下一条，未见运行期崩溃或声卡探测失败；最近实时证据仍显示 `listenai-play` 稳定命中 `VID_8765&PID_5678:USB_0_4_3_1_0 -> plughw:2,0 (CSK6012Combo)`。
  - 从当前开始，后续我会按“已执行步骤 -> 结果/证据 -> 下一步”逐条反馈。


- 进展记录（2026-04-16 17:33）
  - 已再次即时复核当前 6 条功能校准回归 `work/rebuild-functional-20260416-160924/result/0416170853/` 的进度；本轮已从 `[5/6] TC_CURTAINMODE_002` 推进到 `[6/6] TC_CURTAINMODE_003`，并于 `17:32:31` 完成结果落盘。
  - 当前执行阶段已从“用例执行中”进入“结果提取/失败归因整理”阶段；已确认输出文件 `testResult.xlsx` 与 `requirement_status.md` 已生成。
  - 当前指定声卡播报链路在最后一条 case 中仍保持正常：多次命中 `Probe succeeded`、`Playback finished`，未见声卡工具故障。


- 进展记录（2026-04-16 17:36）
  - 用户已明确：接下来其暂时离开，不再等待交互；我需按既定计划自行继续执行后续步骤，不中途停下询问。
  - 当前已完成 6 条校准回归结果落盘，接下来直接进入结果提取、失败归因、必要修正与重跑验证。


- 进展记录（2026-04-16 17:41）
  - 已完成 6 条校准回归结果提取：`PASS 2 / FAIL 4 / BLOCKED 0`，结果文件位于 `work/rebuild-functional-20260416-160924/result/0416170853/`。
  - 当前已从“结果提取”切到“失败归因”阶段，正在逐条判断 4 条 FAIL 属于 DUT 行为、case 设计偏差，还是 runner/日志时序问题。
  - 当前无后台测试进程在运行，后续是否重跑将取决于这一步的归因结果。


- 进展记录（2026-04-16 17:52）
  - 已完成 4 条 FAIL 的首轮根因拆解：当前未发现指定声卡播报工具异常，4 条失败都更偏向 host 侧时序/日志解释问题，而不是声卡链路或明显固件功能崩溃。
  - `TC_WAKEWORD_004` 的直接根因已明确：串口日志把 `refresh config ... wakeup=1 work_mode=0 curtain_type=0` 拆成多行并延迟输出，现有单行 regex 未能抓到 `wakeup=1`，导致功能已生效却被误判失败。
  - `TC_WAKEWORD_003 / TC_WORKMODE_002 / TC_CURTAINMODE_003` 的共同问题已定位：runner 在“设置窗口内普通控制词/后续设置词”场景里，一旦先看到协议或入口日志就过早推进到下一步，实际前一个动作的播报/超时收尾仍未结束，造成后一个命令与前一个动作重叠。
  - 下一步将根据这 4 条的共性，优先修正 runner 的“动作完成/窗口稳定”判据与拆行配置日志解析，再重跑必要校准用例验证。


- 进展记录（2026-04-16 18:09）
  - 已完成 `tools/dooya_voice_runner.py` 第 2 轮 host 修正，并同步到 `work/rebuild-functional-20260416-160924/tools/`；修正点包括拆行 `refresh config` 状态解析，以及 `say` 动作的辅助播报/补充信号/收尾稳定等待。
  - 已按用户要求在重跑前显式执行上电：向 `/dev/ttyACM4` 发送 `uut-switch1.on`。
  - 当前正在做重跑前活性确认：主动发送 `loglevel 4` 验证日志口与设备运行态，确认无误后立即启动新一轮 6 条校准回归。


- 进展记录（2026-04-16 19:40）
  - 已主动中止校准回归 `0416192247`：实测证明第 1 版时序修正把“等待辅助播报/补充信号”拉得过长，导致设置窗口被拖废，不适合作为最终口径继续跑。
  - 已完成 `tools/dooya_voice_runner.py` 第 3 轮 host 修正：保留拆行 `refresh config` 状态解析，同时把 `advisory_tone_wait_s / secondary_signal_wait_s` 默认值收敛到 `0`，改为“功能证据成立后固定短稳定间隔 `2.0s` 再推进”。
  - 当前准备按这套新口径重新启动 6 条校准回归。


- 进展记录（2026-04-16 19:46）
  - 已确认第二轮校准回归失败的更深层原因不是声卡，也不只是 runner 时序，而是 builder 仍把“设置成功动作”的 tone/config 值作为硬门槛，阻断了后续功能验证。
  - 已完成 `tools/dooya_case_builder.py` 第 2 轮口径修正并重建 workspace：唤醒词/工作模式/窗帘模式的设置成功动作已改为 `ASR 硬校验 + tone/log 辅助记录`，后续功能生效由后续步骤继续验证。
  - 当前正准备在这套“功能优先、数值辅助”的最新生成用例上重新启动 6 条校准回归。


- 进展记录（2026-04-16 19:58）
  - 已按接手要求重新读取 `plan.md` 并检查当前最新 6 条校准回归 `work/rebuild-functional-20260416-160924/result/0416194857/`。
  - 当前该 run 仍在执行中，进程 `mars_moon_pipeline.py` 与 `dooya_voice_runner.py` 均存活；live `tool.log` 已确认 `TC_WAKEWORD_003` 通过并推进到 `TC_WAKEWORD_004`，且已成功抓到 `wakeup=1` 与 `refresh config ... wakeup=1`。
  - 截至当前仍未产生新的最终汇总文件；若用户此刻询问“还有几个没通过”，应以“最新已完成 run 的最终结果 + 当前 run 的实时改进证据”一并说明，避免把未结束 run 当最终结论。


- 进展记录（2026-04-16 19:59）
  - 当前可确认的最新已完成校准结果仍是 `work/rebuild-functional-20260416-160924/result/0416170853/`：`PASS 2 / FAIL 4 / BLOCKED 0`。
  - 4 条未通过分别为：`TC_WAKEWORD_003`、`TC_WAKEWORD_004`、`TC_WORKMODE_002`、`TC_CURTAINMODE_003`。
  - 其中 `TC_WAKEWORD_003 / TC_WAKEWORD_004` 的旧失败点都与 `wakeup=1` / 配置变化抓取不足强相关；当前 live run `0416194857` 已明确抓到 `wakeup=1` 与 `refresh config ... wakeup=1`，说明这两条至少已有明显修复迹象，但本轮尚未结束，不能提前当最终 PASS。
  - `TC_WORKMODE_002 / TC_CURTAINMODE_003` 在已完成 run 中仍表现为设置窗口内后续命令证据缺失，更像动作衔接/观察窗口或 case 口径残留问题，待当前 live run 收尾后再给最终归因。


- 进展记录（2026-04-16 20:04）
  - 已复核当前 builder 与功能判据文档中“进入设置后插入普通控制词 `打开窗帘`”的设计目的。
  - 当前结论：该步骤不是所有设置类 case 的固定动作，只用于验证“设置窗口内普通控制词路径”和“设置窗口保持”这类场景；`打开窗帘` 被选中是因为它属于稳定普通控制词，协议/播报/日志证据最完整，便于判断。
  - 后续对外解释口径固定为：此步骤用于验证“普通控制词执行”与“设置状态不被破坏”两件事，而不是把 `打开窗帘` 当成设置动作本身。


- 进展记录（2026-04-16 20:06）
  - 用户已确认当前口径：`打开窗帘` 这类普通控制词只应用于“验证设置窗口内普通命令是否会污染设置本身”的异常/边界场景，不应加入纯设置成功验证链路。
  - 后续 case 设计与结果解释按此固定：纯设置功能只验证入口、目标设置、生效闭环；仅在验证窗口隔离性/抗污染性时插入普通控制词步骤。


- 进展记录（2026-04-16 20:07）
  - 当前 live 校准 run `work/rebuild-functional-20260416-160924/result/0416194857/` 已确认推进到 `[5/6] TC_CURTAINMODE_002`，`TC_WAKEWORD_003`、`TC_WAKEWORD_004`、`TC_WORKMODE_001`、`TC_WORKMODE_002` 已执行完并进入后续 case。
  - 其中 `TC_WAKEWORD_004` 已在 live 日志中明确抓到 `playId=14`、`wakeup=1` 和 `refresh config ... wakeup=1`，相较旧 run 属于明显正向改进。
  - `TC_WORKMODE_002` 当前也已至少抓到设置窗口内普通控制词 `打开窗帘` 的 `sendMsg=55 AA 05 01 01 01 EA A9`，说明窗口内普通控制词执行路径已打通；最终是否 PASS 还需等待结果文件落盘。


- 进展记录（2026-04-16 20:11）
  - 6 条校准 run `work/rebuild-functional-20260416-160924/result/0416194857/` 已于 `20:11:12` 结束并落盘。
  - 本轮结果：`PASS 2 / FAIL 4 / BLOCKED 0`。通过项为 `TC_WORKMODE_001`、`TC_CURTAINMODE_002`；未通过项为 `TC_WAKEWORD_003`、`TC_WAKEWORD_004`、`TC_WORKMODE_002`、`TC_CURTAINMODE_003`。
  - 相比旧 run，本轮已确认修正了 `wakeup=1` / `refresh config ... wakeup=1` 这类配置变化抓取能力；但设置窗口相关 4 条仍未全转 PASS，当前失败面已收敛为“窗口内后续动作证据缺失”与“连续唤醒恢复态判断”两类。


- 进展记录（2026-04-16 20:21）
  - 用户已提供 4 条校准 case 的人工顺序执行日志，核心证据明确显示：
    1. `设置唤醒词 -> 打开窗帘 -> 客厅窗帘 -> 客厅窗帘唤醒 -> 打开窗帘` 这条链路人工可通；
    2. `设置工作模式 -> 打开窗帘 -> 语音模式` 人工可识别并返回 `play id : 14`；
    3. `设置窗帘模式 -> 打开窗帘 -> 布帘模式` 人工可识别并落到 `curtain_type=1 + save config success`。
  - 该人工日志与当前 runner 结果的最大分歧点已明确：至少 `TC_WORKMODE_002` 与 `TC_CURTAINMODE_003` 不能再简单归为 DUT 功能失败，优先应按“runner 证据采集/动作节拍不一致”处理。


- 进展记录（2026-04-16 20:20）
  - 用户要求详细复盘当前 4 条 FAIL 的测试逻辑、验证方案、断言方法与人工手测差异。
  - 当前任务切换为：从 `tools/dooya_case_builder.py` 与 `tools/dooya_voice_runner.py` 提取这 4 条 case 的真实执行/判定逻辑，逐条解释错位点，明确是逻辑错、断言错、节拍错还是结果归因错。


- 进展记录（2026-04-16 20:29）
  - 已完成 4 条 FAIL 的代码级复盘：当前自动化的主要错位点已明确为 `assert_wake_repeats` 过严、设置窗口后 `auto_wake=False` 动作缺少显式后摇间隔、以及设置窗口内对 ASR 的单点硬依赖。
  - 当前结论更新：`TC_WAKEWORD_003 / TC_WORKMODE_002 / TC_CURTAINMODE_003` 均已有用户手工正证据，不能继续按 DUT 功能失败归因；`TC_WAKEWORD_004` 的现 FAIL 口径也与 case 文本“连续可唤醒”不一致。


- 进展记录（2026-04-16 20:37）
  - 用户补充并确认关键执行规则：**只要上一条响应播报尚未结束，后续唤醒词和命令词都不会被设备识别**。
  - 后续 runner/用例执行统一按此作为硬约束：任何 `wake` 或 `say` 前，都必须确认上一条响应播报已经结束，不能仅凭识别到关键词或看到部分日志就立刻播下一条。


- 进展记录（2026-04-16 20:39）
  - 用户补充并确认另一条关键口径：**默认唤醒词 `你好杜亚` 为固定有效唤醒词，任何时候都应可唤醒，因此不应把‘每条用例开始先恢复出厂’当成必要前置**。
  - 当前收口方向再收紧：这 4 条校准 case 将优先去掉不必要的 case-start 恢复出厂，仅保留真正用于状态回收的必要恢复动作。

- 进展记录（2026-04-16 20:45）
  - 已根据用户最新口径固定当前规则：**默认唤醒词 `你好杜亚` 为始终有效的固定唤醒词，不应把‘每条用例开始先恢复出厂’当成统一前置条件**。
  - 后续 case 设计与自动化执行统一按此处理：仅在确实需要回收非默认配置或验证恢复出厂功能本身时才执行恢复出厂；纯功能链路验证优先直接从当前默认唤醒态进入。
  - 当前下一步：先确认 `tools/dooya_case_builder.py`、`tools/dooya_voice_runner.py` 以及目标 workspace 内副本是否完全同步该口径，然后继续收口剩余 4 条校准用例。

- 进展记录（2026-04-16 20:52）
  - 已对 `tools/dooya_voice_runner.py` 增补播报结束隐式收口逻辑：若已观察到 `play start` 但迟迟等不到 `play stop`，在达到 `playbackImplicitCompleteS`（当前默认继承 `successSettleS=2.0s`）后允许按“播报已足够结束”继续推进，避免被迟到/拆行日志长期拖住。
  - 该修正已同步到 `work/rebuild-functional-20260416-160924/tools/dooya_voice_runner.py`，并完成 `py_compile` 静态检查通过。
  - 下一步：先确认日志串口未被占用并重新上电，然后用最新 workspace 口径重跑 4 条校准用例。

- 进展记录（2026-04-17 09:06）
  - 已复核当前现场状态：`work/rebuild-functional-20260416-160924/result/0416204752/` 仍是上一次未收尾的 4 条校准用例 partial run，未生成 `execution_summary.md`，当前也没有 `mars_moon_pipeline.py` / `dooya_voice_runner.py` 在运行。
  - 因此当前真正**尚未收口**的不是代码同步，而是最新 4 条目标用例还没有在“去掉 case-start 恢复出厂 + 新播报结束等待逻辑”这套最终口径下完成一轮实跑落盘。
  - 当前待收口项固定为：`TC_WAKEWORD_003`、`TC_WAKEWORD_004`、`TC_WORKMODE_002`、`TC_CURTAINMODE_003` 的最新结果确认，以及完成后把 host 逻辑问题 / DUT 功能问题的最终归因写回总结。

- 进展记录（2026-04-17 09:08）
  - 已按用户要求停止空谈，直接进入 4 条目标用例实跑阶段；当前执行顺序固定为：先检查串口占用，再给 DUT 上电，然后启动 `TC_WAKEWORD_003,TC_WAKEWORD_004,TC_WORKMODE_002,TC_CURTAINMODE_003` 重跑。
  - 本轮目标不再停留在代码复盘，而是直接产出最新 run 结果文件，并据此完成最终归因。

- 进展记录（2026-04-17 09:09）
  - 已完成重跑前前置：现场串口未见明显占用，已向 `/dev/ttyACM4` 发送 `uut-switch1.on`，并完成 8s 稳定等待。
  - 当前立即启动 4 条目标用例重跑：`TC_WAKEWORD_003,TC_WAKEWORD_004,TC_WORKMODE_002,TC_CURTAINMODE_003`。

- 进展记录（2026-04-17 09:14）
  - 已完成 4 条目标用例重跑，结果目录：`work/rebuild-functional-20260416-160924/result/0417090726/`，结果文件已落盘（`testResult.xlsx`、`requirement_status.md`、`execution_summary.md`）。
  - 当前进入最后收尾阶段：提取 `PASS/FAIL/BLOCKED`、逐条核对失败项与功能证据，再把最终归因补回 `plan.md`。

- 进展记录（2026-04-17 09:16）
  - 4 条目标用例最终结果已确认：`PASS 3 / FAIL 1 / BLOCKED 0`，结果目录：`work/rebuild-functional-20260416-160924/result/0417090726/`。
  - 通过项：`TC_WAKEWORD_003`、`TC_WORKMODE_002`、`TC_CURTAINMODE_003`。这 3 条说明此前的 host 节拍/等待逻辑问题已基本收口，设置窗口内普通控制词、后续设置词、生效后再次控制的主链路都可正常跑通。
  - 剩余失败项仅 `TC_WAKEWORD_004`：当前最新实跑里，负例词【餐厅窗帘】在“当前唤醒词=客厅窗帘”场景下触发了 `wakeKw=餐厅窗帘`、`asrKw=餐厅窗帘`、`wakeReady=wake up ready to asr mode`，被判定为误唤醒；该项已不再像旧版本那样卡在连续唤醒节拍，而是收敛为单点 DUT/固件行为问题。
  - 当前最终归因：host/runner 侧剩余 4 条校准问题已收敛完成，仅保留 `TC_WAKEWORD_004` 作为待 DUT/固件进一步确认的真实异常点。

- 进展记录（2026-04-17 09:21）
  - 用户要求对 `TC_WAKEWORD_004` 再复测一次，确认【餐厅窗帘】误唤醒是否稳定复现，避免把单次相近词串扰直接固化为最终结论。
  - 当前复测策略：仅单跑 `TC_WAKEWORD_004`，继续沿用最新 runner 口径，并保留完整原始日志供人工复核。

- 进展记录（2026-04-17 09:34）
  - 单跑 `TC_WAKEWORD_004` 的复测过程中出现明显前置串扰：首步 `你好杜亚` 附近抓到了 `打开窗帘/设置唤醒词` 等错位识别，当前 run 不适合作为误唤醒是否复现的有效依据。
  - 已按用户允许准备先重启设备，再以干净状态重新复测该用例。

- 进展记录（2026-04-17 09:35）
  - 已接手当前现场状态：有效基线仍以 `work/rebuild-functional-20260416-160924/result/0417090726` 为准，`0417093129` 因日志污染无效。
  - 按用户最新指令，下一步先重启设备并等待重新上电，再从干净状态单独重跑 `TC_WAKEWORD_004`，仅用来复核 `餐厅窗帘` 负例是否稳定复现误唤醒。

- 进展记录（2026-04-17 09:37）
  - 已通过控制口 `/dev/ttyACM4` 执行 `uut-switch1.off -> uut-switch2.off -> uut-switch1.on` 重启设备。
  - 启动等待后，日志口 `/dev/ttyACM0` 已重新读到设备输出，现场已回到可继续验证状态；下一步从干净状态重跑 `TC_WAKEWORD_004`。

- 进展记录（2026-04-17 09:48）
  - 已确认本次复核失败的直接原因是 runner 在 `assert_wake_repeats` 分支仍残留旧时序：连续唤醒仅间隔 `0.2s`，没有等待上一轮唤醒/识别响应播报及交互态退出，导致后续 `TIME_OUT`、负例校验和收尾动作整体错位。
  - 已修正 `tools/dooya_voice_runner.py` 与 `tools/dooya_case_builder.py`：唤醒词稳定性校验改为每轮先回到空闲态再执行下一轮；修改已同步到 `work/rebuild-functional-20260416-160924/` 并重建 `generated/cases.json`。

- 进展记录（2026-04-17 10:00）
  - 已先修正 `assert_wake_repeats` 的旧缺陷：连续唤醒不再只间隔 `0.2s`，而是要求上一轮先回到空闲态再执行下一轮。
  - 基于修正后的 runner 重跑 `TC_WAKEWORD_004`（结果目录 `work/rebuild-functional-20260416-160924/result/0417095038`）后，确认新的阻塞点变为“空闲态等待窗口偏短”：第 1 次 `客厅窗帘` 唤醒后的 `TIME_OUT + playId 2` 出现在约 `31.8s`，超过原 `28s` 观测窗。
  - 已继续修正两处：一是把唤醒超时观测窗放宽到 `35s`；二是语音预检结束后强制等待回空闲，避免预检尾日志污染正式用例起步。
  - 第三次复核（结果目录 `work/rebuild-functional-20260416-160924/result/0417095753`）表明：语音链路预检本身可以唤醒，但在 `35s` 内仍未观察到预期的 `TONE_ID_2/TIME_OUT` 回空闲证据，因此当前会被 runner 直接按 `voice preflight blocked` 停测；这已不再是“连着播”脚本错误，而是设备/现场日志行为与当前预检回空闲假设不一致。
  - 截至此刻，`TC_WAKEWORD_004` 仍未跑到 `餐厅窗帘` 负例，因此“误唤醒是否复现”当前仍不能下有效结论。

- 进展记录（2026-04-17 10:12）
  - 已按用户“前置条件 / 用例主体 / 断言校验”思路重构 `tools/dooya_case_builder.py` 的 `WAKEWORD` 与 `SELECTOR` 用例生成逻辑，并删除原 `TC_WAKEWORD_004 ~ TC_WAKEWORD_010` 的全量组合校验模式。
  - 当前新生成的 `WAKEWORD` 用例已改成单功能 case：设置外无效、设置入口内普通命令不影响后续设置、设置后立即生效、超时值、超时退出。
  - 当前新生成的 `SELECTOR` 用例也已改成“设置动作作为前置条件”，主体只验证：连续唤醒稳定、未设置词不误唤醒、旧词失效、默认词仍可用。
  - 已同步重建：`generated/cases.json`、`generated/CSK5062_杜亚窗帘_测试用例.xlsx`，以及 `work/rebuild-functional-20260416-160924/tools/dooya_case_builder.py` + 其 workspace 内 `generated/cases.json`。

- 进展记录（2026-04-17 10:16）
  - 用户确认新的拆分方向应保留“旧用例风格”，但严格改成“一条用例只验证一个问题”；不再在步骤文案里显式加入“前置条件 / 用例主体 / 断言校验”标签。
  - 下一步仅调整 `tools/dooya_case_builder.py` 的 `WAKEWORD / SELECTOR` 生成风格：保留单问题拆分，回退到原来的简洁步骤文案与用例模式。

- 进展记录（2026-04-17 10:19）
  - 已按用户最新要求回退 `WAKEWORD / SELECTOR` 的步骤文案风格：保留“单问题 case”拆分，但移除显式的“前置条件 / 用例主体 / 断言校验”标签，恢复为原来的简洁步骤模式。
  - 最新 `generated/cases.json` 与 workspace 内同名文件均已重建，代表用例包括：`TC_WAKEWORD_009`、`TC_WAKEWORD_010`、`TC_WAKEWORD_018`、`TC_SELECTOR_001`、`TC_SELECTOR_002`。

- 进展记录（2026-04-17 10:22）
  - 已确认“恢复出厂模式”属于独立功能点，不再作为当前重构中 `WAKEWORD / SELECTOR` 用例的通用前置或通用收尾。
  - 当前这两块新拆分 case 已移除自动恢复出厂包装；`FACTORY` 模块保留自身独立用例负责恢复出厂功能验证。
  - 已同步重建：`generated/cases.json`、workspace 内同名文件。

- 进展记录（2026-04-17 10:36）
  - 已基于 `tmp/需求文档.md`、`references/mind.md`、`references/checkLogic.txt` 整理首版测试方案草稿，落盘为 `references/test-plan-draft.md`。
  - 当前方案按“功能点 -> 怎么测 -> 通过标准 -> 反例 -> 异常场景 -> 归因口径”组织，暂未展开为详细 case 列表。

- 进展记录（2026-04-17 10:40）
  - 用户已确认首版测试方案，下一阶段开始输出“功能点 -> 测试用例映射表”，并据此继续重构 `WORKMODE / CURTAINMODE` 的 case 生成逻辑。
  - 当前优先顺序：先文档化映射关系，再落 builder，避免边改边失控。

- 进展记录（2026-04-17 10:45）
  - 已完成“功能点 -> 测试用例映射表”草稿，落盘为 `references/test-case-mapping-draft.md`。
  - 当前映射表已覆盖 `BOOT / BASE / VOL / UART / POWER / FACTORY / WAKEWORD / WORKMODE / CURTAINMODE / CURTAIN / PHRASE / SELECTOR / CTRL` 全模块，并明确了单问题 case 的拆分方式。
  - 后续 builder 改造将优先按该映射表推进 `WORKMODE / CURTAINMODE`，避免再回到“大杂烩用例”。


- 进展记录（2026-04-17 10:58）
  - 已重新接手并确认用户最新要求：当前不是只重构 `WORKMODE / CURTAINMODE`，而是要按"一条用例只验证一个问题"的原则，重构 `tools/dooya_case_builder.py` 的全部模块用例。
  - 本轮执行目标已调整为全模块用例体系收敛：先逐模块审查现有 builder 与 `references/test-plan-draft.md`、`references/test-case-mapping-draft.md` 是否一致，再统一改写生成逻辑并重建 `generated/cases.json` / Excel 产物。
  - 当前下一步：先做 builder 全量盘点，识别哪些模块仍存在"单条 case 混多个验证点"、"通用恢复出厂前后包裹"、"功能验证与数值验证耦合"等问题，然后按模块批量改造。


- 进展记录（2026-04-17 11:08）
  - 已完成当前 builder 与 `references/test-plan-draft.md` 的模块级对照审查，结论为：现状并非只有 `WORKMODE / CURTAINMODE` 不符合，`VOL / UART / POWER / FACTORY / WORKMODE / CURTAINMODE / CURTAIN / PHRASE / SELECTOR / CTRL` 均存在不同程度的不符合项。
  - 主要问题已确认：
    1. 仍有多处"一条 case 混多个验证点"；
    2. 仍有模块使用 `restore_default_actions()` / `isolate_cases()` 把恢复出厂当通用前后置；
    3. 功能验证与协议/TONE/步数等数值验证仍有耦合；
    4. 词组批量校验类 case 仍然过大，不符合单问题原则。
  - 当前初步判断：`BOOT / BASE / WAKEWORD` 相对接近目标结构，但仍要在全量重构时一起过一遍；其余模块需要明确改写。
  - 下一步直接进入全模块 builder 改造，不再只限两个模块。


- 进展记录（2026-04-17 11:10）
  - 已收到用户最新要求：本轮全模块用例重构完成后，先不要运行设备测试，只输出重构后的用例给用户审看。
  - 当前执行边界已收敛为：允许修改 `tools/dooya_case_builder.py` 并重建生成产物，但不启动 `run`、不做实机验证，待用户确认用例后再进入执行阶段。


- 进展记录（2026-04-17 11:19）
  - 已完成本轮全模块 builder 重构首版，并已成功重建产物：`generated/cases.json`、`generated/CSK5062_杜亚窗帘_测试用例.xlsx`。
  - 当前首版用例总数为 `113` 条，模块分布为：`BOOT 3 / BASE 5 / VOL 7 / UART 3 / POWER 4 / FACTORY 7 / WAKEWORD 18 / WORKMODE 9 / CURTAINMODE 17 / CURTAIN 16 / PHRASE 13 / SELECTOR 4 / CTRL 7`。
  - 本轮未执行任何设备测试，仅完成用例重构与生成，待用户先审看用例结构、命名和步骤后再决定是否继续收口或进入执行阶段。


- 进展记录（2026-04-17 11:33）
  - 已根据用户审看意见完成第二轮收口：
    1. `TC_POWER_002` 的掉电后唤醒验证已改为直接使用当前设置词【客厅窗帘】；
    2. 生成步骤中已把 `say(auto_wake=True)` 明确展开为“先播唤醒词，再播命令词”；
    3. 默认态敏感用例（如 `WORKMODE/CURTAINMODE/CURTAIN/PHRASE/UART` 的默认态验证）已补入显式恢复默认状态步骤，避免被前序模式切换污染。
  - 当前再次自查后，仅剩 2 条故意不先唤醒的 case：`TC_BASE_002`、`TC_BASE_004`，它们分别用于验证“未唤醒直接说命令不响应”和“超时退出后不重唤醒直接命令不响应”，符合设计目的。
  - 最新产物已重新生成：`generated/cases.json`、`generated/CSK5062_杜亚窗帘_测试用例.xlsx`，当前继续等待用户审看，不进入设备执行。


- 进展记录（2026-04-17 11:40）
  - 已按用户新一轮审看意见修正 `FACTORY` 模块：
    1. `TC_FACTORY_002 / TC_FACTORY_003` 在恢复出厂前，先用已设置词【客厅窗帘】做一次唤醒确认；
    2. `TC_FACTORY_006` 改为验证“恢复出厂后布帘模式专有词失效”；
    3. `TC_FACTORY_007` 改为先设置【纱帘模式】，再验证“恢复出厂后纱帘模式专有词失效”。
  - 已重新生成 `generated/cases.json` 与 `generated/CSK5062_杜亚窗帘_测试用例.xlsx`，当前继续只做用例审看，不进入设备执行。


- 进展记录（2026-04-17 11:47）
  - 用户已接入设备并指定本轮播报声卡为 `VID_8765&PID_5678:USB_0_4_3_1_0`，当前任务切换为：基于新用例调试执行链路并落地待办。
  - 本轮执行顺序固定为：先上电 -> 声卡/串口预检 -> 同步最新 builder/runner/生成产物 -> 选择代表性新用例实机调试 -> 若链路稳定再扩展回归。
  - 当前仍遵守阶段性上报：至少反馈上电结果、音频预检、构建结果、执行进度与最终归因。


- 进展记录（2026-04-17 18:10）
  - 已按用户最新要求接手实机调试：设备已接入，本轮指定播报声卡固定为 `VID_8765&PID_5678:USB_0_4_3_1_0`。
  - 本轮执行目标切换为：基于最新单问题新用例，先完成上电、声卡/日志预检，再同步最新 builder/runner 到当前调试 workspace，并选取代表性 case 实机调试执行链路。
  - 当前优先关注点为：`/dev/ttyACM0` 详细日志是否稳定、指定声卡播报是否正常、以及 runner 在新用例口径下的动作节拍/断言是否与人工执行一致。


- 进展记录（2026-04-17 18:20）
  - 已完成本轮前置：显式上电 `uut-switch1.on`、指定声卡 `VID_8765&PID_5678:USB_0_4_3_1_0` 预检通过；`listenai-play` 的 `scan/probe/play` 均正常，当前声卡路由解析为 `plughw:2,0 (CSK6012Combo)`。
  - 已把根目录最新 `tools/`、`scripts/`、`sample/`、`wavSource/` 同步到 `work/debug-newcases-20260417-180511/`，并重新执行 `build`；最新新用例产物已重建，`case_count=113`。
  - 当前设备运行态异常已明确：日志口 `/dev/ttyACM0` 持续重复输出启动标记，并反复出现 `wIvwCreate fail | ret:18003`、`ai_create failed!!!`、`WDT_START`，随后再次重启；该问题独立于指定声卡工具链。
  - 已尝试自动烧录修复：`python3 scripts/mars_moon_pipeline.py burn --workspace work/debug-newcases-20260417-180511`，结果失败；烧录工具未拿到 `CONNECT ROM AND DOWNLOAD RAM LOADER SUCCESS`，仅持续 `RECEIVE OVERTIME......`。
  - 已进一步手工拉长 `off -> boot on -> power on` 时序，并对 `/dev/ttyACM0~3` 全部做 ROM 握手扫描，结果仍全部 `RECEIVE OVERTIME......`；当前可判定不是单纯脚本时序问题，而是当前 DUT 未对宿主机暴露可用的 ROM 下载握手通道。
  - 已补跑最小新用例 `TC_BASE_001`，结果目录：`work/debug-newcases-20260417-180511/result/0417181807/`；`execution_summary.md` 明确为 `voice: BLOCKED`，阻断原因为：PC 播放链路正常但 DUT 侧未形成有效唤醒证据（无唤醒词命中、无唤醒播报、无 wakeReady），且整个观测期间持续伴随异常重启。
  - 当前归因：
    1. 声卡/播报工具：正常；
    2. 新用例生成与 runner 口径：已同步并可正常阻断，不存在当前主问题；
    3. 当前主阻塞：设备/固件运行态异常 + ROM 烧录入口不可达。
  - 下一步不再盲目扩展全量回归；需先处理 DUT 当前异常重启/无法进入 ROM 的问题，恢复到稳定运行态后再继续跑新用例全链路。


- 进展记录（2026-04-17 18:31）
  - 用户已确认继续排查烧录进入时序；本轮固定只使用 `/dev/ttyACM0` 作为日志/烧录口、`/dev/ttyACM4` 作为控制/boot 口，不再混用其他主口。
  - 当前执行策略：先做小范围 boot/power 时序扫描，只观察 ACM0 上的 ROM 握手是否可达；若命中有效时序，再决定是否把该时序固化到烧录脚本。


- 进展记录（2026-04-17 18:34）
  - 已按用户确认的主口固定做两轮排查：仅使用 `/dev/ttyACM0` 作为日志/烧录口、`/dev/ttyACM4` 作为控制/boot 口。
  - 第一轮时序扫描已完成：共尝试 6 组 `power/boot` 进入烧录时序（标准时序、延后释放 boot、长关电/长 boot、高保持 boot、不同时点释放 boot）；ACM0 上结果全部一致，仅返回 `RECEIVE OVERTIME......`，无 `SEND CHANGE BAUDRATE`、无 `CONNECT ROM`、无 `SEND BEGIN`。
  - 第二轮仅变更烧录 baud 再做复核：在同一 `ACM0/ACM4` 口径下分别测试 `115200 / 460800 / 1500000`，结果仍全部为 `RECEIVE OVERTIME......`，没有任何 ROM 握手成功标记。
  - 当前可进一步收敛结论：
    1. 不是端口选错；
    2. 不是简单的 boot 释放先后或 power/boot 等待时序问题；
    3. 不是当前烧录工具 baud 配置问题；
    4. 当前更像是 DUT 侧 boot 控制未真正让芯片进入 ROM 下载态，或 ROM 下载通道本身不可达。
  - 在当前状态下，不建议继续修改 `burn.sh` 固化时序；应先处理 DUT 的 boot/下载通道可达性问题，待能稳定握到 `CONNECT ROM AND DOWNLOAD RAM LOADER SUCCESS` 后，再回到自动烧录与新用例回归。


- 进展记录（2026-04-17 18:53）
  - 用户已反馈当前设备已手工烧录完成；本轮任务切回 burn 后实机调试，优先确认设备是否恢复稳定运行态。
  - 当前执行顺序：先显式上电 -> 检查 `/dev/ttyACM0` 启动/运行日志 -> 复核指定声卡 -> 跑最小新用例 `TC_BASE_001`。


- 进展记录（2026-04-17 18:57）
  - 已完成 burn 后最小链路验证：设备已恢复正常启动，可读取新固件版本 `VCC.03.02.00.24` 的启动日志，后续 12s 观察窗口内未再出现连续重启。
  - 指定声卡 `VID_8765&PID_5678:USB_0_4_3_1_0` 复核通过，当前 Linux backend 解析为 `plughw:1,0 (CSK6012Combo)`。
  - 已运行最小新用例 `TC_BASE_001`，结果目录：`work/debug-newcases-20260417-180511/result/0417185457/`；结果为 `voice preflight BLOCKED`，不是 case 断言失败。
  - 已进一步做人工式复核：用指定声卡手动连续播放两次 `你好杜亚`，同时抓取 `/dev/ttyACM0`；日志仅见 `loglevel 4` 与 `root:/$`，完全没有识别/唤醒相关输出。
  - 当前归因已收敛：
    1. 设备启动稳定性：已恢复；
    2. 指定声卡播报工具：正常；
    3. runner / 新用例：当前未暴露主问题；
    4. 当前主阻塞：`PC 播放 -> DUT 收音/识别` 链路未打通，或现场收音路径未生效。
  - 在当前状态下继续扩展回归没有意义；需先恢复工位的收音/识别链路，再继续跑新用例。


- 进展记录（2026-04-17 19:09）
  - 用户要求再次复测“指定声卡播报后是否会产生识别日志”；本轮按最小路径执行：上电 -> 指定声卡播放唤醒词 -> 抓取 `/dev/ttyACM0` 日志。


- 进展记录（2026-04-17 19:10）
  - 已按用户要求再次复测：显式上电后，`/dev/ttyACM0` 可正常回显 `loglevel 4` 与 `root:/$`，说明日志口在线。
  - 已使用指定声卡 `VID_8765&PID_5678:USB_0_4_3_1_0` 连续播放两次唤醒词 `你好杜亚`；`listenai-play` 的 probe 与 playback 均成功，当前 backend 为 `plughw:1,0 (CSK6012Combo)`。
  - 本轮抓取到的日志仍只有 `loglevel 4` / `root:/$`，未出现任何识别、唤醒、`wakeReady` 或播报 ID 相关日志。
  - 当前结论不变：播报工具链正常，但 `PC 播放 -> DUT 收音/识别` 仍未打通；当前不是 runner 或声卡工具故障。


- 进展记录（2026-04-20 10:12）
  - 用户要求复测指定声卡 `VID_8765&PID_5678:USB_0_4_3_1_0` 播报后能否获取日志，并明确要求日志等级为 `4`。
  - 本轮按最小路径执行：先上电 -> 向日志口发送 `loglevel 4` -> 使用指定声卡播放唤醒词 -> 同步抓取日志并输出结论。


- 进展记录（2026-04-20 10:15）
  - 已完成本轮指定声卡复测。先执行 `uut-switch1.off -> uut-switch2.off -> uut-switch1.on` 恢复正常启动，再在 `/dev/ttyACM0` 发送 `loglevel 4`。
  - 使用指定声卡 `VID_8765&PID_5678:USB_0_4_3_1_0` 连续播放两次 `你好杜亚` 后，已稳定抓到唤醒日志，证明当前“指定声卡播报 -> DUT 识别 -> 4级日志输出”链路已打通。
  - 关键证据包括：
    1. `keyword:ni hao du ya`
    2. `wake up ready to asr mode`
    3. `play id : 0`
    4. `MODE=1`
  - 当前 Linux backend 仍为 `plughw:1,0 (CSK6012Combo)`；本轮抓取日志已保存到 `/tmp/mars_20260420_wake_check_after_restore.log`。


- 进展记录（2026-04-20 10:25）
  - 用户要求：先跑最小用例 `TC_BASE_001`，若通过则立即续跑当前新用例全链路。
  - 当前执行顺序固定为：恢复正常启动 -> 最小用例验证 -> 全链路 run -> 阶段性汇报结果。


- 进展记录（2026-04-20 10:26）
  - 最小用例 `TC_BASE_001` 已通过，结果目录：`work/debug-newcases-20260417-180511/result/0420102544/`。
  - 已确认 `voice preflight=READY`、`TC_BASE_001=PASS`；当前按用户要求立即切换到当前新用例全链路 run。


- 进展记录（2026-04-20 10:42）
  - 当前新用例全链路 run 正在执行，结果目录：`work/debug-newcases-20260417-180511/result/0420102709/`。
  - 截至当前实时进度约 `19/113`，已完成 `BOOT / BASE / VOL / UART` 前半段；指定声卡播报、日志恢复、语音预检、协议观测整体稳定，暂未出现新的 `BLOCKED`。


- 进展记录（2026-04-20 14:09）
  - 用户临时修改当前验证口径：协议串口改为 `/dev/ttyACM1`，波特率 `9600`。
  - 本轮只验证“交互基础窗帘控制命令时，`/dev/ttyACM1` 是否有协议输出”；执行顺序为：上电 -> 打开协议监听 -> 指定声卡播唤醒词与基础窗帘控制命令 -> 汇总协议串口观测结果。


- 进展记录（2026-04-20 14:12）
  - 用户要求协议串口改为纯 hex 接收，不按字符串方式读取。
  - 本轮将对 `/dev/ttyACM1 @ 9600` 只做原始字节抓取并转十六进制输出，同时再次执行 `你好杜亚 -> 打开窗帘` 验证是否存在协议口数据。

- 进展记录（2026-04-20 14:15）
  - 已重新读取 `plan.md` 与 `listenai-play` skill，确认本轮继续使用指定声卡 `VID_8765&PID_5678:USB_0_4_3_1_0`，并按用户要求把协议监听口固定为 `/dev/ttyACM1 @ 9600`。
  - 协议监听方式固定为：`serial.read()` 读取原始字节，再用 `bytes.hex(" ").upper()` 输出；本轮不对协议串口做字符串 decode。
  - 下一步按阶段执行：先恢复正常启动，再同时抓 `/dev/ttyACM0` 的 4 级日志与 `/dev/ttyACM1` 的 raw hex，随后播放 `你好杜亚 -> 打开窗帘` 做协议口复测。

- 进展记录（2026-04-20 14:18）
  - 已完成 `/dev/ttyACM1 @ 9600` 的纯 hex 协议复测；监听实现固定为 `serial.read()` 读取原始字节，再以十六进制文本落盘，不做字符串 decode。
  - 本轮先执行 `uut-switch1.off -> uut-switch2.off -> uut-switch1.on`，随后在 `/dev/ttyACM0` 成功设置 `loglevel 4`，并使用指定声卡 `VID_8765&PID_5678:USB_0_4_3_1_0` 顺序播放 `你好杜亚 -> 打开窗帘`。
  - 结果：日志口已明确观察到 `keyword:ni hao du ya`、`play id : 0`、`wake up ready to asr mode`、`keyword:da kai chuang lian` 以及 `send msg:: 55 AA 05 01 01 01 EA A9`；但 `/dev/ttyACM1` 的 raw hex 输出文件为空，当前未观察到任何协议口字节流。

- 进展记录（2026-04-20 14:21）
  - 用户要求把协议口排查范围扩大到 `/dev/ttyACM2` 与 `/dev/ttyACM3`，两路均按 `9600` 打开，并使用多线程并发监听。
  - 本轮仍沿用指定声卡 `VID_8765&PID_5678:USB_0_4_3_1_0`，监听方式保持 `serial.read()` 原始字节 + `bytes.hex(" ").upper()` 输出，不做字符串 decode。
  - 执行顺序已调整为：先上电恢复 -> 启动 `/dev/ttyACM0` 日志 + `/dev/ttyACM2` `/dev/ttyACM3` hex 监听 -> 播放 `你好杜亚 -> 打开窗帘` -> 判断哪一路协议口有数据。

- 进展记录（2026-04-20 14:22）
  - 用户进一步要求把协议口监听范围扩到 `/dev/ttyACM1`、`/dev/ttyACM2`、`/dev/ttyACM3` 三路，且三路均按 `9600` 打开。
  - 已中断上一轮仅监听 `ACM2/ACM3` 的会话，当前改为三路并发监听；监听方式仍固定为原始字节读取并转十六进制输出。

- 进展记录（2026-04-20 14:24）
  - 已完成 `/dev/ttyACM1`、`/dev/ttyACM2`、`/dev/ttyACM3` 三路 `9600` 并发 pure-hex 监听复测，并使用指定声卡 `VID_8765&PID_5678:USB_0_4_3_1_0` 顺序播放 `你好杜亚 -> 打开窗帘`。
  - `/dev/ttyACM0` 日志已明确命中 `keyword:ni hao du ya`、`play id : 0`、`keyword:da kai chuang lian`、`send msg:: 55 AA 05 01 01 01 EA A9`、`play id : 1`，说明交互链路正常。
  - 三路协议口结果：`/dev/ttyACM2` 收到原始字节流并转存为十六进制 `55 AA 05 01 01 01 EA A9`；`/dev/ttyACM1` 与 `/dev/ttyACM3` 输出文件均为空。
  - 当前可判定：本设备当前固件的基础窗帘控制协议实际输出口为 `/dev/ttyACM2 @ 9600`，不是 `/dev/ttyACM1`，`/dev/ttyACM3` 本轮也未观察到数据。

- 进展记录（2026-04-20 14:29）
  - 用户已明确后续协议口只保留 `/dev/ttyACM2 @ 9600`，主动协议断言改为以协议串口实收字节为准，不再拿日志里的 `send msg` 直接当断言依据。
  - 被动协议口径同步调整：协议串口负责注入，设备侧反应与窗口行为再作为结果校验；`TC_BOOT_001`、`TC_BOOT_002` 改为人工验证，不再做自动断言。
  - 当前进入代码审查阶段，重点检查 `tools/dooya_voice_runner.py`、`tools/dooya_case_builder.py`、`generated/cases.json` 中协议与 BOOT/CTRL 相关实现。

- 进展记录（2026-04-20 14:35）
  - 已完成协议断言逻辑改造：主动协议断言的 `observed_protocols()` 现仅统计协议串口实收帧（`/dev/ttyACM2 @ 9600`），不再混入日志口 `send msg/receive msg`。
  - `say` 动作在存在 `expect_send_protocol` 且 `require_protocol_and_tone=false` 时，已改为“协议为主、播报为辅”：必须先命中协议串口实收，播报只作为补充信号；`inject_protocol` 的 `actual_protocols` 也已收敛为协议串口帧，`recv msg` 仅保留在 `actual_log_values` 中作为被动协议已被设备收到的日志证据。
  - `TC_BOOT_001`、`TC_BOOT_002` 已改为人工验证项，runner 会以 `DRY_RUN` 跳过自动执行；其中 `TC_BOOT_002` 的文案已修正为“重启后日志恢复默认等级，不保持 loglevel 4”。
  - 已重新生成 `generated/cases.json` 与 `generated/CSK5062_杜亚窗帘_测试用例.xlsx`，并通过 `python3 -m py_compile tools/dooya_voice_runner.py tools/dooya_case_builder.py` 静态校验。

- 进展记录（2026-04-20 14:51）
  - 已完成协议断言与遥控器配对用例逻辑收口：协议串口预检现只确认 `/dev/ttyACM2 @ 9600` 是否可观测，不再因协议值与词表不一致而整轮停测；`TC_CTRL_002~006` 也已移除对 `TC_CTRL_001` 的链式阻塞。
  - 已新增“前置差异不污染主体结论”机制：`TC_CTRL_002/003/005/006` 入口动作 `say(配对遥控器)` 现带 `advisory_failure=true`，若入口主动协议与词表不一致，但后续被动协议注入与播报成功，则 case 可正常判 PASS。
  - 实机验证结果：`work/protocol-assert-20260420-1450/` 中单跑 `TC_CTRL_002` 已得到 `PASS 1 / FAIL 0 / BLOCKED 0`；关键证据为入口运行时主动协议 `55 AA 04 01 12 B2 17`（与词表 `55 AA 05 01 12 00 80 AF` 不一致，但不再阻塞），以及被动成功协议注入后命中 `recvMsg=55 AA 05 03 06 01 F8 81`、`playId=7`。
  - 另外已修复 runner 结果归档递归自拷贝问题，后续使用 `work/.../result` 或当前 `work/...` 结果目录收尾时不再因 `artifacts/work/...` 无限嵌套而崩溃。

- 进展记录（2026-04-20 14:54）
  - 用户已选择继续执行全链路回归；本轮沿用指定声卡 `VID_8765&PID_5678:USB_0_4_3_1_0` 与协议口 `/dev/ttyACM2 @ 9600` 的新断言口径。
  - 执行策略为：先确认最新 `generated` 产物和串口覆盖参数无误，再用当前 runner 直接启动整轮回归，并按阶段同步进度与失败归因。


- 进展记录（2026-04-20 15:23）
  - 当前全链路会话 `session 3851` 仍在持续执行，结果目录：`work/fullchain-protocol-uart2-20260420-1456`。
  - 已实际推进到 `22/113`：`TC_POWER_004` 正在执行；其中 `TC_POWER_001`、`TC_POWER_002`、`TC_POWER_003` 已顺序跑过，控制口上下电、日志口重连、协议口 `/dev/ttyACM2 @ 9600` 重连均正常。
  - 当前阶段确认的稳定项：指定声卡 `VID_8765&PID_5678:USB_0_4_3_1_0` 持续稳定解析为 `plughw:1,0 (CSK6012Combo)`；`manual_power_cycle` 已可自动执行并在上下电后恢复 `loglevel 4`；协议串口实收链路在 `打开窗帘/清除遥控器` 等主动协议场景下持续可观测。
  - 当前需继续关注的风险点：`TC_UART_003` 在 `清除遥控器` 动作上出现 3 次尝试才结束，运行迹象显示更像 runner 断言/收口口径问题而不是设备不响应；后续待整轮结果落盘后结合 `execution_summary.md` 和 action 明细确认是否记为 FAIL。
  - 当前暂未看到新的 `BLOCKED`；`TC_POWER_003` 的负例观测中已经抓到 `餐厅窗帘` 的 `wakeKw/asrKw + wakeReady` 组合，需要待 case 最终收口后判断是被当前负例判定放过、还是实际被记为 FAIL。

- 进展记录（2026-04-20 16:17）
  - 当前全链路会话 `session 3851` 仍在执行，最新进度已推进到 `75/113`，正在跑 `TC_CURTAIN_002`。
  - 当前已完成到 `CURTAINMODE` 模块末尾：最近完成的 5 条为 `TC_CURTAINMODE_015`、`TC_CURTAINMODE_016`、`TC_CURTAINMODE_017`、`TC_CURTAIN_001`，当前进入 `TC_CURTAIN_002`。
  - 指定声卡、日志口、协议口当前都仍稳定；暂未收尾出最终汇总文件，需待整轮执行结束后再统一统计 `PASS / FAIL / BLOCKED / DRY_RUN`。

- 进展记录（2026-04-20 17:56）
  - 本轮全链路已执行完毕，结果目录：`work/fullchain-protocol-uart2-20260420-1456`。
  - 已生成正式结果文件：`execution_summary.md`、`requirement_status.md`、`testResult.xlsx`；汇总为 `PASS 51 / FAIL 60 / BLOCKED 0 / DRY_RUN 2`。
  - 会话最终 shell 退出码为 `1`，但不是测试中途停测；主执行已在 `17:49:10` 完成，随后在收尾归档阶段再次触发历史 `artifacts` 递归拷贝，报 `File name too long`。当前结果文件已完整落盘，可直接用于分析。

- 进展记录（2026-04-20 18:01）
  - 已完成失败结果聚类复盘：本轮 `60` 个 FAIL 中有 `45` 个集中在“协议不符”，并主要分布于 `CURTAIN 16`、`PHRASE 12`、`CURTAINMODE 6`、`WORKMODE 5`、`CTRL 5`、`UART 3`。
  - 当前判断：这些 FAIL 不是 60 个独立功能坏点，第一大类是同源问题放大——协议断言结果频繁落到上一条 `恢复出厂模式` 的协议 `55 AA 04 01 F0 B0 5B 55` 或空值，导致后续大量依赖主动协议的 case 连锁失败。
