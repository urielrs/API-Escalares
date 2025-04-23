from flask import Flask, request, jsonify, render_template
import math
from operator import itemgetter

app = Flask(__name__)

coordenadas = {
    'EDO.MEX': (19.2938258568844, -99.65366252023884),
    'QRO': (20.593537489366717, -100.39004057702225),
    'CDMX': (19.432854452264177, -99.13330004822943),
    'SLP': (22.151725492903953, -100.97657666103268),
    'MTY': (25.673156272083876, -100.2974200019319),
    'PUE': (19.063532268065185, -98.30729139446866),
    'GDL': (20.67714565083998, -103.34696388920293),
    'MICH': (19.702614895389996, -101.19228631929688),
    'SON': (29.075273188617818, -110.95962477655333)
}

# Todos los destinos tendrán un peso unitario para simular una sola entrega
pedidos = {k: 1 for k in coordenadas}

def distancia(coord1, coord2):
    lat1, lon1 = coord1
    lat2, lon2 = coord2
    return math.sqrt((lat1 - lat2) ** 2 + (lon1 - lon2) ** 2) * 111

def en_ruta(rutas, c):
    for r in rutas:
        if c in r:
            return r
    return None

def peso_ruta(ruta, pedidos):
    return sum([pedidos[c] for c in ruta])

def calcular_distancia_ruta(ruta, coord, almacen):
    distancia_total = 0
    puntos = [almacen] + [coord[c] for c in ruta] + [almacen]
    for i in range(len(puntos) - 1):
        distancia_total += distancia(puntos[i], puntos[i + 1])
    return distancia_total

def vrp_voraz(coord, pedidos, almacen, max_carga, velocidad_promedio, rendimiento_combustible):
    s = {}
    for c1 in coord:
        for c2 in coord:
            if c1 != c2 and (c2, c1) not in s:
                d_c1_c2 = distancia(coord[c1], coord[c2])
                d_c1_almacen = distancia(coord[c1], almacen)
                d_c2_almacen = distancia(coord[c2], almacen)
                s[(c1, c2)] = d_c1_almacen + d_c2_almacen - d_c1_c2

    s = sorted(s.items(), key=itemgetter(1), reverse=True)

    rutas = []
    for (c1, c2), _ in s:
        rc1 = en_ruta(rutas, c1)
        rc2 = en_ruta(rutas, c2)

        if rc1 is None and rc2 is None:
            if peso_ruta([c1, c2], pedidos) <= max_carga:
                rutas.append([c1, c2])
        elif rc1 is not None and rc2 is None:
            if rc1[0] == c1 and peso_ruta(rc1, pedidos) + pedidos[c2] <= max_carga:
                rc1.insert(0, c2)
            elif rc1[-1] == c1 and peso_ruta(rc1, pedidos) + pedidos[c2] <= max_carga:
                rc1.append(c2)
        elif rc1 is None and rc2 is not None:
            if rc2[0] == c2 and peso_ruta(rc2, pedidos) + pedidos[c1] <= max_carga:
                rc2.insert(0, c1)
            elif rc2[-1] == c2 and peso_ruta(rc2, pedidos) + pedidos[c1] <= max_carga:
                rc2.append(c1)
        elif rc1 != rc2:
            if rc1[0] == c1 and rc2[-1] == c2 and peso_ruta(rc1 + rc2, pedidos) <= max_carga:
                rutas.remove(rc1)
                rc2.extend(rc1)
            elif rc1[-1] == c1 and rc2[0] == c2 and peso_ruta(rc1 + rc2, pedidos) <= max_carga:
                rutas.remove(rc2)
                rc1.extend(rc2)

    detalles_rutas = []
    for ruta in rutas:
        distancia_total = calcular_distancia_ruta(ruta, coord, almacen)
        tiempo_estimado = distancia_total / velocidad_promedio
        combustible_consumido = distancia_total / rendimiento_combustible
        detalles_rutas.append({
            'ruta': ruta,
            'distancia_total_km': distancia_total,
            'tiempo_estimado_horas': tiempo_estimado,
            'combustible_consumido_litros': combustible_consumido
        })

    return detalles_rutas

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/resolver", methods=["POST"])
def resolver():
    data = request.get_json()
    origen = data.get("origen")
    destino = data.get("destino")  # este campo se conserva pero no se usa en el algoritmo
    velocidad = float(data.get("velocidad", 60))
    gasolina = float(data.get("gasolina", 10))
    max_carga = float(data.get("maxCarga", 40))

    almacen = coordenadas.get(origen, (19.432854452264177, -99.13330004822943))

    detalles = vrp_voraz(coordenadas, pedidos, almacen, max_carga, velocidad, gasolina)
    return jsonify({"detalles": detalles})

if __name__ == "__main__":
    app.run(debug=True)
