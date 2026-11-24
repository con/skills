# Lens: compute

Numerical and scientific code, high-performance and GPU computing, batch
jobs on clusters, and code whose speed or memory use matters.

## Recognize

Code using NumPy, SciPy, pandas, xarray, Dask, Numba, JAX, PyTorch,
TensorFlow, CuPy or Cython; C, C++, Fortran, CUDA or Julia kernels; cluster
job scripts (`#SBATCH` or `#PBS` lines, `*.slurm`, `sbatch` wrappers);
benchmarks (`benchmarks/`, `asv.conf.json`); readers and writers of large
array files (HDF5, Zarr, NWB, NetCDF); simulation and model code.

## Context to read

The dtypes and precision the project uses; reference results, golden files
and tolerances in its tests; its benchmark suite; the hardware and cluster
it runs on; the size of real inputs (a function fine on a test array may
run on terabytes).

## Checks

**Numerical correctness** (usually blocking)
- Integer arithmetic in fixed-width types wraps without an error in NumPy
  arrays: subtracting `uint16` values, or sums and products that exceed
  `int32`. Look at the dtype each operand really has.
- Silent dtype changes: integer division, mixing `float32` and `float64`,
  a dtype lost on a round trip through pandas or a file format.
- Floating-point equality (`==`) in code or tests where a tolerance suited to
  the dtype is needed; accumulating many `float32` values without a wider
  accumulator.
- NaN and infinity: NaN-aware reductions where data can be missing; NaN
  is unequal to everything, itself included, so `x == x` is false for it
  and Python's `sorted`, `min` and `max` give order-dependent results; a
  division that can hit zero.
- Shapes: broadcasting a `(n,)` array against `(n, 1)` gives `(n, n)`
  without an error; reductions over the wrong axis; off-by-one in slicing,
  binning and windowing.
- Mutation of inputs: in-place operations on a view change the caller's
  array; chained assignment in pandas (`df[a][b] = x`) may not write
  through.
- Units and conventions: unit conversions, time bases and epochs, time
  zones, index origins (0 or 1), row-major or column-major layout.

**Reproducibility** (should-fix)
- Random generators are seeded through a passed-in generator, not global
  state, and the seed is recorded with results; GPU operations known to be
  nondeterministic are either avoided or disclosed; results do not depend on
  the number of threads or workers.

**Performance and memory** (should-fix on a hot path; else optional)
- Python loops over large arrays where a vectorized operation exists;
  allocation inside hot loops; needless copies; whole datasets loaded into
  memory where chunked or lazy access exists; chunk shapes that fight the
  access pattern; quadratic algorithms on inputs that can be large.
- A claimed speed-up comes with a measurement.

**Parallelism** (blocking for races; should-fix otherwise)
- Workers writing to shared arrays without coordination; large objects
  pickled to every worker; nested parallelism that oversubscribes cores
  (BLAS threads inside processes); memory per worker times workers versus
  the machine.

**Cluster jobs** (should-fix)
- Requested memory, time and GPUs match the work; long jobs checkpoint and
  survive preemption; temporary files go to scratch space and are removed;
  no hard-coded user paths, accounts or partitions.

**Tests** (should-fix)
- Results compared to known references with a stated tolerance; edge cases
  such as empty arrays, a single element, NaN, extreme values and
  non-contiguous arrays.

## Not findings

- Micro-optimizations off the hot path.
- Notation and naming that follow the field's conventions.
- GPU or distributed support the pull request does not set out to add.

## Verification

- **static**: read the dtypes and shapes at each step; search the tests for
  the tolerances used; check claimed complexity against the code.
- **consent**: the project's tests and benchmarks; a small numerical
  experiment in a scratch directory that imports the pull request's code.
