---
id: provider-5d328cbc0cd7b94a4a8cc6f684d4cc76c1d79fff46420826dedf632d7b8f2be3
title: A123X平台知识库API上卷：ADLA CVE DEWARP ISP AE AWB MIPI VI PPU
kind: runbook
domain: projects/a123x
path: projects/a123x/archive/provider-5d328cbc0cd7b94a4a8cc6f684d4cc76c1d79fff46420826dedf632d7b8f2be3.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: provider-candidate-archive
  from: operation:5d328cbc0cd7b94a4a8cc6f684d4cc76c1d79fff46420826dedf632d7b8f2be3
  source_sha256: 2ab9fce900ceb4aacfb7573e7e6375c88829168f5527dfcd877ffeb7e23346c7
  temporary_source_retained: false
review_after: '2027-01-21'
review_status: manual-entry-pending-review
content_review_status: pending
evidence_validation_status: pending
promotion: none
promotion_decision: none; capture does not authorize active promotion or owner decision
tags:
- provider-archive
- runbook
- A123X
- 平台知识库
- 完整知识卷
validation_refs:
- projects/a123x/archive/provider-5d328cbc0cd7b94a4a8cc6f684d4cc76c1d79fff46420826dedf632d7b8f2be3.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/a123x/archive/provider-5d328cbc0cd7b94a4a8cc6f684d4cc76c1d79fff46420826dedf632d7b8f2be3.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-10-23'
updated_at: '2026-10-23'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-10-23'
manual_validation_pending: true
summary_zh: 核对日期：2026-10-23；来源为本地供应商资料和当前RC1源码。AI辅助整理，reviewing候选；仅供内部授权使用。资料/源码事实、项目回传证据与本轮设备实测分开；本轮未操作设备。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
subject_ref: &id001
  type: project
  id: a123x
created_subject_ref: *id001
principal_id: local-user
provider_operation_id: 5d328cbc0cd7b94a4a8cc6f684d4cc76c1d79fff46420826dedf632d7b8f2be3
provenance:
  source_kind: session-conclusion
  source_ref: sanitized-conclusion
  verification_state: declared
---

# A123X平台知识库API上卷：ADLA CVE DEWARP ISP AE AWB MIPI VI PPU

核对日期：2026-10-23；来源为本地供应商资料和当前RC1源码。AI辅助整理，reviewing候选；仅供内部授权使用。资料/源码事实、项目回传证据与本轮设备实测分开；本轮未操作设备。

## A123X平台知识库API：mbi_adla 当前RC1接口签名与PDF页码

核对日期：2026-10-23；来源为本地供应商资料和当前RC1源码。AI辅助整理，reviewing候选；仅供内部授权使用。资料/源码事实、项目回传证据与本轮设备实测分开；本轮未操作设备。

这是当前头文件公开声明的精确速查，不是示例调用或二进制ABI认证。参数类型与参数顺序以此快照为准；结构体布局及条件编译需结合匹配头文件。返回码/阻塞/资源所有权只在对应主题与手册核实后使用。

来源：`workspaces/ipc-c5-rc.1.0/linux/mbp/mbi/adla/include/mbi_adla.h`；SHA-256 `07f8cfa75279f610982ccc46f3769aeb46243ddc301e893542a40c6976c945fa`。

| 接口 | 当前声明 | 源码行 | 对应新版MBI手册物理页 |
| --- | --- | --- | --- |
| `MBI_ADLA_LoadModel` | `MBP_S32 MBI_ADLA_LoadModel(const ADLA_SRC_MEM_INFO_T *pstModelBuf,ADLA_MODEL_T *pstModel);` | 242 | IPC SDK ADLA MBI (0.5).pdf p4,6,7 |
| `MBI_ADLA_GetTskBufSize` | `MBP_S32 MBI_ADLA_GetTskBufSize(MBP_U32 u32MaxBatchNum, MBP_U32 u32MaxBboxNum, const ADLA_MODEL_T *pstModel, MBP_U32 au32TskBufSize[],MBP_U32 u32NetSegNum);` | 243 | IPC SDK ADLA MBI (0.5).pdf p4,6,7,8 |
| `MBI_ADLA_Forward` | `MBP_S32 MBI_ADLA_Forward(ADLA_HANDLE_T *phAdlaHandle, const ADLA_SRC_BLOB_T astSrc[],const ADLA_MODEL_T *pstModel, ADLA_DST_BLOB_T astDst[],const ADLA_FORWARD_CTRL_T *pstForwardCtrl, MBP_BOOL_E bInstant);` | 244 | IPC SDK ADLA MBI (0.5).pdf p4,6,8,9 |
| `MBI_ADLA_Query` | `MBP_S32 MBI_ADLA_Query(ADLA_ID_E enAdlaId,ADLA_HANDLE_T AdlaHandle, MBP_BOOL_E *pbFinish, MBP_BOOL_E bBlock);` | 246 | IPC SDK ADLA MBI (0.5).pdf p4,6,10,11 |
| `MBI_ADLA_UnloadModel` | `MBP_S32 MBI_ADLA_UnloadModel(ADLA_MODEL_T *pstModel);` | 247 | IPC SDK ADLA MBI (0.5).pdf p4,6,11,12 |
| `MBI_ADLA_AddTskBuf` | `MBP_S32 MBI_ADLA_AddTskBuf(const ADLA_MEM_INFO_T* pstTskBuf);` | 248 | 当前新版MBI手册未检出，需源码/其他文档核验 |
| `MBI_ADLA_RemoveTskBuf` | `MBP_S32 MBI_ADLA_RemoveTskBuf(const ADLA_MEM_INFO_T* pstTskBuf);` | 249 | 当前新版MBI手册未检出，需源码/其他文档核验 |
| `MBI_ADLA_ForwardWithBbox` | `MBP_S32 MBI_ADLA_ForwardWithBbox(ADLA_HANDLE_T *phAdlaHandle, const ADLA_SRC_BLOB_T astSrc[], const ADLA_SRC_BLOB_T astBbox[], const ADLA_MODEL_T *pstModel, ADLA_DST_BLOB_T astDst[],const ADLA_FORWARD_CTRL_T *pstForwardCtrl, MBP_BOOL_E bInstant);` | 250 | 当前新版MBI手册未检出，需源码/其他文档核验 |

## A123X平台知识库API：mbi_cve 当前RC1接口签名与PDF页码

核对日期：2026-10-23；来源为本地供应商资料和当前RC1源码。AI辅助整理，reviewing候选；仅供内部授权使用。资料/源码事实、项目回传证据与本轮设备实测分开；本轮未操作设备。

这是当前头文件公开声明的精确速查，不是示例调用或二进制ABI认证。参数类型与参数顺序以此快照为准；结构体布局及条件编译需结合匹配头文件。返回码/阻塞/资源所有权只在对应主题与手册核实后使用。

来源：`workspaces/ipc-c5-rc.1.0/linux/mbp/mbi/cve/include/mbi_cve.h`；SHA-256 `75100801beb6b53e32efcf50e875f724e6b2c539a434900a39ac5e7c5462369b`。

