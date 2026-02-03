from abc import ABC, abstractmethod
from typing import Any, Dict


class DataProvider(ABC):
    """Base class for data providers."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider name for identification."""
        pass

    @abstractmethod
    async def get_data(self) -> Dict[str, Any]:
        """
        Fetch data from this provider.

        Returns:
            Dictionary of data keyed by category
        """
        pass

    async def health_check(self) -> bool:
        """Check if the provider is healthy. Override if needed."""
        return True
