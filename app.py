import streamlit as st
import google.generativeai as genai
import pypdf
import pandas as pd
import json

# --- CẤU HÌNH TRANG ---
st.set_page_config(page_title="Hệ thống Chấm điểm Python - HUTECH", layout="wide", page_icon="🐍")

# --- TÙY CHỈNH GIAO DIỆN (CSS) ---
st.markdown("""
<style>
    .main { background-color: #f8f9fa; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    .clo-card { background-color: #ffffff; padding: 20px; border-radius: 10px; border-left: 5px solid #007bff; margin-bottom: 20px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
    .gvhd-text { color: #2e7d32; font-weight: bold; }
    .gvpb-text { color: #c62828; font-weight: bold; }
    .result-header { background: linear-gradient(90deg, #1e3c72 0%, #2a5298 100%); color: white; padding: 20px; border-radius: 10px; text-align: center; margin-bottom: 30px; }
</style>
""", unsafe_allow_html=True)

# --- SIDEBAR: CẤU HÌNH ---
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/vi/f/f3/Logo_HUTECH.png", width=150) # Bạn có thể thay link ảnh logo nếu muốn
    st.header("⚙️ Cấu hình hệ thống")
    api_key = st.text_input("Nhập Gemini API Key:", type="password")
    
    selected_model = None
    if api_key:
        try:
            genai.configure(api_key=api_key)
            available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
            if available_models:
                default_model = next((m for m in available_models if "1.5-flash" in m), available_models[0])
                selected_model = st.selectbox("Chọn phiên bản AI:", available_models, index=available_models.index(default_model))
                st.success("✅ AI đã sẵn sàng")
        except:
            st.error("❌ Key không hợp lệ")

    st.divider()
    st.info("""
    **Thông tin học phần:** [cite: 3]
    - Môn: Lập trình Python
    - GVHD: ThS. Phạm Quốc Phương [cite: 8]
    - GVPB: ThS. Huỳnh Phát Huy [cite: 9]
    """)

# --- HÀM XỬ LÝ PDF ---
def extract_text_from_pdf(uploaded_file):
    try:
        pdf_reader = pypdf.PdfReader(uploaded_file)
        return "".join([page.extract_text() for page in pdf_reader.pages])
    except: return None

# --- HÀM GỌI AI CHẤM ĐIỂM ---
def grade_submission(text, model_name):
    model = genai.GenerativeModel(model_name=model_name, generation_config={"response_mime_type": "application/json"})
    
    prompt = f"""
    Bạn là một chuyên gia lập trình Python. Hãy chấm điểm báo cáo dựa trên các tiêu chí sau (Trọng số mỗi tiêu chí là 20%): 
    1. CLO1: Trình bày tổng quan các phương pháp xử lý.
    2. CLO2: Trình bày phương pháp xử lý và lưu đồ giải thuật.
    3. CLO3: Phát triển giao diện người dùng (GUI).
    4. CLO4: Đánh giá hiệu quả của phương pháp xử lý.
    5. CLO5: Thuyết trình và hoàn thành báo cáo tiểu luận.

    Yêu cầu: Đóng vai GVHD (ThS. Phạm Quốc Phương) và GVPB (ThS. Huỳnh Phát Huy) để đưa ra điểm số (thang 10) và nhận xét CHI TIẾT, DÀI, CỤ THỂ. [cite: 8, 9]
    
    Trả về JSON:
    {{
        "chi_tiet": [
            {{
                "clo": "CLO1: Tổng quan phương pháp",
                "d_gvhd": <0-10>, "nx_gvhd": "<nhận xét dài, chi tiết>",
                "d_gvpb": <0-10>, "nx_gvpb": "<nhận xét dài, phản biện kỹ>"
            }},
            ... (lặp lại cho đủ 5 CLO)
        ],
        "tong_ket": "<nhận xét chung toàn diện về ưu/nhược điểm>"
    }}
    NỘI DUNG BÁO CÁO: {text}
    """
    try:
        response = model.generate_content(prompt)
        return json.loads(response.text)
    except Exception as e: return {"error": str(e)}

# --- GIAO DIỆN CHÍNH ---
st.markdown("<div class='result-header'><h1>HỆ THỐNG CHẤM ĐIỂM BÁO CÁO PYTHON</h1><p>Viện Kỹ thuật HUTECH</p></div>", unsafe_allow_html=True)

uploaded_file = st.file_uploader("📂 Tải báo cáo sinh viên (PDF)", type="pdf")

if uploaded_file and selected_model:
    if st.button("🚀 BẮT ĐẦU PHÂN TÍCH & CHẤM ĐIỂM"):
        with st.spinner("🤖 AI đang đọc và phân tích nội dung báo cáo..."):
            text = extract_text_from_pdf(uploaded_file)
            if text:
                res = grade_submission(text, selected_model)
                if "error" in res:
                    st.error(f"Lỗi: {res['error']}")
                else:
                    # 1. TÍNH TOÁN ĐIỂM SỐ
                    scores = res["chi_tiet"]
                    avg_gvhd = sum(item['d_gvhd'] for item in scores) / 5
                    avg_gvpb = sum(item['d_gvpb'] for item in scores) / 5
                    final_score = (avg_gvhd + avg_gvpb) / 2

                    # 2. HIỂN THỊ ĐIỂM TỔNG QUÁT
                    st.subheader("📊 Kết quả tổng kết")
                    c1, c2, c3 = st.columns(3)
                    with c1: st.metric("Điểm GVHD (50%)", f"{avg_gvhd:.2f}/10")
                    with c2: st.metric("Điểm GVPB (50%)", f"{avg_gvpb:.2f}/10")
                    with c3: 
                        color = "normal" if final_score >= 4 else "inverse"
                        st.metric("ĐIỂM TRUNG BÌNH", f"{final_score:.2f}/10", delta="ĐẠT" if final_score >=4 else "KHÔNG ĐẠT", delta_color=color)

                    st.divider()

                    # 3. HIỂN THỊ CHI TIẾT TỪNG TIÊU CHÍ (Giải quyết vấn đề mất chữ)
                    st.subheader("📝 Nhận xét chi tiết từng chuẩn đầu ra (CLO)")
                    
                    for item in scores:
                        dtb_clo = (item['d_gvhd'] + item['d_gvpb']) / 2
                        with st.container():
                            st.markdown(f"""
                            <div class="clo-card">
                                <h3>{item['clo']}</h3>
                                <p><b>Điểm trung bình mục này: <span style='color:#007bff'>{dtb_clo:.1f}/10</span></b></p>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            col_a, col_b = st.columns(2)
                            with col_a:
                                with st.expander(f"👨‍🏫 GVHD chấm: {item['d_gvhd']}/10", expanded=True):
                                    st.markdown(f"<span class='gvhd-text'>Nhận xét:</span> {item['nx_gvhd']}", unsafe_allow_html=True)
                            with col_b:
                                with st.expander(f"🔍 GVPB chấm: {item['d_gvpb']}/10", expanded=True):
                                    st.markdown(f"<span class='gvpb-text'>Nhận xét:</span> {item['nx_gvpb']}", unsafe_allow_html=True)

                    # 4. NHẬN XÉT CHUNG
                    st.divider()
                    st.subheader("🏁 Kết luận của Hội đồng")
                    st.success(res["tong_ket"])
            else:
                st.error("Không thể đọc nội dung file PDF.")
elif not api_key:
    st.warning("👈 Vui lòng cấu hình API Key ở thanh bên trái để bắt đầu.")
