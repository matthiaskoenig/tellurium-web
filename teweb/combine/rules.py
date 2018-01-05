import rules


@rules.predicate
def is_archive_author(user, archive):
     return archive.author == user

@rules.predicate
def is_admin(user):
     return user.is_superuser


rules.add_rule('can_edit_archive', is_archive_author | is_admin)
rules.add_rule('can_delete_archive', is_archive_author | is_admin)
rules.add_rule('view_archive', is_archive_author | is_admin)

