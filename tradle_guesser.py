"""
Tradle Hint Triangulator

Core functions for solving Tradle puzzles using distance and direction hints.
"""

import geopandas as gpd
import pandas as pd
import numpy as np
from scipy.spatial.distance import pdist, squareform

# Valid cardinal directions
VALID_DIRECTIONS = {'N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW'}


def load_country_data():
    """
    Load Natural Earth country data and compute centroids.

    Returns:
        tuple: (centroid_list DataFrame, distance_df DataFrame)
            - centroid_list: DataFrame with Country and Centroid columns
            - distance_df: Square distance matrix between all countries
    """
    # Load Natural Earth data directly from their server
    # This avoids the deprecated geopandas.datasets module
    url = "https://naturalearth.s3.amazonaws.com/110m_cultural/ne_110m_admin_0_countries.zip"
    world = gpd.read_file(url)

    # Get country centroids
    # Natural Earth data uses 'NAME' or 'ADMIN' for country names
    name_column = 'NAME' if 'NAME' in world.columns else ('ADMIN' if 'ADMIN' in world.columns else 'name')

    # Project to equal-area CRS for accurate centroids, then convert back to geographic
    # EPSG:6933 is Cylindrical Equal Area, good for global centroid calculations
    world_projected = world.to_crs(epsg=6933)
    centroids_projected = world_projected.centroid
    # Convert centroids back to geographic coordinates (EPSG:4326)
    centroids = centroids_projected.to_crs(epsg=4326)

    centroid_list = pd.concat([world[name_column], centroids], axis=1)
    centroid_list.columns = ['Country', 'Centroid']

    # Extract latitude and longitude from the Centroid geometry
    centroid_coordinates = centroid_list['Centroid'].apply(
        lambda point: (point.y, point.x)
    ).tolist()

    # Compute the pairwise distance matrix using the haversine_distance function
    distance_matrix = pdist(centroid_coordinates, metric=haversine_distance)

    # Convert to square matrix
    square_distance_matrix = squareform(distance_matrix)

    # Create a DataFrame for better readability
    distance_df = pd.DataFrame(
        square_distance_matrix,
        index=centroid_list['Country'],
        columns=centroid_list['Country']
    )

    return centroid_list, distance_df


def haversine_distance(coord1, coord2):
    """
    Calculate the great circle distance in kilometers between two points
    on the earth (specified in decimal degrees).

    Parameters:
        coord1 (tuple): (latitude, longitude) in decimal degrees
        coord2 (tuple): (latitude, longitude) in decimal degrees

    Returns:
        float: Distance in kilometers
    """
    # Convert decimal degrees to radians
    lat1, lon1 = np.radians(coord1)
    lat2, lon2 = np.radians(coord2)

    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = np.sin(dlat/2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2)**2
    c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1-a))

    # 6,371 km is the radius of the Earth
    km = 6371 * c
    return km


def calculate_mismatch(guessed_country, given_distance, centroid_list, distance_df,
                       direction=None, tol=0, penalty=np.inf):
    """
    Calculate the mismatch in distance between each country and the guessed country,
    compared to the given distance.

    Parameters:
        guessed_country (str): The name of the country that was guessed
        given_distance (float): The distance from the guessed country to the correct country
        centroid_list (DataFrame): DataFrame with Country and Centroid columns
        distance_df (DataFrame): Distance matrix between countries
        direction (str, optional): The cardinal direction in which the correct country lies
                                   Must be one of: N, NE, E, SE, S, SW, W, NW
        tol (float): Tolerance for direction filtering (degrees)
        penalty (float): Multiplier for mismatches in wrong direction

    Returns:
        Series: A Series containing the mismatch in distance for each country

    Raises:
        ValueError: If direction is invalid or country not found
    """
    if guessed_country not in distance_df.index:
        raise ValueError(f"Guessed country '{guessed_country}' not found in the distance matrix. "
                        f"Available countries: {sorted(distance_df.index.tolist())}")

    if direction is not None and direction not in VALID_DIRECTIONS:
        raise ValueError(f"Invalid direction '{direction}'. Must be one of: {sorted(VALID_DIRECTIONS)}")

    # Calculate the absolute mismatch for each country
    mismatch = distance_df.loc[guessed_country].apply(lambda x: abs(x - given_distance))

    if direction:
        # Get the latitude and longitude of the guessed country's centroid
        guessed_coord = centroid_list.set_index('Country').loc[guessed_country, 'Centroid']
        lat_guessed, long_guessed = guessed_coord.y, guessed_coord.x

        # Filter countries based on the direction information
        for country in centroid_list['Country']:
            current_coord = centroid_list.set_index('Country').loc[country, 'Centroid']
            lat_current, long_current = current_coord.y, current_coord.x

            # Apply direction filters for latitude (straightforward)
            if 'N' in direction and lat_current <= lat_guessed + tol:
                mismatch.loc[country] *= penalty
            if 'S' in direction and lat_current >= lat_guessed - tol:
                mismatch.loc[country] *= penalty

            # Apply direction filters for longitude (handle date line wrapping)
            # Calculate the shortest angular difference considering wrapping
            lon_diff = long_current - long_guessed
            # Normalize to [-180, 180]
            if lon_diff > 180:
                lon_diff -= 360
            elif lon_diff < -180:
                lon_diff += 360

            if 'E' in direction and lon_diff <= tol:
                mismatch.loc[country] *= penalty
            if 'W' in direction and lon_diff >= -tol:
                mismatch.loc[country] *= penalty

    return mismatch.sort_values()


def best_guesses(input_list, centroid_list, distance_df, tol=0, penalty=2):
    """
    Calculate the best guesses based on a list of hints.

    Parameters:
        input_list (list): A list of tuples, where each tuple contains:
            - guessed country (str)
            - given distance (float)
            - optional direction (str): e.g., 'N', 'NE', 'SW'
        centroid_list (DataFrame): DataFrame with Country and Centroid columns
        distance_df (DataFrame): Distance matrix between countries
        tol (float): Tolerance for direction filtering (degrees)
        penalty (float): Multiplier for countries in wrong direction

    Returns:
        DataFrame: Countries ranked by total mismatch (lower is better)
                   with column 'adjusted_km_total_error'

    Example:
        best_guesses([("Thailand", 7705, 'NW'), ("Eritrea", 4985)],
                     centroid_list, distance_df)
    """
    total_dist_errors = pd.Series(index=distance_df.index, dtype=float)

    for hint in input_list:
        if len(hint) == 3:
            country, dist, direction = hint
            mismatch = calculate_mismatch(
                country, dist, centroid_list, distance_df,
                direction=direction, tol=tol, penalty=penalty
            )
        else:
            country, dist = hint
            mismatch = calculate_mismatch(
                country, dist, centroid_list, distance_df,
                tol=tol, penalty=penalty
            )

        if total_dist_errors.isna().all():
            total_dist_errors = mismatch
        else:
            total_dist_errors += mismatch

    # Convert to DataFrame with named column
    result = total_dist_errors.sort_values().dropna().to_frame(name='adjusted_km_total_error')
    return result
