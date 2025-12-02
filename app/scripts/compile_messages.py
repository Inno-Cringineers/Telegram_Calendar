#!/usr/bin/env python3
"""Script to compile .po files to .mo files using Babel."""

import sys
from pathlib import Path

try:
    from babel.messages.pofile import read_po
    from babel.messages.mofile import write_mo
except ImportError:
    print("Error: Babel is not installed. Please install it with: pip install Babel")
    sys.exit(1)


def compile_po_to_mo(po_path: Path, mo_path: Path) -> None:
    """Compile a .po file to .mo file.

    Args:
        po_path: Path to .po file.
        mo_path: Path to output .mo file.
    """
    with open(po_path, "rb") as po_file:
        catalog = read_po(po_file)

    with open(mo_path, "wb") as mo_file:
        write_mo(mo_file, catalog)

    print(f"Compiled {po_path} -> {mo_path}")


def main() -> None:
    """Main function to compile all .po files."""
    base_dir = Path(__file__).parent.parent
    locales_dir = base_dir / "src" / "i18n" / "locales"

    for lang in ["en", "ru"]:
        lang_dir = locales_dir / lang / "LC_MESSAGES"
        po_file = lang_dir / "messages.po"
        mo_file = lang_dir / "messages.mo"

        if po_file.exists():
            compile_po_to_mo(po_file, mo_file)
        else:
            print(f"Warning: {po_file} not found")


if __name__ == "__main__":
    main()

