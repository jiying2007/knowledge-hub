---
title: V1 到主分支迁移执行计划
doc_type: plan
knowledge_type: process
maturity: draft
status: archived
owner: team-core
created: 2026-05-06
last_updated: 2026-05-12
tags: [v1, migration, plan]
---

# V1 到主分支迁移执行计划

> 归档说明：本文为历史计划，未勾选步骤不代表当前待办；重新执行前必须重新核对源码、构建脚本和验证命令。

## 1. 迁移目标

将 V1 中比主分支好的实现合入主分支，并完善未完成的功能。

## 2. 迁移清单

### 2.1 P0 高优先级 (核心功能)

#### 任务 1: 迁移 api_ai 模块
- **源目录**: examples/robot_pcr02_v1/modules/api/src/api_ai/
- **目标目录**: modules/api/src/api_ai/
- **文件清单**:
  - api_action.c
  - api_blackboard.c
  - api_bt.c
  - api_decisiontree.c
  - api_evaluator.c
  - api_fsm.c
  - api_knowledge.c
- **头文件**: include/api/ (7个文件)
- **待完善**:
  - 补充函数注释
  - 添加错误码定义
  - 完善边界条件检查

#### 任务 2: 迁移 api_robot 模块
- **源目录**: examples/robot_pcr02_v1/modules/api/src/api_robot/
- **目标目录**: modules/api/src/api_robot/
- **文件清单**:
  - api_astar.c
  - api_grid_map.c
  - api_kalman.c
  - api_kinematics.c
  - api_pid.c
- **头文件**: include/api/ (5个文件)
- **待完善**:
  - 添加参数校验
  - 补充单元测试
  - 优化算法性能

### 2.2 P1 中优先级 (通用组件)

#### 任务 3: 迁移 api_system 模块
- **源目录**: examples/robot_pcr02_v1/modules/api/src/api_system/
- **目标目录**: modules/api/src/api_system/
- **文件清单**:
  - api_array_allocator.c
  - api_eventloop.c
  - api_task_queue.c
  - api_vector.c
- **头文件**: include/api/ (5个文件)
- **待完善**:
  - 完善错误处理
  - 添加线程安全保护

#### 任务 4: 迁移 api_codec 模块
- **源目录**: examples/robot_pcr02_v1/modules/api/src/api_codec/
- **目标目录**: modules/api/src/api_codec/
- **文件清单**:
  - api_byteorder.c
  - api_charset.c
  - api_hex.c
  - api_string_builder.c
  - api_string_hash.c
  - api_string_split.c
- **头文件**: include/api/ (6个文件)
- **待完善**:
  - 添加参数校验
  - 补充边界检查

#### 任务 5: 合并 api_container 增量
- **源目录**: examples/robot_pcr02_v1/modules/api/src/api_container/
- **目标目录**: modules/api/src/api_container/
- **新增文件**:
  - api_bitset.c
  - api_blocked_queue.c
  - api_priority_queue.c
  - api_rbtree.c
  - api_skiplist.c
- **头文件**: include/api/ (5个文件)

#### 任务 6: 合并 api_network 增量
- **源目录**: examples/robot_pcr02_v1/modules/api/src/api_network/
- **目标目录**: modules/api/src/api_network/
- **新增文件**:
  - api_conn_pool.c
  - api_http_utils.c
  - api_io_opt.c
  - api_local_ip.c
  - api_multi_socket.c
- **头文件**: include/api/ (5个文件)

#### 任务 7: 合并 api_utils 增量
- **源目录**: examples/robot_pcr02_v1/modules/api/src/api_utils/
- **目标目录**: modules/api/src/api_utils/
- **新增文件**:
  - api_buffered_writer.c
  - api_error_mapper.c
  - api_id_generator.c
  - api_json.c
- **头文件**: include/api/ (4个文件)

### 2.3 P2 低优先级 (增强功能)

#### 任务 8: 合并 app_product_test 增量
- **源目录**: examples/robot_pcr02_v1/app_product_test/
- **目标目录**: app_product_test/
- **新增文件**:
  - pt_perf_sd.c
  - pt_perf_sys.c
  - pt_sd.c
  - pt_wifi.c

## 3. 执行顺序

1. **第一阶段**: P0 任务 (任务 1, 2)
2. **第二阶段**: P1 任务 (任务 3, 4, 5, 6, 7)
3. **第三阶段**: P2 任务 (任务 8)
4. **第四阶段**: 完善与验证

## 4. 验证标准

### 4.1 代码规范
- 匈牙利命名法
- Allman 大括号风格
- 尤达条件判断
- 指针 NULL 防护

### 4.2 编译验证
- 每个模块单独编译通过
- 集成编译无错误
- 无警告

### 4.3 功能验证
- 函数接口正确
- 边界条件处理
- 错误处理完善

## 5. 风险控制

### 5.1 兼容性检查
- 验证函数签名
- 检查数据结构
- 确认依赖关系

### 5.2 回滚策略
- 每个任务完成后提交
- 保留迁移前的备份
- 出现问题及时回滚

---

**计划制定时间**: 2026-05-06
**执行人**: Coder
**状态**: ✅ 计划完成
