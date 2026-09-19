import os 
import re 
import airportsdata
import pycountry
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("AVIATIONSTACK_API_KEY")

# Default origin when user says only destination, e.g. "Japan trip"
# Change this if your default location is not Mumbai.
DEFAULT_ORIGIN_IATA = os.getenv("DEFAULT_ORIGIN_IATA", "BOM")


BASE_URL = "https://api.aviationstack.com/v1/flights"


AIRPORTS = airportsdata.load("IATA")


COUNTRY_ALIASES = {
    "usa": "US",
    "u.s.a": "US",
    "u.s.": "US",
    "america": "US",
    "united states": "US",
    "uk": "GB",
    "u.k.": "GB",
    "britain": "GB",
    "england": "GB",
    "uae": "AE",
    "dubai": "AE",
    "south korea": "KR",
    "korea": "KR",
    "russia": "RU",
    "vietnam": "VN",
    "bangladesh": "BD",
    "india": "IN",
    "japan": "JP",
    "china": "CN",
    "singapore": "SG",
    "malaysia": "MY",
    "thailand": "TH",
    "indonesia": "ID",
    "nepal": "NP",
    "qatar": "QA",
    "saudi arabia": "SA",
    "turkey": "TR",
    "canada": "CA",
    "australia": "AU",
    "germany": "DE",
    "france": "FR",
    "italy": "IT",
    "spain": "ES",
}


# Preferred main airport for country-level search
COUNTRY_MAIN_AIRPORT = {
    "BD": "DAC",
    "IN": "DEL",
    "JP": "NRT",
    "US": "JFK",
    "GB": "LHR",
    "AE": "DXB",
    "SG": "SIN",
    "MY": "KUL",
    "TH": "BKK",
    "ID": "CGK",
    "CN": "PEK",
    "KR": "ICN",
    "NP": "KTM",
    "QA": "DOH",
    "SA": "JED",
    "TR": "IST",
    "CA": "YYZ",
    "AU": "SYD",
    "DE": "FRA",
    "FR": "CDG",
    "IT": "FCO",
    "ES": "MAD",
}




CITY_MAIN_AIRPORT = {
    "dhaka": "DAC",
    "delhi": "DEL",
    "new delhi": "DEL",
    "mumbai": "BOM",
    "kolkata": "CCU",
    "chennai": "MAA",
    "bangalore": "BLR",
    "bengaluru": "BLR",
    "tokyo": "NRT",
    "osaka": "KIX",
    "kyoto": "KIX",
    "new york": "JFK",
    "london": "LHR",
    "dubai": "DXB",
    "singapore": "SIN",
    "kuala lumpur": "KUL",
    "bangkok": "BKK",
    "doha": "DOH",
    "istanbul": "IST",
    "toronto": "YYZ",
    "sydney": "SYD",
    "paris": "CDG",
    "rome": "FCO",
    "madrid": "MAD",
    "frankfurt": "FRA",
}


def clean_text(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text)

    return text


def country_name_to_code(text: str):
    text = clean_text(text)

    if text in COUNTRY_ALIASES:
        return COUNTRY_ALIASES[text]

    try:
        country = pycountry.countries.lookup(text)
        return country.alpha_2
    except LookupError:
        return None
    
    
    
    # If the user passes nothing, what should the function return?
def resolve_location_to_iata(location: str):
    if not location:
        return None
    
    
    
def resolve_location_to_iata(location: str):
    if not location:
        return None

    location = location.strip()

    # 1. User already gave an IATA code
    # IATA airport codes contain exactly 3 letters. Example: BOM, DEL
    # re.fullmatch() checks that the ENTIRE string matches the pattern, rather than just part of the string.
    if re.fullmatch(r"[A-Za-z]{3}", location):
        code = location.upper()

        if code in AIRPORTS:
            return code

    # 2. User gave a city
    # First clean the location: " Mumbai " → "mumbai"
    location_clean = clean_text(location)

    # Look for the city in our predefined city → airport mapping. Example: "mumbai" → "BOM"
    if location_clean in CITY_MAIN_AIRPORT:
        return CITY_MAIN_AIRPORT[location_clean]

    # 3. User gave a country
    # Convert the country name into its ISO 2-letter code. "Japan" → "JP"
    country_code = country_name_to_code(location_clean)

    if country_code:
        return COUNTRY_MAIN_AIRPORT.get(country_code)

    return None



def find_location_mentions(query: str):
    """
    Finds country or city names inside a natural language query.
    """

    # Convert query to lowercase
    q = query.lower()

    # Store found locations
    mentions = []

    # Check country aliases
    for alias in COUNTRY_ALIASES:
        if alias in q:
            mentions.append(alias)

    # Check city names
    for city in CITY_MAIN_AIRPORT:
        if city in q:
            mentions.append(city)

    return mentions




