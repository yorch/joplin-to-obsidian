import os
import sys
import argparse
from moveresources import move_resources
from cleanup import (
    remove_trailing_underscores,
    remove_empty_resources_dirs,
    process_location_frontmatter,
)
from utils import Colors, print_status, print_error, print_step

# Operations that will be performed (base operations, location handling depends on flags)
OPERATIONS = [
    "Move resources from _resources directory to _resources folders next to markdown files",
    "Remove trailing underscores and spaces from files and folders",
    "Remove empty _resources directories",
]


def main():
    parser = argparse.ArgumentParser(
        description="Process Obsidian vault migration and cleanup.",
        epilog=f"""
This script processes a Joplin notebook export in markdown + front matter format.

The target directory should contain:
- Markdown files (.md) exported from Joplin
- A '_resources' directory with attachments/images
- YAML front matter in markdown files (if applicable)

This script will perform the following operations:
{chr(10).join(f"{i + 1}. {op}" for i, op in enumerate(OPERATIONS))}

Use --help to see this message.
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--dir",
        default=os.getcwd(),
        help="The root directory of the Obsidian vault (default: current directory)",
    )
    parser.add_argument(
        "--strip-location",
        action="store_true",
        help="Remove location data (latitude, longitude, altitude) from YAML front matter",
    )
    parser.add_argument(
        "--convert-location",
        action="store_true",
        help="Convert latitude/longitude to human-readable location names and add as 'location' field (keeps coordinates, requires geopy: pip install geopy)",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug output for location API requests and caching",
    )
    parser.add_argument(
        "--add-source",
        action="store_true",
        help="Add 'source: Joplin' field to YAML front matter of all notes",
    )
    args = parser.parse_args()

    if not os.path.exists(args.dir):
        print_error(f"Error: Directory does not exist: {args.dir}")
        return 1

    # Validate flag combinations
    if args.strip_location and args.convert_location:
        print_error(
            "Error: --strip-location and --convert-location cannot be used together"
        )
        print_error("  --strip-location: removes all coordinate data")
        print_error(
            "  --convert-location: adds human-readable location field while keeping coordinates"
        )
        return 1

    # Show what will be done and ask for confirmation
    print(f"{Colors.YELLOW}Obsidian Vault Migration and Cleanup Tool{Colors.RESET}")
    print("=" * 50)
    print(f"Target directory: {Colors.BLUE}{args.dir}{Colors.RESET}")
    print(
        f"\n{Colors.YELLOW}Expected input:{Colors.RESET} Joplin notebook export in markdown + front matter format"
    )
    print("The directory should contain:")
    print("  - Markdown files (.md) exported from Joplin")
    print("  - A '_resources' directory with attachments/images")
    print("  - YAML front matter in markdown files (if applicable)")
    print("\nThis script will perform the following operations:")

    # Show operations, adjusting for flags
    operations_to_show = OPERATIONS.copy()
    if args.strip_location:
        operations_to_show.append(
            "Remove location data (latitude, longitude, altitude) from YAML front matter"
        )
    elif args.convert_location:
        operations_to_show.append(
            "Add human-readable location names from coordinates (keeping original coordinates)"
        )

    if args.add_source:
        operations_to_show.append("Add 'source: Joplin' field to YAML front matter")

    for i, operation in enumerate(operations_to_show, 1):
        print(f"{i}. {operation}")
    print(
        f"\n{Colors.YELLOW}Warning: This script will modify files and directories!{Colors.RESET}"
    )

    try:
        response = input("\nDo you want to continue? (y/N): ").strip().lower()
        if response not in ["y", "yes"]:
            print("Operation cancelled.")
            return 0
    except KeyboardInterrupt:
        print("\nOperation cancelled.")
        return 0

    print_status(f"Starting vault processing in: {args.dir}")

    # Step 1: Move Resources
    print_step(1, "Moving resources to _resources folders")
    try:
        move_resources(args.dir)
        print("Done!")
    except Exception as e:
        print_error(f"Error during resource movement: {e}")
        return 1

    # Step 2: Remove trailing underscores and spaces
    print_step(2, "Removing trailing underscores and spaces from files and folders")
    try:
        remove_trailing_underscores(args.dir)
        print("Done!")
    except Exception as e:
        print_error(f"Error during underscore cleanup: {e}")
        return 1

    # Step 3: Remove empty _resources directories
    print_step(3, "Removing empty _resources directories")
    try:
        removed_dirs = remove_empty_resources_dirs(args.dir)
        print(f"Removed {len(removed_dirs)} empty _resources directories")
    except Exception as e:
        print_error(f"Error during empty directory cleanup: {e}")
        return 1

    # Step 4: Process location data and source in YAML front matter (optional)
    if args.strip_location or args.convert_location or args.add_source:
        step_descriptions = []
        if args.convert_location:
            step_descriptions.append(
                "adding human-readable location names (keeping coordinates)"
            )
        if args.strip_location:
            step_descriptions.append("removing location data")
        if args.add_source:
            step_descriptions.append("adding source field")

        step_title = "Processing YAML front matter: " + ", ".join(step_descriptions)
        print_step(4, step_title)

        if args.convert_location:
            print(
                "Note: This may take a while due to API rate limits (1 request/second)"
            )
            if args.debug:
                print_status(
                    "[DEBUG] Debug mode enabled - detailed API request logging active"
                )

        try:
            processed_files = process_location_frontmatter(
                args.dir,
                convert_to_location=args.convert_location,
                strip_coordinates=args.strip_location,
                add_source=args.add_source,
                debug=args.debug,
            )
            print(f"\nProcessed {len(processed_files)} markdown files")
        except Exception as e:
            print_error(f"Error during frontmatter processing: {e}")
            return 1
    else:
        print(
            "\nNo front matter changes requested (use --strip-location, --convert-location, or --add-source)"
        )

    print(f"\n{Colors.GREEN}All operations completed successfully!{Colors.RESET}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
