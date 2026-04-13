from abc import ABC, abstractmethod
from typing import Dict, Any, Tuple, Optional, List


class BaseLogParser(ABC):
    """
    Abstract base class for all log parsers.
    Defines the interface for parsing raw log entries.
    """

    @abstractmethod
    def parse(
        self, log_entry: str, source: Optional[str] = None
    ) -> Tuple[Dict[str, Any], str]:
        """
        Parses a raw log entry string into a dictionary of structured data.

        Args:
            log_entry: The raw log entry string to parse.
            source: An optional string indicating the source of the log (e.g., "syslog", "apache").
                    Can be used by parsers to apply source-specific logic.

        Returns:
            A tuple containing:
            - A dictionary representing the structured, parsed data.
            - The original raw log entry string (for consistency, may be identical to log_entry).
        """
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """
        Returns the unique name of the parser.
        """
        pass

    @property
    @abstractmethod
    def supported_types(self) -> List[str]:
        """
        Returns a list of log types this parser can handle (e.g., ["json", "syslog"]).
        """
        pass
