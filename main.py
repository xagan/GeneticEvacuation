import rasterio  # برای کار با داده‌های رستری
import numpy as np  # برای محاسبات عددی
import random  # برای تولید اعداد تصادفی
import folium  # برای نقشه‌سازی
import osmnx as ox  # برای کار با داده‌های OpenStreetMap
import networkx as nx  # برای تحلیل شبکه


# این بخش ثابت‌های برنامه را تعریف می‌کند، شامل مختصات مبدأ و مقصد، اندازه جمعیت در الگوریتم ژنتیک، تعداد نسل‌ها، نرخ جهش و نرخ ترکیب.
ORIGIN = (38.0718474, 46.3440139)
DESTINATION = (38.05018367, 46.36721120)
POPULATION_SIZE =4
NUM_GENERATIONS = 200
MUTATION_RATE = 0.01
CROSSOVER_RATE = 0.8

# Load the road network
# این کد یک گراف جاده‌ای را از OpenStreetMap برای منطقه مورد نظر دانلود می‌کند.
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



#این تابع نزدیک‌ترین گره در شبکه جاده‌ای را به یک نقطه مشخص پیدا می‌کند.
def get_nearest_node(point):
    return ox.nearest_nodes(G, point[1], point[0])


#این تابع یک مسیر تصادفی بین مبدأ و مقصد ایجاد می‌کند با استفاده از شبکه جاده‌ای.
def create_random_route():
    origin_node = get_nearest_node(ORIGIN)
    destination_node = get_nearest_node(DESTINATION)
    try:
        path = nx.shortest_path(G, origin_node, destination_node, weight='length')
        route = [ORIGIN] + [(G.nodes[node]['y'], G.nodes[node]['x']) for node in path[1:-1]] + [DESTINATION]
        # Add some random deviations
        for _ in range(random.randint(1, 5)):
            i = random.randint(1, len(route) - 2)
            new_point = (
                route[i][0] + random.uniform(-0.001, 0.001),
                route[i][1] + random.uniform(-0.001, 0.001)
            )
            route.insert(i, new_point)
        return route
    except nx.NetworkXNoPath:
        return [ORIGIN, DESTINATION]



#این تابع جمعیت اولیه را برای الگوریتم ژنتیک ایجاد می‌کند.
def create_initial_population():
    return [create_random_route() for _ in range(POPULATION_SIZE)]



#این تابع مقدار داده رستری را در یک نقطه مشخص برمی‌گرداند.
def get_raster_value_at_point(lat, lon, raster_dataset):
    row, col = raster_dataset.index(lon, lat)
    if 0 <= row < raster_dataset.height and 0 <= col < raster_dataset.width:
        return raster_dataset.read(1)[row, col]
    return 0



# این تابع میزان برازندگی یک مسیر را محاسبه می‌کند با توجه به داده‌های رستری مختلف.
def calculate_fitness(route):
    total_value = 0
    for point in route:
        for dataset in [slope_dataset, risk_dataset, population_dataset, landuse_dataset,
                        building_age_dataset, road_width_dataset, floors_dataset,
                        building_quality_dataset, fault_dataset]:
            value = get_raster_value_at_point(point[0], point[1], dataset)
            print(f"Value for dataset {dataset.name} at point {point}: {value}")
            total_value += value
    fitness = 1 / (total_value + 1)
    print(f"Total value: {total_value}, Fitness: {fitness}")
    return fitness


#این تابع دو والد را برای تولید مثل انتخاب می‌کند، با احتمال بیشتر برای مسیرهای با برازندگی بالاتر.
def select_parents(population, fitnesses):
    return random.choices(population, weights=fitnesses, k=2)


# این تابع عملیات ترکیب را بین دو والد انجام می‌دهد تا دو فرزند جدید ایجاد کند.
# Single-Point Crossover
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



# این تابع جهش را در یک مسیر اعمال می‌کند، با تغییر تصادفی یک نقطه در مسیر.
# Point Mutation
def mutate(route):
    if len(route) > 2 and random.random() < MUTATION_RATE:
        i = random.randint(1, len(route) - 2)
        deviation = 0.001  # Adjust this value based on your map scale
        new_point = (
            route[i][0] + random.uniform(-deviation, deviation),
            route[i][1] + random.uniform(-deviation, deviation)
        )
        route[i] = new_point
    return route


# این تابع اطمینان حاصل می‌کند که تمام قطعات مسیر از طریق شبکه جاده‌ای به هم متصل هستند.
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



# این تابع جمعیت را در طول یک نسل تکامل می‌دهد.
def evolve_population(population):
    fitnesses = [calculate_fitness(route) for route in population]
    new_population = []
    for _ in range(POPULATION_SIZE // 2):
        parent1, parent2 = select_parents(population, fitnesses)
        child1, child2 = crossover(parent1, parent2)
        new_population.extend([mutate(child1), mutate(child2)])
    return new_population


# این تابع بهترین مسیر را روی نقشه نمایش می‌دهد و آن را به صورت یک فایل HTML ذخیره می‌کند.
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


def plot_all_generations(all_best_routes):
    midpoint = ((ORIGIN[0] + DESTINATION[0]) / 2, (ORIGIN[1] + DESTINATION[1]) / 2)
    route_map = folium.Map(location=midpoint, zoom_start=13)

    # Add markers for origin and destination
    folium.Marker(location=ORIGIN, popup="Origin", icon=folium.Icon(color='green')).add_to(route_map)
    folium.Marker(location=DESTINATION, popup="Destination", icon=folium.Icon(color='red')).add_to(route_map)

    # Create a color gradient for the routes
    n_generations = len(all_best_routes)
    color_scale = [f'#{int(255*i/n_generations):02x}0000' for i in range(n_generations)]

    # Plot each generation's best route
    for gen, route in enumerate(all_best_routes):
        folium.PolyLine(
            route,
            color=color_scale[gen],
            weight=2,
            opacity=0.8,
            popup=f'Generation {gen}'
        ).add_to(route_map)

    # Save the map
    route_map.save("all_generations_routes.html")


def main():
    try:
        population = create_initial_population()
        print(f"Initial population size: {len(population)}")
        best_route = None
        best_fitness = 0
        all_best_routes = []

        for generation in range(NUM_GENERATIONS):
            print(f"Starting generation {generation}")
            population = evolve_population(population)
            print(f"Population size after evolution: {len(population)}")
            fitnesses = [calculate_fitness(route) for route in population]
            print(f"Fitnesses: {fitnesses}")
            max_fitness = max(fitnesses)
            if max_fitness > best_fitness:
                best_fitness = max_fitness
                best_route = population[fitnesses.index(max_fitness)]
                all_best_routes.append(best_route)

            print(f"Generation {generation}: Best Fitness = {best_fitness}")

        # Plot the best route
        plot_route(best_route)

        # Plot all generations
        plot_all_generations(all_best_routes)

        print(f"Total number of generations: {len(all_best_routes)}")
        print(f"Final best fitness: {best_fitness}")
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
