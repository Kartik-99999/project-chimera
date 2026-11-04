"""Shared scripted fakes for the read-only lookup workflows (no browser).

One small stateful fake per lookup target (Wikipedia, Wiktionary,
PyPI, BBC, GitHub, crates.io, BBC Weather, GitHub search, Steam,
arXiv, Stack Overflow, Amazon) with failure injection. Used by
driver tests and workbench executor tests.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from adapters import wikipedia as wiki
from adapters import wiktionary as wikt
from adapters import pypi as pypi
from adapters import bbc as bbc
from adapters import github as github
from adapters import crates as crates
from adapters import weather as weather
from adapters import github_search as gsearch
from adapters import steam as steam
from adapters import arxiv as arxiv
from adapters import stackoverflow as so
from adapters import amazon as amazon


class _StubLocator:
    def __init__(self, page: "_StubPage", selector: str) -> None:
        self._page = page
        self._selector = selector

    @property
    def first(self) -> "_StubLocator":
        return self

    def count(self) -> int:
        return len(self._page._texts(self._selector))

    def text_content(self, **kwargs: Any) -> Optional[str]:
        texts = self._page._texts(self._selector)
        return texts[0] if texts else None

    def all_text_contents(self) -> List[str]:
        # No kwargs: real Playwright's all_text_contents() takes none,
        # and the other fakes match it. Keep it strict so adapters
        # that pass a timeout fail here instead of live.
        return list(self._page._texts(self._selector))

    def is_visible(self, **kwargs: Any) -> bool:
        return self._page._visible(self._selector)

    def fill(self, value: str, **kwargs: Any) -> None:
        self._page._fill(self._selector, value)

    def nth(self, index: int) -> "_StubIndexedLocator":
        return _StubIndexedLocator(self._page, self._selector, index)

    def get_attribute(self, name: str, **kwargs: Any) -> Optional[str]:
        return self._page._attribute(self._selector, 0, name)

    def wait_for(self, state: Optional[str] = None, **kwargs: Any) -> None:
        if state == "visible" and not self._page._visible(self._selector):
            raise TimeoutError(f"{self._selector} never became visible")


class _StubIndexedLocator:
    def __init__(self, page: "_StubPage", selector: str,
                 index: int) -> None:
        self._page = page
        self._selector = selector
        self._index = index

    def get_attribute(self, name: str, **kwargs: Any) -> Optional[str]:
        return self._page._attribute(self._selector, self._index, name)

    def text_content(self, **kwargs: Any) -> Optional[str]:
        texts = self._page._texts(self._selector)
        return texts[self._index] if 0 <= self._index < len(texts) else None


class _StubPage:
    def locator(self, selector: str, **kwargs: Any) -> _StubLocator:
        return _StubLocator(self, selector)

    def screenshot(self, path: Optional[str] = None, **kwargs: Any) -> bytes:
        from pathlib import Path as _Path

        if path:
            _Path(path).write_bytes(b"fake-png")
        return b"fake-png"


class _StubContext:
    def close(self) -> None:
        pass


class _StubBrowser:
    def close(self) -> None:
        pass


WIKI_RESULTS = [
    {"title": "Badminton", "href": "/wiki/Badminton"},
    {"title": "Badminton at the Summer Olympics",
     "href": "/wiki/Badminton_at_the_Summer_Olympics"},
    {"title": "Badminton World Federation",
     "href": "/wiki/Badminton_World_Federation"},
]

WIKI_SUMMARY = ("Badminton is a racquet sport played using racquets to hit "
                "a shuttlecock across a net with plenty more words here.")


class FakeWikiPage(_StubPage):
    """Scripted Wikipedia: home, search, redirect, article."""

    def __init__(self, *, redirect: bool = False, no_results: bool = False,
                 empty_article: bool = False) -> None:
        self.url = ""
        self.redirect = redirect
        self.no_results = no_results
        self.empty_article = empty_article
        self.filled: Dict[str, str] = {}

    def _on_article(self) -> bool:
        path = self.url.replace(wiki.APPROVED_ORIGIN, "").split("?", 1)[0]
        return bool(wiki.ARTICLE_PATH_RE.match(path or "/"))

    def _texts(self, selector: str) -> List[str]:
        if selector == wiki.SEL_SEARCH_INPUT:
            return [""] if not self._on_article() else []
        if selector == wiki.SEL_RESULT_LINK:
            if self._on_article() or self.no_results:
                return []
            return [r["title"] for r in WIKI_RESULTS]
        if selector == wiki.SEL_ARTICLE_H1:
            if not self._on_article() or self.empty_article:
                return []
            slug = self.url.split("/wiki/", 1)[-1].split("?", 1)[0]
            for r in WIKI_RESULTS:
                if r["href"].split("?")[0].endswith(slug):
                    return [r["title"]]
            return [slug.replace("_", " ")]
        if selector == wiki.SEL_CONTENT_PARA:
            if not self._on_article() or self.empty_article:
                return []
            return ["", WIKI_SUMMARY, "A second paragraph follows here."]
        return []

    def _visible(self, selector: str) -> bool:
        return bool(self._texts(selector))

    def _fill(self, selector: str, value: str) -> None:
        self.filled[selector] = value

    def _attribute(self, selector: str, index: int,
                   name: str) -> Optional[str]:
        if (selector == wiki.SEL_RESULT_LINK and name == "href"
                and not self._on_article() and not self.no_results
                and 0 <= index < len(WIKI_RESULTS)):
            return WIKI_RESULTS[index]["href"]
        return None

    def goto(self, url: str, **kwargs: Any) -> None:
        self.url = url
        if self.redirect and url.startswith(wiki.APPROVED_ORIGIN
                                            + wiki.SEARCH_PREFIX):
            self.url = wiki.APPROVED_ORIGIN + "/wiki/Badminton"

    def title(self) -> str:
        return "Fake Wikipedia"


WIKT_DEFINITIONS = [
    "A racquet sport played with a shuttlecock across a net.",
    "A light projectile with feathers, used in the game above.",
]


class FakeWiktPage(_StubPage):
    """Scripted Wiktionary: entry page or missing-entry marker."""

    def __init__(self, *, missing: bool = False,
                 empty_defs: bool = False) -> None:
        self.url = ""
        self.missing = missing
        self.empty_defs = empty_defs

    def _slug(self) -> str:
        tail = self.url.split("/wiki/", 1)[-1].split("?", 1)[0]
        return tail.replace("_", " ")

    def _texts(self, selector: str) -> List[str]:
        if selector == wikt.SEL_ENTRY_H1:
            return [self._slug()] if self.url else []
        if selector == wikt.SEL_NO_ENTRY:
            return ["Wiktionary does not have an entry."] if self.missing else []
        if selector == wikt.SEL_DEFINITION:
            if self.missing or self.empty_defs:
                return []
            return list(WIKT_DEFINITIONS)
        return []

    def _visible(self, selector: str) -> bool:
        return bool(self._texts(selector))

    def _fill(self, selector: str, value: str) -> None:
        raise AssertionError("wiktionary fake is read-only")

    def _attribute(self, selector: str, index: int,
                   name: str) -> Optional[str]:
        return None

    def goto(self, url: str, **kwargs: Any) -> None:
        self.url = url

    def title(self) -> str:
        return "Fake Wiktionary"


PYPI_SUMMARY = ("Python library for reliable browser automation with a "
                "single expressive API.")


class FakePypiPage(_StubPage):
    """Scripted PyPI: project header or missing-challenge page."""

    def __init__(self, *, challenge: bool = False,
                 empty_summary: bool = False) -> None:
        self.url = ""
        self.challenge = challenge
        self.empty_summary = empty_summary

    def _slug(self) -> str:
        tail = self.url.split("/project/", 1)[-1].split("?", 1)[0]
        return tail.strip("/")

    def _texts(self, selector: str) -> List[str]:
        if selector == pypi.SEL_PROJECT_H1:
            if not self.url or self.challenge:
                return []
            return [f"{self._slug()} 1.64.1"]
        return []

    def _visible(self, selector: str) -> bool:
        return bool(self._texts(selector))

    def _fill(self, selector: str, value: str) -> None:
        raise AssertionError("pypi fake is read-only")

    def _attribute(self, selector: str, index: int,
                   name: str) -> Optional[str]:
        if (selector == pypi.SEL_META_DESCRIPTION and name == "content"
                and index == 0 and self.url and not self.challenge
                and not self.empty_summary):
            return PYPI_SUMMARY
        return None

    def goto(self, url: str, **kwargs: Any) -> None:
        self.url = url

    def title(self) -> str:
        return "Fake PyPI"


BBC_HEADLINES = [
    "Fake parliament passes landmark testing bill",
    "Fake observatory spots scripted comet over Bern",
    "Fake bakery wins third consecutive pastry prize",
]


class FakeBbcPage(_StubPage):
    """Scripted BBC: section front with headlines, or an empty front."""

    def __init__(self, *, empty: bool = False) -> None:
        self.url = ""
        self.empty = empty

    def _section(self) -> str:
        tail = self.url.split("bbc.com/", 1)[-1].split("?", 1)[0]
        return tail.strip("/").split("/")[0]

    def _texts(self, selector: str) -> List[str]:
        if selector == bbc.SEL_H1:
            label = bbc.SECTION_LABELS.get(self._section(), "")
            return [label] if label else []
        if selector == bbc.SEL_HEADLINE:
            if self.empty or not self.url:
                return []
            return list(BBC_HEADLINES)
        return []

    def _visible(self, selector: str) -> bool:
        return bool(self._texts(selector))

    def _fill(self, selector: str, value: str) -> None:
        raise AssertionError("bbc fake is read-only")

    def _attribute(self, selector: str, index: int,
                   name: str) -> Optional[str]:
        return None

    def goto(self, url: str, **kwargs: Any) -> None:
        self.url = url

    def title(self) -> str:
        return "Fake BBC"


class FakeGithubPage(_StubPage):
    """Scripted GitHub: public profile or a handle-less 404."""

    def __init__(self, *, missing: bool = False,
                 empty_name: bool = False) -> None:
        self.url = ""
        self.missing = missing
        self.empty_name = empty_name

    def _slug(self) -> str:
        tail = self.url.split("github.com/", 1)[-1].split("?", 1)[0]
        return tail.strip("/").split("/")[0]

    def _texts(self, selector: str) -> List[str]:
        if selector == github.SEL_NICKNAME:
            if not self.url or self.missing:
                return []
            return [self._slug()]
        if selector == github.SEL_NAME:
            if not self.url or self.missing or self.empty_name:
                return []
            return [f"{self._slug()} Example"]
        return []

    def _visible(self, selector: str) -> bool:
        return bool(self._texts(selector))

    def _fill(self, selector: str, value: str) -> None:
        raise AssertionError("github fake is read-only")

    def _attribute(self, selector: str, index: int,
                   name: str) -> Optional[str]:
        return None

    def goto(self, url: str, **kwargs: Any) -> None:
        self.url = url

    def title(self) -> str:
        return "Fake GitHub"


CRATES_SUMMARY = ("A generic serialization/deserialization framework for "
                  "Rust data structures.")


class FakeCratesPage(_StubPage):
    """Scripted crates.io: crate header or a not-found page."""

    def __init__(self, *, missing: bool = False,
                 empty_summary: bool = False) -> None:
        self.url = ""
        self.missing = missing
        self.empty_summary = empty_summary

    def _slug(self) -> str:
        tail = self.url.split("/crates/", 1)[-1].split("?", 1)[0]
        return tail.strip("/").split("/")[0]

    def _texts(self, selector: str) -> List[str]:
        if selector == crates.SEL_H1:
            if not self.url:
                return []
            if self.missing:
                return [f'Crate "{self._slug()}" not found']
            return [f"{self._slug()} v1.2.3"]
        return []

    def _visible(self, selector: str) -> bool:
        return bool(self._texts(selector))

    def _fill(self, selector: str, value: str) -> None:
        raise AssertionError("crates fake is read-only")

    def _attribute(self, selector: str, index: int,
                   name: str) -> Optional[str]:
        if (selector == crates.SEL_META_DESCRIPTION and name == "content"
                and index == 0 and self.url and not self.missing
                and not self.empty_summary):
            return CRATES_SUMMARY
        return None

    def goto(self, url: str, **kwargs: Any) -> None:
        self.url = url

    def title(self) -> str:
        return "Fake crates.io"


WEATHER_TEMPS = ["12°", "11°", "9°", "8°"]


class FakeWeatherPage(_StubPage):
    """Scripted BBC Weather: city heading with temps, or no temps."""

    def __init__(self, *, empty: bool = False) -> None:
        self.url = ""
        self.empty = empty

    def _label(self) -> str:
        tail = self.url.split("/weather/", 1)[-1].split("?", 1)[0]
        locid = tail.strip("/").split("/")[0]
        for _key, (cid, label) in weather.CITIES.items():
            if cid == locid:
                return label
        return ""

    def _texts(self, selector: str) -> List[str]:
        if selector == weather.SEL_H1:
            label = self._label()
            return [f"{label} - Fake forecast"] if label else []
        if selector == weather.SEL_TEMP:
            if self.empty or not self._label():
                return []
            return list(WEATHER_TEMPS)
        return []

    def _visible(self, selector: str) -> bool:
        return bool(self._texts(selector))

    def _fill(self, selector: str, value: str) -> None:
        raise AssertionError("weather fake is read-only")

    def _attribute(self, selector: str, index: int,
                   name: str) -> Optional[str]:
        return None

    def goto(self, url: str, **kwargs: Any) -> None:
        self.url = url

    def title(self) -> str:
        return "Fake BBC Weather"


GSEARCH_TITLES = [
    "microsoft / playwright",
    "playwright-community / playwright",
    "fake-org / playwright-demo",
]


class FakeGsearchPage(_StubPage):
    """Scripted GitHub search: served list with titles, or no matches."""

    def __init__(self, *, empty: bool = False) -> None:
        self.url = ""
        self.empty = empty

    def _texts(self, selector: str) -> List[str]:
        if selector == gsearch.SEL_LIST:
            return ["results"] if self.url else []
        if selector == gsearch.SEL_RESULT:
            if not self.url or self.empty:
                return []
            return list(GSEARCH_TITLES)
        return []

    def _visible(self, selector: str) -> bool:
        return bool(self._texts(selector))

    def _fill(self, selector: str, value: str) -> None:
        raise AssertionError("github-search fake is read-only")

    def _attribute(self, selector: str, index: int,
                   name: str) -> Optional[str]:
        return None

    def goto(self, url: str, **kwargs: Any) -> None:
        self.url = url

    def title(self) -> str:
        return "Fake GitHub search"


STEAM_RESULTS = [
    {"name": "Portal", "href": "/app/400/Portal/"},
    {"name": "Portal 2", "href": "/app/620/Portal_2/"},
    {"name": "Portal Stories: Mel", "href": "/app/317400/Portal_Stories_Mel/"},
]

STEAM_PRICE = "$19.99"


class FakeSteamPage(_StubPage):
    """Scripted Steam: search rows, then one game page with a price."""

    def __init__(self, *, no_results: bool = False,
                 empty_game: bool = False) -> None:
        self.url = ""
        self.no_results = no_results
        self.empty_game = empty_game

    def _on_game(self) -> bool:
        return "/app/" in (self.url or "")

    def _game_name(self) -> str:
        tail = (self.url or "").split("/app/", 1)[-1].strip("/")
        bits = tail.split("/", 1)
        slug = bits[1] if len(bits) == 2 else bits[0]
        return slug.replace("_", " ")

    def _texts(self, selector: str) -> List[str]:
        if selector == steam.SEL_SEARCH_ROW:
            if self._on_game() or self.no_results or not self.url:
                return []
            return [r["name"] for r in STEAM_RESULTS]
        if selector == steam.SEL_RESULT_NAME:
            if self._on_game() or self.no_results or not self.url:
                return []
            return [r["name"] for r in STEAM_RESULTS]
        if selector == steam.SEL_GAME_NAME:
            if not self._on_game() or self.empty_game:
                return []
            return [self._game_name()]
        if selector == steam.SEL_PRICE:
            if not self._on_game() or self.empty_game:
                return []
            return [STEAM_PRICE]
        return []

    def _visible(self, selector: str) -> bool:
        return bool(self._texts(selector))

    def _fill(self, selector: str, value: str) -> None:
        raise AssertionError("steam fake is read-only")

    def _attribute(self, selector: str, index: int,
                   name: str) -> Optional[str]:
        if (selector == steam.SEL_SEARCH_ROW and name == "href"
                and not self._on_game() and not self.no_results
                and 0 <= index < len(STEAM_RESULTS)):
            return STEAM_RESULTS[index]["href"]
        return None

    def goto(self, url: str, **kwargs: Any) -> None:
        self.url = url

    def title(self) -> str:
        return "Fake Steam"


ARXIV_TITLES = [
    "Attention Is All You Need",
    "Fake Transformers for Scripted Benchmarks",
    "A Fake Survey of Nonexistent Architectures",
]


class FakeArxivPage(_StubPage):
    """Scripted arXiv: served search with titles, or no matches."""

    def __init__(self, *, empty: bool = False) -> None:
        self.url = ""
        self.empty = empty

    def _texts(self, selector: str) -> List[str]:
        if selector == arxiv.SEL_SUMMARY:
            if not self.url:
                return []
            if self.empty:
                return ["Search"]
            return ["Showing 1–50 of 183,731 results for all: transformer"]
        if selector == arxiv.SEL_ROW:
            if not self.url or self.empty:
                return []
            return list(ARXIV_TITLES)
        if selector == arxiv.SEL_TITLE:
            if not self.url or self.empty:
                return []
            return list(ARXIV_TITLES)
        return []

    def _visible(self, selector: str) -> bool:
        return bool(self._texts(selector))

    def _fill(self, selector: str, value: str) -> None:
        raise AssertionError("arxiv fake is read-only")

    def _attribute(self, selector: str, index: int,
                   name: str) -> Optional[str]:
        return None

    def goto(self, url: str, **kwargs: Any) -> None:
        self.url = url

    def title(self) -> str:
        return "Fake arXiv"


SO_TITLES = [
    "How to click with Playwright Python?",
    "Fake timeout waiting for a selector",
    "Fake locator strict-mode violation",
]


class FakeSoPage(_StubPage):
    """Scripted Stack Overflow: results, or a challenge gate page."""

    def __init__(self, *, gate: bool = False,
                 empty: bool = False) -> None:
        self.url = ""
        self.gate = gate
        self.empty = empty

    def _texts(self, selector: str) -> List[str]:
        if selector == 'input[name="cf-turnstile-response"]':
            return ["challenge"] if self.gate and self.url else []
        if selector in (so.SEL_ROW, so.SEL_TITLE):
            if not self.url or self.gate or self.empty:
                return []
            return list(SO_TITLES)
        return []

    def _visible(self, selector: str) -> bool:
        return bool(self._texts(selector))

    def _fill(self, selector: str, value: str) -> None:
        raise AssertionError("stackoverflow fake is read-only")

    def _attribute(self, selector: str, index: int,
                   name: str) -> Optional[str]:
        return None

    def goto(self, url: str, **kwargs: Any) -> None:
        self.url = url

    def title(self) -> str:
        if self.gate and self.url:
            return "Just a moment..."
        return "Fake Stack Overflow"


AMAZON_RESULTS = [
    {"brand": "FakeBrand", "title": "Fake Kindle E-reader WiFi 16GB",
     "href": "/dp/B012345678/"},
    {"brand": "FakeBrand", "title": "Fake Echo Dot 5th Gen",
     "href": "/dp/B076545678/"},
    {"brand": "OtherBrand", "title": "Fake Fire Tablet HD 10",
     "href": "https://www.amazon.com/gp/slredirect/picassoRedirect.html"},
]


def _amazon_joined(result):
    return f"{result['brand']} {result['title']}"

AMAZON_PRICE = "$129.99"


class FakeAmazonPage(_StubPage):
    """Scripted Amazon: search rows, one product page, or a bot gate."""

    def __init__(self, *, gate: bool = False, dog: bool = False,
                 no_results: bool = False,
                 empty_product: bool = False) -> None:
        self.url = ""
        self.gate = gate
        self.dog = dog
        self.no_results = no_results
        self.empty_product = empty_product

    def _search_visible(self) -> bool:
        return bool(self.url) and not self.gate and not self.dog \
            and not self.no_results

    def _on_product(self) -> bool:
        return "/dp/" in (self.url or "") or "/gp/" in (self.url or "")

    def _product_name(self) -> str:
        for r in AMAZON_RESULTS:
            marker = r["href"].split("?")[0]
            if marker in (self.url or ""):
                return _amazon_joined(r)
        return ""

    def _row_index(self, selector: str) -> Optional[int]:
        """Parse a per-row chained selector, else None.

        Live Amazon rows carry brand + title as separate ``h2 span``
        texts with the product anchors outside the ``h2`` (no
        ``h2 a`` exists page-wide), so the adapter reads each row
        through ``SEL_ROW >> nth=i >> <sub>`` chains.
        """
        prefix = f"{amazon.SEL_ROW} >> nth="
        if not selector.startswith(prefix):
            return None
        try:
            return int(selector[len(prefix):].split(" >> ", 1)[0])
        except (ValueError, IndexError):
            return None

    def _texts(self, selector: str) -> List[str]:
        if selector == "body":
            if self.gate and self.url:
                return [f"junk {amazon.GATE_TEXT_MARKER} junk"]
            if self.dog and self.url:
                return ["junk getElementById(\"d\") "
                        f"{amazon.DOG_BODY_MARKER} junk"]
            return []
        if selector == amazon.SEL_ROW:
            if self._on_product() or not self._search_visible():
                return []
            return [f"row{i}" for i in range(len(AMAZON_RESULTS))]
        row_index = self._row_index(selector)
        if row_index is not None:
            if (self._on_product() or not self._search_visible()
                    or not 0 <= row_index < len(AMAZON_RESULTS)):
                return []
            if selector.endswith(f">> {amazon.SEL_ROW_TITLE}"):
                row = AMAZON_RESULTS[row_index]
                return [row["brand"], row["title"]]
            return []
        if selector == amazon.SEL_TITLE:
            if not self._on_product() or self.empty_product:
                return []
            return [self._product_name()]
        for candidate in amazon.SEL_PRICE_CANDIDATES:
            if selector == candidate:
                if not self._on_product() or self.empty_product:
                    return []
                return [AMAZON_PRICE]
        return []

    def _visible(self, selector: str) -> bool:
        return bool(self._texts(selector))

    def _fill(self, selector: str, value: str) -> None:
        raise AssertionError("amazon fake is read-only")

    def _attribute(self, selector: str, index: int,
                   name: str) -> Optional[str]:
        row_index = self._row_index(selector)
        if (row_index is not None and name == "href"
                and selector.endswith(f">> {amazon.SEL_ROW_HREF}")
                and not self._on_product() and self._search_visible()
                and 0 <= row_index < len(AMAZON_RESULTS)):
            return AMAZON_RESULTS[row_index]["href"]
        return None

    def goto(self, url: str, **kwargs: Any) -> None:
        self.url = url

    def title(self) -> str:
        if self.dog and self.url:
            return "Sorry! Something went wrong!"
        return "Fake Amazon"
