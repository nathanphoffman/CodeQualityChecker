# Words in a name that suggest it holds something private.
SECRET_WORDS = ("password", "passwd", "secret", "token", "api_key", "apikey", "private_key", "credential")

# Words in a name that suggest it holds something a user typed or sent.
INPUT_WORDS = ("request", "req", "user", "input", "param", "query", "form", "body", "argv")

# A string shorter than this is not treated as a real secret.
MIN_SECRET_LENGTH = 8

# Values containing these are examples, not real secrets.
PLACEHOLDER_HINTS = ("example", "changeme", "change_me", "your", "xxxx", "placeholder", "dummy", "fake", "test",
                     "sample", "<", "${", "{{", "env")

# Config files can hold secrets too, not just code.
CONFIG_SUFFIXES = (".json", ".yaml", ".yml", ".toml")

# File names that usually hold secrets. Examples and templates of them are fine.
SECRET_FILE_PATTERNS = (".env", ".env.*", "*.pem", "*.key", "*.pfx", "*.p12", "id_rsa", "id_ed25519", "credentials.json")
SAFE_FILE_ENDINGS = (".example", ".sample", ".template", ".dist")