| 接口 | 当前声明 | 源码行 | 对应新版MBI手册物理页 |
| --- | --- | --- | --- |
| `MBI_CVE_DMA` | `MBP_S32 MBI_CVE_DMA(CVE_HANDLE *pCveHandle, CVE_DATA_T *pstSrc, CVE_DST_DATA_T *pstDst, CVE_DMA_CTRL_T *pstDmaCtrl, MBP_BOOL_E bInstant);` | 37 | IPC SDK CVE MBI (0.7).pdf p4,10,12 |
| `MBI_CVE_LumaStatArray` | `MBP_S32 MBI_CVE_LumaStatArray(CVE_HANDLE *pCveHandle, CVE_SRC_IMAGE_T *pstSrc, CVE_DST_MEM_INFO_T *pstDst, const CVE_RECT_U16_T astCveLumaRect[], CVE_LUMA_STAT_ARRAY_CTRL_T *pstLumaStatArrayCtrl, MBP_BOOL_E bInstant);` | 39 | IPC SDK CVE MBI (0.7).pdf p4,10,14,15 |
| `MBI_CVE_Filter` | `MBP_S32 MBI_CVE_Filter(CVE_HANDLE *pCveHandle, CVE_SRC_IMAGE_T *pstSrc, CVE_DST_IMAGE_T *pstDst, CVE_DST_MEM_INFO_T *pstDstMem, CVE_FILTER_CTRL_T *pstFltCtrl, MBP_BOOL_E bInstant);` | 43 | IPC SDK CVE MBI (0.7).pdf p4,10,16,19,20,21,52 |
| `MBI_CVE_CSC` | `MBP_S32 MBI_CVE_CSC(CVE_HANDLE *pCveHandle, CVE_SRC_IMAGE_T *pstSrc, CVE_DST_IMAGE_T *pstDst, CVE_CSC_CTRL_T *pstCscCtrl, MBP_BOOL_E bInstant);` | 46 | IPC SDK CVE MBI (0.7).pdf p4,10,19,21 |
| `MBI_CVE_FilterAndCSC` | `MBP_S32 MBI_CVE_FilterAndCSC(CVE_HANDLE *pCveHandle, CVE_SRC_IMAGE_T *pstSrc, CVE_DST_IMAGE_T *pstDst, CVE_FILTER_AND_CSC_CTRL_T *pstFltCscCtrl, MBP_BOOL_E bInstant);` | 48 | IPC SDK CVE MBI (0.7).pdf p4,10,19,20 |
| `MBI_CVE_Dilate` | `MBP_S32 MBI_CVE_Dilate(CVE_HANDLE *pCveHandle, CVE_SRC_IMAGE_T *pstSrc, CVE_DST_IMAGE_T *pstDst, CVE_DILATE_CTRL_T *pstDilateCtrl, MBP_BOOL_E bInstant);` | 51 | IPC SDK CVE MBI (0.7).pdf p4,10,29,33,73 |
| `MBI_CVE_Erode` | `MBP_S32 MBI_CVE_Erode(CVE_HANDLE *pCveHandle, CVE_SRC_IMAGE_T *pstSrc, CVE_DST_IMAGE_T *pstDst, CVE_ERODE_CTRL_T *pstErodeCtrl, MBP_BOOL_E bInstant);` | 53 | IPC SDK CVE MBI (0.7).pdf p4,10,31,32,73 |
| `MBI_CVE_Bernsen` | `MBP_S32 MBI_CVE_Bernsen(CVE_HANDLE *pCveHandle, CVE_SRC_IMAGE_T *pstSrc, CVE_DST_IMAGE_T *pstDst, CVE_BERNSEN_CTRL_T *pstBernsenCtrl, MBP_BOOL_E bInstant);` | 55 | IPC SDK CVE MBI (0.7).pdf p5,11,72,156 |
| `MBI_CVE_Thresh` | `MBP_S32 MBI_CVE_Thresh(CVE_HANDLE *pCveHandle, CVE_SRC_IMAGE_T *pstSrc, CVE_DST_IMAGE_T *pstDst, CVE_THRESH_CTRL_T *pstThrCtrl, MBP_BOOL_E bInstant);` | 57 | IPC SDK CVE MBI (0.7).pdf p4,10,34,36,45,46,47,49,83 |
| `MBI_CVE_Sobel` | `MBP_S32 MBI_CVE_Sobel(CVE_HANDLE *pCveHandle, CVE_SRC_IMAGE_T *pstSrc, CVE_DST_IMAGE_T *pstDstH, CVE_DST_IMAGE_T *pstDstV, CVE_SOBEL_CTRL_T *pstSobelCtrl, MBP_BOOL_E bInstant);` | 59 | IPC SDK CVE MBI (0.7).pdf p4,10,21,27 |
| `MBI_CVE_MagAndAng` | `MBP_S32 MBI_CVE_MagAndAng(CVE_HANDLE *pCveHandle, CVE_SRC_IMAGE_T *pstSrc, CVE_DST_IMAGE_T *pstDstMag, CVE_DST_IMAGE_T *pstDstAng, CVE_MAG_AND_ANG_CTRL_T *pstMagAndAngCtrl, MBP_BOOL_E bInstant);` | 62 | IPC SDK CVE MBI (0.7).pdf p4,10,23 |
| `MBI_CVE_Integ` | `MBP_S32 MBI_CVE_Integ(CVE_HANDLE *pCveHandle, CVE_SRC_IMAGE_T *pstSrc, CVE_DST_IMAGE_T *pstDst, CVE_INTEG_CTRL_T *pstIntegCtrl, MBP_BOOL_E bInstant);` | 65 | IPC SDK CVE MBI (0.7).pdf p4,10,43 |
| `MBI_CVE_Hist` | `MBP_S32 MBI_CVE_Hist(CVE_HANDLE *pCveHandle, CVE_SRC_IMAGE_T *pstSrc, CVE_DST_MEM_INFO_T *pstDst, CVE_HIST_CTRL_T *pstHistCtrl, MBP_BOOL_E bInstant);` | 67 | IPC SDK CVE MBI (0.7).pdf p4,10,44,54 |
| `MBI_CVE_Query` | `MBP_S32 MBI_CVE_Query(CVE_HANDLE cveHandle, MBP_BOOL_E *pbFinish, MBP_BOOL_E bBlock);` | 69 | IPC SDK CVE MBI (0.7).pdf p4,12,71 |
| `MBI_CVE_NCC` | `MBP_S32 MBI_CVE_NCC(CVE_HANDLE *pCveHandle, CVE_SRC_IMAGE_T *pstSrc1, CVE_SRC_IMAGE_T *pstSrc2, CVE_DST_MEM_INFO_T *pstDst, CVE_NCC_CTRL_T *pstNccCtrl, MBP_BOOL_E bInstant);` | 70 | IPC SDK CVE MBI (0.7).pdf p4,10,54,55 |
| `MBI_CVE_NormGrad` | `MBP_S32 MBI_CVE_NormGrad(CVE_HANDLE *pCveHandle, CVE_SRC_IMAGE_T *pstSrc, CVE_DST_IMAGE_T *pstDstH, CVE_DST_IMAGE_T *pstDstV, CVE_DST_IMAGE_T *pstDstHV, CVE_NORM_GRAD_CTRL_T *pstNormGradCtrl, MBP_BOOL_E bInstant);` | 72 | IPC SDK CVE MBI (0.7).pdf p4,11,62 |
| `MBI_CVE_Thresh_S16` | `MBP_S32 MBI_CVE_Thresh_S16(CVE_HANDLE *pCveHandle, CVE_SRC_IMAGE_T *pstSrc, CVE_DST_IMAGE_T *pstDst, CVE_THRESH_S16_CTRL_T *pstThrS16Ctrl, MBP_BOOL_E bInstant);` | 75 | IPC SDK CVE MBI (0.7).pdf p4,10,36,45,46,49 |
| `MBI_CVE_Thresh_U16` | `MBP_S32 MBI_CVE_Thresh_U16(CVE_HANDLE *pCveHandle, CVE_SRC_IMAGE_T *pstSrc, CVE_DST_IMAGE_T *pstDst, CVE_THRESH_U16_CTRL_T *pstThrU16Ctrl, MBP_BOOL_E bInstant);` | 77 | IPC SDK CVE MBI (0.7).pdf p4,10,36,47 |
| `MBI_CVE_OrdStatFilter` | `MBP_S32 MBI_CVE_OrdStatFilter(CVE_HANDLE *pCveHandle, CVE_SRC_IMAGE_T *pstSrc, CVE_DST_IMAGE_T *pstDst, CVE_ORD_STAT_FILTER_CTRL_T *pstOrdStatFltCtrl, MBP_BOOL_E bInstant);` | 79 | IPC SDK CVE MBI (0.7).pdf p4,10,19,51 |
| `MBI_CVE_16BitTo8Bit` | `MBP_S32 MBI_CVE_16BitTo8Bit(CVE_HANDLE *pCveHandle, CVE_SRC_IMAGE_T *pstSrc, CVE_DST_IMAGE_T *pstDst, CVE_16BIT_TO_8BIT_CTRL_T *pst16BitTo8BitCtrl, MBP_BOOL_E bInstant);` | 82 | IPC SDK CVE MBI (0.7).pdf p4,10,49 |
| `MBI_CVE_MatchBgModel` | `MBP_S32 MBI_CVE_MatchBgModel(CVE_HANDLE *pCveHandle, CVE_SRC_IMAGE_T *pstCurImg, CVE_SRC_IMAGE_T *pstPreImg, CVE_MEM_INFO_T *pstBgModel, CVE_DST_IMAGE_T *pstFg, CVE_DST_IMAGE_T *pstBg, CVE_DST_IMAGE_T *pstCurDiffBg, CVE_DST_IMAGE_T *pstFrmDiff, CVE_MATCH_BG_MODEL_CTRL_T *pstMatchBgModelCtrl, MBP_BOOL_E bInstant);` | 85 | IPC SDK CVE MBI (0.7).pdf p4,10,27,29 |
| `MBI_CVE_UpdateBgModel` | `MBP_S32 MBI_CVE_UpdateBgModel(CVE_HANDLE *pCveHandle, CVE_SRC_IMAGE_T *pstCurImg, CVE_MEM_INFO_T *pstBgModel1, CVE_MEM_INFO_T *pstBgModel2, CVE_DST_MEM_INFO_T *pstStatData, CVE_UPDATE_BG_MODEL_CTRL_T *pstUpdateBgModelCtrl, MBP_BOOL_E bInstant);` | 90 | IPC SDK CVE MBI (0.7).pdf p4,10,28 |
| `MBI_CVE_LBP` | `MBP_S32 MBI_CVE_LBP(CVE_HANDLE *pCveHandle, CVE_SRC_IMAGE_T *pstSrc, CVE_DST_IMAGE_T *pstDst, CVE_LBP_CTRL_T *pstLbpCtrl, MBP_BOOL_E bInstant);` | 95 | IPC SDK CVE MBI (0.7).pdf p4,11,60 |
| `MBI_CVE_EqualizeHist` | `MBP_S32 MBI_CVE_EqualizeHist(CVE_HANDLE *pCveHandle, CVE_SRC_IMAGE_T *pstSrc, CVE_DST_IMAGE_T *pstDst, CVE_EQUALIZE_HIST_CTRL_T *pstEqualizeHistCtrl, MBP_BOOL_E bInstant);` | 97 | IPC SDK CVE MBI (0.7).pdf p4,10,45,53,54 |
| `MBI_CVE_CCL` | `MBP_S32 MBI_CVE_CCL(CVE_HANDLE *pCveHandle, CVE_SRC_IMAGE_T *pstSrc, CVE_DST_IMAGE_T *pstDst, CVE_DST_MEM_INFO_T *pstBlob, CVE_CCL_CTRL_T *pstCclCtrl, MBP_BOOL_E bInstant);` | 100 | IPC SDK CVE MBI (0.7).pdf p4,10,56 |
| `MBI_CVE_GMM` | `MBP_S32 MBI_CVE_GMM(CVE_HANDLE *pCveHandle, CVE_SRC_IMAGE_T *pstSrc, CVE_SRC_IMAGE_T *pstFactor, CVE_DST_IMAGE_T *pstFg, CVE_DST_IMAGE_T *pstBg, CVE_MEM_INFO_T *pstModel, CVE_GMM_CTRL_T *pstGmmCtrl, MBP_BOOL_E bInstant);` | 102 | IPC SDK CVE MBI (0.7).pdf p4,11,57 |
| `MBI_CVE_CannyHysEdge` | `MBP_S32 MBI_CVE_CannyHysEdge(CVE_HANDLE *pCveHandle, CVE_SRC_IMAGE_T *pstSrc, CVE_DST_IMAGE_T *pstEdge, CVE_DST_MEM_INFO_T *pstStack, CVE_CANNY_HYS_EDGE_CTRL_T *pstCannyHysEdgeCtrl, MBP_BOOL_E bInstant);` | 105 | IPC SDK CVE MBI (0.7).pdf p4,11,58,59,60 |
| `MBI_CVE_CannyEdge` | `MBP_S32 MBI_CVE_CannyEdge(CVE_IMAGE_T *pstEdge, CVE_MEM_INFO_T *pstStack, CVE_CANNY_EDGE_CTRL_T *pstCannyEdgeCtrl);` | 108 | IPC SDK CVE MBI (0.7).pdf p4,11,59,60 |
| `MBI_CVE_STCandiCorner` | `MBP_S32 MBI_CVE_STCandiCorner(CVE_HANDLE *pCveHandle, CVE_SRC_IMAGE_T *pstSrc, CVE_DST_IMAGE_T *pstLabel, CVE_DST_IMAGE_T *pstCandiCorner, CVE_DST_MEM_INFO_T *pstCandiCornerPoint, CVE_ST_CANDI_CORNER_CTRL_T *pstStCandiCornerCtrl, MBP_BOOL_E bInstant);` | 110 | IPC SDK CVE MBI (0.7).pdf p4,11,66 |
| `MBI_CVE_STCorner` | `MBP_S32 MBI_CVE_STCorner(CVE_SRC_MEM_INFO_T *pstCandiCornerPoint, CVE_DST_MEM_INFO_T *pstCornerPoint, CVE_ST_CORNER_CTRL_T *pstStCornerCtrl);` | 115 | IPC SDK CVE MBI (0.7).pdf p4,11,67 |
| `MBI_CVE_SAD` | `MBP_S32 MBI_CVE_SAD(CVE_HANDLE *pCveHandle, CVE_SRC_IMAGE_T *pstSrc1, CVE_SRC_IMAGE_T *pstSrc2, CVE_DST_IMAGE_T *pstSad, CVE_DST_IMAGE_T *pstThr, CVE_SAD_CTRL_T *pstSadCtrl, MBP_BOOL_E bInstant);` | 117 | IPC SDK CVE MBI (0.7).pdf p4,11,68 |
| `MBI_CVE_BuildLKOpticalFlowPyr` | `MBP_S32 MBI_CVE_BuildLKOpticalFlowPyr( CVE_HANDLE *pCveHandle, CVE_SRC_IMAGE_T *pstSrcPrevPyr, CVE_DST_IMAGE_T astDstPyr[], CVE_BUILD_LK_OPTICAL_FLOW_PYR_CTRL_T *pstBuildLkOptiFlowPyrCtrl, MBP_BOOL_E bInstant);` | 120 | IPC SDK CVE MBI (0.7).pdf p4,11,63 |
| `MBI_CVE_LKOpticalFlowPyr` | `MBP_S32 MBI_CVE_LKOpticalFlowPyr(CVE_HANDLE *pCveHandle, CVE_SRC_IMAGE_T astSrcPrevPyr[], CVE_SRC_IMAGE_T astSrcNextPyr[], CVE_SRC_MEM_INFO_T *pstPrevPts, CVE_MEM_INFO_T *pstNextPts, CVE_DST_MEM_INFO_T *pstStatus, CVE_LK_OPTICAL_FLOW_PYR_CTRL_T *pstLkOptiFlowPyrCtrl, MBP_BOOL_E bInstant);` | 123 | IPC SDK CVE MBI (0.7).pdf p4,11,65 |
| `MBI_CVE_Map` | `MBP_S32 MBI_CVE_Map(CVE_HANDLE *pCveHandle, CVE_SRC_IMAGE_T *pstSrc, CVE_SRC_MEM_INFO_T *pstMap, CVE_DST_IMAGE_T *pstDst, CVE_MAP_CTRL_T *pstMapCtrl, MBP_BOOL_E bInstant);` | 128 | IPC SDK CVE MBI (0.7).pdf p4,10,52,53 |
| `MBI_CVE_And` | `MBP_S32 MBI_CVE_And(CVE_HANDLE *pCveHandle, CVE_SRC_IMAGE_T *pstSrc0, CVE_SRC_IMAGE_T *pstSrc1, CVE_DST_IMAGE_T *pstDst, CVE_AND_CTRL_T *pstAndCtrl, MBP_BOOL_E bInstant);` | 130 | IPC SDK CVE MBI (0.7).pdf p4,10,38,39,41,43,74,76 |
| `MBI_CVE_Sub` | `MBP_S32 MBI_CVE_Sub(CVE_HANDLE *pCveHandle, CVE_SRC_IMAGE_T *pstSrc0, CVE_SRC_IMAGE_T *pstSrc1, CVE_DST_IMAGE_T *pstDst, CVE_DST_MEM_INFO_T *pstDstMem, CVE_SUB_CTRL_T *pstSubCtrl, MBP_BOOL_E bInstant);` | 132 | IPC SDK CVE MBI (0.7).pdf p4,10,36,39,40,41,43,74,75 |
| `MBI_CVE_Or` | `MBP_S32 MBI_CVE_Or(CVE_HANDLE *pCveHandle, CVE_SRC_IMAGE_T *pstSrc0, CVE_SRC_IMAGE_T *pstSrc1, CVE_DST_IMAGE_T *pstDst, CVE_OR_CTRL_T *pstOrCtrl, MBP_BOOL_E bInstant);` | 135 | IPC SDK CVE MBI (0.7).pdf p4,10,19,38,40,41,43,51,74,76 |
| `MBI_CVE_Xor` | `MBP_S32 MBI_CVE_Xor(CVE_HANDLE *pCveHandle, CVE_SRC_IMAGE_T *pstSrc0, CVE_SRC_IMAGE_T *pstSrc1, CVE_DST_IMAGE_T *pstDst, CVE_XOR_CTRL_T *pstXorCtrl, MBP_BOOL_E bInstant);` | 137 | IPC SDK CVE MBI (0.7).pdf p4,10,38,39,40,43,74,76 |
| `MBI_CVE_Dot` | `MBP_S32 MBI_CVE_Dot(CVE_HANDLE *pCveHandle, CVE_SRC_IMAGE_T *pstSrc0, CVE_SRC_IMAGE_T *pstSrc1, CVE_DST_IMAGE_T *pstDst, CVE_DOT_CTRL_T *pstDotCtrl, MBP_BOOL_E bInstant);` | 139 | IPC SDK CVE MBI (0.7).pdf p5,11,74,158 |
| `MBI_CVE_Add` | `MBP_S32 MBI_CVE_Add(CVE_HANDLE *pCveHandle, CVE_SRC_IMAGE_T *pstSrc0, CVE_SRC_IMAGE_T *pstSrc1, CVE_DST_IMAGE_T *pstDst, CVE_DST_MEM_INFO_T *pstDstMem, CVE_ADD_CTRL_T *pstAddCtrl, MBP_BOOL_E bInstant);` | 141 | IPC SDK CVE MBI (0.7).pdf p4,5,10,11,38,39,40,41,42,73,158 |
| `MBI_CVE_AddMap255To1` | `MBP_S32 MBI_CVE_AddMap255To1(CVE_HANDLE *pCveHandle, CVE_SRC_IMAGE_T *pstSrc0, CVE_SRC_IMAGE_T *pstSrc1, CVE_DST_IMAGE_T *pstDst, CVE_DST_MEM_INFO_T *pstDstMem, CVE_ADD_MAP_255_TO_1_CTRL_T *pstAddMap255To1Ctrl, MBP_BOOL_E bInstant);` | 144 | IPC SDK CVE MBI (0.7).pdf p5,11,73,158 |
| `MBI_CVE_KCF_GET_YF` | `MBP_S32 MBI_CVE_KCF_GET_YF(CVE_HANDLE *pCveHandle, CVE_SRC_MEM_INFO_T *pstSrcMem, CVE_DST_MEM_INFO_T *pstDstMem, CVE_KCF_GET_YF_CTRL_T *pstKcfGetYfCtrl, MBP_BOOL_E bInstant);` | 148 | IPC SDK CVE MBI (0.7).pdf p5,11,76,78,79 |
| `MBI_CVE_KCF_GET_FEATURE` | `MBP_S32 MBI_CVE_KCF_GET_FEATURE(CVE_HANDLE *pCveHandle, CVE_SRC_IMAGE_T *pstSrcImage, CVE_DST_MEM_INFO_T *pstDstMem0, CVE_DST_MEM_INFO_T *pstDstMem1, CVE_KCF_GET_FEATURE_CTRL_T *pstKcfGetFeatureCtrl, MBP_BOOL_E bInstant);` | 151 | IPC SDK CVE MBI (0.7).pdf p5,11,77,79,88 |
| `MBI_CVE_KCF_GET_TRAIN_AND_TRACK` | `MBP_S32 MBI_CVE_KCF_GET_TRAIN_AND_TRACK( CVE_HANDLE *pCveHandle, CVE_SRC_MEM_INFO_T *pstSrcMem1, CVE_SRC_MEM_INFO_T *pstSrcMem2, CVE_SRC_MEM_INFO_T *pstSrcMem3, CVE_DST_MEM_INFO_T *pstDstMem0, CVE_DST_MEM_INFO_T *pstDstMem1, CVE_DST_MEM_INFO_T *pstDstMem2, CVE_KCF_TRAIN_AND_TRACK_CTRL_T *pstKcfTrainAndTrackCtrl, MBP_BOOL_E bInstant);` | 155 | IPC SDK CVE MBI (0.7).pdf p5,11,77,78 |
| `MBI_CVE_LINE_FILTER` | `MBP_S32 MBI_CVE_LINE_FILTER(CVE_HANDLE *pCveHandle, CVE_SRC_IMAGE_T *pstSrcImage, CVE_DST_IMAGE_T *pstDstImage, CVE_LINE_FILTER_CTRL_T *pstLineFilterCtrl, MBP_BOOL_E bInstant);` | 160 | IPC SDK CVE MBI (0.7).pdf p5,11,79,81 |
| `MBI_CVE_NOISE_REMOVE` | `MBP_S32 MBI_CVE_NOISE_REMOVE(CVE_HANDLE *pCveHandle, CVE_SRC_IMAGE_T *pstSrcImage, CVE_DST_IMAGE_T *pstDstImage, CVE_NOISE_REMOVE_CTRL_T *pstNoiseRemoveCtrl, MBP_BOOL_E bInstant);` | 163 | IPC SDK CVE MBI (0.7).pdf p5,11,80,81 |
| `MBI_CVE_ADP_THRESH` | `MBP_S32 MBI_CVE_ADP_THRESH(CVE_HANDLE *pCveHandle, CVE_SRC_IMAGE_T *pstSrcImage0, CVE_SRC_IMAGE_T *pstSrcImage1, CVE_DST_IMAGE_T *pstDstImage, CVE_ADP_THRESH_CTRL_T *pstAdpThreshCtrl, MBP_BOOL_E bInstant);` | 166 | IPC SDK CVE MBI (0.7).pdf p5,11,82 |
| `MBI_CVE_REDUCE` | `MBP_S32 MBI_CVE_REDUCE(CVE_HANDLE *pCveHandle, CVE_SRC_IMAGE_T *pstSrcImage, CVE_DST_MEM_INFO_T *pstDstMem0, CVE_DST_MEM_INFO_T *pstDstMem1, CVE_DST_MEM_INFO_T *pstDstMem2, CVE_REDUCE_CTRL_T *pstReduceCtrl, MBP_BOOL_E bInstant);` | 169 | IPC SDK CVE MBI (0.7).pdf p5,11,83 |
| `MBI_CVE_PERSP_TRANS` | `MBP_S32 MBI_CVE_PERSP_TRANS(CVE_HANDLE *pCveHandle, CVE_SRC_IMAGE_T *pstSrcImage, CVE_DST_IMAGE_T *pstDstImage, CVE_PERSP_TRANS_CTRL_T *pstPerspTransCtrl, MBP_BOOL_E bInstant);` | 173 | IPC SDK CVE MBI (0.7).pdf p5,11,84,89 |
| `MBI_CVE_FAST_GUIDE_FILTER` | `MBP_S32 MBI_CVE_FAST_GUIDE_FILTER(CVE_HANDLE *pCveHandle, CVE_SRC_IMAGE_T *pstSrcImage0, CVE_SRC_IMAGE_T *pstSrcImage1, CVE_DST_IMAGE_T *pstDstImage0, CVE_DST_IMAGE_T *pstDstImage1, CVE_DST_IMAGE_T *pstDstImage2, CVE_FAST_GUIDE_FILTER_CTRL_T *pstFastGuideFilterCtrl, MBP_BOOL_E bInstant);` | 176 | IPC SDK CVE MBI (0.7).pdf p5,11,85 |
| `MBI_CVE_HOG` | `MBP_S32 MBI_CVE_HOG(CVE_HANDLE *pCveHandle, CVE_SRC_IMAGE_T *pstSrcImage, CVE_SRC_MEM_INFO_T *pstSrcMem, CVE_DST_IMAGE_T *pstDstImage, CVE_HOG_CTRL_T *pstHogCtrl, MBP_BOOL_E bInstant);` | 181 | IPC SDK CVE MBI (0.7).pdf p5,11,86,87 |
| `MBI_CVE_RESIZE` | `MBP_S32 MBI_CVE_RESIZE(CVE_HANDLE *pCveHandle, CVE_SRC_IMAGE_T *pstSrcImage, CVE_SRC_IMAGE_T *pstSrcImage1, CVE_DST_IMAGE_T *pstDstImage, CVE_DST_IMAGE_T *pstDstImage1, CVE_RESIZE_CTRL_T *pstResizeCtrl, MBP_BOOL_E bInstant);` | 184 | IPC SDK CVE MBI (0.7).pdf p5,11,85,88 |
| `MBI_CVE_SVM_KERNEL` | `MBP_S32 MBI_CVE_SVM_KERNEL(CVE_HANDLE *pCveHandle, CVE_SRC_MEM_INFO_T *pstSrcMem0, CVE_SRC_MEM_INFO_T *pstSrcMem1, CVE_DST_MEM_INFO_T *pstDstMem, CVE_SVM_KERNEL_CTRL_T *pstSvmKernelCtrl, MBP_BOOL_E bInstant);` | 188 | IPC SDK CVE MBI (0.7).pdf p5,11,89,91 |
| `MBI_CVE_SVM_PREDICT` | `MBP_S32 MBI_CVE_SVM_PREDICT(CVE_HANDLE *pCveHandle, CVE_SRC_MEM_INFO_T *pstSrcMem0, CVE_SRC_MEM_INFO_T *pstSrcMem1, CVE_DST_MEM_INFO_T *pstDstMem0, CVE_DST_MEM_INFO_T *pstDstMem1, CVE_SVM_PREDICT_CTRL_T *pstSvmPredictCtrl, MBP_BOOL_E bInstant);` | 191 | IPC SDK CVE MBI (0.7).pdf p5,11,90 |
| `MBI_CVE_RESHAPE` | `MBP_S32 MBI_CVE_RESHAPE(CVE_HANDLE *pCveHandle, CVE_SRC_IMAGE_T *pstSrcImage, CVE_DST_IMAGE_T *pstDstImage, CVE_RESHAPE_CTRL_T *pstReShapeCtrl, MBP_BOOL_E bInstant);` | 195 | IPC SDK CVE MBI (0.7).pdf p5,12,91 |
| `MBI_CVE_IM2COL` | `MBP_S32 MBI_CVE_IM2COL(CVE_HANDLE *pCveHandle, CVE_SRC_IMAGE_T *pstSrcImage, CVE_DST_IMAGE_T *pstDstImage, CVE_IM2COL_CTRL_T *pstImToColCtrl, MBP_BOOL_E bInstant);` | 198 | IPC SDK CVE MBI (0.7).pdf p5,12,92,96 |
| `MBI_CVE_GEMM` | `MBP_S32 MBI_CVE_GEMM(CVE_HANDLE *pCveHandle, CVE_SRC_IMAGE_T *pstSrcImage0, CVE_SRC_IMAGE_T *pstSrcImage1, CVE_SRC_IMAGE_T *pstSrcImage2, CVE_DST_IMAGE_T *pstDstImage, CVE_GEMM_CTRL_T *pstGemmCtrl, MBP_BOOL_E bInstant);` | 201 | IPC SDK CVE MBI (0.7).pdf p5,12,93,94 |
| `MBI_CVE_POOLING` | `MBP_S32 MBI_CVE_POOLING(CVE_HANDLE *pCveHandle, CVE_IMAGE_T *pstSrcImage, CVE_IMAGE_T *pstDstImage, CVE_POOLING_CTRL_T *pstPoolingCtrl, MBP_BOOL_E bInstant);` | 205 | IPC SDK CVE MBI (0.7).pdf p5,12,95 |
| `MBI_CVE_AIISP_TNR_PRE_PROCESS` | `MBP_S32 MBI_CVE_AIISP_TNR_PRE_PROCESS(CVE_HANDLE *pCveHandle, CVE_RAW_AIISP_T *pstSrcRaw0, CVE_RAW_AIISP_T *pstSrcRaw1, CVE_IMAGE_T *pstDstImage, CVE_AIISP_TNR_PRE_PROCESS_CTRL_T *pstAiIspTnrPreProcessCtrl, MBP_BOOL_E bInstant);` | 207 | 当前新版MBI手册未检出，需源码/其他文档核验 |
| `MBI_CVE_AIISP_TNR_POST_PROCESS` | `MBP_S32 MBI_CVE_AIISP_TNR_POST_PROCESS( CVE_HANDLE *pCveHandle, CVE_RAW_AIISP_T *pstSrcRaw0, CVE_RAW_AIISP_T *pstSrcRaw1, CVE_SRC_IMAGE_T *pstSrcImage2, CVE_IMAGE_T *pstSrcImage3, CVE_IMAGE_T *pstDstImage0, CVE_RAW_AIISP_T *pstDstRaw1, CVE_DST_IMAGE_T *pstDstImage2, CVE_DST_IMAGE_T *pstDstImage3, CVE_AIISP_TNR_POST_PROCESS_CTRL_T *pstAiIspTnrPostProcessCtrl, MBP_BOOL_E bInstant);` | 211 | 当前新版MBI手册未检出，需源码/其他文档核验 |
| `MBI_CVE_AIISP_SNR_POST_PROCESS` | `MBP_S32 MBI_CVE_AIISP_SNR_POST_PROCESS( CVE_HANDLE *pCveHandle, CVE_IMAGE_T *pstSrcImage0, CVE_IMAGE_T *pstSrcImage1, CVE_SRC_IMAGE_T *pstSrcImage2, CVE_RAW_AIISP_T *pstDstRaw, CVE_AIISP_SNR_POST_PROCESS_CTRL_T *pstAiIspSnrPostProcessCtrl, MBP_BOOL_E bInstant);` | 216 | 当前新版MBI手册未检出，需源码/其他文档核验 |
| `MBI_CVE_AIISP_TNR_MFNR_PROCESS` | `MBP_S32 MBI_CVE_AIISP_TNR_MFNR_PROCESS( CVE_HANDLE *pCveHandle, CVE_RAW_AIISP_T *pstSrcRaw, CVE_IMAGE_T *pstDstImage, CVE_AIISP_TNR_MFNR_PROCESS_CTRL_T *pstAiIspTnrMfnrProcessCtrl, MBP_BOOL_E bInstant);` | 220 | 当前新版MBI手册未检出，需源码/其他文档核验 |
| `MBI_CVE_AIISP_SNR_MFNR_PROCESS` | `MBP_S32 MBI_CVE_AIISP_SNR_MFNR_PROCESS( CVE_HANDLE *pCveHandle, CVE_IMAGE_T *pstSrcImage, CVE_RAW_AIISP_T *pstDstRaw, CVE_AIISP_SNR_MFNR_PROCESS_CTRL_T *pstAiIspSnrMfnrProcessCtrl, MBP_BOOL_E bInstant);` | 223 | 当前新版MBI手册未检出，需源码/其他文档核验 |

