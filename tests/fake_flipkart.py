"""Shared scripted Flipkart fake for harness tests (no browser).

A stateful fake marketplace: home, search, product, and cart pages
with failure injection. Used by driver tests and workbench executor
tests.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from adapters import flipkart as adapter


A = adapter  # short alias for selector constants

FAKE_RESULTS = [
    {"title": "YONEX GR 303i Black, Red Strung Badminton Racquet",
     "href": "/yonex-gr-303i-black-red-strung-badminton-racquet/p/itmFAKE0001?pid=X"},
    {"title": "YONEX Nanoray 18i Graphite Strung Badminton Racquet",
     "href": "/yonex-nanoray-18i-graphite-strung-badminton-racquet/p/itmFAKE0002?pid=Y"},
    {"title": "YONEX Mavis 350 Nylon White Shuttlecock, Pack of 6",
     "href": "/yonex-mavis-350-nylon-white-shuttlecock-pack-of-6/p/itmFAKE0003?pid=Z"},
]


class FakeFlipLocator:
    def __init__(self, page: "FakeFlipPage", selector: str) -> None:
        self._page = page
        self._selector = selector

    @property
    def first(self) -> "FakeFlipLocator":
        return self

    def count(self) -> int:
        return len(self._page._texts(self._selector))

    def text_content(self, **kwargs: Any) -> Optional[str]:
        texts = self._page._texts(self._selector)
        return texts[0] if texts else None

    def all_text_contents(self) -> List[str]:
        return list(self._page._texts(self._selector))

    def is_visible(self, **kwargs: Any) -> bool:
        return self._page._visible(self._selector)

    def fill(self, value: str, **kwargs: Any) -> None:
        self._page._fill(self._selector, value)

    def click(self, **kwargs: Any) -> None:
        self._page._click(self._selector)

    def nth(self, index: int) -> "_FakeFlipIndexedLocator":
        return _FakeFlipIndexedLocator(self._page, self._selector, index)

    def get_attribute(self, name: str, **kwargs: Any) -> Optional[str]:
        return self._page._attribute(self._selector, 0, name)

    def wait_for(self, state: Optional[str] = None, **kwargs: Any) -> None:
        if state == "visible" and not self._page._visible(self._selector):
            raise TimeoutError(f"{self._selector} never became visible")


class _FakeFlipIndexedLocator:
    def __init__(self, page: "FakeFlipPage", selector: str,
                 index: int) -> None:
        self._page = page
        self._selector = selector
        self._index = index

    def get_attribute(self, name: str, **kwargs: Any) -> Optional[str]:
        return self._page._attribute(self._selector, self._index, name)

    def text_content(self, **kwargs: Any) -> Optional[str]:
        texts = self._page._texts(self._selector)
        return texts[self._index] if 0 <= self._index < len(texts) else None

    def inner_text(self, **kwargs: Any) -> str:
        return self.text_content() or ""


class FakeFlipPage:
    """A scripted Flipkart: search, product, cart, and error flags."""

    def __init__(self, *, modal: bool = True, no_results: bool = False,
                 add_fails: bool = False, wrong_item: bool = False,
                 fail_clicks: frozenset = frozenset(),
                 fail_fills: frozenset = frozenset()) -> None:
        self.url = ""
        self.modal = modal
        self.no_results = no_results
        self.add_fails = add_fails
        self.wrong_item = wrong_item
        self.fail_clicks = fail_clicks
        self.fail_fills = fail_fills
        self.filled: Dict[str, str] = {}
        self.added_href: Optional[str] = None
        self.cart: List[str] = []

    # -- element table -------------------------------------------------

    def _path(self) -> str:
        return self.url.replace(A.APPROVED_ORIGIN, "") or "/"

    def _on_product(self, href: str = "") -> bool:
        path = (href or self._path()).split("?")[0]
        return bool(A.PRODUCT_PATH_RE.match(path))

    def _texts(self, selector: str) -> List[str]:
        path = self._path()
        if selector == A.SEL_SEARCH_INPUT:
            return [""] if path in ("/", "/search") else []
        if selector == A.SEL_MODAL_CANCEL:
            return ["Cancel"] if self.modal and path == "/" else []
        if selector == A.SEL_RESULT_LINK:
            if path.startswith("/search"):
                if self.no_results:
                    return []
                return [r["title"] for r in FAKE_RESULTS]
            if path == A.VIEWCART_PATH:
                return [self._cart_name(h) for h in self.cart]
            return []
        if selector == A.SEL_ADD_TO_CART:
            if self._on_product() and self.added_href is None:
                return ["Add to cart"]
            return []
        if selector == A.SEL_GO_TO_CART:
            if self._on_product() and self.added_href is not None:
                return ["Go to cart"]
            return []
        if selector == A.SEL_CART_LINK:
            return [f"{len(self.cart)} Cart"]
        if selector == A.SEL_CART_QTY:
            return ["Qty: 1"] if self.cart else []
        if selector == A.SEL_TOTAL_LABEL:
            return ["Total Amount"] if self.cart else []
        if selector == A.SEL_CART_LEAVES:
            if self._path() != A.VIEWCART_PATH or not self.cart:
                return []
            leaves = ["BESTSELLER", "Zoom"]
            for href in self.cart:
                leaves += ["Qty: 1", self._cart_name(href),
                           "Pack of: 1", "Delivery by Mon Nov 9"]
            return leaves
        if selector == "body":
            return [self._body()]
        return []

    def _cart_name(self, href: str) -> str:
        for r in FAKE_RESULTS:
            if r["href"] == href:
                return r["title"] + " (Pack of: 1)"
        return "A completely different marketplace product"

    def _body(self) -> str:
        if self._path() != A.VIEWCART_PATH:
            return ""
        if not self.cart:
            return "Your cart is empty"
        lines = ["Qty: 1"]
        for href in self.cart:
            lines.append(self._cart_name(href))
        lines += ["Total Amount", "₹599"]
        return "\n".join(lines)

    def _visible(self, selector: str) -> bool:
        return bool(self._texts(selector))

    def title(self) -> str:
        if self._on_product():
            for r in FAKE_RESULTS:
                if r["href"].split("?")[0] in self._path():
                    return r["title"] + " - Buy Online at Best Price | Flipkart.com"
        if self._path().startswith("/search"):
            return "Search results | Flipkart.com"
        return "Flipkart.com"

    # -- actions --------------------------------------------------------

    def goto(self, url: str, **kwargs: Any) -> None:
        self.url = url

    def locator(self, selector: str, **kwargs: Any) -> FakeFlipLocator:
        return FakeFlipLocator(self, selector)

    def screenshot(self, path: Optional[str] = None, **kwargs: Any) -> bytes:
        from pathlib import Path as _Path

        if path:
            _Path(path).write_bytes(b"fake-png")
        return b"fake-png"

    def _fill(self, selector: str, value: str) -> None:
        if selector in self.fail_fills:
            raise RuntimeError(f"fake fill failure on {selector}")
        self.filled[selector] = value

    def _click(self, selector: str) -> None:
        if selector in self.fail_clicks:
            raise RuntimeError(f"fake click failure on {selector}")
        if selector == A.SEL_MODAL_CANCEL:
            self.modal = False
        elif selector == A.SEL_ADD_TO_CART and self._on_product():
            if not self.add_fails:
                href = self._current_product_href()
                self.added_href = href
                if self.wrong_item:
                    self.cart.append("WRONG")
                elif href and href not in self.cart:
                    self.cart.append(href)

    def _current_product_href(self) -> Optional[str]:
        for r in FAKE_RESULTS:
            if r["href"].split("?")[0] in self._path():
                return r["href"]
        return None

    def _attribute(self, selector: str, index: int,
                   name: str) -> Optional[str]:
        if selector == A.SEL_RESULT_LINK and name == "href":
            if self._path().startswith("/search") and not self.no_results:
                if 0 <= index < len(FAKE_RESULTS):
                    return FAKE_RESULTS[index]["href"]
        return None


class FakeFlipContext:
    def close(self) -> None:
        pass


class FakeFlipBrowser:
    def close(self) -> None:
        pass
