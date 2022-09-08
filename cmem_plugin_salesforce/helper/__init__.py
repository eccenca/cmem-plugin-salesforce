""" Helper classes."""


class MarkdownLink:
    """Helper class to manage documentation links."""

    url: str
    label: str

    def __init__(self, url: str, label: str) -> None:
        self.url = url
        self.label = label

    def __str__(self):
        return f"[{self.label}]({self.url})"