def parse_route(query: str):
    """
    Extract departure and arrival IATA codes from a query.
    """

    q = query.strip()

    # Case 1: Direct IATA route
    # Example: "BOM to NRT"
    codes = re.findall(r"\b[A-Z]{3}\b", q)

    if len(codes) >= 2:
        return codes[0], codes[1]

    # Case 2: Natural language route
    # Example: "Plan a trip from Mumbai to Japan"
    match = re.search(
        r"\bfrom\s+(.+?)\s+\bto\s+(.+?)(?:\s+(?:on|for|under|including|with|in|at)\b|[.!?]|$)",
        q.lower()
    )

    if match:
        origin_text = match.group(1)
        destination_text = match.group(2)

        departure = resolve_location_to_iata(origin_text)
        arrival = resolve_location_to_iata(destination_text)

        return departure, arrival

    # Case 3: "to X from Y"
    # Example: "I want to go to Tokyo from Mumbai"
    # The issue is that the sentence contains two possible to's 
    # but because the regex was allowed to start at an earlier to, it could match:
    # "to Tokyo from Mumbai"
    # which should actually be fine — but in your previous version, the surrounding matching behavior allowed the destination capture to become go to Tokyo.
    # So we changed it : The important addition is: .*
    # That makes the regex consume as much as possible before the to, so it prefers the last relevant to.
    # I want to go to Tokyo from Mumbai
    # ^^^^^^^^^^^^^
    #  consumed by .*
    match = re.search(
        r".*\bto\s+(.+?)\s+\bfrom\s+(.+?)(?:[.!?]|$)",
        q.lower()
    )

    if match:
        destination_text = match.group(1)
        origin_text = match.group(2)

        arrival = resolve_location_to_iata(destination_text)
        departure = resolve_location_to_iata(origin_text)

        return departure, arrival

    # Case 4: Origin only
    # Example: "Find flights from Mumbai"
    match = re.search(
        r"\bfrom\s+(.+?)(?:[.!?]|$)",
        q.lower()
    )

    if match:
        origin_text = match.group(1)

        departure = resolve_location_to_iata(origin_text)

        return departure, None

    # Case 5: Destination only
    # Example: "Find flights to Tokyo"
    
    # print("REGEX =", re.search(r"\bto\s+(.+?)(?:[.!?]|$)", q.lower()))
    match = re.search(
        r"\bto\s+(.+?)(?:[.!?]|$)",
        q.lower()
    )

    if match:
        
        destination_text = match.group(1)

        arrival = resolve_location_to_iata(destination_text)

        if arrival:
            return None, arrival
        
    ''' The problem was that Case 5 found the word “to” in “I want to visit Thailand” 
     and treated “visit Thailand” as the destination, but it wasn’t a valid location, 
     so we needed to let the parser continue to Case 6 and find “Thailand” correctly.'''

    # Case 6: Fallback
    # If we couldn't find a clear route,
    # look for known locations mentioned in the query.
    
    mentions = find_location_mentions(query)

    if mentions:
        destination = resolve_location_to_iata(mentions[-1])

        return None, destination

    # Nothing could be resolved
    return None, None



def format_flight(flight: dict):
    """
    Convert raw flight data into a simple format.
    """

    departure = flight.get("departure", {})
    arrival = flight.get("arrival", {})
    airline = flight.get("airline", {})
    flight_info = flight.get("flight", {})
    
    # The API response can contain lots of information, but we only keep
    return {
        "airline": airline.get("name"),
        "flight_number": flight_info.get("iata"),
        "departure_airport": departure.get("airport"),
        "departure_iata": departure.get("iata"),
        "departure_time": departure.get("scheduled"),
        "arrival_airport": arrival.get("airport"),
        "arrival_iata": arrival.get("iata"),
        "arrival_time": arrival.get("scheduled"),
    }
    
    
    
    
def search_flights(query: str, date: str = None):
    """
    Search flights based on a user query.
    """

    # Parse route
    departure, arrival = parse_route(query)

    # Check route
    if not departure and not arrival:
        return []

    # Build API parameters
    params = {
        "access_key": API_KEY
    }

    if departure:
        params["dep_iata"] = departure

    if arrival:
        params["arr_iata"] = arrival

    # Add date if provided
    if date:
        params["flight_date"] = date

    # Send API request
    response = requests.get(BASE_URL, params=params)

    # Check HTTP errors
    response.raise_for_status()

    # Convert response to dictionary
    data = response.json()

    # Check API errors
    if "error" in data:
        return []

    # Get flight list
    flights = data.get("data", [])
    
    # Keep only a small number of results
    flights = flights[:5]

    # Format flights
    results = []

    for flight in flights:
        results.append(format_flight(flight))

    return results


