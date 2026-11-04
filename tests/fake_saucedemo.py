"""Shared scripted SauceDemo fake for harness tests (no browser).

A stateful fake store page: transitions, cart, sort, login/info
error flags, and failure injection. Used by driver tests and
workbench executor tests.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from adapters import saucedemo as adapter


A = adapter  # short alias for selector constants


def ordered_names(sort: str) -> List[str]:
    items = [(info["name"], float(info["price"].replace("$", "")))
             for info in A.CATALOG.values()]
    if sort == "az":
        return [n for n, _ in sorted(items)]
    if sort == "za":
        return [n for n, _ in sorted(items, reverse=True)]
    pairs = sorted(items, key=lambda p: (p[1], p[0]))
    ordered = [n for n, _ in pairs]
    return ordered if sort == "lohi" else list(reversed(ordered))


class FakeSauceLocator:
    def __init__(self, page: "FakeSaucePage", selector: str) -> None:
        self._page = page
        self._selector = selector

    @property
    def first(self) -> "FakeSauceLocator":
        return self

    def count(self) -> int:
        return len(self._page._texts(self._selector))

    def text_content(self) -> Optional[str]:
        texts = self._page._texts(self._selector)
        return texts[0] if texts else None

    def input_value(self) -> str:
        return self._page._input_value(self._selector)

    def all_text_contents(self) -> List[str]:
        return list(self._page._texts(self._selector))

    def is_visible(self, **kwargs: Any) -> bool:
        return self._page._visible(self._selector)

    def fill(self, value: str, **kwargs: Any) -> None:
        self._page._fill(self._selector, value)

    def click(self, **kwargs: Any) -> None:
        self._page._click(self._selector)

    def select_option(self, value: Any, **kwargs: Any) -> None:
        self._page._select(self._selector, value)

    def nth(self, index: int) -> "_FakeSauceIndexedLocator":
        return _FakeSauceIndexedLocator(self._page, self._selector, index)

    def get_attribute(self, name: str, **kwargs: Any) -> Optional[str]:
        return self._page._attribute(self._selector, 0, name)

    def wait_for(self, state: Optional[str] = None, **kwargs: Any) -> None:
        if state == "visible" and not self._page._visible(self._selector):
            raise TimeoutError(f"{self._selector} never became visible")


class _FakeSauceIndexedLocator:
    def __init__(self, page: "FakeSaucePage", selector: str,
                 index: int) -> None:
        self._page = page
        self._selector = selector
        self._index = index

    def get_attribute(self, name: str, **kwargs: Any) -> Optional[str]:
        return self._page._attribute(self._selector, self._index, name)

    def inner_text(self, **kwargs: Any) -> str:
        texts = self._page._texts(self._selector)
        return texts[self._index] if self._index < len(texts) else ""


class FakeSaucePage:
    """A scripted SauceDemo: transitions, cart, sort, and error flags."""

    def __init__(self, *, login_ok: bool = True, info_ok: bool = True,
                 fail_clicks: frozenset = frozenset(),
                 fail_fills: frozenset = frozenset(),
                 images_404: bool = False, sort_broken: bool = False,
                 info_reject: bool = False) -> None:
        self.url = ""
        self.login_ok = login_ok
        self.info_ok = info_ok
        self.fail_clicks = fail_clicks
        self.fail_fills = fail_fills
        # problem-user modes: placeholder images, dead sort, checkout
        # rejected despite complete info.
        self.images_404 = images_404
        self.sort_broken = sort_broken
        self.info_reject = info_reject
        self.filled: Dict[str, str] = {}
        self.cart: List[str] = []
        self.sort = "az"
        self.login_error: Optional[str] = None
        self.info_error: Optional[str] = None

    # -- element table -------------------------------------------------

    def _path(self) -> str:
        return self.url.replace(A.APPROVED_ORIGIN, "") or "/"

    def _texts(self, selector: str) -> List[str]:
        path = self._path()
        if path == "/":
            if selector == A.SEL_LOGIN_ERROR and self.login_error:
                return [self.login_error]
            if selector in (A.SEL_USERNAME, A.SEL_PASSWORD,
                            A.SEL_LOGIN_BUTTON):
                return [""]
            return []
        if path == A.INVENTORY_PATH:
            if selector == A.SEL_INVENTORY_LIST:
                return [""]
            if selector == A.SEL_ITEM_IMG:
                return [""] * len(
                    ordered_names(self._effective_sort()))
            if selector == A.SEL_ITEM_NAME:
                return ordered_names(self._effective_sort())
            if selector == A.SEL_ITEM_PRICE:
                by_name = {i["name"]: i["price"]
                           for i in A.CATALOG.values()}
                return [by_name[n]
                        for n in ordered_names(self._effective_sort())]
            if selector == A.SEL_SORT:
                return [""]
            if selector.startswith('[data-test="add-to-cart-'):
                return [""]
            if selector == A.SEL_CART_LINK:
                return [""]
            return []
        if path == A.CART_PATH:
            if selector == A.SEL_CART_LIST:
                return [""]
            if selector == f"{A.SEL_CART_ITEM} {A.SEL_ITEM_NAME}":
                return [A.CATALOG[s]["name"] for s in self.cart]
            if selector == f"{A.SEL_CART_ITEM} {A.SEL_CART_QTY}":
                return ["1" for _ in self.cart]
            if selector == f"{A.SEL_CART_ITEM} {A.SEL_ITEM_PRICE}":
                return [A.CATALOG[s]["price"] for s in self.cart]
            if selector == A.SEL_CART_BADGE and self.cart:
                return [str(len(self.cart))]
            if selector == A.SEL_CHECKOUT:
                return [""]
            return []
        if path == A.INFO_PATH:
            if selector in (A.SEL_FIRST, A.SEL_LAST, A.SEL_POSTAL,
                            A.SEL_CONTINUE):
                return [""]
            if selector == A.SEL_INFO_ERROR and self.info_error:
                return [self.info_error]
            return []
        if path == A.OVERVIEW_PATH:
            if selector == A.SEL_TOTAL:
                total = sum(float(A.CATALOG[s]["price"].replace("$", ""))
                            for s in self.cart)
                return [f"Total: ${total:.2f}"]
            if selector == f"{A.SEL_CART_ITEM} {A.SEL_ITEM_NAME}":
                return [A.CATALOG[s]["name"] for s in self.cart]
            if selector == A.SEL_FINISH:
                return [""]
            return []
        if path == A.COMPLETE_PATH:
            if selector == A.SEL_COMPLETE_HEADER:
                return [A.COMPLETE_HEADER]
            if selector == A.SEL_COMPLETE_TEXT:
                return ["Your order has been dispatched."]
            return []
        return []

    def _visible(self, selector: str) -> bool:
        return bool(self._texts(selector))

    def _input_value(self, selector: str) -> str:
        if selector == A.SEL_SORT:
            return self.sort
        return self.filled.get(selector, "")

    # -- actions --------------------------------------------------------

    def goto(self, url: str, **kwargs: Any) -> None:
        self.url = url

    def locator(self, selector: str, **kwargs: Any) -> FakeSauceLocator:
        return FakeSauceLocator(self, selector)

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
        if selector == A.SEL_LOGIN_BUTTON and self._path() == "/":
            user = self.filled.get(A.SEL_USERNAME, "")
            valid = ("standard_user", "performance_glitch_user",
                     "problem_user")
            if self.login_ok and user in valid:
                self.url = A.APPROVED_ORIGIN + A.INVENTORY_PATH
                self.login_error = None
            else:
                self.login_error = (
                    "Epic sadface: Sorry, this user has been locked out.")
        elif selector.startswith('[data-test="add-to-cart-'):
            slug = selector[len('[data-test="add-to-cart-'):-2]
            if slug in A.CATALOG and slug not in self.cart:
                self.cart.append(slug)
        elif selector.startswith('[data-test="remove-'):
            slug = selector[len('[data-test="remove-'):-2]
            if slug in self.cart:
                self.cart.remove(slug)
        elif selector == A.SEL_CART_LINK:
            self.url = A.APPROVED_ORIGIN + A.CART_PATH
        elif selector == A.SEL_CHECKOUT:
            self.url = A.APPROVED_ORIGIN + A.INFO_PATH
        elif selector == A.SEL_CONTINUE and self._path() == A.INFO_PATH:
            complete = all(self.filled.get(s, "") for s in
                           (A.SEL_FIRST, A.SEL_LAST, A.SEL_POSTAL))
            if self.info_ok and complete and not self.info_reject:
                self.url = A.APPROVED_ORIGIN + A.OVERVIEW_PATH
                self.info_error = None
            else:
                self.info_error = "Error: First Name is required"
        elif selector == A.SEL_FINISH and self._path() == A.OVERVIEW_PATH:
            self.url = A.APPROVED_ORIGIN + A.COMPLETE_PATH

    def _select(self, selector: str, value: Any) -> None:
        if selector == A.SEL_SORT and str(value) in A.SORTS:
            self.sort = str(value)

    def _effective_sort(self) -> str:
        # A broken sort control accepts the value but never reorders.
        return "az" if self.sort_broken else self.sort

    def _attribute(self, selector: str, index: int,
                   name: str) -> Optional[str]:
        if selector == A.SEL_ITEM_IMG and name == "src" \
                and self._path() == A.INVENTORY_PATH:
            names = ordered_names(self._effective_sort())
            if 0 <= index < len(names):
                if self.images_404:
                    return "/assets/sl-404-fake.jpg"
                slug = next(s for s, info in A.CATALOG.items()
                            if info["name"] == names[index])
                return f"/assets/{slug}-fake.jpg"
        return None


class FakeSauceContext:
    def close(self) -> None:
        pass


class FakeSauceBrowser:
    def close(self) -> None:
        pass


def sauce_order(**overrides: Any) -> Dict[str, Any]:
    base: Dict[str, Any] = {
        "user": "standard_user",
        "password": "secret_sauce",
        "items": ["sauce-labs-backpack", "sauce-labs-bike-light"],
        "sort": "az",
        "info": {"firstName": "Ada", "lastName": "Lovelace",
                 "postalCode": "12345"},
    }
    base.update(overrides)
    return base


def sauce_expected(order: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "username": order["user"],
        "items": [A.CATALOG[s]["name"] for s in order["items"]],
        "sort": order["sort"],
    }


def sauce_stress_expected(order: Dict[str, Any]) -> Dict[str, Any]:
    added = [A.CATALOG[s]["name"] for s in order["items"]]
    remove = order.get("remove")
    remaining = None
    if remove and remove in order["items"]:
        remaining = [A.CATALOG[s]["name"] for s in order["items"]
                     if s != remove]
    return {
        "username": order["user"],
        "added": added,
        "remaining": remaining,
        "sort": order["sort"],
    }

