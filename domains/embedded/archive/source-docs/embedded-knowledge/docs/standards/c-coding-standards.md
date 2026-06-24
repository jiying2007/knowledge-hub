---
title: 项目定制 C 语言代码规范
doc_type: standard
knowledge_type: guideline
maturity: verified
status: active
owner: team-core
created: 2026-05-12
last_updated: 2026-05-12
tags: [c, coding-standard]
related: []
validation_refs: []
---

# 项目定制 C 语言代码规范

本规范基于当前项目中 `include`、`hdi`、`api`、`app` 目录下的代码风格提炼而成。所有新编写的 C 代码均应遵循本规范。

## 0. 适用范围与执行边界 (Scope & Enforcement)

### 0.1 适用范围
*   本规范适用于本仓库内业务 C 代码及对外头文件，包括但不限于：`modules/hdi`、`modules/api`、`modules/app`、`include/hdi`、`include/api`、`include/app`。
*   新增代码、修改代码、重构代码均必须满足本规范，不区分“存量”与“增量”。

### 0.2 第三方/移植代码边界
*   对明确来源于第三方或芯片厂商的导入代码（例如带外部版权头的文件），原则上保持原有实现语义，不做与业务无关的风格性重写。
*   若必须修改第三方/移植代码，修改部分应尽量遵循本规范；若因上游接口、ABI、回调签名等原因无法完全遵循，必须将偏离约束在最小范围，并在代码注释或提交说明中写明原因。

### 0.3 执行要求
*   本规范为强制要求，代码评审、联调提测、发布前检查均按本规范执行。
*   对不符合项不得以“历史代码”为由豁免；触达即整改。

## 1. 命名规范 (Naming Conventions)

本项目采用 **模块前缀** 结合 **匈牙利命名法 (Hungarian Notation)** 的混合命名风格。

### 1.1 模块与通用前缀
*   **全局接口与类型** 必须带有模块前缀，例如：`VSAPILIST_`、`VSAPIMSG_`、`VSHDIOS_` 等。
*   **基础类型** 统一使用 `VS_` 前缀，如 `VS_S32`, `VS_U32`, `VS_BOOL`, `VS_VOID`, `VS_CHAR`。
*   **通用宏定义** 使用 `VS_` 前缀，如 `VS_SUCCESS`, `VS_FAILURE`, `VS_TRUE`, `VS_FALSE`, `VS_INVALID_ID`。

### 1.2 变量命名 (匈牙利命名法)
变量名需以前缀标明其类型，主体采用大驼峰（PascalCase）或小驼峰（camelCase）命名：
*   **`p`** / **`pv`**: 指针 (Pointer / Pointer to void)，如 `pvData`, `pvMsg`。
*   **`pst`**: 结构体指针 (Pointer to Struct)，如 `pstList`, `pstNode`, `pstQueue`。
*   **`st`**: 结构体实例 (Struct)，如 `stListHead`。
*   **`u32`** / **`u16`** / **`u8`**: 无符号整型，如 `u32MutexId`, `u32MsgLen`。
*   **`s32`** / **`s16`** / **`s8`**: 有符号整型，如 `s32Ret`, `s32Index`。
*   **`b`**: 布尔类型 (`VS_BOOL`)，如 `bRet`, `bBlock`, `bUsePool`。
*   **`ac`**: 字符数组/字符串 (Array of Char)，如 `acName`。
*   **`au8`**: 字节数组 (Array of uint8)，如 `au8Data`。
*   **`en`**: 枚举变量 (Enum)，如 `enPriority`。
*   **`g_`**: 全局变量 (Global)，如 `g_bInitialized`, `g_astQueueElems`。

### 1.3 函数命名
*   **对外接口 (Public API)**：`模块前缀_动作目标()`，采用大驼峰。
    ```c
    VS_S32 VSAPIMSG_Create(...);
    VS_VOID *VSAPILIST_SearchNode(...);
    VS_S32 VSAPPDIAG_CmdNodeInit(...);
    ```
