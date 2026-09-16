# Hyperparameter sweep for the KG vs CG experiment.
# Runs the 50-question suite once per hyperparameter value (a fresh Python
# process per run, so each variant genuinely reads its env var at import
# time -- no in-process config patching, which wouldn't propagate correctly).
# One-off analysis tool: delete this file, sweep_results/, and
# kg_cg_experiment/tests/summarize_sweep.py when you're done with it.
#
# Run:  .\run_sweep.ps1

$root = "kg_cg_experiment/sweep_results"
New-Item -ItemType Directory -Force -Path $root | Out-Null

# --- Temperature sweep (structured track) ---
foreach ($T in "0","0.3","0.7","1.0") {
    Write-Host "=== temperature=$T ==="
    $env:OLLAMA_TEMPERATURE = $T
    python -m kg_cg_experiment.tests.run_queries_retail_tests
    $dir = "$root/temperature_$T"
    New-Item -ItemType Directory -Force -Path $dir | Out-Null
    Copy-Item kg_cg_experiment/results_retail/raw_log.md "$dir/raw_log.md"
    Copy-Item kg_cg_experiment/results_retail/index.md   "$dir/index.md"
}
$env:OLLAMA_TEMPERATURE = "0"

# --- Trace similarity threshold sweep (structured track) ---
foreach ($S in "0.4","0.5","0.65","0.75","0.85","0.95") {
    Write-Host "=== trace_threshold=$S ==="
    $env:TRACE_SIMILARITY_THRESHOLD = $S
    python -m kg_cg_experiment.tests.run_queries_retail_tests
    $dir = "$root/trace_threshold_$S"
    New-Item -ItemType Directory -Force -Path $dir | Out-Null
    Copy-Item kg_cg_experiment/results_retail/raw_log.md "$dir/raw_log.md"
    Copy-Item kg_cg_experiment/results_retail/index.md   "$dir/index.md"
}
Remove-Item Env:\TRACE_SIMILARITY_THRESHOLD

# --- Chunk similarity threshold sweep (unstructured track) ---
foreach ($C in "0.3","0.4","0.45","0.55","0.65") {
    Write-Host "=== chunk_threshold=$C ==="
    $env:CHUNK_SIMILARITY_THRESHOLD = $C
    python -m kg_cg_experiment.tests.run_queries_unstructured_source_tests
    $dir = "$root/chunk_threshold_$C"
    New-Item -ItemType Directory -Force -Path $dir | Out-Null
    Copy-Item kg_cg_experiment/results_retail_unstructured/raw_log.md "$dir/raw_log.md"
    Copy-Item kg_cg_experiment/results_retail_unstructured/index.md   "$dir/index.md"
}
Remove-Item Env:\CHUNK_SIMILARITY_THRESHOLD

Write-Host "=== sweep complete, summarizing ==="
python -m kg_cg_experiment.tests.summarize_sweep
