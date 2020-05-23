import geopandas as gpd
import networkx as nx
import osmnx as ox

# Filepath
fp = "data/test_Digiroad.gpkg"

# In the GeoPackage there are three layers (we are interested in all of them)
links = gpd.read_file(fp, layer='DR_LINKKI_K')
speedlimits = gpd.read_file(fp, layer='DR_NOPEUSRAJOITUS_K')
signals = gpd.read_file(fp, layer='DR_LIIKENNEVALO')

# Check links
links.plot()

links.head(2)

speedlimits.plot()

speedlimits.head(2)

signals.plot()

signals.head(2)

from tools import apply_intersection_delays
help(apply_intersection_delays)

dr_data = apply_intersection_delays(links, speedlimits, signals)

# What did we get?
dr_data.head(2)

from tools import build_graph_from_Digiroad

# Print the "manual"
help(build_graph_from_Digiroad)

# Build the graph
G = build_graph_from_Digiroad(dr_data)

# Check type
G

ox.plot_graph(G)

# Addresses
# Origin
orig_address = "Otakaari 12, Espoo"
orig_y, orig_x = ox.geocode(orig_address)  # notice the coordinate order (y, x)!

# Destination
dest_address = "Fabianinkatu 33, Helsinki"
dest_y, dest_x = ox.geocode(dest_address)

# 1. Find the closest nodes for origin and destination
orig_node_id, dist_to_orig = ox.get_nearest_node(G, point=(orig_y, orig_x), method='haversine', return_dist=True)
dest_node_id, dist_to_dest = ox.get_nearest_node(G, point=(dest_y, dest_x), method='haversine', return_dist=True)

# 2. Calculate the shortest paths by car during midday
midday_path = nx.dijkstra_path(G, source=orig_node_id, target=dest_node_id, weight='Keskpva_aa')

# Get also the actual travel time (summarize)
midday_t = nx.dijkstra_path_length(G, source=orig_node_id, target=dest_node_id, weight='Keskpva_aa')

def node_list_to_coordinate_lines(G, node_list, use_geom=True, weight_col='length'):
    """Obtained from OSMnx with custom weight_col."""
    edge_nodes = list(zip(node_list[:-1], node_list[1:]))
    lines = []
    for u, v in edge_nodes:
        # if there are parallel edges, select the shortest in length
        data = min(G.get_edge_data(u, v).values(), key=lambda x: x[weight_col])

        # if it has a geometry attribute (ie, a list of line segments)
        if 'geometry' in data and use_geom:
            # add them to the list of lines to plot
            xs, ys = data['geometry'].xy
            lines.append(list(zip(xs, ys)))
        else:
            # if it doesn't have a geometry attribute, the edge is a straight
            # line from node to node
            x1 = G.nodes[u]['x']
            y1 = G.nodes[u]['y']
            x2 = G.nodes[v]['x']
            y2 = G.nodes[v]['y']
            line = [(x1, y1), (x2, y2)]
            lines.append(line)
    return lines

def plot_graph_route(G, route, weight_col='length', bbox=None, fig_height=6, fig_width=None,
                     margin=0.02, bgcolor='w', axis_off=True, show=True,
                     save=False, close=True, file_format='png', filename='temp',
                     dpi=300, annotate=False, node_color='#999999',
                     node_size=15, node_alpha=1, node_edgecolor='none',
                     node_zorder=1, edge_color='#999999', edge_linewidth=1,
                     edge_alpha=1, use_geom=True, origin_point=None,
                     destination_point=None, route_color='r', route_linewidth=4,
                     route_alpha=0.5, orig_dest_node_alpha=0.5,
                     orig_dest_node_size=100, orig_dest_node_color='r',
                     orig_dest_point_color='b'):
    """
    Modified from OSMnx with custom weight_col, see:
    """
    from matplotlib.collections import LineCollection

    # plot the graph but not the route
    fig, ax = ox.plot_graph(G, bbox=bbox, fig_height=fig_height, fig_width=fig_width,
                         margin=margin, axis_off=axis_off, bgcolor=bgcolor,
                         show=False, save=False, close=False, filename=filename,
                         dpi=dpi, annotate=annotate, node_color=node_color,
                         node_size=node_size, node_alpha=node_alpha,
                         node_edgecolor=node_edgecolor, node_zorder=node_zorder,
                         edge_color=edge_color, edge_linewidth=edge_linewidth,
                         edge_alpha=edge_alpha, use_geom=use_geom)

    # the origin and destination nodes are the first and last nodes in the route
    origin_node = route[0]
    destination_node = route[-1]

    if origin_point is None or destination_point is None:
        # if caller didn't pass points, use the first and last node in route as
        # origin/destination
        origin_destination_lats = (G.nodes[origin_node]['y'], G.nodes[destination_node]['y'])
        origin_destination_lons = (G.nodes[origin_node]['x'], G.nodes[destination_node]['x'])
    else:
        # otherwise, use the passed points as origin/destination
        origin_destination_lats = (origin_point[0], destination_point[0])
        origin_destination_lons = (origin_point[1], destination_point[1])
        orig_dest_node_color = orig_dest_point_color

    # scatter the origin and destination points
    ax.scatter(origin_destination_lons, origin_destination_lats, s=orig_dest_node_size,
               c=orig_dest_node_color, alpha=orig_dest_node_alpha, edgecolor=node_edgecolor, zorder=4)

    # plot the route lines
    lines = node_list_to_coordinate_lines(G, route, use_geom, weight_col)

    # add the lines to the axis as a linecollection
    lc = LineCollection(lines, colors=route_color, linewidths=route_linewidth, alpha=route_alpha, zorder=3)
    ax.add_collection(lc)

    # save and show the figure as specified
    fig, ax = ox.save_and_show(fig, ax, save, show, close, filename, file_format, dpi, axis_off)
    return fig, ax

# Let's plot our path with the custom functions
# Visualize static map
fig, ax = plot_graph_route(G, midday_path, weight_col='Keskpva_aa')

# Add the travel time as title
ax.set_xlabel("Drive time {t: .1f} minutes.".format(t=midday_t))