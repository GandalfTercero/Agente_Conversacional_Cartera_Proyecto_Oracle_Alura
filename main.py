"""
Punto de entrada del proyecto.

Uso:
    python main.py [ruta_al_pdf]

Si no se indica ruta, usa por defecto datos/reporte_cartera_erp_v2.pdf.

Al iniciar, extrae los datos del PDF de cartera y abre un chat en la
terminal donde puedes preguntarle al agente sobre la cartera
(ej: "¿quién tiene el saldo más alto?", "¿qué clientes deben hace más
de 90 días?", "dame un resumen de alertas").

Escribe 'salir' para terminar.
"""

import sys

from orquestador import cargar_datos, crear_agente


def main():
    ruta_pdf = sys.argv[1] if len(sys.argv) > 1 else "datos/reporte_cartera_erp_v2.pdf"

    print(f"Cargando y extrayendo datos de: {ruta_pdf} ...")
    cargar_datos(ruta_pdf)
    print("Datos cargados. Agente listo.\n")

    agente = crear_agente()

    print("Escribe tu pregunta sobre la cartera (o 'salir' para terminar).\n")
    while True:
        pregunta = input("Tú: ").strip()
        if pregunta.lower() in {"salir", "exit", "quit"}:
            print("¡Hasta luego!")
            break
        if not pregunta:
            continue

        respuesta = agente.invoke({"entrada": pregunta})
        print(f"\nAgente: {respuesta['output']}\n")


if __name__ == "__main__":
    main()
    