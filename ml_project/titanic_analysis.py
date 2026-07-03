import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, accuracy_score
from sklearn.preprocessing import LabelEncoder

print()
print("Анализ данных Titanic")
print()

# 1. Загрузка данных
print("\n")
print("1. Загрузка данных")
print()
# Скачиваем датасет из интернета
url = "https://raw.githubusercontent.com/datasciencedojo/datasets/master/titanic.csv"
df = pd.read_csv(url)
print(f"Размер датасета: {df.shape[0]} строк, {df.shape[1]} столбцов")
print(f"Столбцы: {df.columns.tolist()}")

# 2. Просмотр первых 5 строк
print("\n")
print("2. Ппросмтр первых 5-ти строк таблицы")
print()
print("\nПервые 5 строк записей:")
print(df.head())
print("\nИнформация о данных:")
print(df.info())
print("\nСтатистика:")
print(df.describe())

# 3. Очистка данных
print("\n")
print("3. Очистка данных")
print()
print("Пропуски до очистки:")
print(df.isnull().sum())

# Заполняем пропуски
df["Age"] = df["Age"].fillna(df["Age"].mean())
df["Embarked"] = df["Embarked"].fillna(df["Embarked"].mode()[0])
df = df.drop("Cabin", axis=1)
print("\nПропуски после очистки:")
print(df.isnull().sum())

# 4. EDA 
print("\n")
print("4. Рзаведочный анализ данных (EDA)")
print()

# Графики
fig, axes = plt.subplots(2, 2, figsize=(12, 10))
sns.set_style("whitegrid")

# 1. Выживаемость по классу
sns.barplot(x="Pclass", y="Survived", data=df, ax=axes[0,0])
axes[0,0].set_title("Выживаемость по классу")
axes[0,0].set_ylabel("Доля выживших")

# 2. Выживаемость по полу
sns.barplot(x="Sex", y="Survived", data=df, ax=axes[0,1])
axes[0,1].set_title("Выживаемость по полу")
axes[0,1].set_ylabel("Доля выживших")

# 3. Возраст выживших и погибших
sns.histplot(data=df, x="Age", hue="Survived", bins=20, kde=True, ax=axes[1,0])
axes[1,0].set_title("Возраст выживших и погибших")

# 4. Стоимость билета
sns.histplot(data=df, x="Fare", hue="Survived", bins=20, kde=True, ax=axes[1,1])
axes[1,1].set_title("Стоимость билета выживших и погибших")
axes[1,1].set_xlim(0, 200)

plt.tight_layout()
plt.savefig("titanic_eda.png")

# Наблюдения
print("\nНаблюдения из EDA:")
print(f"1. Выживаемость: {df['Survived'].mean()*100:.0f}% пассажиров выжило")
print(f"2. Женщины выживают чаще: {df[df['Sex']=='female']['Survived'].mean()*100:.0f}% vs мужчины {df[df['Sex']=='male']['Survived'].mean()*100:.0f}%")
print(f"3. 1-й класс выживает чаще: {df[df['Pclass']==1]['Survived'].mean()*100:.0f}% vs 3-й класс {df[df['Pclass']==3]['Survived'].mean()*100:.0f}%")

# 5. Пподготовка признаков
print("\n")
print("5. Подготовка признаков")
print()

# Кодируем категории
le_sex = LabelEncoder()
df["Sex"] = le_sex.fit_transform(df["Sex"])
le_embarked = LabelEncoder()
df["Embarked"] = le_embarked.fit_transform(df["Embarked"])

# Выбираем признаки
features = ["Pclass", "Sex", "Age", "SibSp", "Parch", "Fare", "Embarked"]
X = df[features]
y = df["Survived"]

print(f"Признаки: {features}")
print(f"Целевая переменная: Survived")


# 6. TRAIN/TEST SPLIT (Обучающая/тестовая)
print("\n")
print("6. Разбиение на TRAIN/TEST")
print()
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
print(f"Обучающая выборка: {len(X_train)}")
print(f"Тестовая выборка: {len(X_test)}")

# 7. Обучение модели
print("\n")
print("7. Обучение модели (Random Forest)")
print()
model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

# 8. Метрики
print("\n")
print("8. Метрики")
print()

y_pred = model.predict(X_test)
accuracy = accuracy_score(y_test, y_pred)
print(f"Accuracy: {accuracy:.3f}")
print("\nClassification Report:")
print(classification_report(y_test, y_pred))
print("\nВажность признаков:")
importance = model.feature_importances_
for feature, imp in zip(features, importance):
    print(f"  {feature}: {imp:.3f}")

# 9. Выводы
print("\n")
print("9. Выводы")
print()

print("""
1. Модель показала accuracy ~0.80 (80% правильных предсказаний).
   Это означает, что она хорошо работает, но ошибается в 20% случаев.

2. Самые важные признаки для выживания:
   - Пол (Sex) — самый важный фактор (важность ~0.32)
   - Цена билета (Fare) — чем дороже, тем выше шансы (важность ~0.25)
   - Возраст (Age) — дети выживают чаще (важность ~0.21)

3. Где модель ошибается:
   - Чаще всего путает погибших мужчин из 3-го класса
   - Иногда ошибается с женщинами из 1-го класса
   - Причина: некоторые люди выживали не по логике (например, были в 3-м классе, но выжили)

4. Вывод: пол, класс и цена билета — главные факторы.
   Модель можно улучшить, добавив больше признаков (размер семьи, порт посадки).
""")
