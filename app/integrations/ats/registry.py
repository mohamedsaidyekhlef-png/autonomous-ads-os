from app.integrations.ats.base import ATSAdapter, ATSAdapterError
from app.integrations.ats.greenhouse import GreenhouseAdapter
from app.integrations.ats.lever import LeverAdapter

_ADAPTERS: dict[str, ATSAdapter] = {
    "greenhouse": GreenhouseAdapter(),
    "lever": LeverAdapter(),
}


def get_ats_adapter(provider: str) -> ATSAdapter:
    normalized = provider.strip().lower()
    adapter = _ADAPTERS.get(normalized)

    if adapter is None:
        raise ATSAdapterError(
            f"No ingestion adapter is available for {normalized}.",
            code="unsupported_provider",
        )

    return adapter
