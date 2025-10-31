# Tradle Geographic Triangulator

[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/ClayCampaigne/tradle-geo-triangulator/voila-ui?urlpath=voila%2Frender%2Ftradle_app.ipynb) **← CLICK HERE TO LAUNCH THE APP!**

An interactive web app to help solve [Tradle](https://oec.world/en/tradle/) puzzles using distance and direction hints.

## What is Tradle?

[Tradle](https://oec.world/en/tradle/) is a daily geography puzzle game similar to Wordle, but for countries. You guess a country, and the game tells you:
- The distance (in kilometers) from your guess to the target country
- The direction (cardinal directions: N, S, E, W, NE, NW, SE, SW) to the target country

## How This Tool Works

This notebook triangulates the target country by:

1. **Distance Calculation**: Uses the Haversine formula to compute great circle distances between all country centroids
2. **Mismatch Analysis**: For each guess, calculates how well every possible country matches the given distance
3. **Direction Filtering**: Applies directional constraints to eliminate countries in the wrong direction
4. **Ranking**: Sums up mismatches across all hints to rank candidate countries (lower score = better match)

The country with the lowest total mismatch is most likely the answer.

## Quick Start

### Option 1: Interactive Web App (No Installation)

Click the badge above to launch the interactive app in your browser. No installation required!

The app provides a user-friendly interface where you can:
- Add/remove hints with dropdown menus
- Adjust the direction penalty
- See results instantly

### Option 2: Run Locally

#### Interactive App (Voila)

```bash
# Clone this repository
git clone https://github.com/ClayCampaigne/tradle-geo-triangulator.git
cd tradle-geo-triangulator

# Install dependencies
pip install -r requirements.txt

# Run the interactive app
voila tradle_app.ipynb
```

#### Jupyter Notebook (Code Access)

```bash
# Same setup as above, then:
jupyter notebook tradle_guesser.ipynb
```

## Usage

The main function is `best_guesses()`, which takes a list of hints:

```python
# Each hint is a tuple: (country_name, distance, direction)
# Direction is optional
hints = [
    ("Thailand", 7705, 'NW'),  # With direction
    ("Eritrea", 4985)           # Without direction
]

result = best_guesses(hints, centroid_list, distance_df, penalty=10)
result.head(10)  # Show top 10 candidates
# Output shows total distance error in km (lower is better)
```

### Input Format

Each hint tuple contains:
1. **Country name** (str): The country you guessed in Tradle
2. **Distance** (float): The distance shown by Tradle in kilometers
3. **Direction** (str, optional): Cardinal direction shown by Tradle (e.g., 'N', 'SE', 'NW')

### Example Workflow

1. Play Tradle and make your first guess
2. Record the distance and direction shown
3. Add this hint to the notebook
4. Run `best_guesses()` to see top candidates
5. Make your next guess based on the results
6. Add the new hint and repeat until you solve it!

## Examples

The notebook includes three complete examples showing:
- Basic usage with distance and direction
- How multiple hints narrow down the answer
- The power of directional filtering

### Output Format

The output shows **total distance error in kilometers** for each candidate country (lower is better). Countries in the wrong direction have their error multiplied by the penalty.

## Parameters

The `best_guesses()` function accepts optional parameters:

- **`penalty`** (float, default=2): Multiplier applied to countries in the wrong direction
  - Controls the strength of direction filtering
  - `penalty=10`: Strong filtering - wrong direction gets 10× the error (recommended)
  - `penalty=2`: Weak filtering - wrong direction gets 2× the error
  - `penalty=100` or `float('inf')`: Nearly complete exclusion of wrong directions

- **`tol`** (float, default=0): Tolerance in degrees for direction filtering
  - Defines a buffer zone around exact directions
  - `tol=0`: Strict - "West" means any longitude less than the guess (default)
  - `tol=5`: Lenient - "West" means 5° or more west of the guess
  - Rarely needed; most users should leave at 0

**How they work together:** `tol` defines the buffer zone, `penalty` determines what happens to countries outside that zone. For most use cases, just use `penalty=10` and `tol=0`.

## Data Source

Country centroids are from Natural Earth data via GeoPandas, which includes approximately 177 countries.

## Limitations

- Uses country centroids rather than population centers
- Some small island nations may have less accurate positions
- Direction filtering uses simple lat/long comparisons (not great circle bearings)

## License

MIT

## Links

- Play Tradle: https://oec.world/en/tradle/
- GitHub Repository: https://github.com/ClayCampaigne/tradle-geo-triangulator
- Original Gist: https://gist.github.com/ClayCampaigne/c93c859a36fb2732214a776f7c21959d
