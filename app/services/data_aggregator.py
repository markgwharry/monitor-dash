from typing import Any, Dict, List

from app.services.providers.base import DataProvider


class DataAggregator:
    """Aggregates data from multiple providers."""

    def __init__(self, providers: List[DataProvider] = None):
        self.providers = providers or []

    def add_provider(self, provider: DataProvider) -> None:
        """Add a data provider."""
        self.providers.append(provider)

    async def get_dashboard_data(self) -> Dict[str, Any]:
        """
        Fetch and merge data from all providers.

        Later providers override earlier ones for the same keys.
        """
        merged = {}

        for provider in self.providers:
            try:
                data = await provider.get_data()
                # Deep merge would be better, but shallow is fine for Phase 1
                for key, value in data.items():
                    if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
                        merged[key].update(value)
                    else:
                        merged[key] = value
            except Exception as e:
                print(f"Error fetching from {provider.name}: {e}")

        return merged
