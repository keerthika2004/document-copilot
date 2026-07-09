#!/usr/bin/env -S uv run --project ../backend python
import shutil
import time
from pathlib import Path
from docling.document_converter import DocumentConverter


def main():
    script_dir = Path(__file__).resolve().parent
    downloads_dir = script_dir / "downloads"
    markdown_dir = script_dir / "markdown"

    print(f"Downloads Directory: {downloads_dir}")
    print(f"Markdown Directory:  {markdown_dir}")

    if not downloads_dir.exists():
        print(f"Error: Downloads directory {downloads_dir} does not exist.")
        return

    # 1. Create destination directory if not exists
    markdown_dir.mkdir(parents=True, exist_ok=True)

    # 2. Copy manifest.json if present in the downloads directory
    manifest_source = downloads_dir / "manifest.json"
    manifest_dest = markdown_dir / "manifest.json"
    if manifest_source.exists():
        print("Copying manifest.json...")
        shutil.copy2(manifest_source, manifest_dest)

    # 3. Initialize Docling DocumentConverter
    print(
        "Initializing Docling DocumentConverter (this may load deep learning models)..."
    )
    converter = DocumentConverter()

    # 4. Find all .htm files recursively
    htm_files = sorted(list(downloads_dir.glob("**/*.htm")))
    print(f"Found {len(htm_files)} HTM files to convert.")

    for i, htm_path in enumerate(htm_files, 1):
        relative_path = htm_path.relative_to(downloads_dir)
        dest_md_path = markdown_dir / relative_path.with_suffix(".md")

        print(f"[{i}/{len(htm_files)}] Converting {relative_path}...")

        # Create destination parent folder structure (e.g. data/markdown/2021)
        dest_md_path.parent.mkdir(parents=True, exist_ok=True)

        start_time = time.time()
        try:
            # Convert document using Docling
            result = converter.convert(htm_path)
            markdown_content = result.document.export_to_markdown()

            # Write markdown file output
            with open(dest_md_path, "w", encoding="utf-8") as f:
                f.write(markdown_content)

            elapsed = time.time() - start_time
            print(
                f"    Saved to {dest_md_path.relative_to(script_dir)} ({elapsed:.2f}s)"
            )
        except Exception as e:
            print(f"    Error converting {relative_path}: {e}")

    print("All conversions complete!")


if __name__ == "__main__":
    main()
