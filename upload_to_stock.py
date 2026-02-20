import os
import subprocess
import csv
import time
from dotenv import load_dotenv
from google import genai
from google.genai import types
from ftplib import FTP_TLS

# 讀取 .env 檔案
load_dotenv()

# ================= 從環境變數讀取設定 =================
API_KEY = os.getenv("GEMINI_API_KEY")
SS_USER = os.getenv("SS_USER")
SS_PASS = os.getenv("SS_PASS")
LOCATION = os.getenv("LOCATION", "Taiwan")
SS_FTP_HOST = "ftp.shutterstock.com"

# 指定使用最新的模型
MODEL_NAME = os.getenv("MODEL_NAME") 
# =====================================================

client = genai.Client(api_key=API_KEY)

def get_ai_metadata(image_path):
    print(f"正在分析圖片: {os.path.basename(image_path)}...")
    try:
        with open(image_path, "rb") as f:
            image_bytes = f.read()

        prompt = f"""
        You are a professional stock photo contributor. 
        Analyze this image (Location: {LOCATION}). 
        Provide:
        1. TITLE: SEO title (max 20 words).
        2. KEYWORDS: 50 keywords separated by commas.
        3. CATEGORY: Pick 1 or 2 from: [Abstract, Animals/Wildlife, The Arts, Backgrounds/Textures, Beauty/Fashion, Biology, Buildings/Landmarks, Business/Finance, Education, Food and Drink, Healthcare/Medical, Holidays, Industrial, Interiors, Nature, Objects, Parks/Outdoor, People, Religion, Science, Signs/Symbols, Sports/Recreation, Technology, Transportation, Travel].
        
        Format response EXACTLY:
        TITLE: [Title]
        KEYWORDS: [Keywords]
        CATEGORY: [Category1,Category2]
        """

        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=[prompt, types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg")]
        )
        
        text = response.text
        title = text.split("TITLE:")[1].split("KEYWORDS:")[0].strip()
        keywords = text.split("KEYWORDS:")[1].split("CATEGORY:")[0].strip()
        category = text.split("CATEGORY:")[1].strip().lower()
        
        return title, keywords, category
    except Exception as e:
        print(f"❌ AI 分析失敗: {e}")
        return None, None, None

def create_csv(data_list):
    csv_file = "shutterstock_upload.csv"
    headers = ['Filename', 'Description', 'Keywords', 'Categories', 'Editorial', 'Mature content', 'illustration']
    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        for row in data_list:
            writer.writerow([row['file'], row['title'], row['keys'], row['cat'], 'no', 'no', 'no'])
    return csv_file

def upload_ftp(file_path):
    print(f"正在傳送: {os.path.basename(file_path)}...")
    try:
        ftp = FTP_TLS(SS_FTP_HOST)
        ftp.login(user=SS_USER, passwd=SS_PASS)
        ftp.prot_p()
        with open(file_path, 'rb') as f:
            ftp.storbinary(f'STOR {os.path.basename(file_path)}', f)
        ftp.quit()
        return True
    except Exception as e:
        print(f"❌ FTP 失敗: {e}")
        return False

def main():
    files = [f for f in os.listdir('.') if f.lower().endswith(('.jpg', '.jpeg'))]
    if not files:
        print("沒有找到圖片！")
        return

    all_data = []
    for file_name in files:
        if "_original" in file_name: continue
        
        title, keywords, category = get_ai_metadata(file_name)
        if title:
            # 寫入 Metadata
            subprocess.run(['.\\exiftool.exe', f'-Description={title}', f'-Keywords={keywords}', '-overwrite_original', file_name], capture_output=True)
            
            # 存入列表並上傳圖片
            all_data.append({'file': file_name, 'title': title, 'keys': keywords, 'cat': category})
            if upload_ftp(file_name):
                print(f"✅ 圖片 {file_name} 上傳成功")
            
            time.sleep(1)

    if all_data:
        csv_file = create_csv(all_data)
        print("正在同步分類資訊 (上傳 CSV)...")
        upload_ftp(csv_file)
        print(f"🚀 任務完成！")

if __name__ == "__main__":
    main()