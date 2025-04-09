import os
import rasterio
from rasterio.warp import transform_bounds
import folium
import random
from shapely.geometry import box

# Поиск всех файлов tif в текущей директории
tif_files = []
for root, dirs, files in os.walk("."):
    for file in files:
        if file.endswith(".tif"):
            tif_files.append((os.path.join(root, file)))


def get_tif_bounds(tif_path):
    """Получает границы TIF-файла в координатах WGS84 (EPSG:4326)"""
    with rasterio.open(tif_path) as src:
        # Получаем границы в исходной системе координат
        left, bottom, right, top = src.bounds

        # Преобразуем границы в WGS84 (EPSG:4326)
        bounds_wgs84 = transform_bounds(src.crs, 'EPSG:4326', left, bottom, right, top)

        return bounds_wgs84


def get_random_color():
    """Генерирует случайный цвет"""
    r = random.random()
    g = random.random()
    b = random.random()
    return f'rgba({int(r * 255)}, {int(g * 255)}, {int(b * 255)})'


def create_tif_map(tif_files, output_html='tif_zones_map.html'):
    """Создает карту с наложенными границами TIF-файлов"""
    # Список для хранения всех границ
    all_bounds = []

    # Обрабатываем каждый файл
    for tif_file in tif_files:
        try:
            bounds = get_tif_bounds(tif_file)
            all_bounds.append((os.path.basename(tif_file), bounds))
            print(f"Обработан файл: {os.path.basename(tif_file)}")
        except Exception as e:
            print(f"Ошибка при обработке файла {tif_file}: {str(e)}")

    if not all_bounds:
        print("Не удалось получить границы ни для одного файла.")
        return

    # Вычисляем центр для начального отображения карты
    all_lats = []
    all_lons = []

    for _, (minx, miny, maxx, maxy) in all_bounds:
        all_lons.extend([minx, maxx])
        all_lats.extend([miny, maxy])

    center_lat = (max(all_lats) + min(all_lats)) / 2
    center_lon = (max(all_lons) + min(all_lons)) / 2

    # Создаем карту с центром в вычисленной точке
    m = folium.Map(location=[center_lat, center_lon], zoom_start=10)

    # Добавляем каждую зону на карту с уникальным цветом
    for filename, (minx, miny, maxx, maxy) in all_bounds:
        # Генерируем случайный цвет для зоны
        color = get_random_color()

        # Создаем полигон границы
        bounds_polygon = box(minx, miny, maxx, maxy)

        # Добавляем полигон на карту
        folium.GeoJson(
            data={
                "type": "Feature",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[[p[0], p[1]] for p in bounds_polygon.exterior.coords]]
                },
                "properties": {"name": filename
                               }
            },
            style_function=lambda x, color=color: {
                'fillColor': color,
                'color': 'black',
                'weight': 2,
                'fillOpacity': 0.3
            },
            tooltip=folium.Tooltip(filename)
        ).add_to(m)

        # Добавляем подпись в центре полигона
        center_lat = (miny + maxy) / 2
        center_lon = (minx + maxx) / 2

        folium.Marker(
            location=[center_lat, center_lon],
            icon=folium.DivIcon(
                icon_size=(100, 36),
                icon_anchor=(50, 18),
                html=f'<div style="font-size: 10pt; color: black; background-color: white; '
                     f'border: 1px solid black; border-radius: 3px; padding: 3px; '
                     f'opacity: 0.8; text-align: center;">{filename}</div>'
            )
        ).add_to(m)

    # Добавляем слой спутниковых снимков (после OpenStreetMap)
    folium.TileLayer(
        tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
        attr='Esri',
        name='Esri Satellite',
        overlay=False
    ).add_to(m)

    # Добавляем OpenStreetMap как базовый слой
    folium.TileLayer(
        tiles='OpenStreetMap',
        name='OpenStreetMap',
        overlay=False,
        control=True
    ).add_to(m)

    # Добавляем контроллер слоев
    folium.LayerControl().add_to(m)

    # Сохраняем карту в HTML-файл
    m.save(output_html)
    print(f"Карта сохранена в файл {output_html}")

    return m


print(f"Найдено {len(tif_files)} TIF-файлов.")

# Создаем карту с наложенными зонами
create_tif_map(tif_files)
