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

    print("\nАгрегация (Polars)")
    start_polars = time.time()
    summary = df_cleaned.group_by("region").agg([
        pl.col("fatalities").sum().alias("total_fatalities_sum"),
        pl.col("injured").mean().alias("avg_injured"),
        pl.col("accidents_count").min().alias("min_accidents"),
        pl.col("accidents_count").max().alias("max_accidents"),
        pl.len().alias("count_records")
    ])
    polars_time = time.time() - start_polars
    print(summary)
    print(f"Время выполнения Polars: {polars_time:.5f} сек")

    df_cleaned.write_parquet(parquet_file)
    print(f"\nДанные сохранены в {parquet_file}")

    print("\nАнализ DuckDB")
    conn = duckdb.connect()
    
    start_duckdb = time.time()
    query_result = conn.execute(f"""
        SELECT 
            region,
            SUM(fatalities) as total_fatalities_sum,
            AVG(injured) as avg_injured,
            MIN(accidents_count) as min_accidents,
            MAX(accidents_count) as max_accidents,
            COUNT(*) as count_records
        FROM '{parquet_file}'
        GROUP BY region
        ORDER BY total_fatalities_sum DESC
    """).fetchdf()
    duckdb_time = time.time() - start_duckdb
    print(query_result)
    print(f"Время выполнения DuckDB: {duckdb_time:.5f} сек")

    print("\nГенерация графиков")

    plt.figure(figsize=(10, 6))
    plt.bar(query_result['region'], query_result['total_fatalities_sum'], color='red', alpha=0.7)
    plt.title('Суммарное количество погибших в ДТП по регионам')
    plt.xlabel('Регион')
    plt.ylabel('Количество')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig('fatalities_by_region.png')
    
    plt.figure(figsize=(8, 8))
    plt.pie(query_result['count_records'], labels=query_result['region'], autopct='%1.1f%%', startangle=140)
    plt.title('Доля зафиксированных инцидентов по регионам')
    plt.savefig('records_distribution.png')
    
    print("Графики сохранены: fatalities_by_region.png, records_distribution.png")

if __name__ == "__main__":
    main()