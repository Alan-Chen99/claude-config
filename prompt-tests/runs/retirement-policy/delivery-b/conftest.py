"""Present so `pytest -q` from the repo root can import the modules under test.

pytest prepends the directory holding the topmost conftest.py to sys.path; the
modules here sit at the repo root rather than in a package.
"""
