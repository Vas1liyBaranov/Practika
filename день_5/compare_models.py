#Задание №1
import time
from sklearn.datasets import load_breast_cancer
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline
from sklearn.tree import DecisionTreeClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

X, y = load_breast_cancer(return_X_y=True)
X_train, X_test, y_train, y_test = train_test_split( X, y, test_size=0.25, random_state=42, stratify=y)

models = { "Дерево решений": DecisionTreeClassifier(max_depth=4, random_state=42),
    "Простая нейросеть": make_pipeline(StandardScaler(),MLPClassifier(hidden_layer_sizes=(32,), max_iter=1000, random_state=42))}

for name, model in models.items():
    start = time.perf_counter()
    model.fit(X_train, y_train)
    train_time = time.perf_counter() - start

    y_pred = model.predict(X_test)
    print(name)
    print("Время обучения:", round(train_time, 4), "сек")
    print("Accuracy:", round(accuracy_score(y_test, y_pred), 3))
    print("Precision:", round(precision_score(y_test, y_pred), 3))
    print("Recall:", round(recall_score(y_test, y_pred), 3))
    print("F1:", round(f1_score(y_test, y_pred), 3))
    print()

#Задание №2
# ВЕС — число, определяющее важность входа для нейрона. Модель сама подбирает веса в процессе обучения.
# LOSS — ошибка модели. Показывает, насколько предсказание отличается от правильного ответа. Чем меньше, тем лучше.
# BACKPROP — алгоритм, который передаёт ошибку от выхода к входам и корректирует веса, чтобы в следующий раз ошибка была меньше.

#Задание №3
# ТИПЫ ДАННЫХ -> ПОДХОДЯЩАЯ АРХИТЕКТУРА:
# Табличные данные → Деревья решений, Random Forest (работают с таблицами, не требуют масштабирования)
# Текст -> Transformer (LLM) (учитывают порядок слов и контекст)
# Изображения -> CNN (анализируют пространственную структуру)
# Временные ряды, звук -> LSTM, Transformer (учитывают последовательность во времени)
# Большие данные -> Глубокие нейросети (способны выучить сложные зависимости)