## A123X平台知识库API：mbi_dewarp 当前RC1接口签名与PDF页码

核对日期：2026-10-23；来源为本地供应商资料和当前RC1源码。AI辅助整理，reviewing候选；仅供内部授权使用。资料/源码事实、项目回传证据与本轮设备实测分开；本轮未操作设备。

这是当前头文件公开声明的精确速查，不是示例调用或二进制ABI认证。参数类型与参数顺序以此快照为准；结构体布局及条件编译需结合匹配头文件。返回码/阻塞/资源所有权只在对应主题与手册核实后使用。

来源：`workspaces/ipc-c5-rc.1.0/linux/mbp/mbi/dewarp/include/mbi_dewarp.h`；SHA-256 `24543c1bc8e268d7f977261f34f58862af3e6c95b626c4df48b385a31dbcae39`。

| 接口 | 当前声明 | 源码行 | 对应新版MBI手册物理页 |
| --- | --- | --- | --- |
| `MBI_DEW_Open` | `MBP_S32 MBI_DEW_Open(MBP_VOID);` | 41 | IPC SDK DEWARP MBI (0.7).pdf p5,8,20 |
| `MBI_DEW_Close` | `MBP_VOID MBI_DEW_Close(MBP_VOID);` | 42 | IPC SDK DEWARP MBI (0.7).pdf p5,8,9,20 |
| `MBI_DEW_CancelJob` | `MBP_S32 MBI_DEW_CancelJob(DEW_HANDLE u64Handle);` | 44 | IPC SDK DEWARP MBI (0.7).pdf p5,8,10,20 |
| `MBI_DEW_EndJob` | `MBP_S32 MBI_DEW_EndJob(DEW_HANDLE handle, MBP_BOOL_E bBlock, MBP_U32 u32TimeOut);` | 46 | IPC SDK DEWARP MBI (0.7).pdf p5,8,11,20 |
| `MBI_DEW_WaitDone` | `MBP_S32 MBI_DEW_WaitDone(DEW_HANDLE u64Handle);` | 47 | IPC SDK DEWARP MBI (0.7).pdf p5,8,12,20 |
| `MBI_DEW_AddCorrectionTask` | `MBP_S32 MBI_DEW_AddCorrectionTask(DEW_TASK_T *pstDewTask);` | 49 | IPC SDK DEWARP MBI (0.7).pdf p5,8,13,20 |
| `MBI_DEW_AddRectBoxTask` | `MBP_S32 MBI_DEW_AddRectBoxTask(DEW_RECT_BOX_TASK_T *pstDewBoxTask);` | 50 | IPC SDK DEWARP MBI (0.7).pdf p5,8,14,20 |
| `MBI_DEW_LoadFirmware` | `MBP_S32 MBI_DEW_LoadFirmware(MBP_CHAR *pcFWFileName, MBP_VOID *pToVirAddr, MBP_U32 u32Bytes);` | 51 | IPC SDK DEWARP MBI (0.7).pdf p5,8,14,20 |
| `MBI_DEW_CalcAndLoadFirmware` | `MBP_S32 MBI_DEW_CalcAndLoadFirmware(DEW_FW_PARAM_T *pstFwParams, MBP_VOID *pToVirAddr);` | 54 | IPC SDK DEWARP MBI (0.7).pdf p5,8,15,20；IPC SDK PPU MBI (0.6).pdf p22,23 |
| `MBI_DEW_RectBox_CalcAndLoadFirmware` | `MBP_S32 MBI_DEW_RectBox_CalcAndLoadFirmware(DEW_FW_RECT_BOX_PARAM_T *pstRectBox, MBP_VOID *pToVirAddr);` | 56 | IPC SDK DEWARP MBI (0.7).pdf p5,8,16,20 |
| `MBI_DEW_Append_RectBox_CalcAndLoadFirmware` | `MBP_S32 MBI_DEW_Append_RectBox_CalcAndLoadFirmware(MBP_VOID *pOldFwVirAddr, MBP_U32 u32OldFwSize, DEW_FW_RECT_BOX_PARAM_T *pstFwRectBox, MBP_VOID *pNewVirAddr);` | 58 | IPC SDK DEWARP MBI (0.7).pdf p5,8,17,20 |
| `MBI_DEW_StoreFirmwareIntoMbd` | `MBP_S32 MBI_DEW_StoreFirmwareIntoMbd(DEW_STORED_FW_T *pstStored_fw);` | 62 | IPC SDK DEWARP MBI (0.7).pdf p5,8,18,20 |
| `MBI_DEW_DisconnectOnlineMode` | `MBP_S32 MBI_DEW_DisconnectOnlineMode(MBP_VOID);` | 63 | IPC SDK DEWARP MBI (0.7).pdf p5,8,19,20 |
| `MBI_DEW_ConnectOnlineMode` | `MBP_S32 MBI_DEW_ConnectOnlineMode(MBP_VOID);` | 64 | IPC SDK DEWARP MBI (0.7).pdf p5,8,20 |

