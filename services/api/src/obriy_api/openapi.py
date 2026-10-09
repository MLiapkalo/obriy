import json
from typing import Any

from obriy_api.main import create_app


def build_spec() -> dict[str, Any]:
    return create_app().openapi()


def main() -> None:
    spec = build_spec()
    print(json.dumps(spec, indent=2))


if __name__ == "__main__":
    main()
