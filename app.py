import streamlit as st
import google.generativeai as genai
import pypdf
import pandas as pd
import json

# --- CẤU HÌNH TRANG ---
st.set_page_config(page_title="Chấm Điểm Đồ Án - AI Auto", layout="wide", page_icon="🎓")

# --- CSS TÙY CHỈNH CHO GIAO DIỆN GỌN GÀNG ---
st.markdown("""
<style>
    .stButton>button {width: 100%; background-color: #ff4b4b; color: white;}
    .reportview-container {margin-top: -2em;}
    h1 {text-align: center; color: #2e86c1;}
</style>
""", unsafe_allow_html=True)

# --- TIÊU ĐỀ ---
st.title("🎓 APP CHẤM ĐIỂM BÁO CÁO TỰ ĐỘNG (AUTO-DETECT)")

# --- SIDEBAR: CẤU HÌNH ---
with st.sidebar:
    st.header("1. Nhập Key & Chọn Model")
    api_key = st.text_input("Dán API Key vào đây:", type="password")
    
    selected_model = None
    
    if api_key:
        try:
            # TỰ ĐỘNG DÒ TÌM MODEL HỢP LỆ VỚI KEY
            genai.configure(api_key=api_key)
            available_models = []
            for m in genai.list_models():
                if 'generateContent' in m.supported_generation_methods:
                    available_models.append(m.name)
            
            if available_models:
                st.success(f"✅ Đã tìm thấy {len(available_models)} model khả dụng.")
                # Ưu tiên chọn flash hoặc pro nếu có
                default_index = 0
                for i, m in enumerate(available_models):
                    if "flash" in m:
                        default_index = i
                        break
                selected_model = st.selectbox("Chọn Model:", available_models, index=default_index)
            else:
                st.error("Key hợp lệ nhưng không tìm thấy Model nào. Hãy thử tạo Key mới.")
        except Exception as e:
            st.error(f"❌ Key không hoạt động: {e}")
            st.info("Hãy vào aistudio.google.com tạo Key mới.")

    st.markdown("---")
    st.markdown("**Hướng dẫn nhanh:**")
    st.markdown("1. Nhập API Key -> Đợi App tự tìm Model.")
    st.markdown("2. Tải file PDF báo cáo.")
    st.markdown("3. Bấm 'Chấm điểm ngay'.")

# --- HÀM XỬ LÝ ---
def extract_text_from_pdf(uploaded_file):
    try:
        pdf_reader = pypdf.PdfReader(uploaded_file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text()
        return text
    except:
        return None

def grade_submission(text, model_name):
    # Cấu hình AI trả về JSON
    model = genai.GenerativeModel(
        model_name=model_name,
        generation_config={"response_mime_type": "application/json"}
    )

    prompt = f"""
    Đóng vai GVHD và GVPB chấm điểm báo cáo môn Lập trình Python (Thang 10).
    
    **TIÊU CHÍ (20% mỗi mục):**
    1. CLO1: Tổng quan (GVHD: logic, GVPB: so sánh).
    2. CLO2: Giải thuật (GVHD: rõ ràng, GVPB: tối ưu).
    3. CLO3: GUI (GVHD: chạy được, GVPB: thân thiện).
    4. CLO4: Đánh giá (GVHD: có minh chứng, GVPB: phân tích sâu).
    5. CLO5: Báo cáo (GVHD: trình bày, GVPB: chuyên nghiệp).

    **OUTPUT JSON (Bắt buộc):**
    {{
        "chi_tiet": [
            {{
                "tieu_chi": "CLO1", "d_gvhd": <0-10>, "d_gvpb": <0-10>, 
                "nx_gvhd": "ngắn gọn", "nx_gvpb": "ngắn gọn"
            }},
            {{
                "tieu_chi": "CLO2", "d_gvhd": <0-10>, "d_gvpb": <0-10>, 
                "nx_gvhd": "...", "nx_gvpb": "..."
            }},
            {{
                "tieu_chi": "CLO3", "d_gvhd": <0-10>, "d_gvpb": <0-10>, 
                "nx_gvhd": "...", "nx_gvpb": "..."
            }},
            {{
                "tieu_chi": "CLO4", "d_gvhd": <0-10>, "d_gvpb": <0-10>, 
                "nx_gvhd": "...", "nx_gvpb": "..."
            }},
            {{
                "tieu_chi": "CLO5", "d_gvhd": <0-10>, "d_gvpb": <0-10>, 
                "nx_gvhd": "...", "nx_gvpb": "..."
            }}
        ],
        "nhan_xet_chung": "..."
    }}
    **NỘI DUNG:** {text}
    """
    
    try:
        response = model.generate_content(prompt)
        return json.loads(response.text)
    except Exception as e:
        return {"error": str(e)}

# --- GIAO DIỆN CHÍNH ---
col_upload, col_action = st.columns([2, 1])

with col_upload:
    uploaded_file = st.file_uploader("Tải file báo cáo (PDF)", type="pdf")

if uploaded_file and selected_model:
    with col_action:
        st.write("") # Spacer
        st.write("") # Spacer
        btn_grade = st.button("🚀 CHẤM ĐIỂM NGAY")

    if btn_grade:
        with st.spinner("⏳ Đang đọc và chấm điểm..."):
            text_content = extract_text_from_pdf(uploaded_file)
            if text_content:
                result = grade_submission(text_content, selected_model)
                
                if "error" in result:
                    st.error(f"Lỗi AI: {result['error']}")
                else:
                    # Xử lý kết quả
                    data = []
                    t_gvhd = t_gvpb = 0
                    for i in result["chi_tiet"]:
                        row = {
                            "Tiêu chí": i["tieu_chi"],
                            "Điểm GVHD": i["d_gvhd"],
                            "NX GVHD": i["nx_gvhd"],
                            "Điểm GVPB": i["d_gvpb"],
                            "NX GVPB": i["nx_gvpb"],
                            "ĐTB": (i["d_gvhd"] + i["d_gvpb"])/2
                        }
                        data.append(row)
                        t_gvhd += i["d_gvhd"]
                        t_gvpb += i["d_gvpb"]
                    
                    final = (t_gvhd/5 + t_gvpb/5)/2
                    
                    # Hiển thị
                    st.divider()
                    c1, c2, c3 = st.columns(3)
                    c1.metric("GVHD (50%)", f"{t_gvhd/5:.1f}")
                    c2.metric("GVPB (50%)", f"{t_gvpb/5:.1f}")
                    c3.metric("TỔNG KẾT", f"{final:.1f}", delta="Đạt" if final >=4 else "Không đạt")
                    
                    st.dataframe(pd.DataFrame(data).style.background_gradient(subset=["ĐTB"], cmap="Greens"), use_container_width=True)
                    st.info(f"**Kết luận:** {result['nhan_xet_chung']}")
            else:
                st.error("File PDF lỗi hoặc không có chữ.")
elif not api_key:
    st.info("👈 Vui lòng nhập API Key bên trái.")