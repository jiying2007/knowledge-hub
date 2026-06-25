---
name: voice-audio-normalizer
description: 统一 resource/voices 音频资产为单声道 mp3，自动识别并转换非 mp3 或非单声道文件。
version: 1.0.0
last_updated: 2026-05-15
---

# Voice Audio Normalizer Skill

## 1. 触发条件

- 用户要求统一 `resource/voices` 下音频格式。
- 用户要求“非 mp3 转 mp3”或“全部转单声道”。
- 用户要求批量转码并给出可验证结果。

## 2. 处理范围

- 默认处理目录：`resource/voices`。
- 仅处理音频扩展名：`mp3`、`wav`、`aac`、`m4a`、`flac`、`ogg`、`opus`。
- 目标输出：`mp3` + `1` 声道（mono）。

## 3. 执行步骤

1. 先做预检：
   - 检查 `ffmpeg`、`ffprobe` 是否可用。
   - 扫描待处理目录内音频文件。
2. 执行标准化脚本：
   - 命令：`rtk bash tools/.codex/skills/voice-audio-normalizer/scripts/normalize_voice_audio.sh resource/voices`
3. 完成后复核：
   - 使用 `ffprobe` 检查格式与声道，确认全部为 `mp3|1`。
4. 输出结果时必须给出：
   - 变更文件清单（至少新增/删除/修改统计）。
   - 验证命令与关键结果。

## 4. 失败处理

- 若依赖缺失（`ffmpeg`/`ffprobe`），必须明确报错并停止。
- 若某文件读取失败，脚本返回非 0，输出失败文件路径，禁止声称“全部完成”。

## 5. 最小验证

- 干跑：`rtk bash tools/.codex/skills/voice-audio-normalizer/scripts/normalize_voice_audio.sh --dry-run resource/voices`
- 实跑：`rtk bash tools/.codex/skills/voice-audio-normalizer/scripts/normalize_voice_audio.sh resource/voices`
- 复核：`rtk bash -lc 'for f in resource/voices/*; do ... ffprobe ...; done'`
