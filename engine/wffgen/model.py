"""Deterministic XML element model and serializer.

The serializer defines the canonical AGENOR WFF style: 2-space indent,
double-quoted attributes in a fixed per-tag order, self-closing empty
elements with a space before `/>`, and a stable UTF-8 declaration. The same
document model always serializes to identical bytes.
"""

from __future__ import annotations

from dataclasses import dataclass, field

XML_DECL = '<?xml version="1.0" encoding="utf-8"?>\n'

# Canonical attribute order per tag; attributes not listed sort last,
# alphabetically (still deterministic).
ATTR_ORDER: dict[str, list[str]] = {
    "WatchFace": ["width", "height"],
    "Metadata": ["key", "value"],
    "BitmapFont": ["name", "family", "size", "color"],
    "Character": ["name", "resource", "width", "height"],
    "Scene": ["backgroundColor"],
    "PartImage": ["name", "x", "y", "width", "height", "alpha",
                  "pivotX", "pivotY"],
    "PartText": ["name", "x", "y", "width", "height", "alpha"],
    "PartDraw": ["name", "x", "y", "width", "height", "alpha"],
    "Group": ["name", "x", "y", "width", "height", "alpha",
              "pivotX", "pivotY"],
    "Variant": ["mode", "target", "value", "duration", "startOffset",
                "interpolation"],
    "Transform": ["target", "value"],
    "Image": ["resource"],
    "Text": ["align"],
    "Font": ["family", "size", "color"],
    "Parameter": ["expression"],
    "Reference": ["source", "name", "defaultValue"],
}


def _escape(value: str) -> str:
    return (value.replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


@dataclass
class Elem:
    tag: str
    attrs: dict[str, str] = field(default_factory=dict)
    children: list["Elem"] = field(default_factory=list)
    text: str | None = None  # rendered inline: <Tag ...>text-or-children</Tag>

    def child(self, elem: "Elem") -> "Elem":
        self.children.append(elem)
        return self

    def sorted_attrs(self) -> list[tuple[str, str]]:
        order = ATTR_ORDER.get(self.tag, [])
        keyed = sorted(
            self.attrs.items(),
            key=lambda kv: (order.index(kv[0]) if kv[0] in order
                            else len(order), kv[0]),
        )
        return keyed

    def serialize(self, indent: int = 0, inline: bool = False) -> str:
        pad = "" if inline else "  " * indent
        attrs = "".join(f' {k}="{_escape(str(v))}"'
                        for k, v in self.sorted_attrs())
        open_tag = f"{pad}<{self.tag}{attrs}"
        if not self.children and self.text is None:
            return f"{open_tag} />" if inline else f"{open_tag} />\n"
        if self.text is not None and not self.children:
            body = _escape(self.text)
            close = f"</{self.tag}>"
            return (f"{open_tag}>{body}{close}" if inline
                    else f"{open_tag}>{body}{close}\n")
        # Children render on one line when the element opts in (WFF text
        # stacks like <Text><BitmapFont><Template> are conventionally inline).
        # Mixed content (text followed by children, e.g. <Template>%d<Parameter/>)
        # is supported only inline.
        inline_children = getattr(self, "inline_children", False)
        if inline_children or inline:
            lead = _escape(self.text) if self.text is not None else ""
            body = lead + "".join(c.serialize(0, inline=True)
                                  for c in self.children)
            return (f"{open_tag}>{body}</{self.tag}>" if inline
                    else f"{open_tag}>{body}</{self.tag}>\n")
        out = f"{open_tag}>\n"
        for c in self.children:
            out += c.serialize(indent + 1)
        out += f"{pad}</{self.tag}>\n"
        return out


def inline(elem: Elem) -> Elem:
    """Mark an element to render its children on one line (WFF text stacks)."""
    elem.inline_children = True
    return elem


def document(root: Elem) -> str:
    """Serialize a full document deterministically."""
    return XML_DECL + root.serialize(0)