*   当模块名较长或包含缩写时，保持“模块前缀 + 下划线 + 动作目标”的单下划线分段形式，避免连写风格（如 `VSAPPDIAGCMDNODE_Init`）。
*   同一模块内命名风格必须单轨统一：例如 `VSAPPDIAG_CenterInit` / `VSAPPDIAG_RegistryInit` / `VSAPPDIAG_NodeBridgeStart`，禁止同模块并存 `VSAPPDIAGCENTER_*` 与 `VSAPPDIAG_Center*` 两套风格。
*   **内部静态函数 (Private Static)**：以单下划线开头，采用大驼峰。
    ```c
    static VS_BOOL _LIST_IsEmpty(VSAPILIST_List_t *pstList);
    static VS_S32 _FindFreeQueueIndex(VS_VOID);
    ```
*   **下划线前缀与链接属性必须一致**：凡是以 `_` 开头的函数，必须声明为 `static` 内部函数；非 `static` 函数禁止使用 `_` 前缀，必须使用模块前缀对外命名。

### 1.4 自定义类型命名 (Struct / Enum)
*   **结构体声明**：内部原始定义带有 `_` 前缀，对外 `typedef` 名称以 `_t` 结尾，并带有模块前缀。
    ```c
    typedef struct _List_t
    {
        // ...
    } VSAPILIST_List_t;
    ```
*   **枚举声明**：对外 `typedef` 名称以 `_e` 结尾。
    ```c
    typedef enum
    {
        // ...
    } VSAPIMSG_Priority_e;
    ```

### 1.5 基础类型与外部接口边界
*   模块内部实现优先使用 `VS_*` 基础类型（如 `VS_S32`、`VS_U64`、`VS_BOOL`）。
*   与标准库、系统调用、第三方库、编译器回调签名对接时，可按外部接口要求使用标准 C 类型（如 `double`、`size_t`、`unsigned long`、`bool`）。
*   标准 C 类型应限制在接口边界层，进入模块内部后应尽快转换为 `VS_*` 类型，避免类型体系在业务逻辑中扩散。
*   日志打印与格式化输出必须与实际类型匹配；如需跨类型打印，应显式转换后再输出。

## 2. 代码格式排版 (Formatting & Bracing)

本项目采用 **Mozilla / Allman 混合风格**，由 `.clang-format` 保证基础排版，以下为必须遵守的核心排版原则：

### 2.1 缩进与空格
*   使用 **4个空格** 进行缩进，**绝对禁止使用 Tab** (`UseTab: Never`, `IndentWidth: 4`)。
*   行宽限制：单行代码最大字符数限制为 **120个字符** (`ColumnLimit: 120`)。
*   关键字（`if`, `for`, `while`, `switch`）后必须保留一个空格 (`SpaceBeforeParens: ControlStatements`)。
*   指针声明对齐：指针星号 `*` 靠近变量名，如 `VS_VOID *pvData` (`PointerAlignment: Right`)。
*   强制对齐：宏定义的值、连续的赋值操作等不需要刻意使用空格对齐 (`AlignConsecutiveMacros: false`, `AlignConsecutiveAssignments: false`)。

### 2.2 大括号 `{}` 位置 (Allman Style)
*   所有左大括号 `{` **必须独占一行**，并与其控制语句左对齐 (`BreakBeforeBraces: Custom`, 所有 `After...: true`)。
    ```c
    // 函数定义
    VS_S32 VSAPIMSG_Init(VS_VOID)
    {
        // ...
    }

    // 控制语句
    if (NULL == pstList)
    {
        return VS_FALSE;
    }
    else
    {
        // ...
    }
    ```
