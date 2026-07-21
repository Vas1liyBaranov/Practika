import streamlit as st
import os
import re
import hashlib
from datetime import datetime
from db import init_db, add_document, get_all_documents, update_document_status, delete_document
from parsers import parse_file
from chunking import chunk_document
from vector_store import init_collection, upsert_chunks, delete_by_document_id
from rag import ask

# настройка страницы
st.set_page_config(
    page_title="Корпоративная база знаний",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Инициализация состояния для темы
if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = False

# стили с поддержкой темной темы
def get_css(dark_mode=False):
    if dark_mode:
        bg_color = "#1a1a2e"
        text_color = "#e0e0e0"
        card_bg = "#2d2d44"
        border_color = "#3d3d5c"
        input_bg = "#2d2d44"
        header_color = "#60A5FA"
        sub_color = "#94A3B8"
        badge_bg = "#3d3d5c"
        badge_text = "#e0e0e0"
        footer_bg = "linear-gradient(135deg, #0F172A 0%, #1E293B 100%)"
    else:
        bg_color = "#ffffff"
        text_color = "#0F172A"
        card_bg = "#F8FAFC"
        border_color = "#E2E8F0"
        input_bg = "#F8FAFC"
        header_color = "#0F172A"
        sub_color = "#64748B"
        badge_bg = "#F1F5F9"
        badge_text = "#0F172A"
        footer_bg = "linear-gradient(135deg, #0F172A 0%, #1E293B 100%)"
    
    return f"""
    <style>
        .main-header {{
            font-size: 2.8rem;
            font-weight: 800;
            color: {header_color};
            margin-bottom: 0.2rem;
            letter-spacing: -1px;
            text-align: center;
        }}
        .sub-header {{
            font-size: 1.1rem;
            color: {sub_color};
            text-align: center;
            margin-bottom: 2rem;
            border-bottom: 2px solid {border_color};
            padding-bottom: 0.8rem;
            font-weight: 300;
        }}
        .sub-header span {{
            color: #60A5FA;
            font-weight: 500;
        }}
        .sidebar-title {{
            font-size: 0.7rem;
            text-transform: uppercase;
            letter-spacing: 1px;
            color: #94A3B8;
            margin: 20px 0 12px 0;
            font-weight: 600;
        }}
        .sidebar-divider {{
            border: none;
            border-top: 1px solid {border_color};
            margin: 16px 0;
        }}
        .stat-mini {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 6px 0;
            border-bottom: 1px solid {border_color};
        }}
        .stat-mini-label {{
            color: {sub_color};
            font-size: 0.8rem;
        }}
        .stat-mini-value {{
            font-weight: 600;
            color: {text_color};
            font-size: 0.9rem;
        }}
        .status-badge {{
            display: inline-block;
            padding: 2px 14px;
            border-radius: 20px;
            font-size: 0.7rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.2px;
        }}
        .status-indexed {{
            background: #D1FAE5;
            color: #065F46;
        }}
        .status-processing {{
            background: #FEF3C7;
            color: #92400E;
        }}
        .status-error {{
            background: #FEE2E2;
            color: #991B1B;
        }}
        .status-uploaded {{
            background: #DBEAFE;
            color: #1E40AF;
        }}
        .doc-row {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 8px 12px;
            background: {card_bg};
            border-radius: 6px;
            border: 1px solid {border_color};
            margin-bottom: 4px;
            transition: 0.15s;
        }}
        .doc-row:hover {{
            background: {badge_bg};
        }}
        .doc-name {{
            font-weight: 500;
            color: {text_color};
            font-size: 0.9rem;
        }}
        .doc-meta {{
            color: {sub_color};
            font-size: 0.75rem;
        }}
        .stButton > button {{
            background: #0F172A;
            color: white;
            border: none;
            border-radius: 8px;
            padding: 8px 20px;
            font-weight: 500;
            transition: 0.15s;
            width: 100%;
        }}
        .stButton > button:hover {{
            background: #1E293B;
            box-shadow: 0 2px 8px rgba(15,23,42,0.2);
        }}
        .stTextInput > div > div > input {{
            border-radius: 8px;
            border: 1px solid {border_color};
            padding: 10px 16px;
            font-size: 0.95rem;
            background: {input_bg};
            color: {text_color};
        }}
        .stTextInput > div > div > input:focus {{
            border-color: #0F172A;
            box-shadow: 0 0 0 3px rgba(15,23,42,0.1);
            background: white;
            color: #0F172A;
        }}
        .footer {{
            margin-top: 60px;
            padding: 24px 0 16px 0;
            background: {footer_bg};
            border-top: 2px solid #1E3A5F;
            border-radius: 12px 12px 0 0;
            text-align: center;
            width: 100%;
        }}
        .footer-content {{
            max-width: 800px;
            margin: 0 auto;
            padding: 0 20px;
        }}
        .footer-name {{
            font-size: 1.05rem;
            font-weight: 600;
            color: #F1F5F9;
        }}
        .footer-info {{
            font-size: 0.9rem;
            color: #94A3B8;
            margin: 4px 0;
        }}
        .footer-info span {{
            color: #60A5FA;
            font-weight: 500;
        }}
        .footer-divider {{
            width: 60px;
            height: 2px;
            background: #1E3A5F;
            margin: 10px auto;
            border-radius: 2px;
        }}
        .footer-company {{
            font-size: 0.85rem;
            color: #64748B;
        }}
        .footer-company span {{
            color: #94A3B8;
        }}
        .footer-year {{
            font-size: 0.75rem;
            color: #475569;
            margin-top: 4px;
        }}
        .answer-card {{
            background: {card_bg};
            border-radius: 8px;
            padding: 16px 20px;
            border-left: 4px solid #1E3A5F;
            margin: 12px 0;
        }}
        .source-card {{
            background: {card_bg};
            border-radius: 6px;
            padding: 12px 16px;
            border: 1px solid {border_color};
            margin: 8px 0;
            transition: 0.15s;
        }}
        .source-card:hover {{
            border-color: #1E3A5F;
            box-shadow: 0 2px 8px rgba(0,0,0,0.04);
        }}
        .score-high {{
            color: #22C55E;
            font-weight: 600;
        }}
        .score-medium {{
            color: #F59E0B;
            font-weight: 600;
        }}
        .score-low {{
            color: #EF4444;
            font-weight: 600;
        }}
        @media (max-width: 768px) {{
            .main-header {{
                font-size: 2rem;
            }}
        }}
        
        .stApp {{
            background-color: {bg_color};
        }}
        .stMarkdown {{
            color: {text_color};
        }}
        .stSelectbox > div > div {{
            background-color: {input_bg};
            color: {text_color};
        }}
    </style>
    """

st.markdown(get_css(st.session_state.dark_mode), unsafe_allow_html=True)

# Переключатель темной темы в сайдбаре
with st.sidebar:
    st.session_state.dark_mode = st.toggle("Темная тема", value=st.session_state.dark_mode)

st.markdown('<div class="main-header">Корпоративная база знаний</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Поиск по документам с <span>проверяемыми источниками</span></div>', unsafe_allow_html=True)

if "init" not in st.session_state:
    init_db()
    init_collection()
    st.session_state.init = True

# статистика
from db import get_all_documents, get_all_queries
docs = get_all_documents()
queries = get_all_queries()

indexed_count = sum(1 for d in docs if d['status'] == 'indexed')
st.sidebar.markdown('<div class="sidebar-title">Статистика</div>', unsafe_allow_html=True)
st.sidebar.markdown(f"""
<div class="stat-mini">
    <span class="stat-mini-label">Документов</span>
    <span class="stat-mini-value">{len(docs)}</span>
</div>
<div class="stat-mini">
    <span class="stat-mini-label">Проиндексировано</span>
    <span class="stat-mini-value">{indexed_count}</span>
</div>
<div class="stat-mini">
    <span class="stat-mini-label">Запросов</span>
    <span class="stat-mini-value">{len(queries)}</span>
</div>
""", unsafe_allow_html=True)
st.sidebar.markdown('<hr class="sidebar-divider">', unsafe_allow_html=True)

# боковое меню
st.sidebar.markdown('<div class="sidebar-title">Навигация</div>', unsafe_allow_html=True)
if "tab" not in st.session_state:
    st.session_state.tab = "Чат"
if st.sidebar.button("Чат", use_container_width=True):
    st.session_state.tab = "Чат"
if st.sidebar.button("Документы", use_container_width=True):
    st.session_state.tab = "Документы"
if st.sidebar.button("История", use_container_width=True):
    st.session_state.tab = "История"

tab = st.session_state.tab

# ============================================================
# 1. ЧАТ
# ============================================================
if tab == "Чат":
    st.markdown("### Задайте вопрос")
    
    question = st.text_input(
        "Вопрос",
        placeholder="Например: Сколько длится стажировка?",
        label_visibility="collapsed",
        key="question_input"
    )
    
    col1, col2 = st.columns([3, 1])
    with col1:
        search_clicked = st.button("Найти ответ", type="primary", use_container_width=True)
    
    if search_clicked:
        if not question or question.strip() == "":
            st.warning("Пожалуйста, введите вопрос")
        else:
            with st.spinner("Поиск..."):
                result = ask(question)
            
            st.markdown("---")
            
            if result.get('status') == 'not_found':
                st.warning("Информация не найдена")
                st.markdown(result.get('answer', ''))
                
                if result.get("sources"):
                    with st.expander("Ближайшие совпадения", expanded=False):
                        for i, src in enumerate(result["sources"], 1):
                            st.markdown(f"""
                            **{i}. {src['filename']}** (стр. {src['page']})
                            - Релевантность: {src['score']:.3f}
                            - {src['excerpt'][:150]}...
                            """)
            else:
                st.markdown("### Ответ")
                
                answer = result.get("answer", "Нет ответа")
                
                # Очищаем ответ от лишних символов
                answer = re.sub(r'\s*\(Источник:[^)]*\)', '', answer)
                answer = re.sub(r'---', '', answer)
                answer = re.sub(r'Документы:', '', answer)
                answer = re.sub(r'Вопрос:', '', answer)
                
                # Форматируем ответ
                formatted_answer = re.sub(
                    r'`([^`]+)`', 
                    r'<span style="color: #00cc44; font-family: monospace; font-weight: 500;">\1</span>', 
                    answer
                )
                
                formatted_answer = formatted_answer.replace('\n', '<br>')
                
                st.markdown(f"""
                <div style="
                    font-family: 'Segoe UI', sans-serif;
                    font-size: 15px;
                    line-height: 1.9;
                    white-space: pre-wrap;
                    word-wrap: break-word;
                    color: {('white' if st.session_state.dark_mode else '#1a1a1a')};
                    background: transparent;
                    padding: 0;
                ">
                    {formatted_answer}
                </div>
                """, unsafe_allow_html=True)
                
                # Показываем источники
                if result and result.get("sources"):
                    with st.expander("Источники", expanded=True):
                        for i, src in enumerate(result["sources"], 1):
                            score = src['score']
                            if score > 0.7:
                                score_text = "Высокая"
                                color = "#22C55E"
                            elif score > 0.5:
                                score_text = "Средняя"
                                color = "#F59E0B"
                            else:
                                score_text = "Низкая"
                                color = "#EF4444"
                            
                            st.markdown(f"""
                            <div style="
                                background: {('#2d2d44' if st.session_state.dark_mode else '#F8FAFC')};
                                border-radius: 6px;
                                padding: 12px 16px;
                                border: 1px solid {('#3d3d5c' if st.session_state.dark_mode else '#E2E8F0')};
                                margin: 8px 0;
                            ">
                                <b>{i}. {src['filename']}</b> (страница {src['page']})
                                <br>
                                <span style="color: {color};">Релевантность: {src['score']:.3f} ({score_text})</span>
                                <br>
                                <span style="color: #64748B; font-size: 0.9rem;">{src['excerpt'][:300]}</span>
                            </div>
                            """, unsafe_allow_html=True)
                
                # Кнопки оценки
                col1, col2 = st.columns(2)
                if col1.button("Полезно", use_container_width=True):
                    from db import add_feedback
                    add_feedback(result["query_id"], 1)
                    st.success("Спасибо за оценку!")
                    st.rerun()
                if col2.button("Неполезно", use_container_width=True):
                    from db import add_feedback
                    add_feedback(result["query_id"], 0)
                    st.success("Спасибо за оценку!")
                    st.rerun()

# ============================================================
# 2. ДОКУМЕНТЫ
# ============================================================
elif tab == "Документы":
    st.markdown("### Управление документами")
    
    # Пакетная загрузка
    uploaded_files = st.file_uploader(
        "Загрузите документы (можно несколько)",
        type=["pdf", "docx", "txt", "md"],
        help="Поддерживаются PDF, DOCX, TXT, MD",
        accept_multiple_files=True
    )
    
    if uploaded_files:
        UPLOAD_DIR = "data/uploads"
        os.makedirs(UPLOAD_DIR, exist_ok=True)
        
        existing_docs = get_all_documents()
        existing_filenames = [doc['filename'] for doc in existing_docs]
        
        for uploaded_file in uploaded_files:
            if uploaded_file.name in existing_filenames:
                st.warning(f"Документ {uploaded_file.name} уже загружен, пропускаем")
                continue
            
            file_path = os.path.join(UPLOAD_DIR, uploaded_file.name)
            
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            doc_id = add_document(uploaded_file.name, uploaded_file.type, file_path)
            update_document_status(doc_id, "processing")
            
            with st.spinner(f"Индексация: {uploaded_file.name}"):
                try:
                    file_type, parsed = parse_file(file_path)
                    chunks = chunk_document(parsed)
                    
                    if chunks:
                        upsert_chunks(doc_id, uploaded_file.name, chunks)
                        update_document_status(doc_id, "indexed", chunks_count=len(chunks))
                        st.success(f"Документ {uploaded_file.name} проиндексирован ({len(chunks)} фрагментов)")
                    else:
                        update_document_status(doc_id, "error", "Нет текста для индексации")
                        st.error(f"Документ {uploaded_file.name} не содержит текста")
                except Exception as e:
                    update_document_status(doc_id, "error", str(e))
                    st.error(f"Ошибка индексации {uploaded_file.name}: {e}")
        
        st.rerun()
    
    st.markdown("---")
    st.markdown("### Список документов")
    
    docs = get_all_documents()
    
    if docs:
        # Поиск по документам
        search_doc = st.text_input("Поиск по названию", placeholder="Введите название документа...")
        
        filtered_docs = docs
        if search_doc:
            filtered_docs = [d for d in docs if search_doc.lower() in d['filename'].lower()]
        
        for doc in filtered_docs:
            col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
            col1.markdown(f'<span class="doc-name">{doc["filename"]}</span>', unsafe_allow_html=True)
            
            status = doc['status']
            if status == "indexed":
                col2.markdown('<span class="status-badge status-indexed">Готов</span>', unsafe_allow_html=True)
            elif status == "processing":
                col2.markdown('<span class="status-badge status-processing">Обработка</span>', unsafe_allow_html=True)
            elif status == "error":
                col2.markdown('<span class="status-badge status-error">Ошибка</span>', unsafe_allow_html=True)
            else:
                col2.write(status)
            
            col3.markdown(f'<span class="doc-meta">{doc["chunks_count"]}</span>', unsafe_allow_html=True)
            
            if col4.button("Удалить", key=f"del_{doc['id']}"):
                delete_by_document_id(doc['id'])
                if doc.get('file_path') and os.path.exists(doc['file_path']):
                    os.remove(doc['file_path'])
                delete_document(doc['id'])
                st.success(f"Документ {doc['filename']} удалён")
                st.rerun()
    else:
        st.info("Документы не загружены")

# ============================================================
# 3. ИСТОРИЯ
# ============================================================
elif tab == "История":
    st.markdown("### История запросов")
    
    # Получаем обновленный список запросов
    from db import get_all_queries
    queries = get_all_queries()
    
    col1, col2, col3 = st.columns([2, 1, 1])
    with col2:
        if st.button("Статистика", use_container_width=True):
            if queries:
                total_queries = len(queries)
                answered = sum(1 for q in queries if q['status'] == 'answered')
                avg_latency = sum(q['latency_ms'] for q in queries if q['latency_ms']) / total_queries if total_queries > 0 else 0
                
                st.info(f"""
                Статистика запросов:
                - Всего: {total_queries}
                - Отвечено: {answered}
                - Среднее время: {avg_latency:.0f} мс
                """)
            else:
                st.info("Нет данных для статистики")
    
    with col3:
        if st.button("Очистить всё", use_container_width=True):
            import sqlite3
            conn = sqlite3.connect("storage/app.db")
            cursor = conn.cursor()
            cursor.execute("DELETE FROM queries")
            cursor.execute("DELETE FROM query_sources")
            cursor.execute("DELETE FROM feedback")
            conn.commit()
            conn.close()
            st.success("История очищена")
            st.rerun()
    
    # Фильтр по статусу
    status_filter = st.selectbox(
        "Фильтр по статусу",
        ["Все", "answered", "processing", "error", "not_found"]
    )
    
    filtered_queries = queries
    if status_filter != "Все":
        filtered_queries = [q for q in queries if q['status'] == status_filter]
    
    if filtered_queries:
        for q in filtered_queries:
            # Безопасное получение ответа
            answer_display = q.get('answer')
            if answer_display is None:
                answer_display = "Нет ответа"
            elif not isinstance(answer_display, str):
                answer_display = str(answer_display)
            
            with st.expander(f"{q['question']} — {q['created_at'][:16]}"):
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.write(f"**Ответ:** {answer_display[:200]}{'...' if len(answer_display) > 200 else ''}")
                    st.write(f"**Статус:** {q['status']}")
                    st.write(f"**Время:** {q['latency_ms']} мс")
                    
                    if q.get('sources'):
                        st.write("**Источники:**")
                        for src in q['sources']:
                            score = src.get('score', 0)
                            if score > 0.7:
                                color_text = "зеленый"
                            elif score > 0.5:
                                color_text = "желтый"
                            else:
                                color_text = "красный"
                            st.caption(f"{src.get('filename', 'unknown')} (стр. {src.get('page', 1)}, релевантность: {score:.3f})")
                with col2:
                    if st.button("Удалить", key=f"del_query_{q['id']}"):
                        import sqlite3
                        conn = sqlite3.connect("storage/app.db")
                        cursor = conn.cursor()
                        cursor.execute("DELETE FROM queries WHERE id = ?", (q['id'],))
                        cursor.execute("DELETE FROM query_sources WHERE query_id = ?", (q['id'],))
                        cursor.execute("DELETE FROM feedback WHERE query_id = ?", (q['id'],))
                        conn.commit()
                        conn.close()
                        st.success("Запрос удалён")
                        st.rerun()
    else:
        st.info("История пуста")

# ============================================================
# ФУТЕР
# ============================================================
st.markdown("""
<div class="footer">
    <div class="footer-content">
        <div class="footer-name">Баранов Василий Геннадьевич</div>
        <div class="footer-info">
            ИДБ-23-06 · 3 курс · <span>МГТУ «СТАНКИН»</span>
        </div>
        <div class="footer-divider"></div>
        <div class="footer-company">
            Производственная практика · <span>ООО «Амбрелла Альянс»</span>
        </div>
        <div class="footer-year">2026</div>
    </div>
</div>
""", unsafe_allow_html=True)