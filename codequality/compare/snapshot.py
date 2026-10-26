import shutil
import subprocess
import tempfile
import warnings
from contextlib import contextmanager
from pathlib import Path

class Compare_Error(Exception):
    """The earlier version could not be checked out: not a git repository, a ref that does not exist, or a folder that was not there yet."""

def git(root: Path, *arguments: str) -> str:
    """The output of a git command run inside root. Raises Compare_Error with git's own message when it fails."""

    try:
        done = subprocess.run(["git", "-C", str(root), *arguments], capture_output=True, text=True, check=True)
    except OSError as error:
        raise Compare_Error(f"git could not be run: {error}") from error
    except subprocess.CalledProcessError as error:
        raise Compare_Error(error.stderr.strip() or f"git {arguments[0]} failed") from error

    return done.stdout.strip()

def short_ref(root: Path, ref: str) -> str:
    """The short commit hash a ref points to, like a5509c6."""

    return git(root, "rev-parse", "--short", "--verify", f"{ref}^{{commit}}")

@contextmanager
def project_at_ref(root: Path, ref: str):
    """Yields the folder holding the project as it was at `ref`, then deletes it. It is a throwaway git worktree, so the real files are never touched."""
    prefix = git(root, "rev-parse", "--show-prefix")  # where root sits inside the repository, empty when root is the top
    short_ref(root, ref)  # fails early, with git's message, for a ref that does not exist
    checkout = Path(tempfile.mkdtemp(prefix="codequality-compare-"))

    try:
        git(root, "worktree", "add", "--detach", str(checkout), ref)
        old_root = checkout / prefix

        if not old_root.is_dir():
            raise Compare_Error(f"{prefix or 'the project folder'} did not exist at {ref}")

        yield old_root
    finally:
        removal = subprocess.run(["git", "-C", str(root), "worktree", "remove", "--force", str(checkout)], capture_output=True, text=True, check=False)

        if removal.returncode:
            warnings.warn(f"git could not remove the temporary checkout {checkout}: {removal.stderr.strip()}")

        if checkout.exists():
            shutil.rmtree(checkout)  # git left it behind, and a stray full copy of the project should not be kept
