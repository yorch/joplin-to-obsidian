# Joplin to Obsidian Migration Tool

A Python tool to convert Joplin notebook exports (markdown + front matter format) into a format suitable for Obsidian vaults. This tool reorganizes resources, cleans up file names, and removes Joplin-specific metadata to create a cleaner Obsidian-compatible structure.

## Migration Workflow

This tool is designed to help you migrate your notes from Joplin to Obsidian in three steps:

1. **Export from Joplin**: Create an export from Joplin using the "Markdown + Front Matter" format
2. **Process with this tool**: Run this migration tool against your Joplin export to clean and reorganize the files
3. **Import to Obsidian**: Import the processed files into your Obsidian vault

## ⚠️ Important Disclaimer

**This tool modifies your files and directories!** Always create a backup of your data before running this tool. The changes are irreversible, and while the tool is designed to be safe, unexpected issues can occur.

## What This Tool Does

This tool processes Joplin exports and performs the following operations:

1. **Resource Organization**: Moves resources from the global `_resources` directory to local `_resources` folders next to each markdown file that references them
2. **File Cleanup**: Removes trailing underscores and spaces from file and folder names
3. **Directory Cleanup**: Removes empty `_resources` directories after processing
4. **Location Data**: By default, location data is kept as-is. Optionally use `--strip-location` to remove coordinates, or `--convert-location` to add human-readable location names while keeping coordinates

## Prerequisites

