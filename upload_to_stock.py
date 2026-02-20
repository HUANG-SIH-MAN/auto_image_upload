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

API_KEY = os.getenv("GEMINI_API_KEY")
SS_USER = os.getenv("SS_USER")
SS_PASS = os.getenv("SS_PASS")
LOCATION = os.getenv("LOCATION", "Taiwan")
SS_FTP_HOST = "ftp.shutterstock.com"
MODEL_NAME = os.getenv("MODEL_NAME") 

client = genai.Client(api_key=API_KEY)

def wait_countdown(seconds):
    for i in range(seconds, 0, -1):
        print(f"\r⏳ 冷卻中... 剩餘 {i} 秒後處理下一張 (按 Ctrl+C 可停止)", end="")
        time.sleep(1)
    print("\r" + " " * 60 + "\r", end="")

def get_ai_metadata(image_path):
    try:
        with open(image_path, "rb") as f:
            image_bytes = f.read()

        prompt = f"""
        You are a professional stock photo contributor. 
        Analyze this image (Location: {LOCATION}). 
        Provide:
        1. TITLE: SEO title (max 20 words).
        2. KEYWORDS: 50 keywords separated by commas.
        3. CATEGORY: Pick 1 or 2 from the official list below: 
           [Abstract, Animals/Wildlife, The Arts, Backgrounds/Textures, Beauty/Fashion, Biology, Buildings/Landmarks, Business/Finance, Education, Food and Drink, Healthcare/Medical, Holidays, Industrial, Interiors, Nature, Objects, Parks/Outdoor, People, Religion, Science, Signs/Symbols, Sports/Recreation, Technology, Transportation, Travel].
        
        Format response EXACTLY (Use correct casing for Categories):
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
        
        # 修正分類：確保首字母大寫且逗號後無空格
        raw_category = text.split("CATEGORY:")[1].strip()
        category = ",".join([c.strip().title() for c in raw_category.split(',')])
        
        return title, keywords, category
    except Exception as e:
        print(f"\n❌ AI 分析失敗: {e}")
        return None, None, None

def create_single_csv(image_name, title, keywords, category):
    """為單張圖片生成專用的 CSV 檔案"""
    csv_name = image_name.rsplit('.', 1)[0] + ".csv"
    with open(csv_name, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f)
        writer.writerow(['Filename', 'Description', 'Keywords', 'Categories', 'Editorial', 'Mature content', 'illustration'])
        writer.writerow([image_name, title, keywords, category, 'no', 'no', 'no'])
    return csv_name

def append_to_adobe_csv(file_path, data, headers):
    """Adobe Stock 依然維持一個總表，因為它需要手動上傳"""
    file_exists = os.path.isfile(file_path)
    with open(file_path, 'a', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(headers)
        writer.writerow(data)

def upload_ftp(file_path):
    try:
        ftp = FTP_TLS(SS_FTP_HOST)
        ftp.login(user=SS_USER, passwd=SS_PASS)
        ftp.prot_p()
        with open(file_path, 'rb') as f:
            ftp.storbinary(f'STOR {os.path.basename(file_path)}', f)
        ftp.quit()
        return True
    except Exception as e:
        print(f"❌ FTP 上傳失敗: {e}")
        return False

def main():
    files = [f for f in os.listdir('.') if f.lower().endswith(('.jpg', '.jpeg')) and "_original" not in f]
    if not files: return

    # Adobe 用的匯總表
    ad_csv = f"{LOCATION.replace(',','_').replace(' ','')}_Adobe_Stock.csv"

    print(f"🚀 開始執行！")

    for index, file_name in enumerate(files):
        print(f"[{index+1}/{len(files)}] 正在處理: {file_name}")
        
        title, keywords, category = get_ai_metadata(file_name)
        
        if title:
            # 1. 寫入圖片內 (IPTC)
            subprocess.run(['.\\exiftool.exe', f'-Description={title}', f'-ObjectName={title}', f'-Keywords={keywords}', '-overwrite_original', file_name], capture_output=True)
            
            # 2. 生成此圖片專用的 CSV (Shutterstock)
            temp_ss_csv = create_single_csv(file_name, title, keywords, category)
            
            # 3. 寫入 Adobe 總表
            append_to_adobe_csv(ad_csv, [file_name, title, keywords, '1', ''], 
                                ['Filename', 'Title', 'Keywords', 'Category', 'Releases'])
            
            # 4. 上傳圖片
            if upload_ftp(file_name):
                # 5. 上傳對應的專用 CSV
                if upload_ftp(temp_ss_csv):
                    print(f"✅ {file_name} 與分類資訊已同步上傳")
                    # 上傳後可以刪除這個臨時 CSV 檔案
                    os.remove(temp_ss_csv)
            
            if index < len(files) - 1:
                wait_countdown(65)
        else:
            print(f"⏩ 跳過 {file_name}")

    print("-" * 50)
    print(f"🎉 任務結束！")

if __name__ == "__main__":
    main()