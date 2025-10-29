import os
import re
import time
from utils import print_status, print_error

# Try to import geopy for reverse geocoding
try:
    from geopy.geocoders import Nominatim
    from geopy.exc import GeocoderTimedOut, GeocoderServiceError

    GEOPY_AVAILABLE = True
except ImportError:
    GEOPY_AVAILABLE = False


def remove_trailing_underscores(directory):
    """Remove trailing underscores and spaces from all files and folders in the directory tree."""
    # Process files and directories from deepest to shallowest to avoid path conflicts
    for root, dirs, files in os.walk(directory, topdown=False):
        # Rename files first
        for file in files:
            # Split filename and extension
            name, ext = os.path.splitext(file)

            # Check if the name part ends with underscores or spaces and has other characters
            if (name.endswith("_") or name.endswith(" ")) and not re.match(
                r"^[_ ]+$", name
            ):
                old_path = os.path.join(root, file)
                new_name = name.rstrip("_ ") + ext
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
            if (dir_name.endswith("_") or dir_name.endswith(" ")) and not re.match(
                r"^[_ ]+$", dir_name
            ):
                old_path = os.path.join(root, dir_name)
                new_name = dir_name.rstrip("_ ")
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
            if dir_name == "_resources":
                dir_path = os.path.join(root, dir_name)
                try:
                    # Check if directory is empty
                    if not os.listdir(dir_path):
                        print_status(f"Removing empty _resources directory: {dir_path}")
                        os.rmdir(dir_path)
                        removed_dirs.append(dir_path)
                    else:
                        print_status(
                            f"_resources directory not empty, skipping: {dir_path}"
                        )
                        # List contents for user information
                        contents = os.listdir(dir_path)
                        print_status(f"  Contents: {contents}")
                except OSError as e:
                    print_error(f"Error checking/removing directory {dir_path}: {e}")

    return removed_dirs


def get_location_name(
    latitude, longitude, geolocator=None, cache=None, max_retries=3, debug=False
):
    """
    Convert latitude and longitude to a human-readable location name.
    Returns the most specific location available (city, town, village, or region).
    Uses caching to avoid redundant API calls for the same coordinates.

    Args:
        latitude: Latitude coordinate
        longitude: Longitude coordinate
        geolocator: Optional pre-initialized Nominatim geolocator instance
        cache: Optional dictionary to cache results (coordinates tuple -> location name)
        max_retries: Number of retry attempts for timeouts (default: 3)
        debug: If True, print debug messages for API requests (default: False)

    Returns:
        String with location name (e.g., "New York, New York, United States") or None if failed
    """
    if not GEOPY_AVAILABLE:
        return None

    # Round coordinates to reduce cache misses from minor differences
    # 5 decimal places = ~1.1 meter precision, good enough for city-level lookup
    coord_key = (round(latitude, 5), round(longitude, 5))

    # Check cache first
    if cache is not None and coord_key in cache:
        if debug:
            cached_value = cache[coord_key]
            if cached_value:
                print_status(
                    f"[DEBUG] Cache HIT for ({latitude}, {longitude}) -> {cached_value}"
                )
            else:
                print_status(
                    f"[DEBUG] Cache HIT for ({latitude}, {longitude}) -> (no location found)"
                )
        return cache[coord_key]

    try:
        # Use provided geolocator or create new one
        if geolocator is None:
            geolocator = Nominatim(user_agent="joplin-to-obsidian-converter")

        # Retry logic for handling timeouts
        for attempt in range(max_retries):
            try:
                # Respect Nominatim's usage policy: max 1 request per second
                time.sleep(1)

                if debug:
                    print_status(
                        f"[DEBUG] Making API request for ({latitude}, {longitude}) - Attempt {attempt + 1}/{max_retries}"
                    )

                location = geolocator.reverse(
                    f"{latitude}, {longitude}", language="en", timeout=10
                )

                if debug:
                    if location:
                        print_status(
                            f"[DEBUG] API response received for ({latitude}, {longitude})"
                        )
                    else:
                        print_status(
                            f"[DEBUG] API returned no location for ({latitude}, {longitude})"
                        )

                if location and location.raw.get("address"):
                    address = location.raw["address"]

                    # Try to get the most specific location in order of preference
                    location_parts = []

                    # City, town, or village
                    if "city" in address:
                        location_parts.append(address["city"])
                    elif "town" in address:
                        location_parts.append(address["town"])
                    elif "village" in address:
                        location_parts.append(address["village"])
                    elif "hamlet" in address:
                        location_parts.append(address["hamlet"])
                    elif "municipality" in address:
                        location_parts.append(address["municipality"])

                    # State/Region
                    if "state" in address:
                        location_parts.append(address["state"])
                    elif "region" in address:
                        location_parts.append(address["region"])

                    # Country
                    if "country" in address:
                        location_parts.append(address["country"])

                    if location_parts:
                        result = ", ".join(location_parts)
                        # Cache the successful result
                        if cache is not None:
                            cache[coord_key] = result
                        return result

                # Cache the None result to avoid retrying failed lookups
                if cache is not None:
                    cache[coord_key] = None
                return None

            except GeocoderTimedOut:
                if attempt < max_retries - 1:
                    print_status(
                        f"Geocoding timeout for ({latitude}, {longitude}), retrying... (attempt {attempt + 2}/{max_retries})"
                    )
                    time.sleep(2)  # Wait a bit longer before retry
                else:
                    print_error(
                        f"Geocoding timeout for ({latitude}, {longitude}) after {max_retries} attempts"
                    )
                    return None
            except GeocoderServiceError as e:
                print_error(
                    f"Geocoding service error for ({latitude}, {longitude}): {e}"
                )
                return None

    except Exception as e:
        print_error(f"Error during geocoding: {e}")
        return None


