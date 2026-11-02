import importlib.util
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[2] / "scripts"

def load_script(name: str):
    spec = importlib.util.spec_from_file_location(f"script_{name}", SCRIPTS / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    return module

@pytest.fixture
def build_script():
    return load_script("build_claude")

@pytest.fixture
def cleanup_script():
    return load_script("cleanup")

@pytest.fixture
def sync_script():
    return load_script("sync_claude")
