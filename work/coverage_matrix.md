# Requirement Coverage Matrix

## CONFIG

- CFG-001: 唤醒时长为 20s | strategy: positive, boundary, state_transition | acceptance: main | source: requirement_doc | validation: runtime_case
- CFG-002: 音量档位数为 4 | strategy: positive, boundary, state_transition | acceptance: main | source: requirement_doc | validation: runtime_case
- CFG-003: 初始化默认音量为 3 | strategy: positive, boundary, state_transition | acceptance: main | source: requirement_doc | validation: runtime_case
- CFG-004: 最小音量下溢提示播报为“音量已最小” | strategy: positive, boundary, state_transition | acceptance: main | source: requirement_doc | validation: runtime_case
- CFG-005: 最大音量上溢提示播报为“音量已最大” | strategy: positive, boundary, state_transition | acceptance: main | source: requirement_doc | validation: runtime_case
- CFG-006: mic 模拟增益为 32 | strategy: static | acceptance: main | source: requirement_doc | validation: static_config
- CFG-007: mic 数字增益为 2 | strategy: static | acceptance: main | source: requirement_doc | validation: static_config
- CFG-008: 协议串口内部编号为 UART1 | strategy: static | acceptance: main | source: requirement_doc | validation: static_config
- CFG-009: 协议串口波特率为 9600 | strategy: positive, boundary, state_transition | acceptance: main | source: requirement_doc | validation: runtime_case
- CFG-010: 日志串口内部编号为 UART0 | strategy: static | acceptance: main | source: requirement_doc | validation: static_config
- CFG-011: 日志串口波特率为 115200 | strategy: positive, boundary, state_transition | acceptance: main | source: requirement_doc | validation: runtime_case
- CFG-012: 唤醒词掉电保存为 否 | strategy: positive, boundary, state_transition | acceptance: main | source: requirement_doc | validation: runtime_case
- CFG-013: 音量掉电保存为 否 | strategy: positive, boundary, state_transition | acceptance: main | source: requirement_doc | validation: runtime_case
- CFG-014: 合成音频发音人为叶子 | strategy: static | acceptance: main | source: requirement_doc | validation: static_config
## FACTORY

- FACT-001: 恢复出厂后恢复默认唤醒词 | strategy: positive, boundary, state_transition | acceptance: main | source: requirement_doc | validation: runtime_case
- FACT-002: 恢复出厂后恢复默认音量 | strategy: positive, boundary, state_transition | acceptance: main | source: requirement_doc | validation: runtime_case
- FACT-003: 恢复出厂后恢复默认工作模式（语音模式） | strategy: positive, boundary, state_transition | acceptance: main | source: requirement_doc | validation: runtime_case
- FACT-004: 恢复出厂后恢复默认窗帘类型（窗帘模式） | strategy: positive, boundary, state_transition | acceptance: main | source: requirement_doc | validation: runtime_case
## WAKEWORD

- WAKE-001: 默认唤醒词“你好杜亚”一直生效 | strategy: positive, boundary, state_transition | acceptance: main | source: requirement_doc | validation: runtime_case
- WAKE-002: 其他候选唤醒词默认不能唤醒，通过设置后才能生效 | strategy: positive, boundary, state_transition | acceptance: main | source: requirement_doc | validation: runtime_case
- WAKE-003: 设置唤醒词模式下说具体唤醒词后立即生效并退出设置模式 | strategy: positive, boundary, state_transition | acceptance: main | source: requirement_doc | validation: runtime_case
- WAKE-004: 设置唤醒词模式下说普通控制词可正常响应且不退出设置 | strategy: positive, boundary, state_transition | acceptance: main | source: user_confirmed | validation: runtime_case
- WAKE-005: 设置唤醒词模式超时后自动退出 | strategy: positive, boundary, state_transition | acceptance: main | source: requirement_doc | validation: runtime_case
## WORKMODE

