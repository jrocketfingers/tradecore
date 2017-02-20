General
=======
    Initial idea was to use MongoDB, as posts are quite nicely suited to be documents. Unfortunately, django-nonrel
    metapackage appears to be dated. Can't recall the issues with django-mongoengine, but there were some as well.
    Will need to revisit this.

Posts
=====
    Posting is limited to the active user. Additional lookups are required if
    concepts like pages are to be introduced. (permission, page-author-id, etc.)

Likes
=====
    
