coverage:
		coverage run --source=../basecfg ./test_basecfg.py
		coverage run --source=../basecfg -a ./test_no_toml.py
		coverage html
		coverage report --fail-under=100
		
all: coverage