import requests
from bs4 import BeautifulSoup
import pyodbc
import pandas as pd

# Пример функции для получения информации о товаре с сайта Ozon
def fetch_product_info_from_ozon(product_name):
    search_url = f"https://www.ozon.ru/search/?from_global=true&text={product_name}"
    response = requests.get(search_url)
    
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        # Найдите необходимую информацию в HTML
        # Пример:
        product_list = soup.find_all('div', class_='product-card')  # Измените на реальный селектор
        for product in product_list:
            title = product.find('span', class_='product-card__title').text
            # Соберите дополнительные параметры
            print(title)

# Пример использования функции
fetch_product_info_from_ozon("Некоторый товар")


# Путь к файлу базы данных Access
db_path = r'C:\hahaton\rzd\bd.accdb'

# Строка подключения
conn_str = (
    r"Driver={Microsoft Access Driver (*.mdb, *.accdb)};"  # Драйвер для работы с Access
    r"DBQ=" + db_path + ";"  # Путь к базе данных
)

# Подключение к базе данных Access
conn = pyodbc.connect(conn_str)
cursor = conn.cursor()

# Основная таблица
table_name = "MTR"

# Извлечение уникальных свойств
query = f"SELECT DISTINCT Наименование, Маркировка, Параметры, ОКПД2 FROM {table_name};"
cursor.execute(query)
products = cursor.fetchall()

# Преобразование данных в DataFrame для удобства обработки
df = pd.DataFrame(products, columns=['Наименование', 'Маркировка', 'Параметры', 'ОКПД2'])

# Группировка по уникальным свойствам
grouped = df.groupby(['Наименование', 'Маркировка', 'ОКПД2']).agg(lambda x: list(x.unique())).reset_index()

# Создание групп товаров с не более чем 10 уникальными свойствами
product_groups = []
for _, group in grouped.iterrows():
    properties = group[['Наименование', 'Маркировка', 'ОКПД2']].values.tolist()
    if len(properties) <= 10:
        product_groups.append(properties)

# Создание новой таблицы для групп товаров
group_table_name = "ProductGroups"
if cursor.execute(f"SELECT COUNT(*) FROM MSysObjects WHERE Name='{group_table_name}' AND Type=1;").fetchone()[0] > 0:
    cursor.execute(f"DROP TABLE {group_table_name};")
    conn.commit()

# Создание таблицы
create_table_query = f"""
CREATE TABLE {group_table_name} (
    id AUTOINCREMENT PRIMARY KEY,
    Наименование TEXT,
    Маркировка TEXT,
    ОКПД2 TEXT
);
"""
cursor.execute(create_table_query)
conn.commit()

# Вставка сгруппированных товаров в таблицу
insert_query = f"INSERT INTO {group_table_name} (Наименование, Маркировка, ОКПД2) VALUES (?, ?, ?)"
for group in product_groups:
    cursor.execute(insert_query, group[0], group[1], group[2])  # Пример вставки только первых трех свойств
    conn.commit()

# Закрытие курсора и соединения
cursor.close()
conn.close()

print("Группировка товаров завершена.")
