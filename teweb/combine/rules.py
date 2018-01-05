#import rules


#@rules.predicate
#def is_archive_author(user, obj):
#     return obj.author == user

#@rules.predicate
#def is_admin(user, obj):
#     return user.is_superuser

#@rules.predicate
#def is_global(user, obj):
#     return obj.user.username == "global"

#rules.add_perm('can_edit_archive', is_archive_author | is_admin)
#rules.add_perm('can_delete_archive', is_archive_author | is_admin)
#rules.add_perm('view_archive', is_archive_author | is_admin | is_global)
#rules.add_perm('view_archive', is_global)

