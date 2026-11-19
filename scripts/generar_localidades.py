import json
import unicodedata
from pathlib import Path

import requests


API_PROVINCIAS = "https://apis.datos.gob.ar/georef/api/provincias"
API_LOCALIDADES = "https://apis.datos.gob.ar/georef/api/localidades"
DESTINO = Path(__file__).resolve().parents[1] / "project" / "static" / "data" / "localidades_ar.json"


def clave_orden(texto):
    return unicodedata.normalize("NFD", texto).encode("ascii", "ignore").decode().lower()


def obtener_provincias():
    respuesta = requests.get(API_PROVINCIAS, params={"campos": "nombre", "max": 100}, timeout=30)
    respuesta.raise_for_status()
    return sorted((p["nombre"] for p in respuesta.json()["provincias"]), key=clave_orden)


def obtener_localidades():
    localidades = {}
    inicio = 0
    while True:
        respuesta = requests.get(
            API_LOCALIDADES,
            params={"campos": "nombre,provincia", "max": 1000, "inicio": inicio},
            timeout=60,
        )
        respuesta.raise_for_status()
        datos = respuesta.json()
        for localidad in datos["localidades"]:
            provincia = localidad["provincia"]["nombre"]
            localidades.setdefault(provincia, set()).add(localidad["nombre"].strip())
        inicio += datos["cantidad"]
        if inicio >= datos["total"] or datos["cantidad"] == 0:
            break
    return localidades


def main():
    provincias = obtener_provincias()
    localidades = obtener_localidades()
    for provincia in provincias:
        localidades.setdefault(provincia, set())

    datos = {
        "provincias": provincias,
        "localidades": {
            provincia: sorted(nombres, key=clave_orden)
            for provincia, nombres in sorted(localidades.items(), key=lambda par: clave_orden(par[0]))
        },
    }

    DESTINO.parent.mkdir(parents=True, exist_ok=True)
    DESTINO.write_text(json.dumps(datos, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")

    total_localidades = sum(len(nombres) for nombres in datos["localidades"].values())
    print(f"Provincias: {len(datos['provincias'])}")
    print(f"Localidades: {total_localidades}")
    print(f"Nogoyá en Entre Ríos: {'Nogoyá' in datos['localidades'].get('Entre Ríos', [])}")
    print(f"Archivo: {DESTINO}")


if __name__ == "__main__":
    main()