## A123X平台知识库API：mbi_ae 当前RC1接口签名与PDF页码

核对日期：2026-10-23；来源为本地供应商资料和当前RC1源码。AI辅助整理，reviewing候选；仅供内部授权使用。资料/源码事实、项目回传证据与本轮设备实测分开；本轮未操作设备。

这是当前头文件公开声明的精确速查，不是示例调用或二进制ABI认证。参数类型与参数顺序以此快照为准；结构体布局及条件编译需结合匹配头文件。返回码/阻塞/资源所有权只在对应主题与手册核实后使用。

来源：`workspaces/ipc-c5-rc.1.0/linux/mbp/mbi/isp/include/mbi_ae.h`；SHA-256 `11ed8cd88cba91184414cbe44f84ac89805184ba34365a102c5593910173a283`。

| 接口 | 当前声明 | 源码行 | 对应新版MBI手册物理页 |
| --- | --- | --- | --- |
| `MBI_AE_Register` | `MBP_S32 MBI_AE_Register(VI_PIPE ViPipe, ALG_LIB_T *pstAeLib);` | 42 | IPC SDK ISP MBI (02).pdf p8,20,137,139 |
| `MBI_AE_UnRegister` | `MBP_S32 MBI_AE_UnRegister(VI_PIPE ViPipe, ALG_LIB_T *pstAeLib);` | 43 | IPC SDK ISP MBI (02).pdf p8,20,138 |

## A123X平台知识库API：mbi_aiisp_process 当前RC1接口签名与PDF页码

核对日期：2026-10-23；来源为本地供应商资料和当前RC1源码。AI辅助整理，reviewing候选；仅供内部授权使用。资料/源码事实、项目回传证据与本轮设备实测分开；本轮未操作设备。

这是当前头文件公开声明的精确速查，不是示例调用或二进制ABI认证。参数类型与参数顺序以此快照为准；结构体布局及条件编译需结合匹配头文件。返回码/阻塞/资源所有权只在对应主题与手册核实后使用。

来源：`workspaces/ipc-c5-rc.1.0/linux/mbp/mbi/isp/include/mbi_aiisp_process.h`；SHA-256 `7d1e564da29582af017208ac84a9c0a4f11c7c2b29a26ec14e2757494e1c84d0`。

| 接口 | 当前声明 | 源码行 | 对应新版MBI手册物理页 |
| --- | --- | --- | --- |
| `MBI_AIISP_TnrPredealFunc` | `MBP_S32 MBI_AIISP_TnrPredealFunc(AI_ISP_MANAGER_T *stAiispMgr, MBP_S32 s32Index);` | 67 | 当前新版MBI手册未检出，需源码/其他文档核验 |
| `MBI_AIISP_TnrModelFunc` | `MBP_S32 MBI_AIISP_TnrModelFunc(AI_ISP_MANAGER_T *stAiispMgr, MBP_S32 s32Index);` | 68 | 当前新版MBI手册未检出，需源码/其他文档核验 |
| `MBI_AIISP_TnrPostdealFunc` | `MBP_S32 MBI_AIISP_TnrPostdealFunc(AI_ISP_MANAGER_T *stAiispMgr, MBP_S32 s32Index);` | 69 | 当前新版MBI手册未检出，需源码/其他文档核验 |
| `MBI_AIISP_SnrPredealFunc` | `MBP_S32 MBI_AIISP_SnrPredealFunc(AI_ISP_MANAGER_T *stAiispMgr, MBP_S32 s32Index);` | 70 | 当前新版MBI手册未检出，需源码/其他文档核验 |
| `MBI_AIISP_SnrModelFunc` | `MBP_S32 MBI_AIISP_SnrModelFunc(AI_ISP_MANAGER_T *stAiispMgr, MBP_S32 s32Index);` | 71 | 当前新版MBI手册未检出，需源码/其他文档核验 |
| `MBI_AIISP_SnrPostdealFunc` | `MBP_S32 MBI_AIISP_SnrPostdealFunc(AI_ISP_MANAGER_T *stAiispMgr, MBP_S32 s32Index);` | 72 | 当前新版MBI手册未检出，需源码/其他文档核验 |
| `MBI_AIISP_InitFunc` | `MBP_S32 MBI_AIISP_InitFunc(AI_ISP_INIT_PARAM_T *stNnInitParam);` | 74 | 当前新版MBI手册未检出，需源码/其他文档核验 |
| `MBI_AIISP_ExitFunc` | `MBP_S32 MBI_AIISP_ExitFunc(MBP_VOID);` | 75 | 当前新版MBI手册未检出，需源码/其他文档核验 |

## A123X平台知识库API：mbi_alg 当前RC1接口签名与PDF页码

核对日期：2026-10-23；来源为本地供应商资料和当前RC1源码。AI辅助整理，reviewing候选；仅供内部授权使用。资料/源码事实、项目回传证据与本轮设备实测分开；本轮未操作设备。

这是当前头文件公开声明的精确速查，不是示例调用或二进制ABI认证。参数类型与参数顺序以此快照为准；结构体布局及条件编译需结合匹配头文件。返回码/阻塞/资源所有权只在对应主题与手册核实后使用。

来源：`workspaces/ipc-c5-rc.1.0/linux/mbp/mbi/isp/include/mbi_alg.h`；SHA-256 `9dac401039801f0e5e45b857866070cc31a2cb1ee1268d45608e8d9f18c5aac5`。

| 接口 | 当前声明 | 源码行 | 对应新版MBI手册物理页 |
| --- | --- | --- | --- |
| `MBI_ALG_Register` | `MBP_S32 MBI_ALG_Register(VI_PIPE ViPipe, ALG_LIB_T *pstAlgLib);` | 42 | IPC SDK ISP MBI (02).pdf p8,21,145,147 |
| `MBI_ALG_UnRegister` | `MBP_S32 MBI_ALG_UnRegister(VI_PIPE ViPipe, ALG_LIB_T *pstAlgLib);` | 43 | IPC SDK ISP MBI (02).pdf p8,21,146 |
| `MBI_ALG_AeRegCallBack` | `MBP_S32 MBI_ALG_AeRegCallBack(VI_PIPE ViPipe, ALG_LIB_T *pstAlgLib, ALG_AE_REGISTER_T *pstRegister);` | 45 | IPC SDK ISP MBI (02).pdf p8,21,148,149,150,318 |
| `MBI_ALG_AeUnRegCallBack` | `MBP_S32 MBI_ALG_AeUnRegCallBack(VI_PIPE ViPipe, ALG_LIB_T *pstAlgLib);` | 46 | IPC SDK ISP MBI (02).pdf p8,21,149 |
| `MBI_ALG_AwbRegCallBack` | `MBP_S32 MBI_ALG_AwbRegCallBack(VI_PIPE ViPipe, ALG_LIB_T *pstAlgLib, ALG_AWB_REGISTER_T *pstRegister);` | 48 | IPC SDK ISP MBI (02).pdf p8,21,150,152,319 |
| `MBI_ALG_AwbUnRegCallBack` | `MBP_S32 MBI_ALG_AwbUnRegCallBack(VI_PIPE ViPipe, ALG_LIB_T *pstAlgLib);` | 49 | IPC SDK ISP MBI (02).pdf p8,21,151 |
| `MBI_ISP_SetExposureAttr` | `MBP_S32 MBI_ISP_SetExposureAttr(VI_PIPE ViPipe, const ISP_EXPOSURE_ATTR_T *pstExpAttr);` | 51 | IPC SDK ISP MBI (02).pdf p7,19,118,120,298 |
| `MBI_ISP_GetExposureAttr` | `MBP_S32 MBI_ISP_GetExposureAttr(VI_PIPE ViPipe, ISP_EXPOSURE_ATTR_T *pstExpAttr);` | 52 | IPC SDK ISP MBI (02).pdf p7,19,119,298 |
| `MBI_ISP_SetAERoiAttr` | `MBP_S32 MBI_ISP_SetAERoiAttr(VI_PIPE ViPipe, const ISP_AE_ROI_ATTR_T *pstAERoiAttr);` | 54 | IPC SDK ISP MBI (02).pdf p7,19,120,121,299 |
| `MBI_ISP_GetAERoiAttr` | `MBP_S32 MBI_ISP_GetAERoiAttr(VI_PIPE ViPipe, ISP_AE_ROI_ATTR_T *pstAERoiAttr);` | 55 | IPC SDK ISP MBI (02).pdf p7,19,120,121,299 |
| `MBI_ISP_QueryExposureInfo` | `MBP_S32 MBI_ISP_QueryExposureInfo(VI_PIPE ViPipe, ISP_EXP_INFO_T *pstExpInfo);` | 57 | IPC SDK ISP MBI (02).pdf p7,20,121,301 |
| `MBI_ISP_SetAERouteAttrEx` | `MBP_S32 MBI_ISP_SetAERouteAttrEx(VI_PIPE ViPipe, const ISP_AE_ROUTE_EX_T *pstAERouteAttrEx);` | 59 | IPC SDK ISP MBI (02).pdf p7,20,122,124,301 |
| `MBI_ISP_GetAERouteAttrEx` | `MBP_S32 MBI_ISP_GetAERouteAttrEx(VI_PIPE ViPipe, ISP_AE_ROUTE_EX_T *pstAERouteAttrEx);` | 60 | IPC SDK ISP MBI (02).pdf p7,20,123,301 |
| `MBI_ISP_SetWBAttr` | `MBP_S32 MBI_ISP_SetWBAttr(VI_PIPE ViPipe, const ISP_WB_ATTR_T *pstWBAttr);` | 62 | IPC SDK ISP MBI (02).pdf p7,20,124,125,304 |
| `MBI_ISP_GetWBAttr` | `MBP_S32 MBI_ISP_GetWBAttr(VI_PIPE ViPipe, ISP_WB_ATTR_T *pstWBAttr);` | 63 | IPC SDK ISP MBI (02).pdf p8,20,125 |
| `MBI_ISP_SetWBCorr` | `MBP_S32 MBI_ISP_SetWBCorr(VI_PIPE ViPipe, const MBP_U32 *u32WBCorr);` | 65 | IPC SDK ISP MBI (02).pdf p8,20,125,126,127 |
| `MBI_ISP_GetWBCorr` | `MBP_S32 MBI_ISP_GetWBCorr(VI_PIPE ViPipe, MBP_U32 *u32WBCorr);` | 66 | IPC SDK ISP MBI (02).pdf p8,20,126,127 |
| `MBI_ISP_SetCCMAttr` | `MBP_S32 MBI_ISP_SetCCMAttr(VI_PIPE ViPipe, const ISP_COLORMATRIX_ATTR_T *pstCCMAttr);` | 68 | IPC SDK ISP MBI (02).pdf p8,20,127,129,307 |
| `MBI_ISP_GetCCMAttr` | `MBP_S32 MBI_ISP_GetCCMAttr(VI_PIPE ViPipe, ISP_COLORMATRIX_ATTR_T *pstCCMAttr);` | 69 | IPC SDK ISP MBI (02).pdf p8,20,128,307 |
| `MBI_ISP_SetSaturationAttr` | `MBP_S32 MBI_ISP_SetSaturationAttr(VI_PIPE ViPipe, const ISP_SATURATION_ATTR_T *pstSatAttr);` | 71 | IPC SDK ISP MBI (02).pdf p8,20,129,131,309 |
| `MBI_ISP_GetSaturationAttr` | `MBP_S32 MBI_ISP_GetSaturationAttr(VI_PIPE ViPipe, ISP_SATURATION_ATTR_T *pstSatAttr);` | 72 | IPC SDK ISP MBI (02).pdf p8,20,130,309 |
| `MBI_ISP_QueryWBInfo` | `MBP_S32 MBI_ISP_QueryWBInfo(VI_PIPE ViPipe, ISP_WB_INFO_T *pstWBInfo);` | 74 | IPC SDK ISP MBI (02).pdf p8,20,131,310 |
| `MBI_ISP_QueryWBObj` | `MBP_S32 MBI_ISP_QueryWBObj(VI_PIPE ViPipe, MBP_S8 *ps8WBObj);` | 75 | IPC SDK ISP MBI (02).pdf p4,9,174,175 |
| `MBI_ISP_QueryAEStats` | `MBP_S32 MBI_ISP_QueryAEStats(VI_PIPE ViPipe, ISP_AE_STATS_ATTR_T *pstAEStats);` | 76 | IPC SDK ISP MBI (02).pdf p9,175,325,326,327 |
| `MBI_ISP_QueryWBStats` | `MBP_S32 MBI_ISP_QueryWBStats(VI_PIPE ViPipe, ISP_WB_STATS_T *pstWBStats);` | 78 | IPC SDK ISP MBI (02).pdf p8,20,131,132,310,312 |
| `MBI_ISP_CalGainByTemp` | `MBP_S32 MBI_ISP_CalGainByTemp(VI_PIPE ViPipe, const ISP_WB_ATTR_T *pstWBAttr, MBP_U16 u16ColorTemp, MBP_S16 s16Shift, MBP_U16 *pu16ALGGain);` | 79 | IPC SDK ISP MBI (02).pdf p8,21,152 |
| `MBI_ISP_GetDistance` | `MBP_U32 MBI_ISP_GetDistance(VI_PIPE ViPipe);` | 81 | IPC SDK ISP MBI (02).pdf p8,21,153,154 |
| `MBI_ISP_SetDistance` | `MBP_VOID MBI_ISP_SetDistance(VI_PIPE ViPipe, MBP_U32 u32Distance);` | 82 | IPC SDK ISP MBI (02).pdf p8,21,153,154 |
| `MBI_ISP_GetZoom` | `MBP_U32 MBI_ISP_GetZoom(VI_PIPE ViPipe);` | 84 | IPC SDK ISP MBI (02).pdf p9,21,179 |
| `MBI_ISP_SetZoom` | `MBP_VOID MBI_ISP_SetZoom(VI_PIPE ViPipe, MBP_U32 u32Zoomx10);` | 85 | IPC SDK ISP MBI (02).pdf p9,21,178,179 |
| `MBI_ISP_GetFocusVal` | `MBP_U32 MBI_ISP_GetFocusVal(VI_PIPE ViPipe);` | 87 | IPC SDK ISP MBI (02).pdf p9,21,177 |
| `MBI_ALG_SensorRegCallBack` | `MBP_S32 MBI_ALG_SensorRegCallBack(VI_PIPE ViPipe, ALG_LIB_T *pstAlgLib, ISP_SNS_ATTR_INFO_T *pstSnsAttrInfo, ALG_SENSOR_REGISTER_T *pstRegister);` | 89 | IPC SDK ISP MBI (02).pdf p8,21,147,148 |
| `MBI_ALG_SensorUnRegCallBack` | `MBP_S32 MBI_ALG_SensorUnRegCallBack(VI_PIPE ViPipe, ALG_LIB_T *pstAlgLib, SENSOR_ID SensorId);` | 91 | IPC SDK ISP MBI (02).pdf p8,21,148 |

