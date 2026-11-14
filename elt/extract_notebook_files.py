import json
from pathlib import Path

notebook = Path("elt/freshcart_elt_colab.ipynb")
output_dir = Path("elt")

data = json.loads(notebook.read_text(encoding="utf-8"))
count = 0

for cell in data["cells"]:
    if cell.get("cell_type") != "code":
        continue

    lines = "".join(cell.get("source", [])).splitlines()

    for i, line in enumerate(lines):
        if line.strip().startswith("%%writefile "):
            filename = line.strip().replace("%%writefile ", "", 1)
            filename = filename.replace("/content/freshcart_elt/", "")

            destination = output_dir / filename
            destination.parent.mkdir(parents=True, exist_ok=True)

            content = "\n".join(lines[i + 1:]) + "\n"
            destination.write_text(content, encoding="utf-8")

            print("Extracted:", destination)
            count += 1
            break

print(f"\nTotal files extracted: {count}")