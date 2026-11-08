# Adquisición y normalización de datos de ventas

Pre-entrega · Data Science II (Coderhouse) — Módulo 3: Adquisición y Normalización con Pandas.

Simula un escenario donde los datos de ventas llegan de distintos departamentos en formatos diferentes: un **CSV de transacciones** y un **Excel con el catálogo de productos**. El proyecto los integra, los limpia y exporta un dataset final en **Parquet**.

## Estructura

```
├── data/
│   ├── raw/
│   │   ├── transacciones.csv      # id_transaccion, id_producto, cantidad, fecha
│   │   └── productos.xlsx         # hoja "maestro": id_producto, nombre_producto, precio_unitario
│   └── processed/
│       └── ventas_final.parquet   # archivo de salida
├── notebooks/
│   └── adquisicion_ventas.ipynb   # proceso paso a paso, con explicaciones
├── src/
│   └── pipeline.py                # mismo proceso como script reproducible
├── requirements.txt
└── README.md
```

## Requisitos

- Python 3.10 o superior
- Librerías: `pandas`, `openpyxl` (lectura de Excel), `pyarrow` (escritura de Parquet), `jupyter` (para el notebook)

## Cómo reproducir

```bash
git clone <URL-del-repo>
cd <carpeta-del-repo>

python -m venv .venv
# Windows: .venv\Scripts\activate   |   macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt

# Opción A: script
python src/pipeline.py

# Opción B: notebook
jupyter notebook notebooks/adquisicion_ventas.ipynb   # ejecutar todas las celdas
```

Ambas opciones generan `data/processed/ventas_final.parquet`.

## Proceso

1. **Adquisición**: `pd.read_csv` para las transacciones y `pd.read_excel(engine="openpyxl")` para el maestro.
2. **Transformación**
   - `fecha` se convierte a `datetime`; los valores inválidos (`"sin fecha"`) pasan a `NaT`.
   - Se eliminan transacciones sin `id_producto` o sin `fecha` (no se pueden atribuir).
   - `cantidad` faltante se imputa con la mediana de cada producto.
   - `id_producto` llega como `float` en el CSV y como texto `"001"` en el Excel: se unifican ambos a `int64` antes del merge.
   - Se elimina un producto duplicado en el maestro.
   - `merge` por `id_producto` con `validate="many_to_one"`; se descartan 2 transacciones con un producto inexistente en el catálogo.
3. **Normalización**: nueva columna `total_venta = cantidad * precio_unitario`.
4. **Validación**: se verifica que no haya nulos en campos críticos y que `fecha` sea `datetime`.
5. **Exportación**: `to_parquet(engine="pyarrow")`.

## Resultado

| | Filas |
|---|---|
| Transacciones originales | 300 |
| Eliminadas por falta de producto o fecha | 9 |
| Eliminadas por producto inexistente | 2 |
| **Dataset final** | **289** |

Columnas finales: `id_transaccion`, `id_producto`, `cantidad`, `fecha`, `nombre_producto`, `precio_unitario`, `total_venta` — sin valores nulos.

> Los archivos fuente son datos de ejemplo generados para el ejercicio, con errores intencionales (nulos, fechas inválidas, tipos distintos en la llave, duplicados) para mostrar la limpieza.
