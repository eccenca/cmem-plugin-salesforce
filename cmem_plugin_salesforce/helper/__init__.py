"""Helper classes."""


class MarkdownLink:
    """Helper class to manage documentation links."""

    url: str
    label: str

    def __init__(self, url: str, label: str):
        """Initialize the class."""
        self.url = url
        self.label = label

    def __str__(self) -> str:
        """Return markdown link."""
        return f"[{self.label}]({self.url})"
