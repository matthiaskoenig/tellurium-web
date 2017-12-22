"""
Definition of users.
Used for filling database and in tests.
"""

from ..utils.data import UserDef

user_defs = [
    UserDef("janekg89", "Jan", "Grzegorzewski", "janekg89@hotmail.de", True),
    UserDef("mkoenig", "Matthias", "König", "konigmatt@googlemail.com", True),
    UserDef("testuser", False, False, False, False),
    UserDef("global", False, False, False, False)]