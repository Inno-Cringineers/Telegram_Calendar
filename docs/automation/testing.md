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


## Quality attribute scenario tests
we have automated only one QAST as we have not yet implemented the functionality of the other QASts.
### QAST-001-1: Fast Response for Typical Command

**Requirements Reference**: [QAST001-1: Fast Response for Typical Command](../requirements/quality-requirements.md#qast001-1-fast-response-for-typical-command)

**Automation Approach**: 

The QAST was automated using **Telethon library** to simulate real user interactions with the Telegram bot. The test performs 10 consecutive `/start` command requests and measures response times for each attempt. (we didn't check 50 times as it says in requirements.md because if you send a lot of messages, tg bans your account for a while.)

**Key implementation components**:
- **Performance testing**: [`app/tests/test_QAST/test.py`](../../app/tests/test_QAST/test.py) - `test_bot_fast_response_10_times()` function
- **Response time measurement**: Measures time between sending command and receiving bot response
- **Statistical validation**: Validates that 9 out of 10 responses meet the 5-second requirement
- **Error handling**: Continues testing even if individual requests fail
- **Detailed reporting**: Provides per-attempt timing statistics and performance metrics

to run the test, write the command `pytest tests/test_QAST/test.py -v -s`