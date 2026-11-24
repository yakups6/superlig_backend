from django.db import migrations


def reset_cached_rivalry_details(apps, schema_editor):
    RivalryMatch = apps.get_model("api", "RivalryMatch")
    RivalryMatch.objects.filter(details_fetched=True).update(
        details_fetched=False,
        events_json=[],
        cards_json=[],
    )


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0008_rivalrymatch_cards_json_rivalrymatch_details_fetched_and_more"),
    ]

    operations = [
        migrations.RunPython(reset_cached_rivalry_details, migrations.RunPython.noop),
    ]
