import math
import time
import requests


# ============================================================
# CONFIGURATION
# ============================================================

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"

OVERPASS_ENDPOINTS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://overpass.private.coffee/api/interpreter",
]

USER_AGENT = (
    "HealthAccessVoiceAgent/1.0 "
    "(educational project)"
)

REQUEST_TIMEOUT = 20


# ============================================================
# DISTANCE
# ============================================================

def calculate_distance(lat1, lon1, lat2, lon2):
    """
    Calculate distance between two coordinates in kilometers.
    """

    earth_radius = 6371.0

    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)

    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)

    a = (
        math.sin(delta_lat / 2) ** 2
        + math.cos(lat1_rad)
        * math.cos(lat2_rad)
        * math.sin(delta_lon / 2) ** 2
    )

    c = 2 * math.atan2(
        math.sqrt(a),
        math.sqrt(1 - a)
    )

    return earth_radius * c


# ============================================================
# HEADERS
# ============================================================

HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": "application/json",
}


# ============================================================
# GEOCODE LOCATION
# ============================================================

def geocode_location(location: str):

    location = location.strip()

    if not location:
        return None

    # --------------------------------------------------------
    # Try the exact user input first
    # --------------------------------------------------------

    queries = [
        location,
        f"{location}, India",
    ]

    for query in queries:

        try:

            print(
                f"[FACILITY] Geocoding: {query}"
            )

            response = requests.get(
                NOMINATIM_URL,
                params={
                    "q": query,
                    "format": "jsonv2",
                    "limit": 5,
                    "addressdetails": 1,
                    "countrycodes": "in",
                },
                headers=HEADERS,
                timeout=REQUEST_TIMEOUT,
            )

            response.raise_for_status()

            results = response.json()

            if not results:
                continue

            # ------------------------------------------------
            # Prefer results that look like a locality/city
            # ------------------------------------------------

            preferred = None

            for result in results:

                result_type = result.get(
                    "type",
                    ""
                )

                result_class = result.get(
                    "class",
                    ""
                )

                if (
                    result_type in {
                        "city",
                        "town",
                        "village",
                        "suburb",
                        "neighbourhood",
                        "administrative",
                        "residential",
                    }
                    or result_class == "place"
                ):
                    preferred = result
                    break

            if preferred is None:
                preferred = results[0]

            latitude = float(
                preferred["lat"]
            )

            longitude = float(
                preferred["lon"]
            )

            display_name = preferred.get(
                "display_name",
                query,
            )

            print(
                "[FACILITY] Location resolved:"
                f" {display_name}"
            )

            print(
                "[FACILITY] Coordinates:"
                f" {latitude}, {longitude}"
            )

            return {
                "latitude": latitude,
                "longitude": longitude,
                "display_name": display_name,
            }

        except requests.exceptions.RequestException as error:

            print(
                f"[FACILITY] Geocoding error: {error}"
            )

        except Exception as error:

            print(
                f"[FACILITY] Geocoding unexpected error: {error}"
            )

    return None


# ============================================================
# OVERPASS QUERY
# ============================================================

def build_overpass_query(
    latitude,
    longitude,
    radius,
):

    return f"""
[out:json][timeout:45];

(
    nwr["amenity"="hospital"](around:{radius},{latitude},{longitude});
    nwr["amenity"="clinic"](around:{radius},{latitude},{longitude});
    nwr["amenity"="doctors"](around:{radius},{latitude},{longitude});

    nwr["healthcare"="hospital"](around:{radius},{latitude},{longitude});
    nwr["healthcare"="clinic"](around:{radius},{latitude},{longitude});
    nwr["healthcare"="doctor"](around:{radius},{latitude},{longitude});
    nwr["healthcare"="centre"](around:{radius},{latitude},{longitude});
    nwr["healthcare"="hospital_ward"](around:{radius},{latitude},{longitude});

    nwr["healthcare"="pharmacy"](around:{radius},{latitude},{longitude});
);

out center tags;
"""


# ============================================================
# QUERY OVERPASS
# ============================================================

