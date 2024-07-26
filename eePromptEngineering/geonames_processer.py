import requests
import re

def call_geonames_api_bounds(bounds, username):
    south, west = bounds['Min_Lat'], bounds['Min_Lon']
    north, east = bounds['Max_Lat'], bounds['Max_Lon']
    url = f"http://api.geonames.org/searchJSON?username={username}&south={south}&west={west}&north={north}&east={east}&maxRows=1"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        if data['totalResultsCount'] > 0:
            geoname_info = data['geonames'][0]
            return geoname_info['geonameId'], geoname_info['name']
    return None

def call_geonames_api_coordinates(coords, username):
    lat, lon = coords
    url = f"http://api.geonames.org/findNearbyPlaceNameJSON?username={username}&lat={lat}&lng={lon}&maxRows=1"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        if 'geonames' in data and len(data['geonames']) > 0:
            geoname_info = data['geonames'][0]
            return geoname_info['geonameId'], geoname_info['name']
    return None

def call_geonames_api_by_name(geoname, username):
    url = f"http://api.geonames.org/searchJSON?username={username}&q={geoname}&maxRows=1"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        if data['totalResultsCount'] > 0:
            geoname_info = data['geonames'][0]
            return geoname_info['geonameId'], geoname_info['name']
    return None

def extract_spatial_coordinates(element, coord_pattern=r'\[?\(?(-?\d+\.\d+),\s*(-?\d+\.\d+)\)?\]?'):
    """Extracts spatial coordinates or bounds from elements."""
    coords = [tuple(map(float, m))  for m in re.findall(coord_pattern, str(element))]
    if len(coords) == 1:
        return {'Coordinates': coords[0]}
    elif len(coords) >= 2:
        lons, lats = zip(*coords)  # 确保第一个是经度，第二个是纬度
        bounds = {'Min_Lat': min(lats), 'Max_Lat': max(lats), 'Min_Lon': min(lons), 'Max_Lon': max(lons)}
        return {'Bounds': bounds}
    return None

   

