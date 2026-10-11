"""Datos de ejemplo de TiendaNova. Fechas relativas a hoy, para que las reglas de plazo
funcionen cualquier día que se ejecute la demo."""
from datetime import date, timedelta

HOY = date.today()

CLIENTES = {
    "C-001": {"nombre": "Laura Gómez"},
    "C-002": {"nombre": "Marcos Ruiz"},
}

PEDIDOS = {
    "TN-1001": {
        "cliente_id": "C-001", "producto": "Cafetera espresso", "categoria": "hogar",
        "importe": 89.90, "estado": "entregado", "fecha_entrega": HOY - timedelta(days=10),
    },
    "TN-1002": {
        "cliente_id": "C-002", "producto": "Auriculares inalámbricos", "categoria": "electronica",
        "importe": 59.00, "estado": "entregado", "fecha_entrega": HOY - timedelta(days=45),
    },
    "TN-1003": {
        "cliente_id": "C-001", "producto": "Cepillo de dientes eléctrico", "categoria": "higiene",
        "importe": 39.95, "estado": "en tránsito", "fecha_entrega": None,
        "incidencia": "retraso de 2 días en el centro logístico de Zaragoza",
    },
}

# La política de TiendaNova es más generosa que el mínimo legal de 14 días:
# un modelo sin herramientas tenderá a contestar "14 días" (eso es la alucinación de la demo).
POLITICA = {
    "plazo_dias": 30,
    "coste_devolucion": 4.95,
    "categorias_excluidas": ["higiene"],
    "texto": (
        "Política de devoluciones de TiendaNova: tienes 30 días naturales desde la entrega. "
        "La devolución cuesta 4,95 €, que se descuentan del reembolso. "
        "Los productos de higiene personal no se pueden devolver una vez abiertos."
    ),
}