def query_overpass(
    latitude,
    longitude,
    radius,
):

    query = build_overpass_query(
        latitude,
        longitude,
        radius,
    )

    for endpoint in OVERPASS_ENDPOINTS:

        try:

            print(
                "[FACILITY] Trying Overpass:"
                f" {endpoint}"
            )

            response = requests.post(
                endpoint,
                data=query,
                headers={
                    "User-Agent": USER_AGENT,
                    "Content-Type": "text/plain",
                },
                timeout=60,
            )

            response.raise_for_status()

            data = response.json()

            elements = data.get(
                "elements",
                [],
            )

            print(
                "[FACILITY] Overpass returned"
                f" {len(elements)} elements."
            )

            return elements

        except requests.exceptions.RequestException as error:

            print(
                "[FACILITY] Overpass endpoint failed:"
                f" {error}"
            )

            continue

        except Exception as error:

            print(
                "[FACILITY] Overpass parsing error:"
                f" {error}"
            )

            continue

    return []


# ============================================================
# FACILITY TYPE
# ============================================================

def get_facility_type(tags):

    healthcare = tags.get(
        "healthcare",
        "",
    ).lower()

    amenity = tags.get(
        "amenity",
        "",
    ).lower()

    mapping = {
        "hospital": "Hospital",
        "clinic": "Clinic",
        "doctor": "Doctor / Clinic",
        "doctors": "Doctor / Clinic",
        "centre": "Healthcare Centre",
        "hospital_ward": "Hospital",
        "pharmacy": "Pharmacy",
    }

    if healthcare in mapping:
        return mapping[healthcare]

    if amenity in mapping:
        return mapping[amenity]

    return "Healthcare Facility"


# ============================================================
# GET FACILITY COORDINATES
# ============================================================

def get_element_coordinates(element):

    # --------------------------------------------------------
    # Node
    # --------------------------------------------------------

    if (
        "lat" in element
        and "lon" in element
    ):

        return (
            float(element["lat"]),
            float(element["lon"]),
        )

    # --------------------------------------------------------
    # Way / Relation center
    # --------------------------------------------------------

    center = element.get(
        "center"
    )

    if center:

        if (
            "lat" in center
            and "lon" in center
        ):

            return (
                float(center["lat"]),
                float(center["lon"]),
            )

    return None


# ============================================================
# BUILD ADDRESS
# ============================================================

def build_address(tags):

    address_parts = []

    keys = [
        "addr:housenumber",
        "addr:street",
        "addr:neighbourhood",
        "addr:suburb",
        "addr:city",
        "addr:district",
        "addr:state",
        "addr:postcode",
    ]

    for key in keys:

        value = tags.get(key)

        if value:

            value = str(value).strip()

            if value:
                address_parts.append(
                    value
                )

    return ", ".join(
        address_parts
    )


# ============================================================
# BUILD FACILITY
# ============================================================

def build_facility(
    element,
    user_lat,
    user_lon,
):

    tags = element.get(
        "tags",
        {},
    )

    # --------------------------------------------------------
    # Name
    # --------------------------------------------------------

    name = (
        tags.get("name")
        or tags.get("official_name")
        or tags.get("short_name")
        or tags.get("brand")
    )

    if not name:
        return None

    name = name.strip()

    # --------------------------------------------------------
    # Coordinates
    # --------------------------------------------------------

    coordinates = get_element_coordinates(
        element
    )

    if coordinates is None:
        return None

    facility_lat, facility_lon = coordinates

    # --------------------------------------------------------
    # Distance
    # --------------------------------------------------------

    distance = calculate_distance(
        user_lat,
        user_lon,
        facility_lat,
        facility_lon,
    )

    # --------------------------------------------------------
    # Contact
    # --------------------------------------------------------

    phone = (
        tags.get("phone")
        or tags.get("contact:phone")
        or ""
    )

    website = (
        tags.get("website")
        or tags.get("contact:website")
        or ""
    )

    opening_hours = tags.get(
        "opening_hours",
        "",
    )

    # --------------------------------------------------------
    # Address
    # --------------------------------------------------------

    address = build_address(
        tags
    )

    # --------------------------------------------------------
    # Type
    # --------------------------------------------------------

    facility_type = get_facility_type(
        tags
    )

    return {
        "name": name,
        "type": facility_type,
        "distance_km": round(
            distance,
            2,
        ),
        "latitude": facility_lat,
        "longitude": facility_lon,
        "address": address,
        "phone": phone,
        "website": website,
        "opening_hours": opening_hours,
    }


