from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("budget", "0001_initial"),
    ]

    operations = [
        migrations.RunSQL(
            sql=[
                "CREATE EXTENSION IF NOT EXISTS ltree;",
                "ALTER TABLE budget_projecttag ALTER COLUMN tag TYPE ltree USING tag::ltree;",
                "CREATE INDEX budget_projecttag_tag_gist ON budget_projecttag USING GIST (tag);",
            ],
            reverse_sql=[
                "DROP INDEX IF EXISTS budget_projecttag_tag_gist;",
                "ALTER TABLE budget_projecttag ALTER COLUMN tag TYPE varchar(256) USING tag::varchar;",
            ],
        )
    ]
