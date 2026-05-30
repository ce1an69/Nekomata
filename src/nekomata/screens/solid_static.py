"""Static text that paints its whole content line."""

from rich.cells import cell_len
from rich.text import Text
from textual.widgets import Static


class SolidStatic(Static):
    """Static text whose padding uses the widget's current CSS style."""

    def __init__(
        self,
        content: str = "",
        *,
        align: str = "left",
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
        disabled: bool = False,
    ) -> None:
        super().__init__("", name=name, id=id, classes=classes, disabled=disabled)
        self._content = content
        self._align = align

    def update(self, content: str = "", *, layout: bool = True) -> None:
        self._content = content
        self.refresh(layout=layout)

    def render(self) -> Text:
        return Text(self._padded_content(), style=self.rich_style)

    def _padded_content(self) -> str:
        width = self.content_size.width
        content_width = cell_len(self._content)
        if width <= content_width:
            return self._content

        remaining = width - content_width
        if self._align == "center":
            left = remaining // 2
            right = remaining - left
            return f"{' ' * left}{self._content}{' ' * right}"
        if self._align == "right":
            return f"{' ' * remaining}{self._content}"
        return f"{self._content}{' ' * remaining}"
