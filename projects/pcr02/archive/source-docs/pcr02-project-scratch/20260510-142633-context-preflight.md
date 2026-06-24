# Context Compression Preflight

## 目标
- 本轮目标：
- 期望输出：

## 当前状态
- 仓库：~/work/sigmastar/pcr02_ssc305/SourceCode/sdk/verify/xcrz_sigmastar_demo
- 分支：dev/pcr02
- 关键文件：
- 已完成：
- 未完成：

### 工作区状态

```text
 M libs/3rdparty/nanopb/python/site-packages/nanopb/generator/proto/nanopb_pb2.py
 M libs/arm/libs/glibc/11.1.0/dynamic/libapi.so
 M libs/arm/libs/glibc/11.1.0/dynamic/libapp.so
 M libs/arm/libs/glibc/11.1.0/dynamic/libbridge.so
 M libs/arm/libs/glibc/11.1.0/dynamic/libcommon.so
 M libs/arm/libs/glibc/11.1.0/dynamic/libhdi.so
 M libs/arm/libs/glibc/11.1.0/dynamic/libproto.so
 M libs/arm/libs/glibc/11.1.0/dynamic/libsensor.so
 M libs/arm/libs/glibc/11.1.0/dynamic/libwifi_manager.so
 M libs/arm/libs/glibc/11.1.0/static/libapi.a
 M libs/arm/libs/glibc/11.1.0/static/libapp.a
 M libs/arm/libs/glibc/11.1.0/static/libbridge.a
 M libs/arm/libs/glibc/11.1.0/static/libcommon.a
 M libs/arm/libs/glibc/11.1.0/static/libhdi.a
 M libs/arm/libs/glibc/11.1.0/static/libproto.a
 M libs/arm/libs/glibc/11.1.0/static/libsensor.a
 M libs/arm/libs/glibc/11.1.0/static/libwifi_manager.a
 M pcr02/dep.mk
 M pcr02/main.cpp
 M pcr02/pcr02.mk
?? .clang-format_c
?? .codex
?? .kilo/
?? app_main/
?? app_ota/
?? app_product_test/
?? build/app_3rdparty.mk
?? build/app_common.mk
?? build/app_sigmastar.mk
?? build/check_diag_layer_deps.py
?? build/check_diag_naming.py
?? build/check_diag_phase6_static.py
?? clean_make.sh
?? cli/
?? cmd_server/
?? daemon/
?? docs/2026-05-07-app-diag-final-plan.md
?? docs/2026-05-07-app-diag-release-notes.md
?? docs/2026-05-07-app-diag-verification-report.md
?? docs/2026-05-07-app-diag-work-orders.md
?? docs/2026-05-08-sigmastar-aov-lightsensor-analysis.md
?? docs/c_coding_standards.20260507
?? docs/common/
?? docs/embedded-linux-thread-design-troubleshooting-optimization.md
?? docs/irlight-sw-threshold-calibration.md
?? docs/project/
?? docs/superpowers/
?? examples/
?? include/api/api_diag_dvr_provider.h
?? include/api/api_diag_media_provider.h
?? include/api/api_diag_test_provider.h
?? include/app/
?? include/common/diag/
?? include/hdi/hdi_diag_test_provider.h
?? include/hdi/hdi_diag_vi_provider.h
?? install_make.sh
?? libs/3rdparty/nanopb/bin/__pycache__/nanopb_generator.cpython-38.pyc
?? libs/3rdparty/nanopb/python/site-packages/nanopb/__pycache__/__init__.cpython-38.pyc
?? libs/3rdparty/nanopb/python/site-packages/nanopb/generator/__pycache__/__init__.cpython-38.pyc
?? libs/3rdparty/nanopb/python/site-packages/nanopb/generator/__pycache__/nanopb_generator.cpython-38.pyc
?? libs/3rdparty/nanopb/python/site-packages/nanopb/generator/proto/__pycache__/__init__.cpython-38.pyc
?? libs/3rdparty/nanopb/python/site-packages/nanopb/generator/proto/__pycache__/_utils.cpython-38.pyc
?? libs/3rdparty/nanopb/python/site-packages/nanopb/generator/proto/__pycache__/nanopb_pb2.cpython-38.pyc
?? libs/arm/libs/glibc/11.1.0/dynamic/libproto_c.so
?? libs/arm/libs/glibc/11.1.0/static/libproto_c.a
?? make.sh
?? modules/app/
?? modules/proto_c/
?? modules/wifi/
```

