# Dependency and License Inventory

`uv.lock` is the executable dependency authority. GitHub Actions also emits a
full SPDX JSON software bill of materials for every validated release build.

Direct runtime dependencies:

| package | locked version | declared license |
|---|---:|---|
| marimo | 0.23.15 | Apache-2.0 |
| NumPy | 2.5.1 | BSD-3-Clause and bundled component licenses |
| SciPy | 1.18.0 | BSD-3-Clause and bundled component licenses |
| scikit-learn | 1.9.0 | BSD-3-Clause |

Direct development dependencies:

| package | locked version | declared license |
|---|---:|---|
| Playwright | 1.61.0 | Apache-2.0 |
| pytest | 9.1.1 | MIT |
| Ruff | 0.16.0 | MIT |

The tables are a human-readable direct-dependency summary, not a substitute for
the generated transitive SBOM or package license texts. Update them together
with `uv.lock`.
