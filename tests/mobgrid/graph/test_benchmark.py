import numpy as np
from mobgrid.graph.benchmark import run_benchmark
from mobgrid.graph.csr import csr_from_indexed_edges, save_graph


def test_benchmark_checkpoints_and_resumes_synthetic_searches(tmp_path):
    paths = {}
    for mode in ("car", "bike", "foot"):
        graph = csr_from_indexed_edges(
            mode,
            np.arange(3, dtype=np.int64),
            np.array([0, 1, 2]),
            np.array([1, 2, 0]),
            {
                "time_s": np.array([1, 2, 3], dtype=np.float32),
                "distance_m": np.array([10, 20, 30], dtype=np.float32),
                "energy_kj": np.array([2, 3, 4], dtype=np.float32),
            },
            reference_mass_kg=74,
            bike_mass_kg=15,
        )
        paths[mode] = tmp_path / f"{mode}.npz"
        save_graph(graph, paths[mode])
    kwargs = dict(
        graph_paths=paths,
        cutoffs_s={"car": 10.0, "bike": 10.0, "foot": 10.0},
        resolution_s=0.1,
        searches=3,
        seed=42,
        checkpoint_dir=tmp_path / "interim",
        log_dir=tmp_path / "logs",
        date="2026-01-01",
    )
    first = run_benchmark(**kwargs)
    checkpoint = next((tmp_path / "interim").glob("car_heap_*.jsonl"))
    with checkpoint.open("ab") as stream:
        stream.write(b'{"origin":')
    resumed = run_benchmark(**kwargs)
    assert first == resumed
    assert len(first) == 6
    assert all(item.searches == 3 for item in first)
    summary = tmp_path / "logs" / "2026-01-01_graph_search_benchmark_summary.md"
    assert summary.is_file()
    text = summary.read_text(encoding="utf-8")
    assert "car" in text
    assert "incomplete checkpoint line" in text