### 变更规模

```text
.../nanopb/generator/proto/nanopb_pb2.py           | 547 +++++++++++++++++++--
 libs/arm/libs/glibc/11.1.0/dynamic/libapi.so       | Bin 2344380 -> 1764664 bytes
 libs/arm/libs/glibc/11.1.0/dynamic/libapp.so       | Bin 258464 -> 434180 bytes
 libs/arm/libs/glibc/11.1.0/dynamic/libbridge.so    | Bin 4721988 -> 4726780 bytes
 libs/arm/libs/glibc/11.1.0/dynamic/libcommon.so    | Bin 6100720 -> 6119984 bytes
 libs/arm/libs/glibc/11.1.0/dynamic/libhdi.so       | Bin 1330876 -> 1335712 bytes
 libs/arm/libs/glibc/11.1.0/dynamic/libproto.so     | Bin 9767564 -> 10186788 bytes
 libs/arm/libs/glibc/11.1.0/dynamic/libsensor.so    | Bin 27182492 -> 27147588 bytes
 .../libs/glibc/11.1.0/dynamic/libwifi_manager.so   | Bin 11196232 -> 11207220 bytes
 libs/arm/libs/glibc/11.1.0/static/libapi.a         | Bin 4328924 -> 3415438 bytes
 libs/arm/libs/glibc/11.1.0/static/libapp.a         | Bin 412210 -> 725618 bytes
 libs/arm/libs/glibc/11.1.0/static/libbridge.a      | Bin 8006512 -> 8011892 bytes
 libs/arm/libs/glibc/11.1.0/static/libcommon.a      | Bin 11378804 -> 11401754 bytes
 libs/arm/libs/glibc/11.1.0/static/libhdi.a         | Bin 2236144 -> 2237644 bytes
 libs/arm/libs/glibc/11.1.0/static/libproto.a       | Bin 20362686 -> 21041868 bytes
 libs/arm/libs/glibc/11.1.0/static/libsensor.a      | Bin 96841680 -> 96787028 bytes
 .../arm/libs/glibc/11.1.0/static/libwifi_manager.a | Bin 23772854 -> 23784586 bytes
 pcr02/dep.mk                                       |  11 +-
 pcr02/main.cpp                                     |  56 ++-
 pcr02/pcr02.mk                                     |   4 +-
 20 files changed, 567 insertions(+), 51 deletions(-)
```

### 最近提交

```text
7956361 change extrinsic params for navi and fix bug of missing xcrz_data_struct.h
94d0b98 增加示弱后退距离的配置
a2fe4e8 docs(asan): add AddressSanitizer debug guide and vendor libasan shared library
d6a0ad2 refactor(build): remove xcrz_application module and its embedded source tree
e253acc 🏗️build(libs): update libiot and libtask static ARM binaries for glibc 11.1.0
```

## 关键决策（只保留可复用）
- 决策 1：
- 决策 2：

## 约束与风险
- 约束：
- 风险：

## 下一步（可执行）
- Step 1:
- Step 2:
- Step 3:

## 验证命令
- `rtk bash scripts/check.sh`
- `rtk git diff --check`

## 恢复提示（Resume Prompt）
继续处理：<一句话任务>
从这些文件继续：<path1>, <path2>
先执行：<第一条命令>
