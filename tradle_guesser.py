"""
Tradle Hint Triangulator

Core functions for solving Tradle puzzles using distance and direction hints.
"""

import geopandas as gpd
import pandas as pd
import numpy as np
from scipy.spatial.distance import pdist, squareform


def load_country_data():
    """
    Load Natural Earth country data and compute centroids.

    Returns:
        tuple: (centroid_list DataFrame, distance_df DataFrame)
            - centroid_list: DataFrame with Country and Centroid columns
            - distance_df: Square distance matrix between all countries
    """
    # Load Natural Earth data via GeoPandas
    world = gpd.read_file(gpd.datasets.get_path('naturalearth_lowres'))

    # Get country centroids
    centroids = world.centroid
    centroid_list = pd.concat([world['name'], centroids], axis=1)
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
        tol (float): Tolerance for direction filtering (degrees)
        penalty (float): Multiplier for mismatches in wrong direction

    Returns:
        Series: A Series containing the mismatch in distance for each country
    """
    if guessed_country not in distance_df.index:
        return f"Guessed country '{guessed_country}' not found in the distance matrix."

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

            # Apply direction filters
            if 'N' in direction and lat_current <= lat_guessed + tol:
                mismatch.loc[country] *= penalty
            if 'S' in direction and lat_current >= lat_guessed - tol:
                mismatch.loc[country] *= penalty
            if 'E' in direction and long_current <= long_guessed + tol:
                mismatch.loc[country] *= penalty
            if 'W' in direction and long_current >= long_guessed - tol:
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
        Series: Countries ranked by total mismatch (lower is better)

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

    return total_dist_errors.sort_values().dropna()
