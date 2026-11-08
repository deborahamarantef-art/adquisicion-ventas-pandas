"""Pipeline de adquisición y normalización de ventas.

Integra un CSV de transacciones con un Excel de maestro de productos,
limpia los datos, calcula total_venta y exporta el resultado a Parquet.

Uso (desde la raíz del repo):
    python src/pipeline.py
"""
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
OUT = ROOT / "data" / "processed" / "ventas_final.parquet"


def cargar_transacciones(ruta: Path) -> pd.DataFrame:
    return pd.read_csv(ruta)


def cargar_productos(ruta: Path) -> pd.DataFrame:
    # engine="openpyxl" requiere tener openpyxl instalado
    return pd.read_excel(ruta, sheet_name="maestro", engine="openpyxl", dtype={"id_producto": str})


def limpiar_transacciones(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    # Fechas a datetime; valores inválidos ("sin fecha") pasan a NaT
    df["fecha"] = pd.to_datetime(df["fecha"], format="%Y-%m-%d", errors="coerce")
    # Sin producto o sin fecha la venta no se puede atribuir -> se elimina
    df = df.dropna(subset=["id_producto", "fecha"])
    # Cantidad faltante -> se imputa con la mediana de ese producto
    df["cantidad"] = df["cantidad"].fillna(
        df.groupby("id_producto")["cantidad"].transform("median")
    )
    df["id_producto"] = df["id_producto"].astype("int64")
    df["cantidad"] = df["cantidad"].astype("int64")
    return df


def limpiar_productos(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    # "001" (texto) -> 1 (entero) para que la llave coincida con el CSV
    df["id_producto"] = df["id_producto"].str.strip().astype("int64")
    df["nombre_producto"] = df["nombre_producto"].str.strip()
    df["precio_unitario"] = df["precio_unitario"].astype("float64")
    return df.drop_duplicates(subset="id_producto")


def integrar(trx: pd.DataFrame, prod: pd.DataFrame) -> pd.DataFrame:
    df = trx.merge(prod, on="id_producto", how="left", validate="many_to_one", indicator=True)
    sin_match = (df["_merge"] == "left_only").sum()
    if sin_match:
        print(f"Aviso: {sin_match} transacciones con id_producto inexistente en el maestro -> eliminadas")
    df = df[df["_merge"] == "both"].drop(columns="_merge")
    df["total_venta"] = (df["cantidad"] * df["precio_unitario"]).round(2)
    return df.sort_values(["fecha", "id_transaccion"]).reset_index(drop=True)


def validar(df: pd.DataFrame) -> None:
    criticos = ["id_transaccion", "id_producto", "cantidad", "fecha",
                "nombre_producto", "precio_unitario", "total_venta"]
    nulos = df[criticos].isna().sum()
    assert nulos.sum() == 0, f"Hay nulos en campos críticos:\n{nulos[nulos > 0]}"
    assert pd.api.types.is_datetime64_any_dtype(df["fecha"]), "fecha no es datetime"


def main() -> pd.DataFrame:
    trx = limpiar_transacciones(cargar_transacciones(RAW / "transacciones.csv"))
    prod = limpiar_productos(cargar_productos(RAW / "productos.xlsx"))
    ventas = integrar(trx, prod)
    validar(ventas)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    ventas.to_parquet(OUT, index=False, engine="pyarrow")
    print(f"OK: {len(ventas)} filas exportadas a {OUT.relative_to(ROOT)}")
    return ventas


if __name__ == "__main__":
    main()
