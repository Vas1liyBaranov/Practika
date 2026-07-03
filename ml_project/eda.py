import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Загрузка
df = pd.read_csv("titanic_clean.csv")
print("Размер:", df.shape)

# --- ГРАФИКИ ---
sns.set_style("whitegrid")
fig, axes = plt.subplots(2, 2, figsize=(12, 10))

# 1. Возраст
sns.histplot(df["Age"], bins=30, kde=True, ax=axes[0,0])
axes[0,0].set_title("Возраст")

# 2. Выживаемость
df["Survived"].value_counts().plot(kind="bar", color=["red", "green"], ax=axes[0,1])
axes[0,1].set_title("Выжившие (1) vs Погибшие (0)")

# 3. Выживаемость по классу
sns.barplot(x="Pclass", y="Survived", data=df, ax=axes[1,0])
axes[1,0].set_title("Выживаемость по классу")

# 4. Выживаемость по полу
sns.barplot(x="Sex", y="Survived", data=df, ax=axes[1,1])
axes[1,1].set_title("Выживаемость по полу")

plt.tight_layout()
plt.savefig("eda_plots.png")
print("Графики сохранены")

# --- ПРОПУСКИ ---
print(f"Пропуски: {df.isnull().sum().sum()}")  # 0

# --- ВЫВОДЫ ---
print("\nВЫВОДЫ:")
print(f"- Выжило {df['Survived'].mean()*100:.0f}% пассажиров")
print(f"- Женщины выживают чаще ({df[df['Sex']=='female']['Survived'].mean()*100:.0f}%)")
print(f"- 1-й класс выживает чаще ({df[df['Pclass']==1]['Survived'].mean()*100:.0f}%)")