*   **单行语句强制使用大括号**。即使 `if`、`for`、`while` 下只有一行代码，也**绝对禁止**省略大括号包裹（包括 `return`、`break`、`continue` 等短语句）。严禁出现如 `if (xxx) return;` 或将单行逻辑紧跟在条件后的写法 (`AllowShortBlocksOnASingleLine: false`, `AllowShortIfStatementsOnASingleLine: Never`, `AllowShortLoopsOnASingleLine: false`)。

## 3. 编程习惯与逻辑控制 (Best Practices)

### 3.1 尤达条件判断 (Yoda Conditions)与布尔判断
在进行相等或不等比较时，必须将常量、宏或明确定义的值放在比较运算符的左侧。
```c
// 强制推荐写法
if (NULL == pstList)
if (VS_SUCCESS != s32Ret)
if (0 >= s32MsgCount)

// 禁止写法
if (pstList == NULL)
if (s32Ret != VS_SUCCESS)
```

**布尔类型特例**：对于 `VS_BOOL` (或 `bool`) 类型的变量在 `if`/`while` 等条件判断中，**禁止** 使用 `VS_TRUE == bVar` 或 `VS_FALSE == bVar` 的写法，必须直接使用变量本身或取反：
```c
// 强制推荐写法
if (bRunning)
if (!bInitialized)

// 禁止写法
if (VS_TRUE == bRunning)
if (bInitialized == VS_FALSE)
```

### 3.2 变量声明与初始化
*   **局部变量定义位置**：所有局部变量必须在函数或代码块的**头部**集中定义。禁止在代码逻辑中间或 `for` 循环内部直接声明变量。
*   **建议始终定义返回变量**：对于有返回值的函数，强烈建议在函数头部定义一个专用的返回变量（如 `VS_S32 s32Ret = VS_SUCCESS;`），以统一函数的返回出口，避免多处直接 `return` 导致的资源泄露或逻辑混乱。
*   **变量声明顺序**：
    1.  首位：返回变量（如 `s32Ret`）。
    2.  次位：重要状态标志或核心操作对象指针（如 `bIsReady`, `pstNode`）。
    3.  其余变量：尽量按照在函数逻辑中**调用的先后顺序**自上而下进行声明，以提升代码的可读性。

    ```c
    // 强制推荐写法
    VS_S32 VSAPIMSG_Process(VS_VOID)
    {
        VS_S32 s32Ret = VS_SUCCESS;   // 1. 返回变量放首位
        VSAPILIST_Node_t *pstNode = NULL; // 2. 核心指针
        VS_U32 u32Idx = 0;            // 3. 循环变量或后续使用的变量
        VS_CHAR acBuffer[256] = {0};  // 4. 后续使用的局部缓存

        // 逻辑代码
        pstNode = _GetNode();
        if (NULL == pstNode)
        {
            s32Ret = VS_FAILURE;
            return s32Ret;
        }

        for (u32Idx = 0; u32Idx < 10; u32Idx++)
        {
            // ...
        }

        return s32Ret; // 统一返回
    }

    // 禁止写法
    VS_S32 VSAPIMSG_Process(VS_VOID)
    {
        // 逻辑代码...
        VS_S32 s32Ret = 0; // 不要在中间定义

        for (VS_U32 u32Idx = 0; u32Idx < 10; u32Idx++) // 禁止在 for 中定义
        {
            // ...
        }
        return s32Ret;
    }
    ```

### 3.3 忽略返回值的显式类型转换
对于不需要处理返回值的函数调用，应在函数前强制转换为 `(VS_VOID)`，以明确告知审查者这是有意忽略返回值的行为 (`SpaceAfterCStyleCast: false`)。
```c
(VS_VOID)VSHDIOS_MutexLock(pstList->u32MutexId);
(VS_VOID)VSHDIOS_MemFree(pstNode);
```

