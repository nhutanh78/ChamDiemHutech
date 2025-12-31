import streamlit as st
import google.generativeai as genai
import pypdf
import pandas as pd
import json

# --- CẤU HÌNH TRANG TỐI ƯU MOBILE ---
st.set_page_config(
    page_title="HUTECH Python Grader", 
    layout="centered", # Chuyển sang centered để hiển thị tốt trên điện thoại
    page_icon="🐍"
)

# --- CSS TÙY CHỈNH CHO MOBILE ---
st.markdown("""
<style>
    /* Làm cho font chữ to hơn trên mobile */
    html, body, [class*="css"] { font-size: 16px; }
    .stMetric { background-color: #ffffff; border: 1px solid #ddd; padding: 10px; border-radius: 8px; }
    .clo-box { 
        background-color: #f0f2f6; 
        padding: 15px; 
        border-radius: 10px; 
        margin-bottom: 15px;
        border-left: 5px solid #ff4b4b;
    }
    .role-title { font-weight: bold; margin-top: 10px; display: block; }
    /* Nút bấm to hơn để dễ chạm trên điện thoại */
    .stButton>button { width: 100%; height: 50px; border-radius: 25px; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# --- SIDEBAR ---
with st.sidebar:
    st.header("⚙️ Cấu hình")
    api_key = st.text_input("Nhập API Key:", type="password")
    
    selected_model = None
    if api_key:
        try:
            genai.configure(api_key=api_key)
            models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
            selected_model = st.selectbox("Chọn AI:", models, index=0)
        except: st.error("Lỗi Key!")

    st.markdown("---")
    st.write("**Học phần:** Lập trình Python [cite: 3]")
    st.write("**Viện:** Kỹ thuật HUTECH [cite: 1]")

# --- GIAO DIỆN CHÍNH ---
st.title("🎓 Chấm Điểm Báo Cáo")
st.caption("Dành cho GVHD & GVPB ")

uploaded_file = st.file_uploader("📂 Tải file PDF báo cáo", type="pdf")

if uploaded_file and selected_model:
    if st.button("🚀 BẮT ĐẦU CHẤM ĐIỂM"):
        with st.spinner("Đang phân tích..."):
            # Trích xuất PDF
            pdf_reader = pypdf.PdfReader(uploaded_file)
            text = "".join([page.extract_text() for page in pdf_reader.pages])
            
            # Gọi AI
            model = genai.GenerativeModel(model_name=selected_model, generation_config={"response_mime_type": "application/json"})
            prompt = f"""
            Chấm điểm báo cáo Python theo 5 tiêu chí (CLO1-CLO5), mỗi mục 20%.
            Đóng vai GVHD (ThS. Phạm Quốc Phương) và GVPB (ThS. Huỳnh Phát Huy)[cite: 8, 9, 13].
            Nhận xét phải CHI TIẾT và KHÔNG ĐƯỢC CẮT NGẮN.
            
            JSON format:
            {{
                "results": [
                    {{"tieu_chi": "CLO1: Tổng quan ", "d_gvhd": 8.5, "nx_gvhd": "...", "d_gvpb": 8.0, "nx_gvpb": "..."}},
                    ...
                ],
                "final_comment": "..."
            }}
            Nội dung: {text}
            """
            
            try:
                raw_res = model.generate_content(prompt)
                res = json.loads(raw_res.text)
                
                # Tính điểm tổng kết 
                avg_gvhd = sum(x['d_gvhd'] for x in res['results']) / 5
                avg_gvpb = sum(x['d_gvpb'] for x in res['results']) / 5
                final = (avg_gvhd + avg_gvpb) / 2

                # HIỂN THỊ KẾT QUẢ TỔNG QUÁT
                st.subheader("📊 Điểm Tổng Kết [cite: 10]")
                st.metric("ĐIỂM TRUNG BÌNH", f"{final:.2f}", delta="ĐẠT" if final >= 4 else "K.ĐẠT")
                
                c1, c2 = st.columns(2)
                c1.metric("GVHD (50%)", f"{avg_gvhd:.1f}")
                c2.metric("GVPB (50%)", f"{avg_gvpb:.1f}")

                st.divider()

                # HIỂN THỊ CHI TIẾT DẠNG THẺ (DỄ ĐỌC TRÊN ĐIỆN THOẠI)
                for item in res['results']:
                    with st.container():
                        st.markdown(f"""
                        <div class="clo-box">
                            <h4 style='margin:0;'>{item['tieu_chi']}</h4>
                            <p style='margin:0; color:#666;'>Trung bình mục: {(item['d_gvhd']+item['d_gvpb'])/2:.1f}</p>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Sử dụng tab để tiết kiệm không gian màn hình điện thoại
                        t1, t2 = st.tabs([f"👨‍🏫 GVHD ({item['d_gvhd']})", f"🔍 GVPB ({item['d_gvpb']})"])
                        with t1: st.write(item['nx_gvhd'])
                        with t2: st.write(item['nx_gvpb'])

                st.success(f"**Kết luận hội đồng:** {res['final_comment']}")
                
            except Exception as e: st.error("AI bận, hãy thử lại!")

elif not api_key:
    st.info("Vui lòng nhập API Key ở menu bên trái.")
