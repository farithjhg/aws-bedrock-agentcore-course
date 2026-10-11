"""Las reglas de negocio son código: se prueban sin modelo y sin AWS.  python -m pytest tests"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "agent"))

from datos import PEDIDOS, POLITICA  # noqa: E402
from herramientas import crear_herramientas, evaluar_reembolso  # noqa: E402


def herramienta(cliente_id, nombre):
    return next(t for t in crear_herramientas(cliente_id) if t.tool_name == nombre)


def test_reembolso_dentro_de_plazo():
    r = evaluar_reembolso(PEDIDOS["TN-1001"])
    assert r == {"elegible": True, "importe_reembolso": 84.95, "dias_desde_entrega": 10}


def test_fuera_de_plazo():
    r = evaluar_reembolso(PEDIDOS["TN-1002"])
    assert not r["elegible"] and "45 días" in r["motivo"]


def test_no_entregado():
    assert not evaluar_reembolso(PEDIDOS["TN-1003"])["elegible"]


def test_politica_es_30_dias_no_14():
    assert POLITICA["plazo_dias"] == 30
    assert "30 días" in herramienta("C-001", "politica_devoluciones")()


def test_un_cliente_no_ve_pedidos_ajenos():
    assert "error" in herramienta("C-002", "consultar_pedido")(pedido_id="TN-1001")
    assert "error" in herramienta("C-002", "calcular_reembolso")(pedido_id="TN-1001")


def test_cliente_ve_sus_pedidos():
    r = herramienta("C-001", "consultar_pedido")(pedido_id="tn-1003")
    assert r["estado"] == "en tránsito" and "cliente_id" not in r
