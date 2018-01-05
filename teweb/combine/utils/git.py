"""
Git helpers.
"""

import subprocess


def get_commit():
    """ Get the current commit of the repository.

    Only works in the context of a git repository.
    Careful it returns the value of the current folder.

    :return: commit hash or None
    """
    try:
        commit = subprocess.check_output(["git", "describe", "--always"])
        commit = commit.strip()
        return commit.decode("utf8")
    except Exception:
        return None