- Python 3.8 or higher
- [uv](https://docs.astral.sh/uv/) - Fast Python package installer and resolver
- A Joplin export in "Markdown + Front Matter" format

## Installation

### Install uv (if not already installed)

```bash
# macOS and Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Or with pip
pip install uv
```

### Clone the repository

```bash
git clone https://go.hugobatista.com/gh/joplin-to-obsidian.git
cd joplin-to-obsidian
```

### Optional Dependencies

The tool works without any external dependencies for basic functionality. However, if you want to use the `--convert-location` feature to convert GPS coordinates to human-readable location names, install the optional dependencies using `uv`:

```bash
uv sync
```

## Usage

### Basic Usage

Run the tool in the directory containing your Joplin export:

```bash
# Using uv (recommended)
uv run main.py

# Or with Python directly
python main.py
```

### Specify a Different Directory

```bash
uv run main.py --dir /path/to/your/joplin/export
```

### Strip Location Data

By default, the tool keeps location data (latitude, longitude, altitude) as-is. To remove this data:

```bash
uv run main.py --strip-location
```

### Convert Location Coordinates to Names

Convert GPS coordinates (latitude/longitude) to human-readable location names and add them as a `location` field. This keeps the original coordinates intact while adding a more readable location:

```bash
uv run main.py --convert-location
```

**Requirements**: This feature requires the `geopy` library (`uv pip install geopy` or `pip install geopy`)

**Example transformation**:
```yaml
# Before
---
title: My Note
latitude: 40.7128
longitude: -74.0060
altitude: 10.5
---

# After
---
title: My Note
latitude: 40.7128
longitude: -74.0060
altitude: 10.5
location: New York, New York, United States
---
```

**Note**: This process respects OpenStreetMap's usage policy with a 1 request per second rate limit, so it may take some time for large note collections.

**Statistics Output**: After processing, you'll see a detailed summary including:
```
============================================================
PROCESSING SUMMARY
============================================================
Total markdown files found: 150
Files with coordinates: 45
Files modified: 45

Location Conversion:
  - Locations added: 42
  - Failed geocoding: 3
  - API requests made: 28

Cache Performance:
  - Cache hits: 17
  - Cache misses: 28
  - Cache hit rate: 37.8%
  - API calls saved: 17
============================================================
```

### Debug Mode

Enable detailed logging for location API requests and caching to troubleshoot or monitor the conversion process:

```bash
uv run main.py --convert-location --debug
```

This will show:
- Cache hits and misses for each coordinate lookup
- API request attempts and responses
- Detailed information about each geocoding operation

### Get Help

```bash
uv run main.py --help
```

## Input Structure

Your Joplin export should have the following structure:

```
your-export-folder/
├── _resources/
│   ├── image1.png
│   ├── document.pdf
│   └── attachment.jpg
├── Note 1.md
├── Note 2.md
├── Subfolder/
│   ├── Note 3.md
│   └── Note 4.md
└── ...
```

Where:
- **Markdown files** (`.md`) contain your notes with YAML front matter
- **`_resources` directory** contains all attachments and images
- **Resource links** in markdown files point to `_resources/filename`

## Output Structure

After processing, the structure becomes:

```
your-export-folder/
├── Note 1.md
├── _resources/
│   └── image1.png
├── Note 2.md
├── _resources/
│   └── document.pdf
├── Subfolder/
│   ├── Note 3.md
│   ├── _resources/
│   │   └── attachment.jpg
│   └── Note 4.md
└── ...
```

## Processing Steps

### Step 1: Resource Migration

The tool scans all markdown files for resource references and moves the corresponding files from the global `_resources` directory to local `_resources` folders next to each markdown file.

**Supported link formats:**
- Markdown images: `![alt text](../_resources/image.png)`
- Markdown links: `[link text](../_resources/document.pdf)`
- HTML images: `<img src="../_resources/image.png" />`

**After processing:**
- `![alt text](../_resources/image.png)` → `![alt text](./_resources/image.png)`
- `[link text](../_resources/document.pdf)` → `[link text](./_resources/document.pdf)`

### Step 2: File Name Cleanup

Removes trailing underscores and spaces from files and folders while avoiding conflicts:

**Examples:**
- `My Note_.md` → `My Note.md`
- `Folder Name_ /` → `Folder Name/`
- `Document   .pdf` → `Document.pdf`

### Step 3: Directory Cleanup

Removes empty `_resources` directories that no longer contain any files after the migration.

### Step 4: Location Data Processing

By default, location data is kept as-is. You can optionally use flags to process this data:

**Default behavior (keeps coordinates):**

Before:
```yaml
---
title: My Note
created: 2023-01-01T10:00:00.000Z
latitude: 40.7128
longitude: -74.0060
altitude: 10.5
---
```

After:
```yaml
---
title: My Note
created: 2023-01-01T10:00:00.000Z
latitude: 40.7128
longitude: -74.0060
altitude: 10.5
---
```

**With `--strip-location` flag (removes all coordinates):**

Before:
```yaml
---
title: My Note
created: 2023-01-01T10:00:00.000Z
latitude: 40.7128
longitude: -74.0060
altitude: 10.5
---
```

After:
```yaml
---
title: My Note
created: 2023-01-01T10:00:00.000Z
---
```

**With `--convert-location` flag (adds location field, keeps coordinates):**

Before:
```yaml
---
title: My Note
created: 2023-01-01T10:00:00.000Z
latitude: 40.7128
longitude: -74.0060
altitude: 10.5
---
```

After:
```yaml
---
title: My Note
created: 2023-01-01T10:00:00.000Z
latitude: 40.7128
longitude: -74.0060
altitude: 10.5
location: New York, New York, United States
---
```

## Examples

### Example 1: Basic Migration (Keep Location Data)

```bash
# Navigate to your Joplin export directory
cd ~/Downloads/joplin-export

# Run the migration tool (keeps location data by default)
uv run /path/to/joplin-to-obsidian/main.py

# The tool will show what it will do and ask for confirmation
```

### Example 2: Remove Location Data

```bash
# Process and strip location coordinates
uv run main.py --dir ~/Documents/my-joplin-notes --strip-location

# This will remove latitude, longitude, and altitude from all notes
```

### Example 3: Convert Coordinates to Location Names

```bash
# Add human-readable location names while keeping coordinates
# Make sure you have geopy installed first: uv pip install geopy
uv run main.py --dir ~/Documents/my-joplin-notes --convert-location

# This will add a location field like "New York, New York, United States"
# while keeping the original latitude/longitude coordinates
```

### Example 4: Batch Processing

```bash
# You can process multiple exports by running the tool multiple times
for dir in ~/Downloads/joplin-export-*; do
    echo "Processing $dir"
    uv run main.py --dir "$dir"
done
```

## Troubleshooting

### Common Issues

1. **"Resource not found" errors**: This happens when markdown files reference resources that don't exist in the `_resources` directory. The tool will skip these references and continue processing.

2. **Permission errors**: Make sure you have write permissions for the directory and all its contents.

3. **File conflicts**: If the cleanup process would create duplicate names, the tool automatically appends numbers to avoid conflicts.

### Validation

After running the tool, verify that:
- All your markdown files still open correctly
- Images and attachments are still accessible
- No important data was lost (this is why backups are crucial!)

## Technical Details

- **Language**: Python 3.8+
- **Package Manager**: [uv](https://docs.astral.sh/uv/)
- **Core Dependencies**: None (uses only standard library)
- **Optional Dependencies**: geopy (for `--convert-location` feature)
- **File Encoding**: UTF-8
- **Supported Platforms**: Cross-platform (Windows, macOS, Linux)

## Contributing

Issues and pull requests are welcome! Please feel free to contribute improvements or report bugs.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

**Remember**: Always backup your data before using this tool!
