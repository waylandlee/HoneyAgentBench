from argparse import Namespace

from scripts.write_run_manifest import build_manifest


def test_manifest_redacts_secret_environment_values(tmp_path, monkeypatch):
    summary = tmp_path / "summary.md"
    summary.write_text("ok", encoding="utf-8")
    monkeypatch.setenv("DEEPSEEK_API_KEY", "secret-value")

    args = Namespace(
        out_dir=str(tmp_path),
        cwd=".",
        phase="phase1-baseline",
        run_name="unit",
        model="unit-model",
        eval_name="unit-eval",
        variant_name="baseline-react",
        scenario_seed="v3-static-baseline",
        response_mode="debug",
        command=["pytest -q"],
        docker_image_tag=None,
        score_log=[],
        result_file=[],
        env_key=["DEEPSEEK_API_KEY"],
        note=["unit test"],
    )

    manifest = build_manifest(args)

    assert manifest["environment"]["DEEPSEEK_API_KEY"]["value"] == "<redacted>"
    assert manifest["result_files"][0]["sha256"] is not None
