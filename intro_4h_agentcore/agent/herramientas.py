"""Herramientas del agente. Las reglas de negocio viven aquí, en código, no en el prompt:
el modelo decide *cuándo* llamar a una herramienta, pero no puede saltarse lo que hace."""
from strands import tool

from datos import HOY, PEDIDOS, POLITICA


def _pedido_del_cliente(pedido_id: str, cliente_id: str) -> dict | None:
    pedido = PEDIDOS.get(pedido_id.strip().upper())
    # Un cliente solo ve sus pedidos. El cliente_id lo fija el servidor, no el modelo.
    if pedido is None or pedido["cliente_id"] != cliente_id:
        return None
    return pedido


def evaluar_reembolso(pedido: dict) -> dict:
    """Regla de devolución, determinista (también se usa en los tests)."""
    if pedido["estado"] != "entregado":
        return {"elegible": False, "motivo": "El pedido aún no se ha entregado."}
    if pedido["categoria"] in POLITICA["categorias_excluidas"]:
        return {"elegible": False, "motivo": "Los productos de higiene no admiten devolución."}
    dias = (HOY - pedido["fecha_entrega"]).days
    if dias > POLITICA["plazo_dias"]:
        return {"elegible": False, "motivo": f"Han pasado {dias} días; el plazo es de {POLITICA['plazo_dias']}."}
    importe = round(pedido["importe"] - POLITICA["coste_devolucion"], 2)
    return {"elegible": True, "importe_reembolso": importe, "dias_desde_entrega": dias}


def crear_herramientas(cliente_id: str) -> list:
    """Devuelve las herramientas ligadas a un cliente concreto."""

    @tool
    def consultar_pedido(pedido_id: str) -> dict:
        """Consulta el estado de un pedido del cliente actual.

        Args:
            pedido_id: identificador del pedido, por ejemplo TN-1001.
        """
        pedido = _pedido_del_cliente(pedido_id, cliente_id)
        if pedido is None:
            return {"error": "No existe ningún pedido con ese identificador para este cliente."}
        datos = {k: v for k, v in pedido.items() if k != "cliente_id"}
        if datos.get("fecha_entrega"):
            datos["fecha_entrega"] = datos["fecha_entrega"].isoformat()
        return datos

    @tool
    def politica_devoluciones() -> str:
        """Devuelve la política oficial de devoluciones de TiendaNova."""
        return POLITICA["texto"]

    @tool
    def calcular_reembolso(pedido_id: str) -> dict:
        """Calcula si un pedido del cliente actual se puede devolver y cuánto se reembolsaría.

        Args:
            pedido_id: identificador del pedido, por ejemplo TN-1001.
        """
        pedido = _pedido_del_cliente(pedido_id, cliente_id)
        if pedido is None:
            return {"error": "No existe ningún pedido con ese identificador para este cliente."}
        return evaluar_reembolso(pedido)

    return [consultar_pedido, politica_devoluciones, calcular_reembolso]