- WORK-001: 工作模式分为语音模式和嘀嗒模式，默认工作模式为 语音模式 | strategy: positive, boundary, state_transition | acceptance: main | source: requirement_doc | validation: runtime_case
- WORK-002: 未进入设置工作模式时，说语音模式或嘀嗒模式不响应 | strategy: positive, boundary, state_transition | acceptance: main | source: requirement_doc | validation: runtime_case
- WORK-003: 进入设置工作模式后，说语音模式或嘀嗒模式可切换到对应模式并退出设置 | strategy: positive, boundary, state_transition | acceptance: main | source: requirement_doc | validation: runtime_case
- WORK-004: 进入设置工作模式后，说普通控制词可正常响应且不影响后续模式设置 | strategy: positive, boundary, state_transition | acceptance: main | source: user_confirmed | validation: runtime_case
- WORK-005: 设置工作模式超时后自动退出 | strategy: positive, boundary, state_transition | acceptance: main | source: requirement_doc | validation: runtime_case
## CURTAINMODE

- CURTAIN-001: 窗帘模式分为窗帘模式、纱帘/窗纱模式、布帘模式，默认窗帘模式为 窗帘模式 | strategy: positive, boundary, state_transition | acceptance: main | source: requirement_doc | validation: runtime_case
- CURTAIN-002: 只有对应模式下相关的窗帘类型命令词才能响应 | strategy: positive, boundary, state_transition | acceptance: main | source: requirement_doc | validation: runtime_case
- CURTAIN-003: 未进入设置窗帘模式时，说纱帘/窗纱模式、布帘模式不响应 | strategy: positive, boundary, state_transition | acceptance: main | source: requirement_doc | validation: runtime_case
- CURTAIN-004: 进入设置窗帘模式后，说纱帘/窗纱模式、布帘模式可切换到对应窗帘类型并退出设置 | strategy: positive, boundary, state_transition | acceptance: main | source: requirement_doc | validation: runtime_case
- CURTAIN-005: 进入设置窗帘模式后，说普通控制词可正常响应且不影响后续模式设置 | strategy: positive, boundary, state_transition | acceptance: main | source: user_confirmed | validation: runtime_case
- CURTAIN-006: 设置窗帘模式超时后自动退出 | strategy: positive, boundary, state_transition | acceptance: main | source: requirement_doc | validation: runtime_case
## BOOT

- DER-BOOT-001: 硬上下电后欢迎语正确播报 | strategy: positive, boundary, state_transition | acceptance: derived | source: tone_reference | validation: runtime_case
- DER-BOOT-002: 重启后日志链路恢复 | strategy: positive, boundary, state_transition | acceptance: derived | source: historical_runner | validation: runtime_case
- DER-BOOT-003: 重启后默认唤醒词仍可用 | strategy: positive, boundary, state_transition | acceptance: derived | source: historical_runner | validation: runtime_case
## BASE

- DER-BASE-001: 默认唤醒词可进入交互态 | strategy: positive, boundary, state_transition | acceptance: derived | source: supplement | validation: runtime_case
- DER-BASE-002: 超时退出后不重新唤醒的直接命令不响应 | strategy: positive, boundary, state_transition | acceptance: derived | source: supplement | validation: runtime_case
- DER-BASE-003: 超时退出后重新唤醒可恢复正常命令响应 | strategy: positive, boundary, state_transition | acceptance: derived | source: supplement | validation: runtime_case
## VOL

- DER-VOL-001: 增大音量命令单步反馈正确 | strategy: positive, boundary, state_transition | acceptance: derived | source: word_table | validation: runtime_case
- DER-VOL-002: 减小音量命令单步反馈正确 | strategy: positive, boundary, state_transition | acceptance: derived | source: word_table | validation: runtime_case
## UART

