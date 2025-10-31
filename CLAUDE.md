# Development Notes

## Local Testing

Use `uv` for local development and testing. Note: geopandas requires Python <3.14 due to GDAL dependencies.

```bash
# Run the test script (uses Python 3.11)
uv run --python 3.11 test_local.py

# Run specific examples
uv run --python 3.11 python -c "from tradle_guesser import load_country_data; print(load_country_data()[0].head())"
```


## Dependencies

The project uses:
- geopandas (with Natural Earth data from S3)
- pandas
- numpy
- scipy

## Changes from Original

1. **Deprecated dataset fix**: Changed from `gpd.datasets.get_path('naturalearth_lowres')` to direct download from Natural Earth S3
2. **Code organization**: Separated implementation (tradle_guesser.py) from interface (notebook)
3. **Column name handling**: Added fallback for NAME/ADMIN/name columns in Natural Earth data
4. **CRS fix**: Project to EPSG:6933 before calculating centroids to avoid warning and improve accuracy
5. **Named output**: Return DataFrame with 'adjusted_km_total_error' column instead of unnamed Series
6. **Better default penalty**: Examples now use penalty=10 for stronger direction filtering (old default of 2 was too weak)
7. **International date line fix**: Properly handle longitude wrapping when filtering E/W directions
8. **Input validation**: Validate direction inputs against allowed set (N, NE, E, SE, S, SW, W, NW)

## Binder Deployment

The Binder badge in README.md automatically works once pushed to GitHub. First build takes a few minutes, subsequent launches are cached.
