"""Custom YAML loader for !include directives."""

import yaml


class IncludeLoader(yaml.SafeLoader):
    """YAML loader that supports !include directive."""

    pass


def include_constructor(_, node):
    """Constructor for !include directive that reads file content."""
    with open(node.value, "r") as f:
        return f.read().strip()


IncludeLoader.add_constructor("!include", include_constructor)
