coverage:
		coverage run --source=../voecfg ./test_voecfg.py
		coverage run --source=../voecfg -a ./test_no_toml.py
		coverage html
		coverage report --fail-under=100
		
all: coverage