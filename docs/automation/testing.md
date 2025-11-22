## Unit tests

### The location and naming conventions for unit test files.

The unit test files are located in the `tests` directory.
The naming conventions for unit test files are:
- `test_<module_name>.py`
- `test_<module_name>_<function_name>.py`
- `test_<module_name>_<class_name>.py`
- `test_<module_name>_<class_name>_<function_name>.py`

### The command to run unit tests.

The command to run unit tests is (you should run it from the app directory):
```bash
pytest
```
or
```bash
pytest tests/<module_name>
```
or
```bash
pytest tests/<module_name>/<function_name>
```

### The command to generate a coverage report.

Coverage report is automatically generated in ci-cd pipeline.

The command to generate a coverage report is (you should run it from the app directory):
```bash
pytest --cov=. --cov-report=xml --cov-report=html --cov-fail-under=30
```

### How to adjust the minimum coverage thresholds.

if you want to adjust the minimum coverage thresholds, you can do it in the `.github/workflows/ci-cd.yml` file.
```yaml
coverage_report:
  fail_under: <your_desired_coverage_threshold>
```

### Why did you choose this coverage report format?

Because it generates automatically by pytest-cov library.

### Why did you choose these minimum coverage thresholds?

We chose 30% as the minimum coverage threshold because it stated in the assignment.

### Which thresholds do you plan to achieve for the MVP and why?

We plan to achieve at least 60% coverage for the MVP.

### Which modules you selected for unit tests and why (e.g., complexity, change frequency, customer impact).

we selected the following modules for unit tests:
- `models`
- `database`
- `repositories`

Because these modules was implemented at this sprint and they are blocking other tasks.

