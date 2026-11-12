#!/usr/bin/env python3
"""Package generated Roblox ModuleScripts into one importable .rbxmx model."""

from pathlib import Path
import sys
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
MODULES_DIR = ROOT / "roblox" / "ModuleScripts"
OUTPUT_FILE = ROOT / "roblox" / "CobaltCityData.rbxmx"


def main() -> int:
    if not MODULES_DIR.is_dir():
        print(f"ERROR: ModuleScripts folder not found: {MODULES_DIR}")
        return 1

    files = sorted(MODULES_DIR.glob("CobaltChunk_*.lua"))
    if not files:
        print(f"ERROR: no CobaltChunk_*.lua files found in {MODULES_DIR}")
        return 1

    root = ET.Element("roblox", {"version": "4"})
    folder = ET.SubElement(root, "Item", {"class": "Folder", "referent": "RBX1"})
    props = ET.SubElement(folder, "Properties")
    ET.SubElement(props, "string", {"name": "Name"}).text = "CobaltCityData"

    total_bytes = 0
    for index, path in enumerate(files, start=2):
        try:
            source = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            print(f"ERROR: invalid UTF-8 source: {path.name}")
            return 1

        item = ET.SubElement(
            folder,
            "Item",
            {"class": "ModuleScript", "referent": f"RBX{index}"},
        )
        item_props = ET.SubElement(item, "Properties")
        ET.SubElement(item_props, "string", {"name": "Name"}).text = path.stem
        ET.SubElement(item_props, "bool", {"name": "Disabled"}).text = "false"
        ET.SubElement(item_props, "ProtectedString", {"name": "Source"}).text = source
        total_bytes += len(source.encode("utf-8"))

    tree = ET.ElementTree(root)
    ET.indent(tree, space="  ")
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    tree.write(OUTPUT_FILE, encoding="utf-8", xml_declaration=True)

    # Parse the written file again so malformed XML is caught before reporting success.
    ET.parse(OUTPUT_FILE)

    size_mib = OUTPUT_FILE.stat().st_size / (1024 * 1024)
    print(f"Roblox model created: {OUTPUT_FILE}")
    print(f"ModuleScripts: {len(files)}")
    print(f"Lua source total: {total_bytes / (1024 * 1024):.2f} MiB")
    print(f"RBXMX file size: {size_mib:.2f} MiB")
    print("XML validation: OK")
    print("Import this model into Roblox Studio, then move CobaltCityData to ServerStorage.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
