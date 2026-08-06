from dataclasses import dataclass, field
from html.parser import HTMLParser


@dataclass
class HTMLElement:
    tag: str
    attrs: dict[str, str | None] = field(default_factory=dict)
    content: str | None = None


class AssertParser(HTMLParser):

    def __init__(self, *, convert_charrefs: bool = True) -> None:
        super().__init__(convert_charrefs=convert_charrefs)
        self.seen: list[HTMLElement] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.seen.append(HTMLElement(tag=tag, attrs=dict(attrs)))

    def handle_data(self, data: str) -> None:
        try:
            self.seen[-1].content = data
        except IndexError:
            pass

    def find(self, target: HTMLElement) -> HTMLElement:
        for i in self.seen:
            if i.tag == target.tag and (target.attrs | i.attrs) == i.attrs:
                return i
        raise LookupError(f"Did not find {target}")


def assert_html(html: bytes, *elements: HTMLElement):
    psr = AssertParser()
    psr.feed(html.decode())
    psr.close()
    for elt in elements:
        assert psr.find(elt)