### 3.4 基础内存与安全指针操作
*   **指针初始化与置空**：指针声明时须初始化为 `NULL`。调用 `VSHDIOS_MemFree` 等释放内存后，必须立刻将指针重新置为 `NULL` 以防止悬挂指针（野指针）。
    ```c
    VSAPILIST_Node_t *pstNode = NULL;
    // ...
    if (NULL != pstNode)
    {
        (VS_VOID)VSHDIOS_MemFree(pstNode);
        pstNode = NULL; // 释放后必须置空
    }
    ```
*   **指针参数校验**：所有对外接口的入参如果包含指针，在函数开头必须进行 `NULL` 校验。
*   使用系统二次封装的 API（如 `VSHDIOS_MemMalloc` / `VSHDIOS_MemFree`）替代原生的 `malloc` 和 `free`。如果存在内存预分配池机制，优先使用内存池实现以防碎片化。

## 4. 头文件规范 (Header Files)

### 4.1 宏防卫 (Include Guards)
使用全大写的宏定义防止头文件重复包含。格式为 `__模块名_H__`。
```c
#ifndef __API_LIST_H__
#define __API_LIST_H__

// 内容

#endif /* End of #ifndef __API_LIST_H__ */
```

### 4.2 C++ 兼容性宏块
为了在 C++ 环境下复用，暴露的 C 语言 API 外层必须用 `extern "C"` 包装块覆盖：
```c
#ifdef __cplusplus
#if __cplusplus
extern "C"
{
#endif /* End of #if __cplusplus */
#endif /* End of #ifdef __cplusplus */

    // 所有的 Typedefs，宏，函数声明...

#ifdef __cplusplus
#if __cplusplus
}
#endif /* End of #if __cplusplus */
#endif /* End of #ifdef __cplusplus */
```

## 5. 日志与调试 (Logging & Debugging)
*   **模块级调试控制**：每个 `.c` 模块通过定义内部的宏（如 `#define API_MSG_DEBUG_LEVEL DEBUG_LEVEL_INFO`）来单独控制该模块打印等级，并在随后 `#undef DEBUG_LEVEL` 及重定义。
*   使用封装好的日志宏（如 `DBG_INFO`, `DBG_ERROR`）输出日志，禁止直接使用 `printf`。

## 6. 函数组织与顺序 (Function Organization & Ordering)

### 6.1 `.c` 文件中 `static` / `extern` 函数顺序
*   **所有 `static` 内部函数必须统一放在所有对外接口函数之前**，禁止与对外接口函数穿插。
*   推荐顺序：
    1. 文件级宏 / 全局静态变量
    2. `static` 辅助函数（按功能分组）
    3. 对外接口函数（`VS...` / `VSHDI...` 等）
*   对外接口开始处建议增加分段注释，提升可读性。

```c
/* 静态辅助函数 */
static VS_VOID _ModHelperA(VS_VOID)
{
    // ...
}

static VS_S32 _ModHelperB(VS_U32 u32Input)
{
    // ...
}

/* 对外接口函数 */
VS_S32 VSMOD_Init(VS_VOID)
{
    // ...
}
```

### 6.2 头文件声明顺序与实现顺序一致
*   `.h` 中对外函数声明顺序应与 `.c` 中对外实现顺序保持一致，便于检索、review 与维护。
*   当 `.c` 中函数分组调整后，必须同步更新对应头文件声明顺序。

```c
/* hdi_os.h */
VS_VOID VSHDIOS_ThreadDebugSetFlags(VS_U32 u32Flags);
VS_U32 VSHDIOS_ThreadDebugGetFlags(VS_VOID);
VS_VOID VSHDIOS_ThreadMonitorEnable(VS_BOOL bEnable);
/* ... */

/* hdi_os_thread.c 中保持同序实现 */
VS_VOID VSHDIOS_ThreadDebugSetFlags(VS_U32 u32Flags) { /* ... */ }
VS_U32 VSHDIOS_ThreadDebugGetFlags(VS_VOID) { /* ... */ }
VS_VOID VSHDIOS_ThreadMonitorEnable(VS_BOOL bEnable) { /* ... */ }
```
