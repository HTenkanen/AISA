import osmnx as ox
import geopandas as gpd
import networkx as nx
from shapely.geometry import Point

# The place where you want to retrieve the data
# OSMnx uses Nominatim/OverPass API to retrieve the data
# You can check that your place name is valid from: https://nominatim.openstreetmap.org/
place = "Kamppi, Helsinki, Finland"

# Retrieve pedestrian data
kamppi = ox.gdf_from_place(place)
G = ox.graph_from_place(place, network_type='walk')

# What did we retrieve?
G

fig, ax = ox.plot_graph(G)

nodes, edges = ox.graph_to_gdfs(G, nodes=True, edges=True)  # you can flag whether you want to e.g. exclude nodes

# Check the first rows of the nodes
nodes.head()

# First rows of the edges
edges.head()

# Calculate the time (in seconds) it takes to walk through road segments
walk_speed = 4.5  # kmph
edges['walk_t'] = (( edges['length'] / (walk_speed*1000) ) * 60 * 60).round(1)

# Do the same for cycling
cycling_speed = 19  # kmph
edges['bike_t'] = (( edges['length'] / (cycling_speed*1000) ) * 60 * 60).round(1)

# Let's check what we got
edges[['length', 'walk_t', 'bike_t']].head()

G = ox.gdfs_to_graph(gdf_nodes=nodes, gdf_edges=edges)
type(G)

# Check only the first row from edges
for fr, to, edge in G.edges(data=True):
    print(edge)
    break

# OSM data is in WGS84 so typically we need to use lat/lon coordinates when searching for the closest node

# Origin
orig_address = "Kalevankatu 16, Helsinki"
orig_y, orig_x = ox.geocode(orig_address)  # notice the coordinate order (y, x)!

# Destination
dest_address = "Ruoholahdenkatu 24, Helsinki"
dest_y, dest_x = ox.geocode(dest_address)

print("Origin coords:", orig_x, orig_y)
print("Destination coords:", dest_x, dest_y)

# 1. Find the closest nodes for origin and destination
orig_node_id, dist_to_orig = ox.get_nearest_node(G, point=(orig_y, orig_x), method='haversine', return_dist=True)
dest_node_id, dist_to_dest = ox.get_nearest_node(G, point=(dest_y, dest_x), method='haversine', return_dist=True)

print("Origin node-id:", orig_node_id, "and distance:", dist_to_orig, "meters.")
print("Destination node-id:", dest_node_id, "and distance:", dist_to_dest, "meters.")

import networkx as nx
# Calculate the paths by walking and cycling
walk_path = nx.dijkstra_path(G, source=orig_node_id, target=dest_node_id, weight='walk_t')
bike_path = nx.dijkstra_path(G, source=orig_node_id, target=dest_node_id, weight='bike_t')

# Get also the actual travel times (summarize)
walk_t = nx.dijkstra_path_length(G, source=orig_node_id, target=dest_node_id, weight='walk_t')
bike_t = nx.dijkstra_path_length(G, source=orig_node_id, target=dest_node_id, weight='bike_t')

# Walking
fig, ax = ox.plot_graph_route(G, walk_path)

# Add the travel time as title
ax.set_xlabel("Walk time {t: .1f} minutes.".format(t=walk_t/60))

# Cycling
fig, ax = ox.plot_graph_route(G, bike_path)

# Add the travel time as title
ax.set_xlabel("Cycling time {t: .1f} minutes.".format(t=bike_t/60))

ox.plot_route_folium(G, walk_path, popup_attribute='walk_t')

# Calculate walk travel times originating from one location
walk_times = nx.single_source_dijkstra_path_length(G, source=orig_node_id, weight='walk_t')

import pandas as pd
# Convert to DataFrame and add column names
walk_times_df = pd.DataFrame([list(walk_times.keys()), list(walk_times.values())]).T
walk_times_df.columns = ['node_id', 'walk_t']

# What do we have now?
walk_times_df.head()

# Check the nodes
nodes.head()

# Merge the datasets
nodes = nodes.merge(walk_times_df, left_on='osmid', right_on='node_id')

# Check
nodes.head()

%matplotlib inline

# Make a GeoDataFrame for the origin point so that we can visualize it
orig = gpd.GeoDataFrame({'geometry': [Point(orig_x, orig_y)]}, index=[0], crs={'init': 'epsg:4326'})

# Plot the results with edges and the origin point (green)
ax = edges.plot(lw=0.5, color='gray', zorder=0, figsize=(10,10))
ax = nodes.plot('walk_t', ax=ax, cmap='RdYlBu', scheme='natural_breaks', k=5, markersize=30, legend=True)
ax = orig.plot(ax=ax, markersize=100, color='green')

# Adjust axis
ax.set_xlim([24.92, 24.945])
ax.set_ylim([60.160, 60.170])

# Take a subgraph until 4 minutes by walking (240 seconds)
subgraph = nx.ego_graph(G, n=orig_node_id, radius=240, distance='walk_t')
fig, ax = ox.plot_graph(subgraph)