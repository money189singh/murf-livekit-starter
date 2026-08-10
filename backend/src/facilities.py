import math
import requests


# ============================================================
# FREE OPENSTREETMAP APIs
# ============================================================

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"

OVERPASS_URL = "https://overpass-api.de/api/interpreter"


# ============================================================
# CALCULATE DISTANCE
# ============================================================

def calculate_distance(lat1, lon1, lat2, lon2):
    """
    Calculate distance between two coordinates in kilometers.
    """

    earth_radius = 6371

    lat1 = math.radians(lat1)
    lat2 = math.radians(lat2)

    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)

    a = (
        math.sin(delta_lat / 2) ** 2
        + math.cos(lat1)
        * math.cos(lat2)
        * math.sin(delta_lon / 2) ** 2
    )

    c = 2 * math.atan2(
        math.sqrt(a),
        math.sqrt(1 - a)
    )

    return earth_radius * c


# ============================================================
# FIND NEAREST HEALTHCARE FACILITIES
# ============================================================

def find_nearest_facility(location: str):
    """
    Find real nearby healthcare facilities using
    OpenStreetMap and Overpass API.

    This uses free public APIs and does not require
    an API key.
    """

    try:

        # ====================================================
        # STEP 1
        # Convert location into latitude/longitude
        # ====================================================

        response = requests.get(
            NOMINATIM_URL,
            params={
                "q": location,
                "format": "jsonv2",
                "limit": 1,
                "countrycodes": "in",
            },
            headers={
                "User-Agent": (
                    "HealthcareVoiceAgent/1.0 "
                    "(educational project)"
                )
            },
            timeout=10,
        )

        response.raise_for_status()

        locations = response.json()

        if not locations:

            return {
                "found": False,
                "message": (
                    f"I couldn't find the location "
                    f"{location}."
                ),
            }

        latitude = float(
            locations[0]["lat"]
        )

        longitude = float(
            locations[0]["lon"]
        )

        logger_message = (
            f"Location found: {location} "
            f"({latitude}, {longitude})"
        )

        print(logger_message)

        # ====================================================
        # STEP 2
        # Search OpenStreetMap for healthcare facilities
        # within 5 KM
        # ====================================================

        query = f"""
[out:json][timeout:20];

(
  node["amenity"="hospital"](around:5000,{latitude},{longitude});
  way["amenity"="hospital"](around:5000,{latitude},{longitude});
  relation["amenity"="hospital"](around:5000,{latitude},{longitude});

  node["amenity"="clinic"](around:5000,{latitude},{longitude});
  way["amenity"="clinic"](around:5000,{latitude},{longitude});
  relation["amenity"="clinic"](around:5000,{latitude},{longitude});

  node["amenity"="doctors"](around:5000,{latitude},{longitude});
  way["amenity"="doctors"](around:5000,{latitude},{longitude});
  relation["amenity"="doctors"](around:5000,{latitude},{longitude});
);

out center tags;
"""

        # ====================================================
        # STEP 3
        # Send query to Overpass
        # ====================================================

        response = requests.post(
            OVERPASS_URL,
            data=query,
            headers={
                "User-Agent": (
                    "HealthcareVoiceAgent/1.0 "
                    "(educational project)"
                )
            },
            timeout=30,
        )

        response.raise_for_status()

        data = response.json()

        # ====================================================
        # STEP 4
        # Process results
        # ====================================================

        facilities = []

        for element in data.get("elements", []):

            tags = element.get("tags", {})

            name = tags.get("name")

            # Ignore unnamed facilities
            if not name:
                continue

            # ------------------------------------------------
            # Get coordinates
            # ------------------------------------------------

            if (
                "lat" in element
                and "lon" in element
            ):

                facility_lat = element["lat"]
                facility_lon = element["lon"]

            elif "center" in element:

                facility_lat = element["center"]["lat"]
                facility_lon = element["center"]["lon"]

            else:

                continue

            # ------------------------------------------------
            # Calculate distance
            # ------------------------------------------------

            distance = calculate_distance(
                latitude,
                longitude,
                facility_lat,
                facility_lon,
            )

            # ------------------------------------------------
            # Get facility information
            # ------------------------------------------------

            facility_type = tags.get(
                "amenity",
                "healthcare"
            )

            address_parts = []

            for key in [
                "addr:housenumber",
                "addr:street",
                "addr:suburb",
                "addr:city",
            ]:

                value = tags.get(key)

                if value:
                    address_parts.append(value)

            address = ", ".join(address_parts)

            phone = tags.get("phone", "")

            website = tags.get("website", "")

            facilities.append(
                {
                    "name": name,
                    "type": facility_type,
                    "distance_km": round(
                        distance,
                        2
                    ),
                    "latitude": facility_lat,
                    "longitude": facility_lon,
                    "address": address,
                    "phone": phone,
                    "website": website,
                }
            )

        # ====================================================
        # STEP 5
        # Sort nearest first
        # ====================================================

        facilities.sort(
            key=lambda facility:
            facility["distance_km"]
        )

        # ====================================================
        # STEP 6
        # No facilities found
        # ====================================================

        if not facilities:

            return {
                "found": False,
                "message": (
                    "I couldn't find a mapped healthcare "
                    f"facility within 5 kilometers of "
                    f"{location}."
                ),
                "data_source": (
                    "OpenStreetMap / Overpass"
                ),
            }

        # ====================================================
        # STEP 7
        # Return top 5 nearest facilities
        # ====================================================

        return {
            "found": True,
            "location": location,
            "facilities": facilities[:5],
            "data_source": (
                "OpenStreetMap / Overpass"
            ),
        }

    # ========================================================
    # TIMEOUT
    # ========================================================

    except requests.exceptions.Timeout:

        print(
            "Healthcare API request timed out."
        )

        return {
            "found": False,
            "error": "timeout",
            "message": (
                "The live healthcare location service "
                "is taking too long to respond. "
                "Please try again."
            ),
        }

    # ========================================================
    # API / NETWORK ERROR
    # ========================================================

    except requests.exceptions.RequestException as error:

        print(
            f"Healthcare API error: {error}"
        )

        return {
            "found": False,
            "error": "api_error",
            "message": (
                "The live healthcare location service "
                "is temporarily unavailable. "
                "I don't want to give you an unverified "
                "facility, so please try again later."
            ),
        }

    # ========================================================
    # OTHER ERROR
    # ========================================================

    except Exception as error:

        print(
            f"Unexpected healthcare lookup error: {error}"
        )

        return {
            "found": False,
            "error": "unknown_error",
            "message": (
                "I couldn't complete the live healthcare "
                "facility search right now."
            ),
        }
