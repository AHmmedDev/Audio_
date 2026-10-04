import streamlit as st
from google import genai
import tempfile
import os
import math

st.set_page_config(page_title="مُحوّل الصوت الذكي", layout="centered")

st.title("🎙️ مُحوّل الصوت الذكي (10 دقائق/قسم)")
st.write("تفريغ المقاطع الصوتية الطويلة (عربي + إنجليزي) عبر الخادم مباشرة.")

# 1. إدخال مفتاح API
api_key = st.text_input("أدخل مفتاح Gemini API الخاص بك:", type="password")

# 2. رفع الملف الصوتي
uploaded_file = st.file_uploader("اختر ملف الصوت (M4A, MP3, WAV, AAC)", type=["m4a", "mp3", "wav", "aac"])

if uploaded_file and api_key:
    try:
        client = genai.Client(api_key=api_key)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            file_bytes = uploaded_file.getvalue()
            total_size = len(file_bytes)
            
            # تقطيع الملف ثنائياً بحجم 10MB (ما يقارب 10 دقائق صوت)
            chunk_size = 10 * 1024 * 1024
            num_chunks = math.ceil(total_size / chunk_size)
            
            st.success(f"تم إعداد الملف وجاهزيته لـ {num_chunks} أجزاء!")
            
            full_transcription = []
            
            for idx in range(num_chunks):
                st.subheader(f"القسم {idx + 1}")
                
                start = idx * chunk_size
                end = min((idx + 1) * chunk_size, total_size)
                chunk_data = file_bytes[start:end]
                
                # استخدام الامتداد الأصلي للملف
                file_ext = os.path.splitext(uploaded_file.name)[1] or ".m4a"
                chunk_path = os.path.join(tmpdir, f"chunk_{idx}{file_ext}")
                
                with open(chunk_path, "wb") as f:
                    f.write(chunk_data)
                
                st.audio(chunk_path)
                
                if st.button(f"تحويل القسم {idx + 1}", key=f"btn_{idx}"):
                    with st.spinner("جاري التفريغ النصي بواسطة Gemini..."):
                        audio_file = client.files.upload(file=chunk_path)
                        
                        prompt = "قم بتفريغ المقطع الصوتي بدقة إلى نص مكتوب. المقطع يحتوي على لغة عربية مع كلمات إنجليزية فقط (Mixed Arabic and English). اكتب الكلام كما قيل تماماً وبدون أي شروحات إضافية."
                        
                        response = client.models.generate_content(
                            model='gemini-1.5-flash',
                            contents=[prompt, audio_file]
                        )
                        
                        text = response.text
                        st.text_area("النص المفرغ:", value=text, height=150)
                        full_transcription.append(f"--- [القسم {idx + 1}] ---\n" + text)

            if full_transcription:
                st.hr()
                st.subheader("📝 النص المجمع النهائي:")
                final_text = "\n\n".join(full_transcription)
                st.text_area("النص الكامل:", value=final_text, height=300)
                st.download_button("تحميل كملف نصي TXT", data=final_text, file_name="transcription.txt")

    except Exception as e:
        st.error(f"حدث خطأ: {e}")
