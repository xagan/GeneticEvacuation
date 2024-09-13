# GeneticEvacuation

GeneticEvacuation is a Python project that uses genetic algorithms to optimize evacuation route based on various geographical and infrastructure factors. The project combines road network data from OpenStreetMap with multiple raster datasets to find the most suitable evacuation path between two points.

## Features

- Utilizes OpenStreetMap data to create a road network graph
- Incorporates multiple raster datasets for route optimization:
  - Slope
  - Population density
  - Land use
  - Building age
  - Road width
  - Risk factors (e.g., fault lines)
  - Number of building floors
  - Building quality
- Implements a genetic algorithm to evolve and optimize routes
- Visualizes the best route and evolution of routes using Folium maps

## Dependencies

- rasterio
- numpy
- random
- folium
- osmnx
- networkx

## Usage

1. Ensure all required dependencies are installed.
2. Prepare your raster datasets and place them in the `Data/` directory.
3. Set the `ORIGIN` and `DESTINATION` coordinates in the script.
4. Adjust genetic algorithm parameters as needed (`POPULATION_SIZE`, `NUM_GENERATIONS`, `MUTATION_RATE`, `CROSSOVER_RATE`).
5. Run the script:

```
python main.py
```

6. The script will generate two HTML files:
   - `best_route.html`: Shows the best evacuation route found
   - `all_generations_routes.html`: Visualizes the evolution of routes across generations

## How It Works

1. The script starts by loading the road network and raster datasets.
2. An initial population of random routes is created.
3. The genetic algorithm evolves the population over multiple generations:
   - Routes are evaluated based on various factors from the raster datasets.
   - The best-performing routes are selected for reproduction.
   - New routes are created through crossover and mutation operations.
4. The best route from each generation is recorded.
5. Finally, the overall best route is visualized on a map.

## Customization

You can customize the project by:
- Adding or removing raster datasets
- Adjusting the fitness calculation method
- Modifying genetic algorithm parameters
- Changing the visualization style

## Note

This project is designed for educational and research purposes. The effectiveness of the evacuation routes should be validated by domain experts before any real-world application.
