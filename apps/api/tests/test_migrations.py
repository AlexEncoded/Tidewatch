from pathlib import Path

from alembic.config import Config
from alembic.script import ScriptDirectory


def test_alembic_revision_identifiers_fit_version_column() -> None:
    api_root = Path(__file__).parents[1]
    config = Config(str(api_root / "alembic.ini"))
    config.set_main_option("script_location", str(api_root / "alembic"))
    script = ScriptDirectory.from_config(config)

    revisions = list(script.walk_revisions())
    identifiers = [revision.revision for revision in revisions]
    identifiers.extend(
        revision.down_revision
        for revision in revisions
        if isinstance(revision.down_revision, str)
    )

    assert identifiers
    assert all(len(identifier) <= 32 for identifier in identifiers)
