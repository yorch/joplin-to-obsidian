import os
import re
from utils import print_status, print_error

def remove_trailing_underscores(directory):
    """Remove trailing underscores and spaces from all files and folders in the directory tree."""
    # Process files and directories from deepest to shallowest to avoid path conflicts
    for root, dirs, files in os.walk(directory, topdown=False):
        # Rename files first
        for file in files:
            # Split filename and extension
            name, ext = os.path.splitext(file)
            
            # Check if the name part ends with underscores or spaces and has other characters
            if (name.endswith('_') or name.endswith(' ')) and not re.match(r'^[_ ]+$', name):
                old_path = os.path.join(root, file)
                new_name = name.rstrip('_ ') + ext
                new_path = os.path.join(root, new_name)
                
                # Avoid overwriting existing files
                counter = 1
                base_new_path = new_path
                while os.path.exists(new_path):
                    base_name, base_ext = os.path.splitext(base_new_path)
                    new_path = f"{base_name}_{counter}{base_ext}"
                    counter += 1
                
                print_status(f"Renaming file: {old_path} -> {new_path}")
                os.rename(old_path, new_path)
        
        # Rename directories
        for dir_name in dirs:
            if (dir_name.endswith('_') or dir_name.endswith(' ')) and not re.match(r'^[_ ]+$', dir_name):
                old_path = os.path.join(root, dir_name)
                new_name = dir_name.rstrip('_ ')
                new_path = os.path.join(root, new_name)
                
                # Avoid overwriting existing directories
                counter = 1
                base_new_path = new_path
                while os.path.exists(new_path):
                    new_path = f"{base_new_path}_{counter}"
                    counter += 1
                
                print_status(f"Renaming directory: {old_path} -> {new_path}")
                os.rename(old_path, new_path)

def remove_empty_resources_dirs(directory):
    """Remove empty '_resources' directories recursively."""
    removed_dirs = []
    
    # Walk from deepest to shallowest to handle nested empty directories
    for root, dirs, files in os.walk(directory, topdown=False):
        for dir_name in dirs:
            if dir_name == '_resources':
                dir_path = os.path.join(root, dir_name)
                try:
                    # Check if directory is empty
                    if not os.listdir(dir_path):
                        print_status(f"Removing empty _resources directory: {dir_path}")
                        os.rmdir(dir_path)
                        removed_dirs.append(dir_path)
                    else:
                        print_status(f"_resources directory not empty, skipping: {dir_path}")
                        # List contents for user information
                        contents = os.listdir(dir_path)
                        print_status(f"  Contents: {contents}")
                except OSError as e:
                    print_error(f"Error checking/removing directory {dir_path}: {e}")
    
    return removed_dirs

def remove_location_frontmatter(directory):
    """Remove latitude, longitude, and altitude attributes from YAML front matter in markdown files."""
    processed_files = []
    
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.lower().endswith(('.md', '.markdown')):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Check if file has YAML front matter
                    if content.startswith('---\n'):
                        # Split content into front matter and body
                        parts = content.split('---\n', 2)
                        if len(parts) >= 3:
                            front_matter = parts[1]
                            body = parts[2]
                            
                            # Remove location attributes using regex
                            original_front_matter = front_matter
                            
                            # Remove latitude, longitude, altitude lines
                            front_matter = re.sub(r'^latitude:\s*[-+]?[0-9]*\.?[0-9]+\s*$', '', front_matter, flags=re.MULTILINE)
                            front_matter = re.sub(r'^longitude:\s*[-+]?[0-9]*\.?[0-9]+\s*$', '', front_matter, flags=re.MULTILINE)
                            front_matter = re.sub(r'^altitude:\s*[-+]?[0-9]*\.?[0-9]+\s*$', '', front_matter, flags=re.MULTILINE)
                            
                            # Clean up multiple consecutive newlines
                            front_matter = re.sub(r'\n\n+', '\n\n', front_matter)
                            front_matter = front_matter.strip()
                            
                            # Only write if changes were made
                            if front_matter != original_front_matter:
                                # Reconstruct the file content
                                if front_matter:
                                    new_content = f"---\n{front_matter}\n---\n{body}"
                                else:
                                    # If front matter is empty, remove it entirely
                                    new_content = body
                                
                                with open(file_path, 'w', encoding='utf-8') as f:
                                    f.write(new_content)
                                
                                print_status(f"Removed location data from: {file_path}")
                                processed_files.append(file_path)
                
                except Exception as e:
                    print_error(f"Error processing file {file_path}: {e}")
    
    return processed_files
