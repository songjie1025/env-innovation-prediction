import json
import sys
import tempfile
import time
import unittest
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parents[1] / "3_models" / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

from run_modeling import _figure_index_rows, build_output_manifest, verify_generated_artifacts  # noqa: E402


class ModelNotebookTests(unittest.TestCase):
    def test_interpretability_notebook_is_display_only_evidence_report(self):
        notebook_path = (
            Path(__file__).resolve().parents[1]
            / "3_models"
            / "notebooks"
            / "modeling_interpretability_analysis.ipynb"
        )
        notebook = json.loads(notebook_path.read_text(encoding="utf-8"))
        notebook_text = notebook_path.read_text(encoding="utf-8")
        markdown_text = "\n".join(
            "".join(cell.get("source", []))
            for cell in notebook["cells"]
            if cell.get("cell_type") == "markdown"
        )

        expected_sections = [
            "Interpretability Scope",
            "Performance Boundary",
            "Global Importance",
            "SHAP Summary",
            "Permutation Importance",
            "Partial Dependence",
            "Cross-Model Consistency",
            "Error-Aware Interpretation",
            "Reviewer Caveats",
        ]
        for section in expected_sections:
            self.assertIn(section, markdown_text)

        expected_artifacts = [
            "COEFFICIENTS_OUTPUT",
            "TREE_HISTORICAL_DELTA_OUTPUT",
            "TREE_IMPORTANCE_OUTPUT",
            "TREE_PARTIAL_DEPENDENCE_OUTPUT",
            "TREE_FIGURE_INDEX_OUTPUT",
            "fig7_permutation_importance",
            "tree_model_shap_summary",
            "abs_coefficient > 1e-12",
            "observed",
            "post-hoc test-block diagnostic",
        ]
        for artifact in expected_artifacts:
            self.assertIn(artifact, notebook_text)

        forbidden_training_calls = [
            "run_tree_modeling(",
            "run_linear_modeling(",
            "run_panel_tree_experiment(",
            "run_panel_linear_experiment(",
            ".fit(",
        ]
        for forbidden in forbidden_training_calls:
            self.assertNotIn(forbidden, notebook_text)

    def test_linear_baseline_notebook_checks_generated_artifacts(self):
        notebook_path = (
            Path(__file__).resolve().parents[1]
            / "3_models"
            / "notebooks"
            / "modeling_linear_baseline.ipynb"
        )
        notebook = json.loads(notebook_path.read_text(encoding="utf-8"))
        verify_cells = [
            cell
            for cell in notebook["cells"]
            if cell.get("cell_type") == "code" and cell.get("id") == "verify-generated-artifacts"
        ]

        self.assertEqual(len(verify_cells), 1)
        source = "".join(verify_cells[0]["source"])
        self.assertIn("verify_generated_artifacts", source)
        self.assertIn("artifact_check", source)
        self.assertIn("run_started_at", source)
        self.assertNotIn("required_output_filenames", source)
        self.assertNotIn("for name, path in results['outputs'].items()", source)
        self.assertLess(len(source.splitlines()), 20)

        manifest = build_output_manifest()
        self.assertIn("specification_registry", manifest)
        self.assertIn("missingness_pattern_summary", manifest)
        self.assertIn("missingness_pattern_country_detail", manifest)
        self.assertIn("persistence_augmented_comparison", manifest)
        self.assertIn("persistence_augmented_test_metrics", manifest)
        self.assertIn("persistence_augmented_coefficients", manifest)
        self.assertIn("skew_transform_plan", manifest)
        self.assertIn("robustness_summary", manifest)
        self.assertIn("robustness_historical_baselines", manifest)
        self.assertIn("historical_baseline_delta_summary", manifest)
        self.assertIn("error_by_year", manifest)
        self.assertIn("error_by_target_quantile", manifest)
        self.assertIn("rolling_origin_summary", manifest)
        self.assertIn("rolling_origin_predictions", manifest)
        self.assertIn("missingness_indicator_plan", manifest)
        self.assertIn("figure_index", manifest)
        filenames = [path.name for path in manifest.values()]
        self.assertEqual(len(filenames), len(set(filenames)))
        self.assertTrue(callable(verify_generated_artifacts))

    def test_artifact_verifier_rejects_empty_registered_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            empty_output = tmp_path / "empty.csv"
            empty_output.write_text("", encoding="utf-8")
            figure_index = tmp_path / "figure_index.csv"
            figure_index.write_text(
                "figure,path,pdf_path\nplot,plot.png,plot.pdf\n",
                encoding="utf-8",
            )
            png_path = tmp_path / "plot.png"
            pdf_path = tmp_path / "plot.pdf"
            png_path.write_bytes(b"png")
            pdf_path.write_bytes(b"pdf")
            results = {
                "outputs": {
                    "empty": empty_output,
                    "figure_index": figure_index,
                },
                "figure_paths": {"plot": png_path},
            }

            with self.assertRaisesRegex(AssertionError, "Empty generated artifact"):
                verify_generated_artifacts(
                    results=results,
                    run_started_at=time.time() - 10,
                    project_root=tmp_path,
                )

    def test_figure_index_rows_include_png_and_pdf_paths(self):
        rows = _figure_index_rows({"partial_dependence": SCRIPT_DIR / "example.png"})

        self.assertEqual(
            rows,
            [
                {
                    "figure": "partial_dependence",
                    "path": "3_models/scripts/example.png",
                    "pdf_path": "3_models/scripts/example.pdf",
                }
            ],
        )

    def test_linear_baseline_notebook_documents_submodels_and_correlation_diagnostics(self):
        notebook_path = (
            Path(__file__).resolve().parents[1]
            / "3_models"
            / "notebooks"
            / "modeling_linear_baseline.ipynb"
        )
        notebook_text = notebook_path.read_text(encoding="utf-8")

        self.assertIn("Main Model Versus Mechanism Submodels", notebook_text)
        self.assertIn("Same-Sample Nested Submodel Tests", notebook_text)
        self.assertIn("ElasticNet Under Correlated Predictors", notebook_text)
        self.assertIn("nested_test_mae_comparison", notebook_text)
        self.assertIn("historical_baseline_mae", notebook_text)
        self.assertIn("top_absolute_errors", notebook_text)
        self.assertIn("main_feature_correlation_heatmap", notebook_text)
        self.assertIn("Persistence Baselines", notebook_text)
        self.assertIn("Persistence-Augmented Model", notebook_text)
        self.assertIn("feature-only main model", notebook_text)
        self.assertIn("block-safe target history", notebook_text)
        self.assertIn("persistence_augmented_comparison", notebook_text)
        self.assertIn("Failure Modes", notebook_text)
        self.assertIn("Missingness Pattern Diagnostics", notebook_text)
        self.assertIn("missingness_pattern_counts", notebook_text)
        self.assertIn("late-start coverage", notebook_text)
        self.assertIn("intermittent gaps", notebook_text)
        self.assertIn("Missingness Sensitivity", notebook_text)
        self.assertIn("Linear Robustness Pack", notebook_text)
        self.assertIn("Skew-Transformed Linear Robustness", notebook_text)
        self.assertIn("skew_transform_plan", notebook_text)
        self.assertIn("robust_main_share_skew_transformed_lag1_3_mean", notebook_text)
        self.assertIn("common-sample lag1 versus lag1_3_mean", notebook_text)
        self.assertIn("env_patents_per_million", notebook_text)
        self.assertIn("target-scale dependent", notebook_text)
        self.assertIn("robustness_validation_test_mae", notebook_text)
        self.assertIn("robustness_history_delta", notebook_text)
        self.assertIn("none of the submodel augmentations improves primary test MAE", notebook_text)
        self.assertIn("run_started_at = time.time()", notebook_text)
        self.assertNotIn("show_figure('target_distribution')", notebook_text)
        self.assertNotIn("show_figure('error_by_year')", notebook_text)
        self.assertNotIn("show_figure('submodel_coefficients')", notebook_text)
        self.assertNotIn("results['top_absolute_errors']", notebook_text)
        self.assertNotIn("display(artifact_table)", notebook_text)
        self.assertNotIn("display(figure_index)", notebook_text)
        self.assertIn("artifact_count_summary", notebook_text)
        self.assertIn("artifact_suffix_summary", notebook_text)

    def test_linear_baseline_notebook_uses_professor_level_teaching_scaffold(self):
        notebook_path = (
            Path(__file__).resolve().parents[1]
            / "3_models"
            / "notebooks"
            / "modeling_linear_baseline.ipynb"
        )
        notebook_text = notebook_path.read_text(encoding="utf-8")

        self.assertIn("First Linear Checkpoint", notebook_text)
        self.assertIn("Question -> Concept -> Output -> How to read -> Takeaway", notebook_text)
        self.assertIn("confirmatory rolling-origin", notebook_text)
        self.assertIn("history_delta_summary", notebook_text)
        self.assertIn("error_by_target_quantile", notebook_text)
        self.assertIn("missingness_indicator_refit", notebook_text)
        self.assertIn("do not claim that external predictors beat national historical persistence", notebook_text)


if __name__ == "__main__":
    unittest.main()
