from app.database.base import Base
from app.database.models import operations  # noqa: F401


def test_operational_tables_are_registered() -> None:
    required = {
        "agent_runs",
        "agent_decisions",
        "campaign_records",
        "experiment_records",
        "creative_asset_records",
        "report_records",
    }

    assert required.issubset(Base.metadata.tables)
