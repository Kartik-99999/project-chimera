"""Workflow registry: the only tasks the Workbench may execute.

A workflow is a fixed, tested browser procedure with a declared
parameter schema. New environments are added by registering a new
:class:`WorkflowDefinition` — never by accepting free-form
instructions at runtime.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Mapping, Optional


@dataclass(frozen=True)
class WorkflowParameter:
    """One user-supplied parameter."""

    name: str
    label: str
    kind: str  # "text" | "select" | "number" | "checkbox"
    required: bool = False
    default: Any = None
    options: tuple = ()  # for "select": ((value, label), ...)
    help: str = ""
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    max_length: Optional[int] = None


@dataclass(frozen=True)
class WorkflowDefinition:
    """A supported browser workflow."""

    workflow_id: str
    title: str
    description: str
    environment: str
    parameters: tuple = ()
    drivers: tuple = ("chimera", "baseline-a")
    future: bool = False  # True: listed as a roadmap item, not runnable
    origin: str = "local"  # "local" | "external" (history facet)
    sessions: tuple = ("clean",)  # + "user": may run on a login profile

    def to_dict(self) -> Dict[str, Any]:
        return {
            "workflow_id": self.workflow_id,
            "title": self.title,
            "description": self.description,
            "environment": self.environment,
            "drivers": list(self.drivers),
            "future": self.future,
            "origin": self.origin,
            "sessions": list(self.sessions),
            "parameters": [
                {
                    "name": p.name,
                    "label": p.label,
                    "kind": p.kind,
                    "required": p.required,
                    "default": p.default,
                    "options": [
                        {"value": v, "label": text}
                        for v, text in p.options
                    ],
                    "help": p.help,
                    "min_value": p.min_value,
                    "max_value": p.max_value,
                    "max_length": p.max_length,
                }
                for p in self.parameters
            ],
        }

    def validate(self, params: Mapping[str, Any]) -> Dict[str, Any]:
        """Validate raw user input; return cleaned params or raise."""
        cleaned: Dict[str, Any] = {}
        unknown = set(params) - {p.name for p in self.parameters}
        if unknown:
            raise WorkflowValidationError(
                f"unknown parameter(s): {sorted(unknown)}")
        for p in self.parameters:
            raw = params.get(p.name, p.default)
            if p.kind == "text":
                value = "" if raw is None else str(raw)
                if p.required and not value.strip():
                    raise WorkflowValidationError(
                        f"{p.label} is required")
                if p.max_length is not None and len(value) > p.max_length:
                    raise WorkflowValidationError(
                        f"{p.label} must be at most {p.max_length} characters")
                cleaned[p.name] = value.strip() if p.required else value
            elif p.kind == "select":
                allowed = [v for v, _ in p.options]
                if raw not in allowed:
                    raise WorkflowValidationError(
                        f"{p.label} must be one of {allowed}")
                cleaned[p.name] = raw
            elif p.kind == "number":
                try:
                    value = int(raw)
                except (TypeError, ValueError):
                    raise WorkflowValidationError(
                        f"{p.label} must be a whole number") from None
                if p.min_value is not None and value < p.min_value:
                    raise WorkflowValidationError(
                        f"{p.label} must be at least {p.min_value}")
                if p.max_value is not None and value > p.max_value:
                    raise WorkflowValidationError(
                        f"{p.label} must be at most {p.max_value}")
                cleaned[p.name] = value
            elif p.kind == "checkbox":
                cleaned[p.name] = bool(raw)
            else:  # pragma: no cover — registry is closed
                raise WorkflowValidationError(
                    f"unsupported parameter kind {p.kind!r}")
        return cleaned


class WorkflowValidationError(ValueError):
    """User input failed workflow validation."""


CREATE_PROJECT = WorkflowDefinition(
    workflow_id="create-project",
    title="Create a project",
    description=(
        "Open the bundled Demo Task Manager, enter a project name, "
        "submit the form, and confirm the project appears in the list. "
        "A fixed script drives the browser — every step, retry, and "
        "verification is recorded and shown."
    ),
    environment="Demo Task Manager (bundled, local)",
    parameters=(
        WorkflowParameter(
            name="project_name", label="Project name", kind="text",
            required=True, default="", max_length=120,
            help="The exact name typed into the form and expected in the list.",
        ),
        WorkflowParameter(
            name="scenario", label="Page condition", kind="select",
            required=True, default="normal",
            options=(
                ("normal", "Normal page"),
                ("slow", "Slow load (form appears after a delay)"),
                ("disabled", "Broken submit (button stays disabled)"),
                ("slow-disabled", "Slow load + broken submit"),
            ),
            help="Deterministic page conditions. Slow/disabled variants "
                 "demonstrate how the driver handles delays and failures.",
        ),
        WorkflowParameter(
            name="slow_ms", label="Slow-load delay (ms)", kind="number",
            default=2100, min_value=0, max_value=15000,
            help="Used only for the slow-load conditions.",
        ),
        WorkflowParameter(
            name="action_timeout_ms",
            label="Per-action timeout override (ms)", kind="number",
            default=0, min_value=0, max_value=60000,
            help="Baseline A only (Chimera's 5 s per-action timeout is "
                 "fixed). 0 keeps the default; lower values force "
                 "timeout failures for demonstration.",
        ),
    ),
)

FILL_CONTACT_FORM = WorkflowDefinition(
    workflow_id="fill-contact-form",
    title="Fill a contact form",
    description=(
        "Open the bundled contact page, fill name, email, subject, and "
        "message, submit, and confirm the message appears in the sent "
        "list. A fixed script drives the browser — every step and "
        "verification is recorded and shown."
    ),
    environment="Demo Task Manager (bundled, local)",
    parameters=(
        WorkflowParameter(
            name="full_name", label="Full name", kind="text",
            required=True, default="", max_length=120,
            help="Typed into the name field; required by the page.",
        ),
        WorkflowParameter(
            name="email", label="Email", kind="text",
            required=True, default="", max_length=120,
            help="Typed into the email field. The page requires a "
                 "valid address; the submission case below can send a "
                 "broken one on purpose.",
        ),
        WorkflowParameter(
            name="subject", label="Subject", kind="text",
            required=False, default="", max_length=120,
            help="Optional on the page; part of the verified entry text.",
        ),
        WorkflowParameter(
            name="message", label="Message", kind="text",
            required=True, default="", max_length=2000,
            help="Typed into the message field; required by the page.",
        ),
        WorkflowParameter(
            name="submission_case", label="Submission case", kind="select",
            required=True, default="complete",
            options=(
                ("complete", "Complete submission"),
                ("missing-message", "Missing message (blanked before send)"),
                ("invalid-email", "Invalid email (broken address sent)"),
            ),
            help="What the driver actually types. The page validates "
                 "every submission and rejects incomplete ones — those "
                 "runs must fail verification honestly.",
        ),
        WorkflowParameter(
            name="scenario", label="Page condition", kind="select",
            required=True, default="normal",
            options=(
                ("normal", "Normal page"),
                ("slow", "Slow load (form appears after a delay)"),
                ("disabled", "Broken submit (button stays disabled)"),
                ("slow-disabled", "Slow load + broken submit"),
            ),
            help="Deterministic page conditions, as in Create a project.",
        ),
        WorkflowParameter(
            name="slow_ms", label="Slow-load delay (ms)", kind="number",
            default=2100, min_value=0, max_value=15000,
            help="Used only for the slow-load conditions.",
        ),
        WorkflowParameter(
            name="action_timeout_ms",
            label="Per-action timeout override (ms)", kind="number",
            default=0, min_value=0, max_value=60000,
            help="Baseline A only (Chimera's 5 s per-action timeout is "
                 "fixed). 0 keeps the default; lower values force "
                 "timeout failures for demonstration.",
        ),
    ),
)

SAUCEDEMO_ORDER = WorkflowDefinition(
    workflow_id="saucedemo-order",
    title="Order from the SauceDemo store",
    description=(
        "Log into the SauceDemo practice store, sort the catalog, add "
        "items to the cart, check out with test details, and confirm "
        "the demo order. A fixed script drives real Chromium — every "
        "step, stage state, and verification is recorded and shown. "
        "SauceDemo is a demo shop with no payment; nothing real is "
        "purchased."
    ),
    environment="SauceDemo practice store (external, approved origin)",
    origin="external",
    parameters=(
        WorkflowParameter(
            name="login_case", label="Login case", kind="select",
            required=True, default="standard",
            options=(
                ("standard", "Standard user (valid login)"),
                ("locked-out", "Locked-out user (login must fail)"),
                ("wrong-password", "Wrong password (login must fail)"),
            ),
            help="Which documented demo credential variant the driver "
                 "types. Failing variants must fail verification honestly.",
        ),
        WorkflowParameter(
            name="cart_preset", label="Cart preset", kind="select",
            required=True, default="backpack+bike-light",
            options=(
                ("backpack+bike-light", "Backpack + bike light (2 items)"),
                ("single-backpack", "Backpack only (1 item)"),
                ("empty-cart", "Empty cart (checkout must be refused)"),
            ),
            help="Which catalog items the driver adds before checkout.",
        ),
        WorkflowParameter(
            name="sort", label="Catalog sort", kind="select",
            required=True, default="az",
            options=(
                ("none", "No sorting"),
                ("az", "Name (A to Z)"),
                ("za", "Name (Z to A)"),
                ("lohi", "Price (low to high)"),
                ("hilo", "Price (high to low)"),
            ),
            help="Sort applied to the catalog and verified from the "
                 "recorded item order.",
        ),
        WorkflowParameter(
            name="first_name", label="First name", kind="text",
            required=False, default="Ada", max_length=60,
            help="Checkout information; mutated by the checkout case.",
        ),
        WorkflowParameter(
            name="last_name", label="Last name", kind="text",
            required=False, default="Lovelace", max_length=60,
            help="Checkout information; mutated by the checkout case.",
        ),
        WorkflowParameter(
            name="postal_code", label="Postal code", kind="text",
            required=False, default="12345", max_length=20,
            help="Checkout information; mutated by the checkout case.",
        ),
        WorkflowParameter(
            name="checkout_case", label="Checkout case", kind="select",
            required=True, default="complete",
            options=(
                ("complete", "Complete information"),
                ("missing-postal", "Missing postal code (must be rejected)"),
                ("blank-info", "Blank information (must be rejected)"),
            ),
            help="What the driver actually types. The store validates "
                 "every checkout and rejects incomplete ones — those "
                 "runs must fail verification honestly.",
        ),
        WorkflowParameter(
            name="action_timeout_ms",
            label="Per-action timeout override (ms)", kind="number",
            default=0, min_value=0, max_value=60000,
            help="Baseline A only (Chimera's 5 s per-action timeout is "
                 "fixed). 0 keeps the default; lower values force "
                 "timeout failures for demonstration.",
        ),
    ),
)

SAUCEDEMO_STRESS = WorkflowDefinition(
    workflow_id="saucedemo-stress",
    title="Stress the SauceDemo store",
    description=(
        "Run the SauceDemo order flow against behaviourally "
        "challenging demo accounts (slow logins, broken images, dead "
        "sorting, rejected checkouts) with add/remove cart consistency "
        "checks. A fixed script drives real Chromium — every step, "
        "stage state, readiness latency, and T-check verdict is "
        "recorded and shown. Nothing real is purchased."
    ),
    environment="SauceDemo practice store (external, approved origin)",
    origin="external",
    parameters=(
        WorkflowParameter(
            name="account", label="Test account", kind="select",
            required=True, default="standard",
            options=(
                ("standard", "Standard user (control)"),
                ("glitch", "Slow login (delayed readiness)"),
                ("problem", "Problem user (site defects)"),
            ),
            help="Which documented demo account the driver logs in as. "
                 "The problem account's own site defects fail checks "
                 "honestly; they are site behaviour, not driver faults.",
        ),
        WorkflowParameter(
            name="cart_preset", label="Cart preset", kind="select",
            required=True, default="backpack+bike-light",
            options=(
                ("backpack+bike-light", "Backpack + bike light (2 items)"),
                ("single-backpack", "Backpack only (1 item)"),
            ),
            help="Which catalog items the driver adds before the "
                 "removal step.",
        ),
        WorkflowParameter(
            name="remove_item", label="Removal step", kind="select",
            required=True, default="last-added",
            options=(
                ("last-added", "Remove the last-added item"),
                ("none", "No removal (cart-after-remove unchecked)"),
            ),
            help="Whether the driver removes one item on the cart page "
                 "and re-verifies the remainder before checkout.",
        ),
        WorkflowParameter(
            name="sort", label="Catalog sort", kind="select",
            required=True, default="az",
            options=(
                ("none", "No sorting"),
                ("az", "Name (A to Z)"),
                ("za", "Name (Z to A)"),
                ("lohi", "Price (low to high)"),
                ("hilo", "Price (high to low)"),
            ),
            help="Sort applied to the catalog and verified from the "
                 "recorded item order.",
        ),
        WorkflowParameter(
            name="first_name", label="First name", kind="text",
            required=False, default="Ada", max_length=60,
            help="Checkout information (always complete; the site "
                 "itself may still reject it).",
        ),
        WorkflowParameter(
            name="last_name", label="Last name", kind="text",
            required=False, default="Lovelace", max_length=60,
            help="Checkout information (always complete).",
        ),
        WorkflowParameter(
            name="postal_code", label="Postal code", kind="text",
            required=False, default="12345", max_length=20,
            help="Checkout information (always complete).",
        ),
        WorkflowParameter(
            name="settle_timeout_ms",
            label="Post-click settle budget (ms)", kind="number",
            default=5000, min_value=100, max_value=30000,
            help="Baseline A only: bound per read-only settle window "
                 "after a click (Chimera instead uses its fixed 5 s "
                 "settle plus 5 s verification waits). Raise for slow "
                 "accounts; both drivers get comparable total budgets.",
        ),
        WorkflowParameter(
            name="action_timeout_ms",
            label="Per-action timeout override (ms)", kind="number",
            default=0, min_value=0, max_value=60000,
            help="Baseline A only (Chimera's 5 s per-action timeout is "
                 "fixed). 0 keeps the default; lower values force "
                 "timeout failures for demonstration.",
        ),
    ),
)

FLIPKART_ADD_TO_CART = WorkflowDefinition(
    workflow_id="flipkart-add-to-cart",
    title="Add a Flipkart item to cart",
    description=(
        "Search the Flipkart marketplace, open one result, add it to "
        "the guest cart, and verify the cart holds exactly that item. "
        "A fixed script drives real Chromium — every step, stage "
        "state, and verification is recorded and shown. Guest cart "
        "only: the driver never logs in, never checks out, and never "
        "buys. Chimera-only: no replay baseline exists for a live "
        "external catalog."
    ),
    environment="Flipkart marketplace (external, approved origin)",
    origin="external",
    drivers=("chimera",),
    parameters=(
        WorkflowParameter(
            name="query", label="Search query", kind="text",
            required=True, default="yonex badminton", max_length=80,
            help="Typed into the Flipkart search box; the results page "
                 "is then loaded deterministically for this query.",
        ),
        WorkflowParameter(
            name="pick", label="Result to add", kind="number",
            default=1, min_value=1, max_value=5,
            help="Which search result to open and add (1-based). The "
                 "run fails honestly when the search returns fewer.",
        ),
    ),
)

WIKIPEDIA_LOOKUP = WorkflowDefinition(
    workflow_id="wikipedia-article-lookup",
    title="Look up a Wikipedia article",
    description=(
        "Search English Wikipedia, open one article, and verify its "
        "heading and summary. A fixed script drives real Chromium — "
        "every step, stage state, and verification is recorded and "
        "shown. Read-only: nothing is edited. Chimera-only: no replay "
        "baseline exists for a live external catalog."
    ),
    environment="English Wikipedia (external, approved origin)",
    origin="external",
    drivers=("chimera",),
    parameters=(
        WorkflowParameter(
            name="query", label="Search query", kind="text",
            required=True, default="badminton", max_length=80,
            help="Typed into the Wikipedia search box; the results "
                 "page is then loaded deterministically for this query.",
        ),
        WorkflowParameter(
            name="pick", label="Result to open", kind="number",
            default=1, min_value=1, max_value=5,
            help="Which search result to open (1-based). Exact-title "
                 "matches redirect straight to the article; the pick "
                 "must then be 1.",
        ),
    ),
)

WIKTIONARY_LOOKUP = WorkflowDefinition(
    workflow_id="wiktionary-word-lookup",
    title="Look up a Wiktionary word",
    description=(
        "Open one Wiktionary dictionary entry and verify the word "
        "exists with recorded definitions. A fixed script drives real "
        "Chromium — every step, stage state, and verification is "
        "recorded and shown. Read-only: nothing is edited. "
        "Chimera-only: no replay baseline exists for a live external "
        "dictionary."
    ),
    environment="English Wiktionary (external, approved origin)",
    origin="external",
    drivers=("chimera",),
    parameters=(
        WorkflowParameter(
            name="word", label="Word", kind="text",
            required=True, default="badminton", max_length=40,
            help="Dictionary headword to open (letters, apostrophes, "
                 "hyphens, spaces). Unknown words fail honestly.",
        ),
    ),
)

PYPI_LOOKUP = WorkflowDefinition(
    workflow_id="pypi-package-lookup",
    title="Look up a PyPI package",
    description=(
        "Open one PyPI project page and verify the package name, "
        "version, and summary. A fixed script drives real Chromium — "
        "every step, stage state, and verification is recorded and "
        "shown. Read-only. Chimera-only: no replay baseline exists "
        "for a live external index."
    ),
    environment="Python Package Index (external, approved origin)",
    origin="external",
    drivers=("chimera",),
    parameters=(
        WorkflowParameter(
            name="package", label="Package name", kind="text",
            required=True, default="playwright", max_length=60,
            help="Project name on PyPI (letters, digits, underscore, "
                 "dot, hyphen). Unknown names fail honestly.",
        ),
    ),
)

BBC_HEADLINES = WorkflowDefinition(
    workflow_id="bbc-headlines",
    title="Capture BBC section headlines",
    description=(
        "Open one BBC section front (News, Business, or Technology) "
        "and verify the section was served with recorded headlines. "
        "A fixed script drives real Chromium — the headline list is "
        "recorded and shown. Read-only. Chimera-only: no replay "
        "baseline exists for a live news front."
    ),
    environment="BBC (external, approved origin)",
    origin="external",
    drivers=("chimera",),
    parameters=(
        WorkflowParameter(
            name="section", label="Section", kind="select",
            required=True, default="news",
            options=(
                ("news", "News"),
                ("business", "Business"),
                ("technology", "Technology"),
            ),
            help="Which BBC section front to open and record.",
        ),
    ),
)

GITHUB_PROFILE = WorkflowDefinition(
    workflow_id="github-profile",
    title="Look up a GitHub profile",
    description=(
        "Open one public GitHub profile and verify the handle and "
        "display name. A fixed script drives real Chromium — every "
        "step, stage state, and verification is recorded and shown. "
        "Read-only: nothing is starred, followed, or changed, and no "
        "login is used. Chimera-only: no replay baseline exists for "
        "a live external profile."
    ),
    environment="GitHub (external, approved origin)",
    origin="external",
    drivers=("chimera",),
    parameters=(
        WorkflowParameter(
            name="username", label="Username", kind="text",
            required=True, default="torvalds", max_length=39,
            help="Public GitHub username (letters, digits, hyphens; "
                 "not first or last). Unknown names fail honestly.",
        ),
    ),
)

CRATES_LOOKUP = WorkflowDefinition(
    workflow_id="crates-lookup",
    title="Look up a Rust crate",
    description=(
        "Open one crates.io crate page and verify the crate name, "
        "version, and summary. A fixed script drives real Chromium — "
        "every step, stage state, and verification is recorded and "
        "shown. Read-only. Chimera-only: no replay baseline exists "
        "for a live external registry."
    ),
    environment="crates.io (external, approved origin)",
    origin="external",
    drivers=("chimera",),
    parameters=(
        WorkflowParameter(
            name="crate", label="Crate name", kind="text",
            required=True, default="serde", max_length=64,
            help="Crate name on crates.io (letters, digits, underscore, "
                 "hyphen). Unknown names fail honestly.",
        ),
    ),
)

BBC_WEATHER = WorkflowDefinition(
    workflow_id="bbc-weather",
    title="Check a BBC Weather city forecast",
    description=(
        "Open one BBC Weather city page and verify the city was "
        "served with recorded temperatures. A fixed script drives "
        "real Chromium — the forecast state is recorded and shown. "
        "Read-only. Chimera-only: no replay baseline exists for a "
        "live weather page."
    ),
    environment="BBC Weather (external, approved origin)",
    origin="external",
    drivers=("chimera",),
    parameters=(
        WorkflowParameter(
            name="city", label="City", kind="select",
            required=True, default="london",
            options=(
                ("london", "London"),
                ("new-york", "New York"),
                ("tokyo", "Tokyo"),
                ("sydney", "Sydney"),
                ("paris", "Paris"),
            ),
            help="Which city forecast to open and record.",
        ),
    ),
)

GITHUB_SEARCH = WorkflowDefinition(
    workflow_id="github-search",
    title="Search GitHub repositories",
    description=(
        "Search GitHub for repositories and verify results were "
        "served with recorded repo names. A fixed script drives real "
        "Chromium — the result list is recorded and shown. "
        "Read-only, no login. Chimera-only: no replay baseline "
        "exists for live search results."
    ),
    environment="GitHub (external, approved origin)",
    origin="external",
    drivers=("chimera",),
    parameters=(
        WorkflowParameter(
            name="query", label="Search query", kind="text",
            required=True, default="playwright", max_length=100,
            help="Repository search text. Queries with no matches "
                 "fail honestly.",
        ),
    ),
)

STEAM_PRICE = WorkflowDefinition(
    workflow_id="steam-price-check",
    title="Check a Steam game price",
    description=(
        "Search the Steam store, open one game, and verify its name "
        "and displayed price. A fixed script drives real Chromium — "
        "every step, stage state, and verification is recorded and "
        "shown. Read-only: nothing is bought, no account is used, "
        "and age gates are never submitted. Chimera-only: no replay "
        "baseline exists for a live store."
    ),
    environment="Steam store (external, approved origin)",
    origin="external",
    drivers=("chimera",),
    parameters=(
        WorkflowParameter(
            name="query", label="Game search", kind="text",
            required=True, default="portal", max_length=100,
            help="Game name to search for in the Steam store.",
        ),
        WorkflowParameter(
            name="pick", label="Result pick", kind="number",
            required=True, default=1, min_value=1, max_value=5,
            help="Which search result to open (1–5). Out-of-range "
                 "picks fail honestly.",
        ),
    ),
)

ARXIV_SEARCH = WorkflowDefinition(
    workflow_id="arxiv-search",
    title="Search arXiv papers",
    description=(
        "Search the arXiv e-print repository and verify results "
        "were served with recorded paper titles. A fixed script "
        "drives real Chromium — the result list is recorded and "
        "shown. Read-only. Chimera-only: no replay baseline exists "
        "for live search results."
    ),
    environment="arXiv (external, approved origin)",
    origin="external",
    drivers=("chimera",),
    parameters=(
        WorkflowParameter(
            name="query", label="Search query", kind="text",
            required=True, default="transformer", max_length=100,
            help="Paper search text. Queries with no matches fail "
                 "honestly.",
        ),
    ),
)

SO_SEARCH = WorkflowDefinition(
    workflow_id="stackoverflow-search",
    title="Search Stack Overflow questions",
    description=(
        "Search Stack Overflow and verify results were served with "
        "recorded question titles. A fixed script drives real "
        "Chromium — the result list is recorded and shown. "
        "Read-only. Clean sessions usually meet a bot gate; re-run "
        "with a logged-in profile to proceed. Chimera-only: no "
        "replay baseline exists for live search results."
    ),
    environment="Stack Overflow (external, approved origin)",
    origin="external",
    drivers=("chimera",),
    sessions=("clean", "user"),
    parameters=(
        WorkflowParameter(
            name="query", label="Search query", kind="text",
            required=True, default="playwright python click",
            max_length=100,
            help="Question search text. Queries with no matches "
                 "fail honestly.",
        ),
    ),
)

AMAZON_PRICE = WorkflowDefinition(
    workflow_id="amazon-price-check",
    title="Check an Amazon product price",
    description=(
        "Search Amazon, open one product, and verify its name and "
        "displayed price. A fixed script drives real Chromium — "
        "every step, stage state, and verification is recorded and "
        "shown. Read-only: nothing is bought, no cart, checkout, or "
        "account page is ever opened. Clean sessions usually meet a "
        "bot gate; re-run with a logged-in profile to proceed. "
        "Chimera-only: no replay baseline exists for a live store."
    ),
    environment="Amazon (external, approved origin)",
    origin="external",
    drivers=("chimera",),
    sessions=("clean", "user"),
    parameters=(
        WorkflowParameter(
            name="query", label="Product search", kind="text",
            required=True, default="kindle", max_length=100,
            help="Product name to search for on Amazon.",
        ),
        WorkflowParameter(
            name="pick", label="Result pick", kind="number",
            required=True, default=1, min_value=1, max_value=5,
            help="Which search result to open (1–5). Out-of-range "
                 "picks fail honestly.",
        ),
    ),
)

# Roadmap items: visible so the boundary is explicit, never runnable.
FUTURE_WORKFLOWS = (
    WorkflowDefinition(
        workflow_id="third-party-sites",
        title="Arbitrary third-party websites",
        description=(
            "Not supported. Operating reliably on sites Chimera was not "
            "built for requires site-specific adapters; only the "
            "SauceDemo, Flipkart, Wikipedia, Wiktionary, PyPI, BBC, "
            "GitHub, crates.io, BBC Weather, GitHub search, Steam, "
            "arXiv, Stack Overflow, and Amazon adapters exist."
        ),
        environment="—",
        drivers=(),
        future=True,
    ),
)

_REGISTRY: Dict[str, WorkflowDefinition] = {
    CREATE_PROJECT.workflow_id: CREATE_PROJECT,
    FILL_CONTACT_FORM.workflow_id: FILL_CONTACT_FORM,
    SAUCEDEMO_ORDER.workflow_id: SAUCEDEMO_ORDER,
    SAUCEDEMO_STRESS.workflow_id: SAUCEDEMO_STRESS,
    FLIPKART_ADD_TO_CART.workflow_id: FLIPKART_ADD_TO_CART,
    WIKIPEDIA_LOOKUP.workflow_id: WIKIPEDIA_LOOKUP,
    WIKTIONARY_LOOKUP.workflow_id: WIKTIONARY_LOOKUP,
    PYPI_LOOKUP.workflow_id: PYPI_LOOKUP,
    BBC_HEADLINES.workflow_id: BBC_HEADLINES,
    GITHUB_PROFILE.workflow_id: GITHUB_PROFILE,
    CRATES_LOOKUP.workflow_id: CRATES_LOOKUP,
    BBC_WEATHER.workflow_id: BBC_WEATHER,
    GITHUB_SEARCH.workflow_id: GITHUB_SEARCH,
    STEAM_PRICE.workflow_id: STEAM_PRICE,
    ARXIV_SEARCH.workflow_id: ARXIV_SEARCH,
    SO_SEARCH.workflow_id: SO_SEARCH,
    AMAZON_PRICE.workflow_id: AMAZON_PRICE,
}


def list_workflows() -> List[WorkflowDefinition]:
    """Runnable workflows plus explicitly labelled roadmap items."""
    return [CREATE_PROJECT, FILL_CONTACT_FORM, SAUCEDEMO_ORDER,
            SAUCEDEMO_STRESS, FLIPKART_ADD_TO_CART, WIKIPEDIA_LOOKUP,
            WIKTIONARY_LOOKUP, PYPI_LOOKUP, BBC_HEADLINES,
            GITHUB_PROFILE, CRATES_LOOKUP, BBC_WEATHER,
            GITHUB_SEARCH, STEAM_PRICE, ARXIV_SEARCH,
            SO_SEARCH, AMAZON_PRICE, *FUTURE_WORKFLOWS]


def get_workflow(workflow_id: str) -> WorkflowDefinition:
    try:
        return _REGISTRY[workflow_id]
    except KeyError:
        raise WorkflowValidationError(
            f"unsupported workflow {workflow_id!r}: only "
            f"{sorted(_REGISTRY)} can run") from None


# Map the workspace scenario names onto fault parameters.
SCENARIO_FAULTS = {
    "normal": {"slow_ms": 0, "disabled": False},
    "slow": {"slow_ms": None, "disabled": False},  # slow_ms from params
    "disabled": {"slow_ms": 0, "disabled": True},
    "slow-disabled": {"slow_ms": None, "disabled": True},
}

# Display names for benchmark scenario IDs in analytics.
BENCHMARK_SCENARIOS = {
    "S-NORM": "Normal page",
    "S-SLOW": "Slow load",
    "S-DIS": "Broken submit",
    "S-SLOWDIS": "Slow load + broken submit",
}
