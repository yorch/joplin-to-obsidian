import os
import sys
import argparse
from moveresources import move_resources
from cleanup import (
    remove_trailing_underscores,
    remove_empty_resources_dirs,
    remove_location_frontmatter
)
from utils import Colors, print_status, print_error, print_step

# Operations that will be performed
OPERATIONS = [
    "Move resources from _resources directory to _resources folders next to markdown files",
    "Remove trailing underscores and spaces from files and folders",
    "Remove empty _resources directories",
    "Remove location data (latitude, longitude, altitude) from YAML front matter"
]

def main():
    parser = argparse.ArgumentParser(
        description='Process Obsidian vault migration and cleanup.',
        epilog=f"""
This script processes a Joplin notebook export in markdown + front matter format.

The target directory should contain:
- Markdown files (.md) exported from Joplin
- A '_resources' directory with attachments/images
- YAML front matter in markdown files (if applicable)

This script will perform the following operations:
{chr(10).join(f"{i+1}. {op}" for i, op in enumerate(OPERATIONS))}

Use --help to see this message.
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument('--dir', default=os.getcwd(),
                      help='The root directory of the Obsidian vault (default: current directory)')
    args = parser.parse_args()
    
    if not os.path.exists(args.dir):
        print_error(f"Error: Directory does not exist: {args.dir}")
        return 1
    
    # Show what will be done and ask for confirmation
    print(f"{Colors.YELLOW}Obsidian Vault Migration and Cleanup Tool{Colors.RESET}")
    print("=" * 50)
    print(f"Target directory: {Colors.BLUE}{args.dir}{Colors.RESET}")
    print(f"\n{Colors.YELLOW}Expected input:{Colors.RESET} Joplin notebook export in markdown + front matter format")
    print("The directory should contain:")
    print("  - Markdown files (.md) exported from Joplin")
    print("  - A '_resources' directory with attachments/images")
    print("  - YAML front matter in markdown files (if applicable)")
    print("\nThis script will perform the following operations:")
    for i, operation in enumerate(OPERATIONS, 1):
        print(f"{i}. {operation}")
    print(f"\n{Colors.YELLOW}Warning: This script will modify files and directories!{Colors.RESET}")
    
    try:
        response = input("\nDo you want to continue? (y/N): ").strip().lower()
        if response not in ['y', 'yes']:
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
    except Exception as e:
        print_error(f"Error during resource movement: {e}")
        return 1
    
    # Step 2: Remove trailing underscores and spaces
    print_step(2, "Removing trailing underscores and spaces from files and folders")
    try:
        remove_trailing_underscores(args.dir)
    except Exception as e:
        print_error(f"Error during underscore cleanup: {e}")
        return 1
    
    # Step 3: Remove empty _resources directories
    print_step(3, "Removing empty _resources directories")
    try:
        removed_dirs = remove_empty_resources_dirs(args.dir)
        print_status(f"Removed {len(removed_dirs)} empty _resources directories")
    except Exception as e:
        print_error(f"Error during empty directory cleanup: {e}")
        return 1
    
    # Step 4: Remove location data from YAML front matter
    print_step(4, "Removing location data from YAML front matter")
    try:
        processed_files = remove_location_frontmatter(args.dir)
        print_status(f"Processed {len(processed_files)} markdown files")
    except Exception as e:
        print_error(f"Error during frontmatter cleanup: {e}")
        return 1
    
    print(f"\n{Colors.GREEN}All operations completed successfully!{Colors.RESET}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
