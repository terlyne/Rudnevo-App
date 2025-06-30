import pandas as pd

# Читаем Excel файл
df = pd.read_excel('schedule_rudnevo1.xlsx', sheet_name='МГОК')

print("=== АНАЛИЗ EXCEL ФАЙЛА ===")
print(f"Колонки: {df.columns.tolist()}")
print(f"Количество строк: {len(df)}")
print(f"Количество колонок: {len(df.columns)}")
print("\nПервые 5 строк:")
print(df.head())
print("\nТипы данных:")
print(df.dtypes) 