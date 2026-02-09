
```
  
.PHONY: test-one  
test-one: install-dev-env  
ifeq ($(test),)  
    @echo "Error: 'test' parameter is required"  
    @echo "Usage: make test-one test=path/to/test_file.py"  
    @echo "Or: make test-one test=path/to/test_file.py::TestClass::test_method"  
    @echo "Or: make test-one test=path/to/test_file.py::test_function"  
    @echo "Or: make test-one test=TestClass (searches by class name)"  
    @echo "Or: make test-one test=test_function_name (searches by test name)"  
    @exit 1  
endif  
    @$(if $(filter yes, $(dev_env)),${compose_command_project} exec dev_container,) \  
    bash -c 'if echo "$(test)" | grep -qE "(^/|\.py|::)"; then \  
       poetry run pytest -vv -s --log-cli-level=INFO $(test); \  
    else \  
       TEST_FILE=$$(grep -rl "class $(test)" monocle_integrations/_api/_test monocle_integrations/_data_streams/_test monocle_integrations/_event_handlers/_test $$(find monocle_integrations -type f -name "*_unit_test.py" | xargs dirname | sort -u) 2>/dev/null | head -1); \  
       if [ -n "$$TEST_FILE" ]; then \  
          poetry run pytest -vv -s --log-cli-level=INFO -k "$(test)" $$TEST_FILE; \  
       else \  
          echo "Could not find test class/function \"$(test)\". Searching in test directories..."; \  
          poetry run pytest -vv -s --log-cli-level=INFO -k "$(test)" \  
          monocle_integrations/_api/_test \  
          monocle_integrations/_data_streams/_test \  
          monocle_integrations/_event_handlers/_test; \  
       fi; \  
    fi'
```