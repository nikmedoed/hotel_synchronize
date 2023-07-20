import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta


with open("wubook_req_log.txt", 'r', encoding='utf8') as f:
    data=f.read()

# Создаем DataFrame из строк с данными
data_list = [line.split('\t') for line in data.strip().split('\n')]
df = pd.DataFrame(data_list, columns=['date', 'identifier', 'response_code', 'calling_function'])
df['date'] = pd.to_datetime(df['date'])

# Убираем микросекунды из даты и времени
df['date'] = df['date'].dt.strftime('%Y-%m-%d %H:%M:%S')

# Преобразуем дату обратно в datetime и устанавливаем ее в качестве индекса
df['date'] = pd.to_datetime(df['date'])
df.set_index('date', inplace=True)

# Фильтруем данные за последний час
# end_time = df.index.max()
end_time = datetime.now()
start_time = end_time - timedelta(hours=1)
df = df[start_time:end_time]

# Группируем данные по идентификатору и подсчитываем количество записей для каждого идентификатора
grouped_data = df.groupby('identifier').size()

# Строим столбчатую диаграмму
if not grouped_data.empty:
    # Строим столбчатую диаграмму
    plt.figure(figsize=(10, 6))
    grouped_data.plot(kind='bar', color='skyblue', edgecolor='black')
    plt.xlabel('Identifier')
    plt.ylabel('Count')
    plt.title('Количество запросов вубук по объектам за последний час')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.show()
else:
    print("Нет данных за последний час.")