from dataclasses import dataclass, field
from functools import cache
from html.parser import HTMLParser
from re import Pattern
from collections import deque


@dataclass
class HTMLElement:
    tag: str
    attrs: dict[str, str | None] = field(default_factory=dict)
    content_lines: list[str] = field(default_factory=list)

    def match(
        self,
        tag: str,
        attrs: dict[str, str | None] | None = None,
        contains: str | Pattern | None = None,
    ) -> bool:
        if self.tag != tag:
            return False
        if attrs and (self.attrs | attrs) != self.attrs:
            return False
        if isinstance(contains, str):
            return any(contains in line for line in self.content_lines)
        elif isinstance(contains, Pattern):
            return any(map(contains.search, self.content_lines))
        return True


class AssertParser(HTMLParser):

    def __init__(self, *, convert_charrefs: bool = True) -> None:
        super().__init__(convert_charrefs=convert_charrefs)
        self.seen: list[HTMLElement] = []
        self._stack: deque = deque()

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        element = HTMLElement(tag=tag, attrs=dict(attrs))
        self._stack.append(element)
        self.seen.append(element)

    def handle_endtag(self, tag: str) -> None:
        self._stack.pop()

    def handle_data(self, data: str) -> None:
        if line := data.strip("\n "):  # avoid stripping &nbsp;
            try:
                self._stack[-1].content_lines.append(line)
            except IndexError:
                pass


@cache
def _parse(html: bytes) -> list[HTMLElement]:
    psr = AssertParser()
    psr.feed(html.decode())
    psr.close()
    return psr.seen.copy()


def match_html_elements(
    html: bytes,
    tag: str,
    attrs: dict[str, str | None] | None = None,
    contains: str | Pattern | None = None,
    expected_matches: int | None = None,
) -> list[HTMLElement]:
    parsed_elements = _parse(html)
    matches = [
        i for i in parsed_elements if i.match(tag=tag, attrs=attrs, contains=contains)
    ]
    if expected_matches is not None:
        assert (
            len(matches) == expected_matches
        ), f"Got {len(matches)} matching elements, expected {expected_matches}"
    return matches