## A123X平台知识库API：mbi_awb 当前RC1接口签名与PDF页码

核对日期：2026-10-23；来源为本地供应商资料和当前RC1源码。AI辅助整理，reviewing候选；仅供内部授权使用。资料/源码事实、项目回传证据与本轮设备实测分开；本轮未操作设备。

这是当前头文件公开声明的精确速查，不是示例调用或二进制ABI认证。参数类型与参数顺序以此快照为准；结构体布局及条件编译需结合匹配头文件。返回码/阻塞/资源所有权只在对应主题与手册核实后使用。

来源：`workspaces/ipc-c5-rc.1.0/linux/mbp/mbi/isp/include/mbi_awb.h`；SHA-256 `4e7a82ce8f1f20a64920b6745e123e0b45bfb89c042116cceece3b8869117d6e`。

| 接口 | 当前声明 | 源码行 | 对应新版MBI手册物理页 |
| --- | --- | --- | --- |
| `MBI_AWB_Register` | `MBP_S32 MBI_AWB_Register(VI_PIPE ViPipe, ALG_LIB_T *pstAwbLib);` | 41 | IPC SDK ISP MBI (02).pdf p8,20,141,143 |
| `MBI_AWB_UnRegister` | `MBP_S32 MBI_AWB_UnRegister(VI_PIPE ViPipe, ALG_LIB_T *pstAwbLib);` | 42 | IPC SDK ISP MBI (02).pdf p8,20,142 |
| `MBI_ISP_QueryWBInfo` | `MBP_S32 MBI_ISP_QueryWBInfo(VI_PIPE ViPipe, ISP_WB_INFO_T *pstWBInfo);` | 52 | IPC SDK ISP MBI (02).pdf p8,20,131,310 |
| `MBI_ISP_CalGainByTemp` | `MBP_S32 MBI_ISP_CalGainByTemp(VI_PIPE ViPipe, const ISP_WB_ATTR_T *pstWBAttr, MBP_U16 u16ColorTemp, MBP_S16 s16Shift, MBP_U16 *pu16AWBGain);` | 53 | IPC SDK ISP MBI (02).pdf p8,21,152 |
| `MBI_ISP_SetCaaControlAttr` | `MBP_S32 MBI_ISP_SetCaaControlAttr(VI_PIPE ViPipe, const ISP_CAA_CONTROl_T *pstSpecAwbCaaAttr);` | 55 | IPC SDK ISP MBI (02).pdf p7,18,91,93,267 |
| `MBI_ISP_GetCaaControlAttr` | `MBP_S32 MBI_ISP_GetCaaControlAttr(VI_PIPE ViPipe, ISP_CAA_CONTROl_T *pstSpecAwbCaaAttr);` | 56 | IPC SDK ISP MBI (02).pdf p7,18,92 |

## A123X平台知识库API：mbi_isp 当前RC1接口签名与PDF页码

核对日期：2026-10-23；来源为本地供应商资料和当前RC1源码。AI辅助整理，reviewing候选；仅供内部授权使用。资料/源码事实、项目回传证据与本轮设备实测分开；本轮未操作设备。

这是当前头文件公开声明的精确速查，不是示例调用或二进制ABI认证。参数类型与参数顺序以此快照为准；结构体布局及条件编译需结合匹配头文件。返回码/阻塞/资源所有权只在对应主题与手册核实后使用。

来源：`workspaces/ipc-c5-rc.1.0/linux/mbp/mbi/isp/include/mbi_isp.h`；SHA-256 `2a1ff1e69916846d48f35f17f16b624fa9d934b9acbbc3ba9b2c886939184bc8`。

