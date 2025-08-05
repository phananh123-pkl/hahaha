import streamlit as st
from pathlib import Path
from cv import graph, extract_pdf_text  # Giả sử file graph là cv.py

st.set_page_config(page_title="Le Phan Anh CV Bot", layout="wide")
st.title("🤖 Le Phan Anh - CV Feedback Bot")

# ✅ Khởi tạo session state
if "cv_state" not in st.session_state:
    st.session_state.cv_state = None

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# ✅ Upload CV
uploaded_file = st.file_uploader("📄 Tải lên CV (.pdf)", type=["pdf"])

if uploaded_file and st.button("🚀 Phân tích CV"):
    with st.spinner("Đang xử lý CV..."):
        # Lưu tạm file
        temp_path = Path("temp_cv.pdf")
        temp_path.write_bytes(uploaded_file.read())

        # Đọc văn bản
        cv_text = extract_pdf_text(str(temp_path))

        # Tạo input ban đầu
        init_state = {
            "file_path": str(temp_path),
            "cv_text": cv_text,
            "user_query": "",
            "already_ask": False,
            "ask_more": False,
        }

        # Chạy graph
        result = graph.invoke(init_state)
        st.session_state.cv_state = result
        st.session_state.chat_history = []  # Reset chat

        # Hiển thị kết quả phân tích
        st.subheader("🧠 Kết quả phân tích:")
        st.markdown(result.get("parsed_data", "Không có kết quả."))

# ✅ Chat hỏi thêm
if st.session_state.cv_state:
    st.markdown("---")
    st.subheader("💬 Hỏi thêm về CV")

    user_input = st.chat_input("Bạn muốn hỏi gì về CV?")
    if user_input:
        state = st.session_state.cv_state.copy()
        state["user_query"] = user_input
        state["ask_more"] = False
        state["already_ask"] = True

        result = graph.invoke(state)
        message = result.get("mes", "")
        if hasattr(message, "content"):
            message = message.content

        st.session_state.chat_history.append((user_input, message))
        st.session_state.cv_state = result  # cập nhật lại state

    # Hiển thị toàn bộ lịch sử chat
    for q, a in st.session_state.chat_history:
        with st.chat_message("user"):
            st.markdown(q)
        with st.chat_message("assistant"):
            st.markdown(a)