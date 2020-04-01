# `common` Role

The `common` role contains common tasks and variables required by other roles is automatically included by other roles.  

For now, all that `common` does is force fact gathering even if fact gathering is disabled as the roles in this collection require fact gathering to operate correctly.

It is likely that in the future some variables and tasks will migrate here if they are found to be needed across multiple roles.