| 接口 | 当前声明 | 源码行 | 对应新版MBI手册物理页 |
| --- | --- | --- | --- |
| `MBI_ISP_RegDump` | `MBP_S32 MBI_ISP_RegDump(MBP_CHAR *arr);` | 55 | IPC SDK ISP MBI (02).pdf p5,15,21 |
| `MBI_ISP_Init` | `MBP_S32 MBI_ISP_Init(VI_PIPE ViPipe);` | 57 | IPC SDK ISP MBI (02).pdf p5,15,22,24,26,27 |
| `MBI_ISP_MemInit` | `MBP_S32 MBI_ISP_MemInit(VI_PIPE ViPipe);` | 58 | IPC SDK ISP MBI (02).pdf p5,15,23 |
| `MBI_ISP_Run` | `MBP_S32 MBI_ISP_Run(VI_PIPE ViPipe);` | 59 | IPC SDK ISP MBI (02).pdf p5,15,24,25,27 |
| `MBI_ISP_Start` | `MBP_S32 MBI_ISP_Start(VI_PIPE ViPipe);` | 60 | IPC SDK ISP MBI (02).pdf p5,15,25 |
| `MBI_ISP_RunOnce` | `MBP_S32 MBI_ISP_RunOnce(VI_PIPE ViPipe);` | 61 | IPC SDK ISP MBI (02).pdf p5,15,25 |
| `MBI_ISP_Get_FrameEnd` | `MBP_S32 MBI_ISP_Get_FrameEnd(VI_PIPE ViPipe, ISP_GET_FRAME_END_PARAM_T *pstFrameEnd);` | 62 | IPC SDK ISP MBI (02).pdf p8,15,157,320 |
| `MBI_ISP_Set_SensorOnOff` | `MBP_S32 MBI_ISP_Set_SensorOnOff(VI_PIPE ViPipe, MBP_S32 status);` | 63 | IPC SDK ISP MBI (02).pdf p8,15,158 |
| `MBI_ISP_Exit` | `MBP_S32 MBI_ISP_Exit(VI_PIPE ViPipe);` | 64 | IPC SDK ISP MBI (02).pdf p5,15,23,24,26 |
| `MBI_ISP_GetPreset` | `MBP_S32 MBI_ISP_GetPreset(VI_PIPE ViPipe, MBP_VOID *p, MBP_U32 u32Size);` | 65 | IPC SDK ISP MBI (02).pdf p8,20,134 |
| `MBI_ISP_SensorRegCallBack` | `MBP_S32 MBI_ISP_SensorRegCallBack(VI_PIPE ViPipe, ISP_SNS_ATTR_INFO_T *pstSnsAttrInfo, ISP_SENSOR_REGISTER_T *pstRegister);` | 67 | IPC SDK ISP MBI (02).pdf p5,15,27,28,29,187,188 |
| `MBI_ISP_SensorUnRegCallBack` | `MBP_S32 MBI_ISP_SensorUnRegCallBack(VI_PIPE ViPipe, SENSOR_ID SensorId);` | 68 | IPC SDK ISP MBI (02).pdf p5,15,28,29 |
| `MBI_ISP_SetPubAttr` | `MBP_S32 MBI_ISP_SetPubAttr(VI_PIPE ViPipe, const ISP_PUB_ATTR_T *pstPubAttr);` | 70 | IPC SDK ISP MBI (02).pdf p5,15,23,29,31,194 |
| `MBI_ISP_SensorSetMode` | `MBP_S32 MBI_ISP_SensorSetMode(VI_PIPE ViPipe, const ISP_PUB_ATTR_T *pstPubAttr);` | 71 | IPC SDK ISP MBI (02).pdf p5,15,30,194 |
| `MBI_ISP_SetIspDwarpMod` | `MBP_S32 MBI_ISP_SetIspDwarpMod(VI_PIPE ViPipe, MBP_U32 *IspDwarpEn);` | 72 | IPC SDK ISP MBI (02).pdf p8,15,159 |
| `MBI_ISP_SensorWriteReg` | `MBP_S32 MBI_ISP_SensorWriteReg(VI_PIPE ViPipe, MBP_S32 s32Addr, MBP_S32 s32Data);` | 74 | IPC SDK ISP MBI (02).pdf p5,15,31,33 |
| `MBI_ISP_SensorReadReg` | `MBP_S32 MBI_ISP_SensorReadReg(VI_PIPE ViPipe, MBP_S32 s32Addr, MBP_S32 *s32Data);` | 75 | IPC SDK ISP MBI (02).pdf p5,15,32 |
| `MBI_ISP_SetBindAttr` | `MBP_S32 MBI_ISP_SetBindAttr(VI_PIPE ViPipe, const ISP_BIND_ATTR_T *pstBindAttr);` | 78 | IPC SDK ISP MBI (02).pdf p5,15,33,34,195 |
| `MBI_ISP_GetBindAttr` | `MBP_S32 MBI_ISP_GetBindAttr(VI_PIPE ViPipe, ISP_BIND_ATTR_T *pstBindAttr);` | 79 | IPC SDK ISP MBI (02).pdf p5,15,33,34,195 |
| `MBI_ISP_AELibRegCallBack` | `MBP_S32 MBI_ISP_AELibRegCallBack(VI_PIPE ViPipe, ALG_LIB_T *pstAeLib, ISP_AE_REGISTER_T *pstRegister);` | 80 | IPC SDK ISP MBI (02).pdf p5,15,34,35,42,196 |
| `MBI_ISP_AWBLibRegCallBack` | `MBP_S32 MBI_ISP_AWBLibRegCallBack(VI_PIPE ViPipe, ALG_LIB_T *pstAwbLib, ISP_AWB_REGISTER_T *pstRegister);` | 82 | IPC SDK ISP MBI (02).pdf p5,15,36,43,197 |
| `MBI_ISP_ALGLibRegCallBack` | `MBP_S32 MBI_ISP_ALGLibRegCallBack(VI_PIPE ViPipe, ALG_LIB_T *pstAlgLib, ISP_ALG_REGISTER_T *pstRegister);` | 84 | IPC SDK ISP MBI (02).pdf p5,15,36,37,43,199 |
| `MBI_ALG_LensRegCallBack` | `MBP_S32 MBI_ALG_LensRegCallBack(VI_PIPE ViPipe, ALG_LIB_T *pstAlgLib, ALG_LENS_REGISTER_T *pstRegister);` | 86 | IPC SDK ISP MBI (02).pdf p8,20,135,137,315 |
| `MBI_ALG_SetStitchMode` | `MBP_S32 MBI_ALG_SetStitchMode(VI_PIPE ViPipe, MBP_S32 s32Mode);` | 90 | IPC SDK ISP MBI (02).pdf p5,16,38 |
| `MBI_ISP_AELibUnRegCallBack` | `MBP_S32 MBI_ISP_AELibUnRegCallBack(VI_PIPE ViPipe, ALG_LIB_T *pstAeLib);` | 97 | IPC SDK ISP MBI (02).pdf p5,16,35,41,42 |
| `MBI_ISP_AWBLibUnRegCallBack` | `MBP_S32 MBI_ISP_AWBLibUnRegCallBack(VI_PIPE ViPipe, ALG_LIB_T *pstAwbLib);` | 98 | IPC SDK ISP MBI (02).pdf p5,16,36,42 |
| `MBI_ISP_ALGLibUnRegCallBack` | `MBP_S32 MBI_ISP_ALGLibUnRegCallBack(VI_PIPE ViPipe, ALG_LIB_T *pstAlgLib);` | 99 | IPC SDK ISP MBI (02).pdf p5,16,37,43 |
| `MBI_ALG_LensUnRegCallBack` | `MBP_S32 MBI_ALG_LensUnRegCallBack(VI_PIPE ViPipe, ALG_LIB_T *pstAlgLib);` | 100 | IPC SDK ISP MBI (02).pdf p8,20,136,137 |
| `MBI_ISP_GetAEStatistics` | `MBP_S32 MBI_ISP_GetAEStatistics(VI_PIPE ViPipe, ISP_AE_STATISTICS_T *pstAeStat);` | 102 | IPC SDK ISP MBI (02).pdf p5,16,43,44,200,202 |
| `MBI_ISP_GetWBStatistics` | `MBP_S32 MBI_ISP_GetWBStatistics(VI_PIPE ViPipe, ISP_WB_STATISTICS_T *pstWBStat);` | 103 | IPC SDK ISP MBI (02).pdf p5,16,44,203 |
| `MBI_ISP_GetISPRegAttr` | `MBP_S32 MBI_ISP_GetISPRegAttr(VI_PIPE ViPipe, ISP_REG_ATTR_T *pstIspRegAttr);` | 105 | IPC SDK ISP MBI (02).pdf p5,16,45,203 |
| `MBI_ISP_SetFMWState` | `MBP_S32 MBI_ISP_SetFMWState(VI_PIPE ViPipe, const ISP_FMW_STATE_E enState);` | 107 | IPC SDK ISP MBI (02).pdf p5,16,46,47,48,204 |
| `MBI_ISP_GetFMWState` | `MBP_S32 MBI_ISP_GetFMWState(VI_PIPE ViPipe, ISP_FMW_STATE_E *penState);` | 108 | IPC SDK ISP MBI (02).pdf p5,16,47,204 |
| `MBI_ISP_SetFSWDRAttr` | `MBP_S32 MBI_ISP_SetFSWDRAttr(VI_PIPE ViPipe, const ISP_WDR_FS_ATTR_T *pstFSWDRAttr);` | 110 | IPC SDK ISP MBI (02).pdf p5,16,48,50,210 |
| `MBI_ISP_GetFSWDRAttr` | `MBP_S32 MBI_ISP_GetFSWDRAttr(VI_PIPE ViPipe, ISP_WDR_FS_ATTR_T *pstFSWDRAttr);` | 111 | IPC SDK ISP MBI (02).pdf p5,16,49,210 |
| `MBI_ISP_SetIspHlcAttr` | `MBP_S32 MBI_ISP_SetIspHlcAttr(VI_PIPE ViPipe, const ISP_HLC_ATTR_T *pstIspHlcAttr);` | 113 | IPC SDK ISP MBI (02).pdf p5,6,16,50,51,85,86,211 |
| `MBI_ISP_GetIspHlcAttr` | `MBP_S32 MBI_ISP_GetIspHlcAttr(VI_PIPE ViPipe, ISP_HLC_ATTR_T *pstIspHlcAttr);` | 114 | IPC SDK ISP MBI (02).pdf p5,6,16,50,51,85,86,211 |
| `MBI_ISP_SetDRCAttr` | `MBP_S32 MBI_ISP_SetDRCAttr(VI_PIPE ViPipe, const ISP_DRC_ATTR_T *pstDRC);` | 116 | IPC SDK ISP MBI (02).pdf p5,16,51,52,53,215 |
| `MBI_ISP_GetDRCAttr` | `MBP_S32 MBI_ISP_GetDRCAttr(VI_PIPE ViPipe, ISP_DRC_ATTR_T *pstDRC);` | 117 | IPC SDK ISP MBI (02).pdf p5,16,52,215 |
| `MBI_ISP_SetDRCGammaAttr` | `MBP_S32 MBI_ISP_SetDRCGammaAttr(VI_PIPE ViPipe, const ISP_DRC_GAMMA_ATTR_T *GammaDRC);` | 119 | IPC SDK ISP MBI (02).pdf p6,16,53,55,217 |
| `MBI_ISP_GetDRCGammaAttr` | `MBP_S32 MBI_ISP_GetDRCGammaAttr(VI_PIPE ViPipe, ISP_DRC_GAMMA_ATTR_T *GammaDRC);` | 120 | IPC SDK ISP MBI (02).pdf p6,16,54,217 |
| `MBI_ISP_SetDehazeAttr` | `MBP_S32 MBI_ISP_SetDehazeAttr(VI_PIPE ViPipe, const ISP_DEHAZE_ATTR_T *pstDehazeAttr);` | 122 | IPC SDK ISP MBI (02).pdf p6,16,55,56,219 |
| `MBI_ISP_GetDehazeAttr` | `MBP_S32 MBI_ISP_GetDehazeAttr(VI_PIPE ViPipe, ISP_DEHAZE_ATTR_T *pstDehazeAttr);` | 123 | IPC SDK ISP MBI (02).pdf p6,16,55,56,219 |
| `MBI_ISP_SetLDCIAttr` | `MBP_S32 MBI_ISP_SetLDCIAttr(VI_PIPE ViPipe, const ISP_LDCI_ATTR_T *pstLDCIAttr);` | 125 | IPC SDK ISP MBI (02).pdf p6,16,56,58,223 |
| `MBI_ISP_GetLDCIAttr` | `MBP_S32 MBI_ISP_GetLDCIAttr(VI_PIPE ViPipe, ISP_LDCI_ATTR_T *pstLDCIAttr);` | 126 | IPC SDK ISP MBI (02).pdf p6,16,57,223 |
| `MBI_ISP_SetLDCILutAttr` | `MBP_S32 MBI_ISP_SetLDCILutAttr(VI_PIPE ViPipe, const ISP_LDCI_LUT_ATTR_T *LutLDCIAttr);` | 128 | IPC SDK ISP MBI (02).pdf p6,16,58,60,223 |
| `MBI_ISP_GetLDCILutAttr` | `MBP_S32 MBI_ISP_GetLDCILutAttr(VI_PIPE ViPipe, ISP_LDCI_LUT_ATTR_T *LutLDCIAttr);` | 129 | IPC SDK ISP MBI (02).pdf p6,16,59,223 |
| `MBI_ISP_SetDNLPAttr` | `MBP_S32 MBI_ISP_SetDNLPAttr(VI_PIPE ViPipe, const ISP_DNLP_ATTR_T *pstDNLPAttr);` | 131 | IPC SDK ISP MBI (02).pdf p6,16,60,61,226 |
| `MBI_ISP_GetDNLPAttr` | `MBP_S32 MBI_ISP_GetDNLPAttr(VI_PIPE ViPipe, ISP_DNLP_ATTR_T *pstDNLPAttr);` | 132 | IPC SDK ISP MBI (02).pdf p6,16,60,61,226 |
| `MBI_ISP_SetModuleControl` | `MBP_S32 MBI_ISP_SetModuleControl(VI_PIPE ViPipe, const ISP_MODULE_CTRL_U *punModCtrl);` | 134 | IPC SDK ISP MBI (02).pdf p6,17,61,63 |
| `MBI_ISP_GetModuleControl` | `MBP_S32 MBI_ISP_GetModuleControl(VI_PIPE ViPipe, ISP_MODULE_CTRL_U *punModCtrl);` | 135 | IPC SDK ISP MBI (02).pdf p6,17,62 |
| `MBI_ISP_SetMeshShadingAttr` | `MBP_S32 MBI_ISP_SetMeshShadingAttr(VI_PIPE ViPipe, const ISP_SHADING_ATTR_T *pstShadingAttr);` | 137 | IPC SDK ISP MBI (02).pdf p6,17,63,65,233 |
| `MBI_ISP_GetMeshShadingAttr` | `MBP_S32 MBI_ISP_GetMeshShadingAttr(VI_PIPE ViPipe, ISP_SHADING_ATTR_T *pstShadingAttr);` | 138 | IPC SDK ISP MBI (02).pdf p6,17,64,233 |
| `MBI_ISP_SetMeshShadingGainLutAttr` | `MBP_S32 MBI_ISP_SetMeshShadingGainLutAttr(VI_PIPE ViPipe, const ISP_SHADING_LUT_ATTR_T *pstShadingGainLutAttr);` | 140 | IPC SDK ISP MBI (02).pdf p6,17,65,66,235 |
| `MBI_ISP_GetMeshShadingGainLutAttr` | `MBP_S32 MBI_ISP_GetMeshShadingGainLutAttr(VI_PIPE ViPipe, ISP_SHADING_LUT_ATTR_T *pstShadingGainLutAttr);` | 141 | IPC SDK ISP MBI (02).pdf p6,17,65,66,235 |
| `MBI_ISP_SetRadialShadingAttr` | `MBP_S32 MBI_ISP_SetRadialShadingAttr(VI_PIPE ViPipe, const ISP_RADIAL_SHADING_ATTR_T *pstRaShadingAttr);` | 143 | IPC SDK ISP MBI (02).pdf p6,17,66,68,235 |
| `MBI_ISP_GetRadialShadingAttr` | `MBP_S32 MBI_ISP_GetRadialShadingAttr(VI_PIPE ViPipe, ISP_RADIAL_SHADING_ATTR_T *pstRaShadingAttr);` | 144 | IPC SDK ISP MBI (02).pdf p6,17,67,235 |
| `MBI_ISP_SetRadialShadingLUT` | `MBP_S32 MBI_ISP_SetRadialShadingLUT(VI_PIPE ViPipe, const ISP_RADIAL_SHADING_LUT_T *pstRaShadingLutAttr);` | 146 | IPC SDK ISP MBI (02).pdf p6,17,68,70,236 |
| `MBI_ISP_GetRadialShadingLUT` | `MBP_S32 MBI_ISP_GetRadialShadingLUT(VI_PIPE ViPipe, ISP_RADIAL_SHADING_LUT_T *pstRaShadingLutAttr);` | 147 | IPC SDK ISP MBI (02).pdf p6,17,69,236 |
| `MBI_ISP_SetRAWNRAttr` | `MBP_S32 MBI_ISP_SetRAWNRAttr(VI_PIPE ViPipe, const ISP_RAWNR_ATTR_T *rawNRAttr);` | 149 | IPC SDK ISP MBI (02).pdf p6,17,70,71,239 |
| `MBI_ISP_GetRAWNRAttr` | `MBP_S32 MBI_ISP_GetRAWNRAttr(VI_PIPE ViPipe, ISP_RAWNR_ATTR_T *rawNRAttr);` | 150 | IPC SDK ISP MBI (02).pdf p6,17,70,71,239 |
| `MBI_ISP_SetSNRAttr` | `MBP_S32 MBI_ISP_SetSNRAttr(VI_PIPE ViPipe, const ISP_SNR_ATTR_T *SNRAttr);` | 152 | IPC SDK ISP MBI (02).pdf p6,17,71,73,245 |
| `MBI_ISP_GetSNRAttr` | `MBP_S32 MBI_ISP_GetSNRAttr(VI_PIPE ViPipe, ISP_SNR_ATTR_T *SNRAttr);` | 153 | IPC SDK ISP MBI (02).pdf p6,17,72,245 |
| `MBI_ISP_SetTNRAttr` | `MBP_S32 MBI_ISP_SetTNRAttr(VI_PIPE ViPipe, const ISP_TNR_ATTR_T *TNRAttr);` | 155 | IPC SDK ISP MBI (02).pdf p6,17,73,75,249 |
| `MBI_ISP_GetTNRAttr` | `MBP_S32 MBI_ISP_GetTNRAttr(VI_PIPE ViPipe, ISP_TNR_ATTR_T *TNRAttr);` | 156 | IPC SDK ISP MBI (02).pdf p6,17,74,249 |
| `MBI_ISP_SetCNRAttr` | `MBP_S32 MBI_ISP_SetCNRAttr(VI_PIPE ViPipe, const ISP_CNR_ATTR_T *CNRAttr);` | 158 | IPC SDK ISP MBI (02).pdf p6,17,75,76,252 |
| `MBI_ISP_GetCNRAttr` | `MBP_S32 MBI_ISP_GetCNRAttr(VI_PIPE ViPipe, ISP_CNR_ATTR_T *CNRAttr);` | 159 | IPC SDK ISP MBI (02).pdf p6,17,75,76,252 |
| `MBI_ISP_SetPurpleAttr` | `MBP_S32 MBI_ISP_SetPurpleAttr(VI_PIPE ViPipe, const ISP_PURPLE_ATTR_T *PurpleAttr);` | 161 | IPC SDK ISP MBI (02).pdf p6,17,76,77,78,161,254 |
| `MBI_ISP_GetPurpleAttr` | `MBP_S32 MBI_ISP_GetPurpleAttr(VI_PIPE ViPipe, ISP_PURPLE_ATTR_T *PurpleAttr);` | 162 | IPC SDK ISP MBI (02).pdf p8,17,77,160,254 |
| `MBI_ISP_SetDMSAttr` | `MBP_S32 MBI_ISP_SetDMSAttr(VI_PIPE ViPipe, const ISP_DMS_ATTR_T *DMSAttr);` | 164 | IPC SDK ISP MBI (02).pdf p6,17,78,80,256 |
| `MBI_ISP_GetDMSAttr` | `MBP_S32 MBI_ISP_GetDMSAttr(VI_PIPE ViPipe, ISP_DMS_ATTR_T *DMSAttr);` | 165 | IPC SDK ISP MBI (02).pdf p6,17,79,256 |
| `MBI_ISP_SetNPAttr` | `MBP_S32 MBI_ISP_SetNPAttr(VI_PIPE ViPipe, const ISP_NP_ATTR_T *NPAttr);` | 167 | IPC SDK ISP MBI (02).pdf p6,17,80,81,258 |
| `MBI_ISP_GetNPAttr` | `MBP_S32 MBI_ISP_GetNPAttr(VI_PIPE ViPipe, ISP_NP_ATTR_T *NPAttr);` | 168 | IPC SDK ISP MBI (02).pdf p6,17,80,81,258 |
| `MBI_ISP_SetGammaAttr` | `MBP_S32 MBI_ISP_SetGammaAttr(VI_PIPE ViPipe, const ISP_GAMMA_ATTR_T *pstGammaAttr);` | 170 | IPC SDK ISP MBI (02).pdf p6,17,81,83,258 |
| `MBI_ISP_GetGammaAttr` | `MBP_S32 MBI_ISP_GetGammaAttr(VI_PIPE ViPipe, ISP_GAMMA_ATTR_T *pstGammaAttr);` | 171 | IPC SDK ISP MBI (02).pdf p6,17,82,258 |
| `MBI_ISP_SetIspSharpenAttr` | `MBP_S32 MBI_ISP_SetIspSharpenAttr(VI_PIPE ViPipe, const ISP_SHARPEN_ATTR_T *pstIspShpAttr);` | 173 | IPC SDK ISP MBI (02).pdf p6,17,83,85 |
| `MBI_ISP_GetIspSharpenAttr` | `MBP_S32 MBI_ISP_GetIspSharpenAttr(VI_PIPE ViPipe, ISP_SHARPEN_ATTR_T *pstIspShpAttr);` | 174 | IPC SDK ISP MBI (02).pdf p6,17,84 |
| `MBI_ISP_SetIspHlcAttr` | `MBP_S32 MBI_ISP_SetIspHlcAttr(VI_PIPE ViPipe, const ISP_HLC_ATTR_T *pstIspHlcAttr);` | 176 | IPC SDK ISP MBI (02).pdf p5,6,16,50,51,85,86,211 |
| `MBI_ISP_GetIspHlcAttr` | `MBP_S32 MBI_ISP_GetIspHlcAttr(VI_PIPE ViPipe, ISP_HLC_ATTR_T *pstIspHlcAttr);` | 177 | IPC SDK ISP MBI (02).pdf p5,6,16,50,51,85,86,211 |
| `MBI_ISP_SetCrosstalkAttr` | `MBP_S32 MBI_ISP_SetCrosstalkAttr(VI_PIPE ViPipe, const ISP_CR_ATTR_T *pstCRAttr);` | 179 | IPC SDK ISP MBI (02).pdf p6,18,86,88,263 |
| `MBI_ISP_GetCrosstalkAttr` | `MBP_S32 MBI_ISP_GetCrosstalkAttr(VI_PIPE ViPipe, ISP_CR_ATTR_T *pstCRAttr);` | 180 | IPC SDK ISP MBI (02).pdf p6,18,87,263 |
| `MBI_ISP_SetBlackLevelAttr` | `MBP_S32 MBI_ISP_SetBlackLevelAttr(VI_PIPE ViPipe, const ISP_BLACK_LEVEL_T *pstBlackLevel);` | 182 | IPC SDK ISP MBI (02).pdf p6,18,88,90,265 |
| `MBI_ISP_GetBlackLevelAttr` | `MBP_S32 MBI_ISP_GetBlackLevelAttr(VI_PIPE ViPipe, ISP_BLACK_LEVEL_T *pstBlackLevel);` | 183 | IPC SDK ISP MBI (02).pdf p7,18,89,265 |
| `MBI_ISP_SetCSCAttr` | `MBP_S32 MBI_ISP_SetCSCAttr(VI_PIPE ViPipe, const ISP_CSC_ATTR_T *pstCSCAttr);` | 185 | IPC SDK ISP MBI (02).pdf p7,18,90,91,266 |
| `MBI_ISP_GetCSCAttr` | `MBP_S32 MBI_ISP_GetCSCAttr(VI_PIPE ViPipe, ISP_CSC_ATTR_T *pstCSCFAttr);` | 186 | IPC SDK ISP MBI (02).pdf p7,18,90,91,266 |
| `MBI_ISP_SetCaaControlAttr` | `MBP_S32 MBI_ISP_SetCaaControlAttr(VI_PIPE ViPipe, const ISP_CAA_CONTROl_T *pstSpecAwbCaaAttr);` | 188 | IPC SDK ISP MBI (02).pdf p7,18,91,93,267 |
| `MBI_ISP_GetCaaControlAttr` | `MBP_S32 MBI_ISP_GetCaaControlAttr(VI_PIPE ViPipe, ISP_CAA_CONTROl_T *pstSpecAwbCaaAttr);` | 189 | IPC SDK ISP MBI (02).pdf p7,18,92 |
| `MBI_ISP_SetCalcFlickerType` | `MBP_S32 MBI_ISP_SetCalcFlickerType(VI_PIPE ViPipe, const ISP_CALCFLICKER_INPUT_T *pstInputParam);` | 191 | IPC SDK ISP MBI (02).pdf p7,18,93,95,268 |
| `MBI_ISP_GetCalcFlickerType` | `MBP_S32 MBI_ISP_GetCalcFlickerType(VI_PIPE ViPipe, ISP_CALCFLICKER_INPUT_T *pstInputParam);` | 192 | IPC SDK ISP MBI (02).pdf p7,18,94,268 |
| `MBI_ISP_GetFlickerOutput` | `MBP_S32 MBI_ISP_GetFlickerOutput(VI_PIPE ViPipe, ISP_CALCFLICKER_OUTPUT_T *pstOutputParam);` | 194 | IPC SDK ISP MBI (02).pdf p7,18,94,95,269 |
| `MBI_ISP_SetAWBAttrEx` | `MBP_S32 MBI_ISP_SetAWBAttrEx(VI_PIPE ViPipe, const ISP_AWB_ATTR_EX_T *pstAWBAttrEx);` | 196 | IPC SDK ISP MBI (02).pdf p7,18,96,97,270 |
| `MBI_ISP_GetAWBAttrEx` | `MBP_S32 MBI_ISP_GetAWBAttrEx(VI_PIPE ViPipe, ISP_AWB_ATTR_EX_T *pstAWBAttrEx);` | 197 | IPC SDK ISP MBI (02).pdf p7,18,96,270 |
| `MBI_ISP_SetDpcAttr` | `MBP_S32 MBI_ISP_SetDpcAttr(VI_PIPE ViPipe, const ISP_DPC_ATTR_T *pstDpcAttr);` | 199 | IPC SDK ISP MBI (02).pdf p7,18,97,99 |
| `MBI_ISP_GetDpcAttr` | `MBP_S32 MBI_ISP_GetDpcAttr(VI_PIPE ViPipe, ISP_DPC_ATTR_T *pstDpcAttr);` | 200 | IPC SDK ISP MBI (02).pdf p7,18,98 |
| `MBI_ISP_SetIRAttr` | `MBP_S32 MBI_ISP_SetIRAttr(VI_PIPE ViPipe, const ISP_IR_ATTR_T *pstIRAttr);` | 202 | IPC SDK ISP MBI (02).pdf p7,18,99,100,273 |
| `MBI_ISP_GetIRAttr` | `MBP_S32 MBI_ISP_GetIRAttr(VI_PIPE ViPipe, ISP_IR_ATTR_T *pstIRAttr);` | 203 | IPC SDK ISP MBI (02).pdf p7,18,100,274 |
| `MBI_ISP_SetHighLightAttr` | `MBP_S32 MBI_ISP_SetHighLightAttr(VI_PIPE ViPipe, const ISP_HIGHLIGHT_ATTR_T *pstHighLightAttr);` | 205 | IPC SDK ISP MBI (02).pdf p8,21,154,311 |
| `MBI_ISP_GetHighLightAttr` | `MBP_S32 MBI_ISP_GetHighLightAttr(VI_PIPE ViPipe, ISP_HIGHLIGHT_ATTR_T *pstHighLightAttr);` | 206 | IPC SDK ISP MBI (02).pdf p8,21,155,156,311 |
| `MBI_ISP_SetCM2AttrEx` | `MBP_S32 MBI_ISP_SetCM2AttrEx(VI_PIPE ViPipe, const ISP_CM2_ATTR_T *pstCm2Attr);` | 208 | IPC SDK ISP MBI (02).pdf p7,18,100,101,102 |
| `MBI_ISP_GetCM2AttrEx` | `MBP_S32 MBI_ISP_GetCM2AttrEx(VI_PIPE ViPipe, ISP_CM2_ATTR_T *pstCm2Attr);` | 209 | IPC SDK ISP MBI (02).pdf p7,18,101 |
| `MBI_ISP_SetRegister` | `MBP_S32 MBI_ISP_SetRegister(VI_PIPE ViPipe, MBP_U32 u32Addr, MBP_U32 u32Value);` | 211 | IPC SDK ISP MBI (02).pdf p7,18,102,104 |
| `MBI_ISP_GetRegister` | `MBP_S32 MBI_ISP_GetRegister(VI_PIPE ViPipe, MBP_U32 u32Addr, MBP_U32 *pu32Value);` | 212 | IPC SDK ISP MBI (02).pdf p7,18,103 |
| `MBI_ISP_FPNCalibrate` | `MBP_S32 MBI_ISP_FPNCalibrate(VI_PIPE ViPipe, ISP_FPN_LUT_ATTR_T *pstCalibrateAttr);` | 215 | IPC SDK ISP MBI (02).pdf p7,18,104,276 |
| `MBI_ISP_SetFPNAttr` | `MBP_S32 MBI_ISP_SetFPNAttr(VI_PIPE ViPipe, const ISP_FPN_ATTR_T *pstFPNAttr);` | 216 | IPC SDK ISP MBI (02).pdf p7,18,105,106,277 |
| `MBI_ISP_GetFPNAttr` | `MBP_S32 MBI_ISP_GetFPNAttr(VI_PIPE ViPipe, ISP_FPN_ATTR_T *pstFPNAttr);` | 217 | IPC SDK ISP MBI (02).pdf p7,18,105,106,277 |
| `MBI_ISP_Calibration` | `MBP_S32 MBI_ISP_Calibration(VI_PIPE ViPipe, AISP_API_TYPE_T *api_type);` | 218 | IPC SDK ISP MBI (02).pdf p7,18,106,108,278 |
| `MBI_ISP_GetDataType` | `MBP_S32 MBI_ISP_GetDataType(VI_PIPE ViPipe, AISP_API_TYPE_T *api_type);` | 219 | IPC SDK ISP MBI (02).pdf p7,18,107,278 |
| `MBI_ISP_SetChnAttr` | `MBP_S32 MBI_ISP_SetChnAttr(ISP_CHN ispChn, const ISP_CHN_ATTR_T *pstChnAttr);` | 221 | IPC SDK ISP MBI (02).pdf p7,19,108,110,132,133,286 |
| `MBI_ISP_GetChnAttr` | `MBP_S32 MBI_ISP_GetChnAttr(ISP_CHN ispChn, ISP_CHN_ATTR_T *pstChnAttr);` | 222 | IPC SDK ISP MBI (02).pdf p7,19,109,286 |
| `MBI_ISP_EnableChn` | `MBP_S32 MBI_ISP_EnableChn(ISP_CHN ispChn);` | 223 | IPC SDK ISP MBI (02).pdf p7,19,110,111 |
| `MBI_ISP_DisableChn` | `MBP_S32 MBI_ISP_DisableChn(ISP_CHN ispChn);` | 224 | IPC SDK ISP MBI (02).pdf p7,19,110,111 |
| `MBI_ISP_SetChnCrop` | `MBP_S32 MBI_ISP_SetChnCrop(ISP_CHN ispChn, const ISP_CHN_CROP_INFO_T *pstCropInfo);` | 225 | IPC SDK ISP MBI (02).pdf p7,19,111,113,287 |
| `MBI_ISP_GetChnCrop` | `MBP_S32 MBI_ISP_GetChnCrop(ISP_CHN ispChn, ISP_CHN_CROP_INFO_T *pstCropInfo);` | 226 | IPC SDK ISP MBI (02).pdf p7,19,112,287 |
| `MBI_ISP_GetChnFrame` | `MBP_S32 MBI_ISP_GetChnFrame(ISP_CHN ispChn, MBP_VIDEO_FRAME_INFO_T *pstVideoFrame, MBP_S32 s32MilliSec);` | 227 | IPC SDK ISP MBI (02).pdf p7,19,113,115,290 |
| `MBI_ISP_PutChnFrame` | `MBP_S32 MBI_ISP_PutChnFrame(ISP_CHN ispChn, const MBP_VIDEO_FRAME_INFO_T *pstVideoFrame);` | 228 | IPC SDK ISP MBI (02).pdf p7,19,114 |
| `MBI_ISP_SetChnRot` | `MBP_S32 MBI_ISP_SetChnRot(ISP_CHN ispChn, const ISP_CHN_ROT_TYPE_E *pstRotType);` | 229 | IPC SDK ISP MBI (02).pdf p7,19,115,116,290 |
| `MBI_ISP_GetChnRot` | `MBP_S32 MBI_ISP_GetChnRot(ISP_CHN ispChn, ISP_CHN_ROT_TYPE_E *pstRotType);` | 230 | IPC SDK ISP MBI (02).pdf p7,19,115,116,290 |
| `MBI_ISP_SetChnDrawAttr` | `MBP_S32 MBI_ISP_SetChnDrawAttr(ISP_CHN ispChn, const ISP_CHN_DRAW_ATTR_T *pstDrawAttr);` | 231 | IPC SDK ISP MBI (02).pdf p8,19,161,163,322 |
| `MBI_ISP_GetChnDrawAttr` | `MBP_S32 MBI_ISP_GetChnDrawAttr(ISP_CHN ispChn, ISP_CHN_DRAW_ATTR_T *pstDrawAttr);` | 232 | IPC SDK ISP MBI (02).pdf p8,162,322 |
| `MBI_ISP_SetChnFps` | `MBP_S32 MBI_ISP_SetChnFps(ISP_CHN ispChn, const ISP_CHN_FPS_T *pstFps);` | 234 | IPC SDK ISP MBI (02).pdf p7,19,116,118,291 |
| `MBI_ISP_GetChnFps` | `MBP_S32 MBI_ISP_GetChnFps(ISP_CHN ispChn, ISP_CHN_FPS_T *pstFps);` | 235 | IPC SDK ISP MBI (02).pdf p7,19,117,291 |
| `MBI_ISP_SetChnLowmem` | `MBP_S32 MBI_ISP_SetChnLowmem(ISP_CHN ispChn, const MBP_S32 s32LowMem);` | 236 | IPC SDK ISP MBI (02).pdf p8,20,132 |
| `MBI_ISP_GetChnLowmem` | `MBP_S32 MBI_ISP_GetChnLowmem(ISP_CHN ispChn, MBP_S32 *s32LowMem);` | 237 | IPC SDK ISP MBI (02).pdf p8,20,133 |
| `MBI_ISP_GetDistance` | `MBP_U32 MBI_ISP_GetDistance(VI_PIPE ViPipe);` | 238 | IPC SDK ISP MBI (02).pdf p8,21,153,154 |
| `MBI_ISP_SetDistance` | `MBP_VOID MBI_ISP_SetDistance(VI_PIPE ViPipe, MBP_U32 u32Distance);` | 239 | IPC SDK ISP MBI (02).pdf p8,21,153,154 |
| `MBI_ISP_GetAIispMode` | `MBP_U32 MBI_ISP_GetAIispMode(VI_PIPE ViPipe);` | 240 | IPC SDK ISP MBI (02).pdf p9,19,164 |
| `MBI_ISP_SetAIispMode` | `MBP_VOID MBI_ISP_SetAIispMode(VI_PIPE ViPipe, MBP_U32 u32AIispMode);` | 241 | IPC SDK ISP MBI (02).pdf p8,19,163,165 |
| `MBI_ISP_Get_RunStatus` | `MBP_U32 MBI_ISP_Get_RunStatus(VI_PIPE ViPipe);` | 242 | IPC SDK ISP MBI (02).pdf p9,19,165 |
| `MBI_ISP_Put_OfflineBuff` | `MBP_S32 MBI_ISP_Put_OfflineBuff(VI_PIPE ViPipe, IPP_CAP_BUFF_T *capBuff);` | 243 | IPC SDK ISP MBI (02).pdf p9,19,166,170,323 |
| `MBI_ISP_SetIPPAttr` | `MBP_S32 MBI_ISP_SetIPPAttr(VI_PIPE ViPipe, IPP_CAP_ATTR_T *capAttr);` | 245 | IPC SDK ISP MBI (02).pdf p9,19,167,168,324 |
| `MBI_ISP_IPPReqBuffs` | `MBP_S32 MBI_ISP_IPPReqBuffs(VI_PIPE ViPipe, IPP_CAP_BUFF_T *capBuff);` | 246 | IPC SDK ISP MBI (02).pdf p9,19,167,169,323 |
| `MBI_ISP_IPPDevStart` | `MBP_S32 MBI_ISP_IPPDevStart(VI_PIPE ViPipe, IPP_CAP_ATTR_T *capAttr);` | 247 | IPC SDK ISP MBI (02).pdf p9,19,170,172,323,324 |
| `MBI_ISP_IPPDevStop` | `MBP_S32 MBI_ISP_IPPDevStop(VI_PIPE ViPipe, IPP_CAP_ATTR_T *capAttr);` | 248 | IPC SDK ISP MBI (02).pdf p9,19,171,323,324 |
| `MBI_ISP_GetIPPDoneBuff` | `MBP_S32 MBI_ISP_GetIPPDoneBuff(VI_PIPE ViPipe, IPP_CAP_BUFF_T *capBuff);` | 249 | IPC SDK ISP MBI (02).pdf p9,19,172,174,323 |
| `MBI_ISP_PutIPPDoneBuff` | `MBP_S32 MBI_ISP_PutIPPDoneBuff(VI_PIPE ViPipe, IPP_CAP_BUFF_T *capBuff);` | 250 | IPC SDK ISP MBI (02).pdf p9,19,173,323 |
| `MBI_ISP_StopPreRoll` | `MBP_S32 MBI_ISP_StopPreRoll(VI_PIPE ViPipe);` | 253 | 当前新版MBI手册未检出，需源码/其他文档核验 |
| `MBI_ISP_GetPreRollLocation` | `MBP_S32 MBI_ISP_GetPreRollLocation(VI_PIPE ViPipe, ISP_PREROLL_LOCATION_ATTR_T *location);` | 254 | 当前新版MBI手册未检出，需源码/其他文档核验 |

