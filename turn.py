import json, geopandas, pandas, random, contextily, re
import matplotlib.pyplot as plt
import matplotlib.patheffects as patheffects
import matplotlib as matplotlib
from adjustText import adjust_text

def play_turn():
    matplotlib.rcParams['hatch.linewidth'] = 3
    pandas.set_option('mode.chained_assignment', None)

    powiaty = geopandas.read_file('map-data/powiaty.shp', encoding = 'utf-8')
    powiaty_shapes = geopandas.read_file('map-data/powiaty-shapes.shp', encoding = 'utf-8')
    powiaty = powiaty.merge(powiaty_shapes, how = 'left', left_index = True, right_index = True)
    powiaty = powiaty.drop(columns = 'code_y')
    powiaty = powiaty.rename(columns = {'code_x': 'code', 'geometry_x': 'geometry', 'geometry_y': 'powiat_shape'})
    powiaty = powiaty.set_geometry('geometry')

    with open('map-data/status.txt', 'r') as f:
        powiaty_left = int(f.readline())
        last_powiat = f.readline().rstrip()

    #find a random powiat, its owner will be conquering
    #a powiat conquering previously has a 40% chance of being chosen for sure
    if last_powiat == '0' or random.random() < 0.6:
        random_powiat_row = powiaty.loc[[random.choice(powiaty.index)]]
    else:
        all_rows_for_conquering_powiat = powiaty[powiaty['belongs_to'] == last_powiat]
        random_powiat_row = all_rows_for_conquering_powiat.loc[[random.choice(all_rows_for_conquering_powiat.index)]]

    random_powiat_code = random_powiat_row['code'].iloc[0]
    random_powiat_belongs_to = random_powiat_row['belongs_to'].iloc[0]
    conquering_powiat_row = powiaty[powiaty['code'] == random_powiat_belongs_to]
    conquering_powiat_code = conquering_powiat_row['code'].iloc[0]
    conquering_powiat_value = conquering_powiat_row['value'].iloc[0]
    conquering_powiat_geometry = conquering_powiat_row['geometry'].iloc[0]

    all_rows_for_conquering_powiat = powiaty[powiaty['belongs_to'] == conquering_powiat_code]
    neighbours = []
    for index, row in powiaty.iterrows():
        if (row['belongs_to'] != conquering_powiat_code):
            if (row['powiat_shape'].touches(conquering_powiat_geometry)):
                neighbours.append(row['code'])

    powiat_to_conquer_code = random.choice(neighbours)
    powiat_to_conquer_row = powiaty[powiaty['code'] == powiat_to_conquer_code]
    powiat_to_conquer_geometry = powiat_to_conquer_row['powiat_shape'].iloc[0]
    powiat_to_conquer_owner_code = powiat_to_conquer_row['belongs_to'].iloc[0]

    conquering_powiat_name = conquering_powiat_row['name'].iloc[0].lstrip('miasto ')
    powiat_to_conquer_name = powiat_to_conquer_row['name'].iloc[0].lstrip('miasto ')

    #merge geometry for conquering powiat
    all_rows_for_conquering_powiat = all_rows_for_conquering_powiat.set_geometry('powiat_shape')
    conquering_powiat_geometry = all_rows_for_conquering_powiat.geometry.unary_union
    conquering_powiat_row['geometry'].iloc[0] = conquering_powiat_geometry

    #find row for conquered powiat owner
    powiat_to_conquer_owner_row = powiaty[powiaty['code'] == powiat_to_conquer_owner_code]
    powiat_to_conquer_owner_name = powiat_to_conquer_owner_row['name'].iloc[0].lstrip('miasto ')
    powiat_to_conquer_owner_value = powiat_to_conquer_owner_row['value'].iloc[0]

    #update values for conquered powiat
    powiaty['belongs_to'][powiaty['code'] == powiat_to_conquer_code] = conquering_powiat_code
    powiaty['value'][powiaty['code'] == powiat_to_conquer_code] = conquering_powiat_value
    conquering_powiat_name[0] = conquering_powiat_name[0].capitalize()

    if (powiat_to_conquer_code != powiat_to_conquer_owner_code):
        message = '{} conquers {} belonging to {}.'.format(conquering_powiat_name, powiat_to_conquer_name, powiat_to_conquer_owner_name)
        print(message)
    else:
        message = '{} conquers {}.'.format(conquering_powiat_name, powiat_to_conquer_name)
        print(message)
        
    #find all rows for conquered powiat owner and merge geometry
    all_rows_for_powiat_to_conquer_owner = powiaty[powiaty['belongs_to'] == powiat_to_conquer_owner_code]
    all_rows_for_powiat_to_conquer_owner = all_rows_for_powiat_to_conquer_owner.set_geometry('powiat_shape')
    powiat_to_conquer_owner_geometry = all_rows_for_powiat_to_conquer_owner.geometry.unary_union
    powiat_to_conquer_row['geometry'].iloc[0] = powiat_to_conquer_geometry
    powiat_to_conquer_owner_row['geometry'].iloc[0] = powiat_to_conquer_owner_geometry
    powiaty['geometry'][powiaty['code'] == powiat_to_conquer_owner_code] = powiat_to_conquer_owner_geometry

    if (all_rows_for_powiat_to_conquer_owner.empty):
        info = '🦀 {} is gone 🦀'.format(powiat_to_conquer_owner_name)
        message = '{}\n{}'.format(message, info)
        print(info)
        powiaty_left -= 1

    info = '{} powiaty left.'.format(powiaty_left)
    message = '{}\n{}'.format(message, info)
    print(info)
    #=== Plotting both maps ===

    cmap = plt.get_cmap('tab20')
    font_dict = {'fontfamily': 'Arial', 'fontsize': 32, 'fontweight': 'bold'}
    path_effects = [patheffects.Stroke(linewidth=4, foreground='black'), patheffects.Normal()]
    texts = []
    fig, ax = plt.subplots(figsize = (20,20))
    powiat_to_conquer = powiat_to_conquer_row.set_geometry('powiat_shape')
    powiat_to_conquer_owner_row = powiat_to_conquer_owner_row.set_geometry('geometry')
    conquering_powiat_row = conquering_powiat_row.set_geometry('geometry')

    #get bbox for the detailed map
    conquering_powiat_row.plot(ax = ax)
    powiat_to_conquer_row.plot(ax = ax)
    if (not all_rows_for_powiat_to_conquer_owner.empty):
        powiat_to_conquer_owner_row.plot(ax = ax)

    x_limit = ax.get_xlim()
    y_limit = ax.get_ylim()
    ax.clear()
    ax.set_axis_off()
    ax.set_aspect('equal')

    #every powiat has to be plotted separately, otherwise it would have a color from a normalized color map
    for i in range(len(powiaty)):
        row = powiaty.loc[[i],]
        row_code = row['code'].iloc[0]
        row_belongs_to = row['belongs_to'].iloc[0]

        if (not powiaty[powiaty['belongs_to'] == row_code].empty):
            row.plot(ax = ax, color = cmap(row['value']), edgecolor = 'k', linewidth = 0.3)

    conquering_powiat_row.plot(ax = ax, color = cmap(conquering_powiat_value), edgecolor = 'green', linewidth = 3)
    powiat_to_conquer_row.plot(ax = ax, color = cmap(powiat_to_conquer_owner_value), edgecolor = cmap(conquering_powiat_value), hatch = '///')
    powiat_to_conquer_row.plot(ax = ax, color = 'none', edgecolor = 'red', linewidth = 3)

    #draw text
    conquering_text = plt.text(s = conquering_powiat_name, x = conquering_powiat_row['geometry'].iloc[0].centroid.x, y = conquering_powiat_row['geometry'].iloc[0].centroid.y, fontdict = font_dict)
    to_conquer_text = plt.text(s = powiat_to_conquer_name, x = powiat_to_conquer_row['powiat_shape'].iloc[0].centroid.x, y = powiat_to_conquer_row['powiat_shape'].iloc[0].centroid.y, fontdict = font_dict)

    conquering_text.set_color('#9DFF9C')
    texts.append(conquering_text)
    to_conquer_text.set_color('#FF977A')
    texts.append(to_conquer_text)

    if (not all_rows_for_powiat_to_conquer_owner.empty):
        powiat_to_conquer_owner_row.plot(ax = ax, color = cmap(powiat_to_conquer_owner_value), edgecolor = 'blue', linewidth = 3)
        to_conquer_owner_text = plt.text(s = powiat_to_conquer_owner_name, x = powiat_to_conquer_owner_row['geometry'].iloc[0].centroid.x, y = powiat_to_conquer_owner_row['geometry'].iloc[0].centroid.y, fontdict = font_dict)
        to_conquer_owner_text.set_color('#788CFF')
        texts.append(to_conquer_owner_text)

    for text in texts:
        text.set_path_effects(path_effects)

    adjust_text(texts, only_move = {'points': 'y', 'texts': 'y'}, va = 'center', autoalign = 'y')
    contextily.add_basemap(ax, source = contextily.sources.ST_TERRAIN_BACKGROUND, zoom = 8)
    plt.savefig('overall-map.png', transparent = True)

    #change few details for the detailed map
    conquering_text.set_position((conquering_powiat_row.geometry.centroid.x, conquering_powiat_row.geometry.centroid.y))
    conquering_text.set_fontsize(40)
    to_conquer_text.set_position((powiat_to_conquer_row.geometry.centroid.x, powiat_to_conquer_row.geometry.centroid.y))
    to_conquer_text.set_fontsize(40)

    if (not all_rows_for_powiat_to_conquer_owner.empty):
        to_conquer_owner_text.set_fontsize(40)

    #set bbox for detailed map
    ax.set_xlim(x_limit)
    ax.set_ylim(y_limit)
    plt.savefig('detail-map.png', transparent = True)

    #finally, update geometry for conquering conquered powiat
    conquering_powiat_geometry = conquering_powiat_geometry.union(powiat_to_conquer_row['powiat_shape'].iloc[0])
    powiaty['geometry'][powiaty['code'] == conquering_powiat_code] = conquering_powiat_geometry
    powiaty = powiaty.drop(columns = 'powiat_shape')
    powiaty.to_file('map-data/powiaty.shp', encoding = 'utf-8')

    with open('map-data/status.txt', 'w') as f:
        f.write('{}\n'.format(powiaty_left))
        f.write(conquering_powiat_code)

    return message, powiaty_left