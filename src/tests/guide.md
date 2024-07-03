# Using Pytest

Run tests in a module

pytest test_mod.py
Run tests in a directory

pytest testing/
Run tests by keyword expressions

pytest -k "MyClass and not method"

**Dependency**: `pytest`

- Running a general test session
```Python
pytest
```

- Running a specific test module
```Python
pytest <MODULE_PATH>
```

**Example**:
```Python
pytest tests/foo.py
```

- Running a test and enabling printout of data
```Python
pytest -s <MODULE_PATH>
```