- DER-UART-001: 稳定命令词触发协议发送可被协议口接收 | strategy: positive, boundary, state_transition | acceptance: derived | source: supplement | validation: runtime_case
- DER-UART-002: 日志口包含 asrKw、playId 等关键字段 | strategy: positive, boundary, state_transition | acceptance: derived | source: supplement | validation: runtime_case
- DER-UART-003: 清除遥控器链路具备稳定日志与协议可观测性 | strategy: positive, boundary, state_transition | acceptance: derived | source: word_table | validation: runtime_case
## POWER

- DER-POWER-001: 上下电后日志恢复且设备回到可交互状态 | strategy: positive, boundary, state_transition | acceptance: derived | source: supplement | validation: runtime_case
## FACTORY

- DER-FACT-001: 恢复出厂入口可达 | strategy: positive, boundary, state_transition | acceptance: derived | source: word_table | validation: runtime_case
## WORKMODE

- DER-WORK-001: 工作模式设置入口可达 | strategy: positive, boundary, state_transition | acceptance: derived | source: word_table | validation: runtime_case
## CURTAINMODE

- DER-CURTAINMODE-001: 窗帘模式设置入口可达 | strategy: positive, boundary, state_transition | acceptance: derived | source: word_table | validation: runtime_case
## CURTAIN

- DER-CURTAIN-001: 默认窗帘模式下默认窗帘控制词可生效 | strategy: positive, boundary, state_transition | acceptance: derived | source: supplement | validation: runtime_case
- DER-CURTAIN-002: 同意图同义词触发协议一致 | strategy: positive, boundary, state_transition | acceptance: derived | source: word_table | validation: runtime_case
- DER-CURTAIN-003: 模式切换后对应模式控制词可生效 | strategy: positive, boundary, state_transition | acceptance: derived | source: supplement | validation: runtime_case
- DER-CURTAIN-004: 不匹配当前模式的控制词不响应 | strategy: positive, boundary, state_transition | acceptance: derived | source: supplement | validation: runtime_case
## PHRASE

- DER-PHRASE-001: 词条按语义组执行，不是逐行平铺 | strategy: positive, negative, state_transition | acceptance: derived | source: derived_logic | validation: runtime_case
- DER-PHRASE-002: 同义词按等价意图集合校验 | strategy: positive, negative, state_transition | acceptance: derived | source: derived_logic | validation: runtime_case
- DER-PHRASE-003: 连续未识别后可重唤醒并继续剩余词条 | strategy: positive, negative, state_transition | acceptance: derived | source: supplement | validation: runtime_case
## SELECTOR

- DER-SELECTOR-001: 候选唤醒词可被设置并稳定唤醒 | strategy: positive, boundary, state_transition | acceptance: derived | source: supplement | validation: runtime_case
- DER-SELECTOR-002: 未选中的候选唤醒词不应误唤醒 | strategy: positive, boundary, state_transition | acceptance: derived | source: supplement | validation: runtime_case
- DER-SELECTOR-003: 切换候选唤醒词后旧候选应失效 | strategy: positive, boundary, state_transition | acceptance: derived | source: derived_logic | validation: runtime_case
## CTRL

- DER-CTRL-001: 遥控器配对入口可达并发送配对协议 | strategy: positive, negative, state_transition | acceptance: derived | source: word_table | validation: runtime_case
- DER-CTRL-002: 窗口内支持配对成功被动播报 | strategy: positive, negative, state_transition | acceptance: derived | source: word_table | validation: runtime_case
- DER-CTRL-003: 窗口内支持配对失败被动播报 | strategy: positive, negative, state_transition | acceptance: derived | source: word_table | validation: runtime_case
- DER-CTRL-004: 配对窗口超时后协议注入无效 | strategy: positive, negative, state_transition | acceptance: derived | source: historical_reference | validation: runtime_case
- DER-CTRL-005: 清除遥控器链路完整 | strategy: positive, negative, state_transition | acceptance: derived | source: word_table | validation: runtime_case
