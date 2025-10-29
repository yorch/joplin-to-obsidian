import os
import re
import shutil
from urllib.parse import unquote
from utils import print_status, print_error


def move_resources(root_dir):
    """Move resources from _resources directory to _resources folders next to markdown files."""
    resources_dir = os.path.join(root_dir, "_resources")

    print(f"Starting resource migration from: {resources_dir}")

    for root, _, files in os.walk(root_dir):
        for file in files:
            if file.endswith(".md"):
                md_path = os.path.join(root, file)
                local_resources_dir = os.path.join(root, "_resources")

                with open(md_path, "r", encoding="utf-8") as f:
                    content = f.read()
                print_status(f"Processing Markdown file: {md_path}")

                # First, collect all resources that exist and all matches for replacement
                resources_to_move = {}  # Dict to store unique resources to move
                all_matches = []  # List to store all matches for link replacement

                # Match both image links ![...](.../_resources/...) and regular links [...](.../_resources/...)
                for match in re.finditer(
                    r"!?\[[^\]]*\]\((?:\.\./)*_resources/([^)]+)\)", content
                ):
                    resource = match.group(1)
                    # URL decode the resource name to handle spaces and special characters
                    decoded_resource = unquote(resource)
                    src = os.path.join(resources_dir, decoded_resource)
                    all_matches.append((match, resource, decoded_resource, "markdown"))

                    if (
                        os.path.exists(src)
                        and decoded_resource not in resources_to_move
                    ):
                        resources_to_move[decoded_resource] = src
                        print_status(f"Found resource: {decoded_resource}")
                    elif (
                        not os.path.exists(src)
                        and decoded_resource not in resources_to_move
                    ):
                        print_error(f"Resource not found: {src}")

                # Also match HTML img tags with src=".../_resources/..."
                for match in re.finditer(
                    r'<img[^>]+src="(?:\.\./)*_resources/([^"]+)"[^>]*>', content
                ):
                    resource = match.group(1)
                    # URL decode the resource name to handle spaces and special characters
                    decoded_resource = unquote(resource)
                    src = os.path.join(resources_dir, decoded_resource)
                    all_matches.append((match, resource, decoded_resource, "html"))

                    if (
                        os.path.exists(src)
                        and decoded_resource not in resources_to_move
                    ):
                        resources_to_move[decoded_resource] = src
                        print_status(f"Found resource: {decoded_resource}")
                    elif (
                        not os.path.exists(src)
                        and decoded_resource not in resources_to_move
                    ):
                        print_error(f"Resource not found: {src}")

                # Only create _resources directory if there are resources to move
                if resources_to_move:
                    if not os.path.exists(local_resources_dir):
                        os.makedirs(local_resources_dir)
                        print_status(
                            f"Created _resources directory: {local_resources_dir}"
                        )

                    # Move unique resources first
                    for resource, src in resources_to_move.items():
                        dst = os.path.join(local_resources_dir, resource)
                        print_status(f"Moving: {resource}")

                        try:
                            shutil.move(src, dst)
                            print_status(f"Moved {resource} to _resources")
                        except Exception as e:
                            print_error(
                                f"Error moving {resource} (referenced in {file}): {e}"
                            )

                    # Then update all links in the content
                    for match, resource, decoded_resource, link_type in all_matches:
                        if (
                            decoded_resource in resources_to_move
                        ):  # Only update links for successfully found resources
                            original_link = match.group(0)

                            if link_type == "html":
                                # It's an HTML img tag, replace the src attribute
                                new_link = re.sub(
                                    r'src="(?:\.\./)*_resources/[^"]*"',
                                    f'src="./_resources/{decoded_resource}"',
                                    original_link,
                                )
                            elif original_link.startswith("!["):
                                # It's a markdown image link
                                new_link = f"![](./_resources/{decoded_resource})"
                            else:
                                # It's a regular markdown link, extract the link text
                                link_text_match = re.match(
                                    r"\[([^\]]*)\]", original_link
                                )
                                if link_text_match:
                                    link_text = link_text_match.group(1)
                                    new_link = f"[{link_text}](./_resources/{decoded_resource})"
                                else:
                                    # Fallback if we can't extract link text
                                    new_link = f"[](./_resources/{decoded_resource})"

                            content = content.replace(original_link, new_link)
                            print_status(
                                f"Updated {link_type} link for {decoded_resource} in {file}"
                            )

                    # Save the updated content only if there were changes
                    with open(md_path, "w", encoding="utf-8") as f:
                        f.write(content)
                        print_status(f"Saved updated {file}")
                else:
                    print_status(f"No resources found in {file}")
