import streamlit as st
import google.generativeai as genai
from pydub import AudioSegment
import os
import tempfile

st.set_page_config(page_title="مُحوّل الصوت الذكي", layout="centered")

st.title("🎙️ مُحوّل الصوت الذكي (10 دقائق/قسم)")
st.write("تفريغ المقاطع الصوتية الطويلة (عربي + إنجليزي) عبر خادم سريع وبدون انهيار الجوال.")

# 1. إدخال مفتاح API
api_key = st.text_input("أدخل مفتاح Gemini API الخاص بك:", type="password")

if api_key:
    genai.configure(api_key=api_key)

# 2. رفع الملف الصوتي
uploaded_file = st.file_uploader("اختر ملف الصوت (M4A, MP3, WAV, AAC)", type=["m4a", "mp3", "wav", "aac"])

if uploaded_file and api_key:
    st.info("جاري حفظ وتقطيع الملف الصوتي على الخادم...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = os.path.join(tmpdir, uploaded_file.name)
        with open(input_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        # قراءة الصوت وتقطيعه إلى 10 دقائق (600,000 مللي ثانية)
        audio = AudioSegment.from_file(input_path)
        ten_minutes = 10 * 60 * 1000
        chunks = [audio[i:i + ten_minutes] for i in range(0, len(audio), ten_minutes)]
        
        st.success(f"تم تقطيع الصوت بنجاح إلى {len(chunks)} أجزاء!")
        
        full_transcription = []
        model = genai.GenerativeModel('gemini-1.5-flash')

        for idx, chunk in enumerate(chunks):
            st.subheader(f"القسم {idx + 1}")
            chunk_path = os.path.join(tmpdir, f"chunk_{idx}.mp3")
            chunk.export(chunk_path, format="mp3")
            
            st.audio(chunk_path)
            
            if st.button(f"تحويل القسم {idx + 1}", key=f"btn_{idx}"):
                with st.spinner("جاري التفريغ النصي بواسطة Gemini..."):
                    audio_file = genai.upload_file(path=chunk_path)
                    prompt = "قم بتفريغ المقطع الصوتي بدقة إلى نص مكتوب. المقطع يحتوي على لغة عربية مع كلمات إنجليزية فقط (Mixed Arabic and English). اكتب الكلام كما قيل تماماً وبدون أي شروحات إضافة."
                    
                    response = model.generate_content([prompt, audio_file])
                    text = response.text
                    st.text_area("النص المفرغ:", value=text, height=150)
                    full_transcription.append(f"--- [القسم {idx + 1}] ---\n" + text)

        if full_transcription:
            st.hr()
            st.subheader("📝 النص المجمع النهائي:")
            final_text = "\n\n".join(full_transcription)
            st.text_area("النص الكامل:", value=final_text, height=300)
            st.download_button("تحميل كملف نصي TXT", data=final_text, file_name="transcription.txt")
