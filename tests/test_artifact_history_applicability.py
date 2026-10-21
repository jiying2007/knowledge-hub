"""Historical artifact navigation must not become current execution authority."""
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "artifacts/README.md"


def test_artifact_readme_keeps_one_title_and_vault_boundaries():
    doc = README.read_text(encoding="utf-8")
    assert doc.count("# Artifacts\n") == 1
    for boundary in (
        "不等同于 `registry/items.jsonl`", "external-reference-only",
        "不得声称本地文件存在", "不得进入 vault", "private keys",
    ):
        assert boundary in doc


def test_history_notice_links_originals_without_rewriting_project_identity():
    doc = README.read_text(encoding="utf-8")
    for value in (
        "manifests/knowledge-hub-manual-recovery-boundary-hardening-20260621.md",
        "manifests/knowledge-hub-recovery-search-manual-hardening-20260622.md",
        "../tools/README.md", "domains/projects/pcr02/",
        "projects/pcr02-ssc305/", "projects/xcrz-sigmastar-demo/",
        "不是可互换命名空间", "不做一对一全局路径替换",
    ):
        assert value in doc


def test_retired_option_is_explained_not_reintroduced_as_an_executable_example():
    doc = README.read_text(encoding="utf-8")
    assert "`--source-status` 已移除" in doc
    assert "退出码 2" in doc
    assert "ERROR unknown argument: --source-status" in doc
    assert "不要恢复此参数" in doc
    for block in re.findall(r"```[^\n]*\n(.*?)```", doc, flags=re.DOTALL):
        assert "--source-status" not in block
        assert "domains/projects/pcr02/" not in block


def test_historical_results_never_confer_new_review_or_operation_authority():
    doc = README.read_text(encoding="utf-8")
    for boundary in (
        "不等于实际执行结果", "不能单独证明命令已经执行",
        "完整制品 SHA-256", "不得补写成功结果", "改写历史原文",
        "自动延后 `review_after`", "代签 Owner", "关闭 owner gate",
        "不授予发布、设备操作、源项目写入或安全审批权限",
        "Issue #176", "不等于全库知识自动审查完成",
    ):
        assert boundary in doc


def test_personal_history_notice_points_to_current_rules_without_scope_promotion():
    doc = README.read_text(encoding="utf-8")
    for value in (
        "manifests/knowledge-hub-manual-entry-owner-personal-source-recommendation-20260623.md",
        "domains/personal/", "notes/personal/", "../AGENTS.md", "scope=team-general",
        "不因路径、scope 或 Owner 名称而转成团队知识", "不进入团队 active index",
        "不读取、迁移或导出个人正文",
    ):
        assert value in doc
