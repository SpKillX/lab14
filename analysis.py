import polars as pl
import duckdb
import time
import matplotlib.pyplot as plt

def main():
    json_file = "accidents_data.json"
    parquet_file = "accidents_cleaned.parquet"

    print("\nЗагрузка данных")
    df = pl.read_ndjson(json_file)
    print("Первые 5 строк:")
    print(df.head(5))
    print(f"Схема данных: {df.schema}")

    print("\nОчистка данных")
    df_cleaned = df.drop_nulls(subset=["region", "date"]).unique(subset=["id"])
    
    df_cleaned = df_cleaned.with_columns([
        pl.col("fatalities").cast(pl.Int32),
        pl.col("injured").cast(pl.Int32),
        pl.col("accidents_count").cast(pl.Int32)
    ])
    print(f"Количество строк после очистки: {df_cleaned.height}")

if __name__ == "__main__":
    main()