## A123X平台知识库API：mbi_mipi_rx 当前RC1接口签名与PDF页码

核对日期：2026-10-23；来源为本地供应商资料和当前RC1源码。AI辅助整理，reviewing候选；仅供内部授权使用。资料/源码事实、项目回传证据与本轮设备实测分开；本轮未操作设备。

这是当前头文件公开声明的精确速查，不是示例调用或二进制ABI认证。参数类型与参数顺序以此快照为准；结构体布局及条件编译需结合匹配头文件。返回码/阻塞/资源所有权只在对应主题与手册核实后使用。

来源：`workspaces/ipc-c5-rc.1.0/linux/mbp/mbi/isp/include/mbi_mipi_rx.h`；SHA-256 `2bd20074612f39586dca25f01ba424893db156ad5c37426714275bc1d9c5e36f`。

| 接口 | 当前声明 | 源码行 | 对应新版MBI手册物理页 |
| --- | --- | --- | --- |
| `MBI_MIPI_RX_MipiDevInit` | `MBP_S32 MBI_MIPI_RX_MipiDevInit(void);` | 39 | IPC SDK MIPI Rx MBI (0.6).pdf p5,8,9,21 |
| `MBI_MIPI_RX_SetMipiHsMode` | `MBP_S32 MBI_MIPI_RX_SetMipiHsMode(LANE_DIVIDE_MODE_E enHsMode);` | 40 | IPC SDK MIPI Rx MBI (0.6).pdf p5,8,9,10,34 |
| `MBI_MIPI_RX_EnableMipiClock` | `MBP_S32 MBI_MIPI_RX_EnableMipiClock(COMBO_DEV_T mipiDev);` | 41 | IPC SDK MIPI Rx MBI (0.6).pdf p5,8,10,20,34 |
| `MBI_MIPI_RX_ResetMipi` | `MBP_S32 MBI_MIPI_RX_ResetMipi(COMBO_DEV_T mipiDev);` | 42 | IPC SDK MIPI Rx MBI (0.6).pdf p5,8,11,15,17,34 |
| `MBI_MIPI_RX_EnableSensorClock` | `MBP_S32 MBI_MIPI_RX_EnableSensorClock(SEN_CLK_SRC_T *Snsclk);` | 43 | IPC SDK MIPI Rx MBI (0.6).pdf p5,8,12,19,35 |
| `MBI_MIPI_RX_ResetSensor` | `MBP_S32 MBI_MIPI_RX_ResetSensor(SNS_RSE_SOURCE_T SnsNum);` | 44 | IPC SDK MIPI Rx MBI (0.6).pdf p5,8,13,16,18,35 |
| `MBI_MIPI_RX_SetMipiAttr` | `MBP_S32 MBI_MIPI_RX_SetMipiAttr(COMBO_DEV_ATTR_T *devAttr);` | 45 | IPC SDK MIPI Rx MBI (0.6).pdf p5,8,14,39 |
| `MBI_MIPI_RX_ResumeMipi` | `MBP_S32 MBI_MIPI_RX_ResumeMipi(COMBO_DEV_T mipiDev);` | 46 | IPC SDK MIPI Rx MBI (0.6).pdf p5,8,16,17,34 |
| `MBI_MIPI_RX_ResumeSensor` | `MBP_S32 MBI_MIPI_RX_ResumeSensor(SNS_RSE_SOURCE_T SnsNum);` | 47 | IPC SDK MIPI Rx MBI (0.6).pdf p5,8,17,18,35 |
| `MBI_MIPI_RX_DisableSensorClock` | `MBP_S32 MBI_MIPI_RX_DisableSensorClock(SNS_CLK_SOURCE_T SnsNum);` | 48 | IPC SDK MIPI Rx MBI (0.6).pdf p5,8,13,18,19 |
| `MBI_MIPI_RX_DisableMipiClock` | `MBP_S32 MBI_MIPI_RX_DisableMipiClock(COMBO_DEV_T mipiDev);` | 49 | IPC SDK MIPI Rx MBI (0.6).pdf p5,8,11,19,34 |
| `MBI_MIPI_RX_MipiDevExit` | `MBP_S32 MBI_MIPI_RX_MipiDevExit(void);` | 50 | IPC SDK MIPI Rx MBI (0.6).pdf p5,8,9,20 |