# ============================================================
# FIND NEAREST HEALTHCARE FACILITIES
# ============================================================

def find_nearest_facility(
    location: str,
):

    location = (
        location or ""
    ).strip()

    if not location:

        return {
            "found": False,
            "error": "missing_location",
            "message": (
                "Please provide a city, area, "
                "locality, or PIN code."
            ),
        }

    print(
        "================================================"
    )

    print(
        "[FACILITY] SEARCH STARTED"
    )

    print(
        f"[FACILITY] User location: {location}"
    )

    print(
        "================================================"
    )

    # ========================================================
    # STEP 1 — GEOCODE
    # ========================================================

    location_data = geocode_location(
        location
    )

    if location_data is None:

        print(
            "[FACILITY] Could not geocode location."
        )

        return {
            "found": False,
            "error": "location_not_found",
            "message": (
                f"I couldn't identify '{location}'. "
                "Please tell me your city, area, "
                "locality, or PIN code."
            ),
        }

    latitude = location_data[
        "latitude"
    ]

    longitude = location_data[
        "longitude"
    ]

    display_name = location_data[
        "display_name"
    ]

    # ========================================================
    # STEP 2 — PROGRESSIVE SEARCH
    # ========================================================

    # Start small.
    # If nothing is found, expand.

    search_radii = [
        5000,
        10000,
        20000,
    ]

    elements = []

    used_radius = None

    for radius in search_radii:

        print(
            "[FACILITY] Searching radius:"
            f" {radius / 1000:.0f} km"
        )

        elements = query_overpass(
            latitude,
            longitude,
            radius,
        )

        if elements:

            used_radius = radius

            print(
                "[FACILITY] Facilities found "
                f"within {radius / 1000:.0f} km."
            )

            break

        print(
            "[FACILITY] No facilities in "
            f"{radius / 1000:.0f} km."
        )

        # Small delay before retry
        time.sleep(0.5)

    # ========================================================
    # STEP 3 — PROCESS
    # ========================================================

    facilities = []

    seen = set()

    for element in elements:

        facility = build_facility(
            element,
            latitude,
            longitude,
        )

        if facility is None:
            continue

        # ----------------------------------------------------
        # Deduplicate by name + coordinates
        # ----------------------------------------------------

        key = (
            facility["name"].lower().strip(),
            round(facility["latitude"], 5),
            round(facility["longitude"], 5),
        )

        if key in seen:
            continue

        seen.add(key)

        facilities.append(
            facility
        )

    # ========================================================
    # STEP 4 — SORT
    # ========================================================

    facilities.sort(
        key=lambda item:
        item["distance_km"]
    )

    # ========================================================
    # STEP 5 — NO RESULTS
    # ========================================================

    if not facilities:

        print(
            "[FACILITY] No healthcare facilities found."
        )

        return {
            "found": False,
            "location": location,
            "resolved_location": display_name,
            "error": "no_facilities",
            "message": (
                "I couldn't find any mapped healthcare "
                "facilities near this location. "
                "You can try a nearby larger locality "
                "or city."
            ),
            "data_source": (
                "OpenStreetMap / Overpass"
            ),
        }

    # ========================================================
    # STEP 6 — TOP 5
    # ========================================================

    top_facilities = facilities[:5]

    print(
        "================================================"
    )

    print(
        f"[FACILITY] TOTAL FOUND: {len(facilities)}"
    )

    print(
        "[FACILITY] CLOSEST FACILITIES:"
    )

    for index, facility in enumerate(
        top_facilities,
        start=1,
    ):

        print(
            f"{index}. "
            f"{facility['name']} | "
            f"{facility['type']} | "
            f"{facility['distance_km']} km"
        )

    print(
        "================================================"
    )

    # ========================================================
    # STEP 7 — RETURN STRUCTURED RESPONSE
    # ========================================================

    return {
        "found": True,
        "location": location,
        "resolved_location": display_name,
        "search_radius_km": (
            used_radius / 1000
            if used_radius
            else None
        ),
        "count": len(
            top_facilities
        ),
        "facilities": top_facilities,
        "data_source": (
            "OpenStreetMap / Overpass"
        ),
        "message": (
            f"I found {len(top_facilities)} "
            "healthcare facilities near "
            f"{location}."
        ),
    }