def process_location_frontmatter(
    directory, convert_to_location=False, strip_coordinates=False, debug=False
):
    """
    Process latitude, longitude, and altitude attributes in YAML front matter.

    Args:
        directory: The directory to process
        convert_to_location: If True, convert lat/lon to a human-readable location name and add as 'location' field.
                           Keeps the original coordinates intact.
        strip_coordinates: If True, remove all coordinate data (latitude, longitude, altitude).
                          Cannot be used together with convert_to_location.
        debug: If True, print debug messages for API requests and caching (default: False)

    Returns:
        List of file paths that were processed/modified
    """
    if convert_to_location and strip_coordinates:
        print_error("convert_to_location and strip_coordinates cannot both be True")
        return []

    if convert_to_location and not GEOPY_AVAILABLE:
        print_error("geopy library not installed. Install with: pip install geopy")
        print("Cannot convert location data without geopy")
        return []

    processed_files = []

    # Initialize geocoder and cache once if we're converting locations
    geolocator = None
    location_cache = {}
    cache_hits = 0
    cache_misses = 0

    # Statistics tracking
    stats = {
        "total_markdown_files": 0,
        "files_with_coordinates": 0,
        "files_processed": 0,
        "locations_added": 0,
        "coordinates_stripped": 0,
        "api_requests": 0,
        "failed_geocoding": 0,
    }

    if convert_to_location:
        geolocator = Nominatim(user_agent="joplin-to-obsidian-converter")
        print_status("Initializing location cache for coordinate lookups")

    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.lower().endswith((".md", ".markdown")):
                stats["total_markdown_files"] += 1
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()

                    # Check if file has YAML front matter
                    if content.startswith("---\n"):
                        # Split content into front matter and body
                        parts = content.split("---\n", 2)
                        if len(parts) >= 3:
                            front_matter = parts[1]
                            body = parts[2]

                            # Store original for comparison
                            original_front_matter = front_matter

                            # Extract latitude and longitude if we need to convert
                            latitude = None
                            longitude = None

                            if convert_to_location:
                                lat_match = re.search(
                                    r"^latitude:\s*([-+]?[0-9]*\.?[0-9]+)\s*$",
                                    front_matter,
                                    re.MULTILINE,
                                )
                                lon_match = re.search(
                                    r"^longitude:\s*([-+]?[0-9]*\.?[0-9]+)\s*$",
                                    front_matter,
                                    re.MULTILINE,
                                )

                                if lat_match and lon_match:
                                    stats["files_with_coordinates"] += 1
                                    latitude = float(lat_match.group(1))
                                    longitude = float(lon_match.group(1))

                                    # Check if this coordinate is already cached
                                    coord_key = (
                                        round(latitude, 5),
                                        round(longitude, 5),
                                    )
                                    was_cached = coord_key in location_cache

                                    # Get location name from coordinates (uses cache internally)
                                    location_name = get_location_name(
                                        latitude,
                                        longitude,
                                        geolocator,
                                        location_cache,
                                        debug=debug,
                                    )

                                    # Track cache statistics
                                    if was_cached:
                                        cache_hits += 1
                                    else:
                                        cache_misses += 1
                                        stats["api_requests"] += 1

                                    if location_name:
                                        # Check if location field already exists
                                        if not re.search(
                                            r"^location:", front_matter, re.MULTILINE
                                        ):
                                            # Add location field (keep coordinates intact)
                                            front_matter += (
                                                f"\nlocation: {location_name}\n"
                                            )
                                            stats["locations_added"] += 1
                                            print_status(
                                                f"Added location: {location_name} to {file_path}"
                                            )
                                        else:
                                            print_status(
                                                f"Location field already exists in {file_path}, skipping"
                                            )
                                    else:
                                        stats["failed_geocoding"] += 1
                                        print_status(
                                            f"Could not geocode coordinates in {file_path}"
                                        )

                            # Strip coordinates if requested (and not converting)
                            if strip_coordinates and not convert_to_location:
                                # Check if file has coordinates before stripping
                                has_coords = bool(
                                    re.search(
                                        r"^(latitude|longitude|altitude):",
                                        front_matter,
                                        re.MULTILINE,
                                    )
                                )

                                # Remove latitude, longitude, altitude lines
                                front_matter = re.sub(
                                    r"^latitude:\s*[-+]?[0-9]*\.?[0-9]+\s*$",
                                    "",
                                    front_matter,
                                    flags=re.MULTILINE,
                                )
                                front_matter = re.sub(
                                    r"^longitude:\s*[-+]?[0-9]*\.?[0-9]+\s*$",
                                    "",
                                    front_matter,
                                    flags=re.MULTILINE,
                                )
                                front_matter = re.sub(
                                    r"^altitude:\s*[-+]?[0-9]*\.?[0-9]+\s*$",
                                    "",
                                    front_matter,
                                    flags=re.MULTILINE,
                                )

                                if has_coords:
                                    stats["coordinates_stripped"] += 1

                            # Clean up multiple consecutive newlines
                            front_matter = re.sub(r"\n\n+", "\n\n", front_matter)
                            front_matter = front_matter.strip()

                            # Only write if changes were made
                            if front_matter != original_front_matter:
                                stats["files_processed"] += 1

                                # Reconstruct the file content
                                if front_matter:
                                    new_content = f"---\n{front_matter}\n---\n{body}"
                                else:
                                    # If front matter is empty, remove it entirely
                                    new_content = body

                                with open(file_path, "w", encoding="utf-8") as f:
                                    f.write(new_content)

                                # Provide accurate message based on operation performed
                                if convert_to_location:
                                    print_status(
                                        f"Added location field to: {file_path}"
                                    )
                                elif strip_coordinates:
                                    print_status(
                                        f"Removed location data from: {file_path}"
                                    )
                                processed_files.append(file_path)

                except Exception as e:
                    print_error(f"Error processing file {file_path}: {e}")

    # Print statistics summary (using print instead of print_status to avoid overwriting)
    print("\n")  # Clear the current line and add newline
    print("=" * 60)
    print("PROCESSING SUMMARY")
    print("=" * 60)
    print(f"Total markdown files found: {stats['total_markdown_files']}")
    print(f"Files with coordinates: {stats['files_with_coordinates']}")
    print(f"Files modified: {stats['files_processed']}")

    if convert_to_location:
        print("\nLocation Conversion:")
        print(f"  - Locations added: {stats['locations_added']}")
        print(f"  - Failed geocoding: {stats['failed_geocoding']}")
        print(f"  - API requests made: {stats['api_requests']}")

        if cache_hits > 0 or cache_misses > 0:
            total_lookups = cache_hits + cache_misses
            cache_rate = (cache_hits / total_lookups * 100) if total_lookups > 0 else 0
            print("\nCache Performance:")
            print(f"  - Cache hits: {cache_hits}")
            print(f"  - Cache misses: {cache_misses}")
            print(f"  - Cache hit rate: {cache_rate:.1f}%")
            print(f"  - API calls saved: {cache_hits}")

    if strip_coordinates:
        print("\nCoordinate Removal:")
        print(f"  - Files with coordinates stripped: {stats['coordinates_stripped']}")

    print("=" * 60)

    return processed_files