## A123X平台知识库API：mbi_vi 当前RC1接口签名与PDF页码

核对日期：2026-10-23；来源为本地供应商资料和当前RC1源码。AI辅助整理，reviewing候选；仅供内部授权使用。资料/源码事实、项目回传证据与本轮设备实测分开；本轮未操作设备。

这是当前头文件公开声明的精确速查，不是示例调用或二进制ABI认证。参数类型与参数顺序以此快照为准；结构体布局及条件编译需结合匹配头文件。返回码/阻塞/资源所有权只在对应主题与手册核实后使用。

来源：`workspaces/ipc-c5-rc.1.0/linux/mbp/mbi/isp/include/mbi_vi.h`；SHA-256 `b47da8fdd79e27f55bfc022746e9b9e4976ee939ce0bcd3e33bc7f683f85d8b0`。

| 接口 | 当前声明 | 源码行 | 对应新版MBI手册物理页 |
| --- | --- | --- | --- |
| `MBI_VI_SetDevAttr` | `MBP_S32 MBI_VI_SetDevAttr(VI_DEV ViDev, const VI_DEV_ATTR_T *pstDevAttr);` | 40 | IPC SDK VI MBI (0.8).pdf p5,8,9,32,41 |
| `MBI_VI_GetDevAttr` | `MBP_S32 MBI_VI_GetDevAttr(VI_DEV ViDev, VI_DEV_ATTR_T *pstDevAttr);` | 41 | IPC SDK VI MBI (0.8).pdf p5,8,9 |
| `MBI_VI_EnableDev` | `MBP_S32 MBI_VI_EnableDev(VI_DEV ViDev);` | 43 | IPC SDK VI MBI (0.8).pdf p5,8,10,11,12,32 |
| `MBI_VI_DisableDev` | `MBP_S32 MBI_VI_DisableDev(VI_DEV ViDev);` | 44 | IPC SDK VI MBI (0.8).pdf p5,8,11,32 |
| `MBI_VI_GetPicBufferSize` | `MBP_U32 MBI_VI_GetPicBufferSize(MBP_U32 u32Width, MBP_U32 u32Height, MBP_PIXEL_FORMAT_E enPixelFormat, MBP_DATA_BITWIDTH_E enBitWidth, MBP_U32 u32Align);` | 46 | IPC SDK VI MBI (0.8).pdf p5,8,27,34 |
| `MBI_VI_GetRawBufferSizeEx` | `MBP_U32 MBI_VI_GetRawBufferSizeEx(MBP_U32 u32Width, MBP_U32 u32Height, MBP_PIXEL_FORMAT_E enPixelFormat, MBP_U32 u32Align);` | 51 | IPC SDK VI MBI (0.8).pdf p5,8,28,34 |

## A123X平台知识库API：mbi_aenc 当前RC1接口签名与PDF页码

核对日期：2026-10-23；来源为本地供应商资料和当前RC1源码。AI辅助整理，reviewing候选；仅供内部授权使用。资料/源码事实、项目回传证据与本轮设备实测分开；本轮未操作设备。

这是当前头文件公开声明的精确速查，不是示例调用或二进制ABI认证。参数类型与参数顺序以此快照为准；结构体布局及条件编译需结合匹配头文件。返回码/阻塞/资源所有权只在对应主题与手册核实后使用。

来源：`workspaces/ipc-c5-rc.1.0/linux/mbp/mbi/mbi_base/include/mbi_aenc.h`；SHA-256 `414e75e1667f9db73a3a796922bb44b64f544f34f443bd26e782d441fdb0fbd0`。

| 接口 | 当前声明 | 源码行 | 对应新版MBI手册物理页 |
| --- | --- | --- | --- |
| `MBI_AENC_CreateChn` | `MBP_S32 MBI_AENC_CreateChn(AENC_CHN AeChn, const AENC_CHN_ATTR_T *pstAttr);` | 41 | IPC SDK AUDIO MBI (0.9).pdf p6,16,70,72,73,74,75,76,77,78,79 |
| `MBI_AENC_DestroyChn` | `MBP_S32 MBI_AENC_DestroyChn(AENC_CHN AeChn);` | 42 | IPC SDK AUDIO MBI (0.9).pdf p6,16,72 |
| `MBI_AENC_SendFrame` | `MBP_S32 MBI_AENC_SendFrame(AENC_CHN AeChn, const AUDIO_FRAME_T *pstFrm, const AEC_FRAME_T *pstAecFrm);` | 44 | IPC SDK AUDIO MBI (0.9).pdf p6,16,72,73 |
| `MBI_AENC_GetFd` | `MBP_S32 MBI_AENC_GetFd(AENC_CHN AeChn);` | 46 | IPC SDK AUDIO MBI (0.9).pdf p6,16,74 |
| `MBI_AENC_RegisterEncoder` | `MBP_S32 MBI_AENC_RegisterEncoder(MBP_S32 *ps32Handle, const AENC_ENCODER_T *pstAencEncoder);` | 48 | IPC SDK AUDIO MBI (0.9).pdf p6,16,77 |
| `MBI_AENC_UnRegisterEncoder` | `MBP_S32 MBI_AENC_UnRegisterEncoder(MBP_S32 s32Handle);` | 49 | IPC SDK AUDIO MBI (0.9).pdf p6,16,78 |
| `MBI_AENC_GetStream` | `MBP_S32 MBI_AENC_GetStream(AENC_CHN AencChn, AUDIO_STREAM_T *pstStream, MBP_S32 s32MilliSec);` | 51 | IPC SDK AUDIO MBI (0.9).pdf p6,16,72,75,77 |
| `MBI_AENC_ReleaseStream` | `MBP_S32 MBI_AENC_ReleaseStream(AENC_CHN AencChn, AUDIO_STREAM_T *pstStream);` | 52 | IPC SDK AUDIO MBI (0.9).pdf p6,16,72,76 |
| `MBI_AENC_GetStreamBufInfo` | `MBP_S32 MBI_AENC_GetStreamBufInfo(AENC_CHN AeChn, MBP_U64* pu64PhysAddr, MBP_U32* pu32Size);` | 54 | IPC SDK AUDIO MBI (0.9).pdf p6,16,77 |

## A123X平台知识库API：mbi_ppu 当前RC1接口签名与PDF页码

核对日期：2026-10-23；来源为本地供应商资料和当前RC1源码。AI辅助整理，reviewing候选；仅供内部授权使用。资料/源码事实、项目回传证据与本轮设备实测分开；本轮未操作设备。

这是当前头文件公开声明的精确速查，不是示例调用或二进制ABI认证。参数类型与参数顺序以此快照为准；结构体布局及条件编译需结合匹配头文件。返回码/阻塞/资源所有权只在对应主题与手册核实后使用。

来源：`workspaces/ipc-c5-rc.1.0/linux/mbp/mbi/ppu/include/mbi_ppu.h`；SHA-256 `32f52eeedc3136af775079aca437bcf5547b8459339c05197373e4fc557e1277`。

| 接口 | 当前声明 | 源码行 | 对应新版MBI手册物理页 |
| --- | --- | --- | --- |
| `MBI_PPU_SetChnLDCAttr` | `MBP_S32 MBI_PPU_SetChnLDCAttr(MBP_S32 ppuDev, PPU_CHN ppuChn, MBP_PPU_LDC_ATTR_T *ldcAttr);` | 55 | IPC SDK PPU MBI (0.6).pdf p5,7,10 |
| `MBI_PPU_GetChnLDCAttr` | `MBP_S32 MBI_PPU_GetChnLDCAttr(MBP_S32 ppuDev, PPU_CHN ppuChn, MBP_PPU_LDC_ATTR_T *ldcAttr);` | 56 | IPC SDK PPU MBI (0.6).pdf p5,7,8 |
| `MBI_PPU_SetChnRotateAttr` | `MBP_S32 MBI_PPU_SetChnRotateAttr(MBP_S32 ppuDev, PPU_CHN ppuChn, MBP_PPU_ROTATE_ATTR_T *rotateAttr);` | 57 | IPC SDK PPU MBI (0.6).pdf p5,7,9 |
| `MBI_PPU_GetChnRotateAttr` | `MBP_S32 MBI_PPU_GetChnRotateAttr(MBP_S32 ppuDev, PPU_CHN ppuChn, MBP_PPU_ROTATE_ATTR_T *rotateAttr);` | 58 | IPC SDK PPU MBI (0.6).pdf p5,7,10 |
| `MBI_PPU_SetRec` | `MBP_S32 MBI_PPU_SetRec(MBP_S32 ppuDev, PPU_CHN ppuChn, PPU_REC_ATTR_T *recAttr);` | 59 | IPC SDK PPU MBI (0.6).pdf p5,7,11 |
| `MBI_PPU_GetChnRec` | `MBP_S32 MBI_PPU_GetChnRec(MBP_S32 ppuDev, PPU_CHN ppuChn, PPU_REC_ATTR_T *recAttr);` | 60 | IPC SDK PPU MBI (0.6).pdf p5,7,12 |
| `MBI_PPU_SetChnAttr` | `MBP_S32 MBI_PPU_SetChnAttr(MBP_S32 ppuDev, PPU_CHN ppuChn, MBP_PPU_CHN_ATTR_T *chnAttr);` | 61 | IPC SDK PPU MBI (0.6).pdf p3,5,7,12,13 |
| `MBI_PPU_GetChnAttr` | `MBP_S32 MBI_PPU_GetChnAttr(MBP_S32 ppuDev, PPU_CHN ppuChn, MBP_PPU_CHN_ATTR_T *chnAttr);` | 62 | IPC SDK PPU MBI (0.6).pdf p3,5,7,13 |
| `MBI_PPU_SetExtChnAttr` | `MBP_S32 MBI_PPU_SetExtChnAttr(MBP_S32 ppuDev, PPU_CHN ppuChn, MBP_PPU_EXTCHN_ATTR_T *extChnAttr);` | 63 | IPC SDK PPU MBI (0.6).pdf p5,7,14 |
| `MBI_PPU_GetExtChnAttr` | `MBP_S32 MBI_PPU_GetExtChnAttr(MBP_S32 ppuDev, PPU_CHN ppuChn, MBP_PPU_EXTCHN_ATTR_T *extChnAttr);` | 64 | IPC SDK PPU MBI (0.6).pdf p5,7,15 |
| `MBI_PPU_GetChnFrame` | `MBP_S32 MBI_PPU_GetChnFrame(MBP_S32 ppuDev, PPU_CHN ppuChn, MBP_VIDEO_FRAME_INFO_T *frame);` | 65 | IPC SDK PPU MBI (0.6).pdf p5,7,16,18,20 |
| `MBI_PPU_ReleaseChnFrame` | `MBP_S32 MBI_PPU_ReleaseChnFrame(MBP_S32 ppuDev, PPU_CHN ppuChn, MBP_VIDEO_FRAME_INFO_T *frame);` | 66 | IPC SDK PPU MBI (0.6).pdf p5,7,17 |
| `MBI_PPU_SetIspVencHwlink` | `MBP_S32 MBI_PPU_SetIspVencHwlink(MBP_S32 ppuDev, PPU_CHN ppuChn, MBP_VIDEO_HWLINK_T *hwlink);` | 67 | IPC SDK PPU MBI (0.6).pdf p5,19 |
| `MBI_PPU_SetDumpAttr` | `MBP_S32 MBI_PPU_SetDumpAttr(MBP_S32 ppuDev, PPU_CHN ppuChn, MBP_PPU_DUMP_ATTR_T *dumpAttr);` | 68 | IPC SDK PPU MBI (0.6).pdf p5,20 |
