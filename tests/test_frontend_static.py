from __future__ import annotations

import ast
from pathlib import Path
from unittest import TestCase


class FrontendStaticTests(TestCase):
    def test_streamlit_globals_are_defined_before_first_use(self) -> None:
        source = Path("frontend/streamlit_app.py").read_text(encoding="utf-8-sig")
        tree = ast.parse(source)
        first_lang_load = None
        first_zh_decision_load = None
        lang_assignment = None
        zh_decision_assignment = None

        for node in ast.walk(tree):
            if isinstance(node, ast.Name) and node.id == "LANG" and isinstance(node.ctx, ast.Load):
                first_lang_load = node.lineno if first_lang_load is None else min(first_lang_load, node.lineno)
            if isinstance(node, ast.Name) and node.id == "ZH_DECISION_TEXT" and isinstance(node.ctx, ast.Load):
                first_zh_decision_load = (
                    node.lineno if first_zh_decision_load is None else min(first_zh_decision_load, node.lineno)
                )
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == "LANG":
                        lang_assignment = node.lineno if lang_assignment is None else min(lang_assignment, node.lineno)
                    if isinstance(target, ast.Name) and target.id == "ZH_DECISION_TEXT":
                        zh_decision_assignment = (
                            node.lineno if zh_decision_assignment is None else min(zh_decision_assignment, node.lineno)
                        )
            if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
                if node.target.id == "LANG":
                    lang_assignment = node.lineno if lang_assignment is None else min(lang_assignment, node.lineno)
                if node.target.id == "ZH_DECISION_TEXT":
                    zh_decision_assignment = (
                        node.lineno if zh_decision_assignment is None else min(zh_decision_assignment, node.lineno)
                    )

        self.assertIsNotNone(lang_assignment)
        self.assertIsNotNone(zh_decision_assignment)
        assert first_lang_load is not None
        assert first_zh_decision_load is not None
        assert lang_assignment is not None
        assert zh_decision_assignment is not None
        self.assertLess(lang_assignment, first_lang_load)
        self.assertLess(zh_decision_assignment, first_zh_decision_load)

    def test_top_level_local_function_calls_are_defined_first(self) -> None:
        source = Path("frontend/streamlit_app.py").read_text(encoding="utf-8-sig")
        tree = ast.parse(source)
        local_function_lines = {
            node.name: node.lineno
            for node in tree.body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        }
        imported_or_assigned_names: set[str] = set()
        for node in tree.body:
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imported_or_assigned_names.add(alias.asname or alias.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    imported_or_assigned_names.add(alias.asname or alias.name)
            elif isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        imported_or_assigned_names.add(target.id)
            elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
                imported_or_assigned_names.add(node.target.id)

        for node in tree.body:
            if not isinstance(node, ast.Expr) or not isinstance(node.value, ast.Call):
                continue
            call = node.value.func
            if not isinstance(call, ast.Name):
                continue
            self.assertTrue(
                call.id in local_function_lines or call.id in imported_or_assigned_names,
                f"{call.id} is called at top level but is not defined or imported",
            )
            if call.id not in local_function_lines:
                continue
            self.assertLess(
                local_function_lines[call.id],
                node.lineno,
                f"{call.id} is called before it is defined",
            )
