import pandas as pd

# Скачиваем датасет
url = "https://raw.githubusercontent.com/datasciencedojo/datasets/master/titanic.csv"
df = pd.read_csv(url)

# Простая очистка
df["Age"] = df["Age"].fillna(df["Age"].mean())
df["Embarked"] = df["Embarked"].fillna(df["Embarked"].mode()[0])
df = df.drop("Cabin", axis=1)

# Сохраняем
df.to_csv("titanic_clean.csv", index=False)
print("Файл titanic_clean.csv создан!")
