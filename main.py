import rasterio
import numpy as np
import random
import folium
import osmnx as ox
import networkx as nx

# Define constants
ORIGIN = (38.0718474, 46.3440139)  # Example coordinates for Tehran
DESTINATION = (38.05018367, 46.36721120)  # Example destination
POPULATION_SIZE = 50
NUM_GENERATIONS = 100
MUTATION_RATE = 0.01
CROSSOVER_RATE = 0.8

# Load the road network
G = ox.graph_from_bbox(max(ORIGIN[0], DESTINATION[0]), min(ORIGIN[0], DESTINATION[0]),
                       max(ORIGIN[1], DESTINATION[1]), min(ORIGIN[1], DESTINATION[1]),
                       network_type='drive')


def load_raster(file_path):
    return rasterio.open(file_path)


# Load raster data
slope_dataset = load_raster('Data/slope.tif')
population_dataset = load_raster('Data/jamiat.tif')
landuse_dataset = load_raster('Data/karbari.tif')
building_age_dataset = load_raster('Data/omr_abnie.tif')
road_width_dataset = load_raster('Data/arze_mabar1.tif')
risk_dataset = load_raster('Data/gosal.tif')
floors_dataset = load_raster('Data/tabaghat.tif')
building_quality_dataset = load_raster('Data/keyfiyat.tif')
fault_dataset = load_raster('Data/khatar.tif')


def get_nearest_node(point):
    return ox.nearest_nodes(G, point[1], point[0])


def create_random_route():
    origin_node = get_nearest_node(ORIGIN)
    destination_node = get_nearest_node(DESTINATION)
    try:
        path = nx.shortest_path(G, origin_node, destination_node, weight='length')
        return [ORIGIN] + [(G.nodes[node]['y'], G.nodes[node]['x']) for node in path[1:-1]] + [DESTINATION]
    except nx.NetworkXNoPath:
        return [ORIGIN, DESTINATION]  # fallback if no path found


def create_initial_population():
    return [create_random_route() for _ in range(POPULATION_SIZE)]


def get_raster_value_at_point(lat, lon, raster_dataset):
    row, col = raster_dataset.index(lon, lat)
    if 0 <= row < raster_dataset.height and 0 <= col < raster_dataset.width:
        return raster_dataset.read(1)[row, col]
    return 0


def calculate_fitness(route):
    total_value = 0
    for point in route:
        total_value += get_raster_value_at_point(point[0], point[1], slope_dataset)
        total_value += get_raster_value_at_point(point[0], point[1], risk_dataset)
        total_value += get_raster_value_at_point(point[0], point[1], population_dataset)
        # Add other raster data checks here
    return 1 / (total_value + 1)  # Higher fitness for lower total value


def select_parents(population, fitnesses):
    return random.choices(population, weights=fitnesses, k=2)


def crossover(parent1, parent2):
    if random.random() < CROSSOVER_RATE:
        point = random.randint(1, min(len(parent1), len(parent2)) - 1)
        child1 = parent1[:point] + parent2[point:]
        child2 = parent2[:point] + parent1[point:]

        # Ensure valid path using network
        child1_path = validate_route(child1)
        child2_path = validate_route(child2)

        return child1_path, child2_path
    return parent1, parent2


def mutate(route):
    if len(route) > 2 and random.random() < MUTATION_RATE:
        i = random.randint(1, len(route) - 2)
        new_point = (random.uniform(min(ORIGIN[0], DESTINATION[0]), max(ORIGIN[0], DESTINATION[0])),
                     random.uniform(min(ORIGIN[1], DESTINATION[1]), max(ORIGIN[1], DESTINATION[1])))
        nearest_node = get_nearest_node(new_point)
        route[i] = (G.nodes[nearest_node]['y'], G.nodes[nearest_node]['x'])
    return validate_route(route)


def validate_route(route):
    """Ensure all segments in the route are connected via the road network."""
    valid_route = [route[0]]
    for i in range(1, len(route)):
        node1 = get_nearest_node(valid_route[-1])
        node2 = get_nearest_node(route[i])
        if node1 != node2:
            try:
                path = nx.shortest_path(G, node1, node2, weight='length')
                valid_route.extend([(G.nodes[node]['y'], G.nodes[node]['x']) for node in path[1:]])
            except nx.NetworkXNoPath:
                continue
        else:
            valid_route.append(route[i])
    return valid_route


def evolve_population(population):
    fitnesses = [calculate_fitness(route) for route in population]
    new_population = []
    for _ in range(POPULATION_SIZE // 2):
        parent1, parent2 = select_parents(population, fitnesses)
        child1, child2 = crossover(parent1, parent2)
        new_population.extend([mutate(child1), mutate(child2)])
    return new_population


def plot_route(best_route):
    # Create a folium map centered around the mid-point between origin and destination
    midpoint = ((ORIGIN[0] + DESTINATION[0]) / 2, (ORIGIN[1] + DESTINATION[1]) / 2)
    route_map = folium.Map(location=midpoint, zoom_start=14)

    # Add the route to the map
    folium.PolyLine(best_route, color="red", weight=2.5, opacity=1).add_to(route_map)

    # Add markers for the origin and destination
    folium.Marker(location=ORIGIN, popup="Origin", icon=folium.Icon(color='green')).add_to(route_map)
    folium.Marker(location=DESTINATION, popup="Destination", icon=folium.Icon(color='blue')).add_to(route_map)

    # Save the map as an HTML file
    route_map.save("best_route.html")


def main():
    population = create_initial_population()
    best_route = None
    best_fitness = 0

    for generation in range(NUM_GENERATIONS):
        population = evolve_population(population)
        fitnesses = [calculate_fitness(route) for route in population]
        max_fitness = max(fitnesses)
        if max_fitness > best_fitness:
            best_fitness = max_fitness
            best_route = population[fitnesses.index(max_fitness)]

        if generation % 100 == 0:
            print(f"Generation {generation}: Best Fitness = {best_fitness}")

    # Plot the best route
    plot_route(best_route)


if __name__ == "__main__":
    main()
