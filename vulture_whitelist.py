# Names vulture cannot see used. Never executed — vulture only parses this file.

SubConfig

# Config fields are populated by voecfg through setattr() and read back through
# getattr(), so every declaration in a test config class looks unused to vulture.
var_int_missing
env_required_int
something
subsub
sub
some_str_we_pretend_is_int
host
password
api_key
db
wrong_type
other

# autouse pytest fixture — pytest resolves it by name, nothing calls it directly.
_env_setup
