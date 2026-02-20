# Auto Image Upload（圖庫自動上傳）

使用 AI 分析圖片並自動產生標題、關鍵字與分類，寫入 IPTC 中繼資料，並支援 **Shutterstock**（FTP 上傳）與 **Adobe Stock**（產出匯總 CSV 供手動上傳）。

## 功能

- **AI 中繼資料**：以 Google Gemini 分析圖片，產生 SEO 標題、約 50 個關鍵字與 1～2 個官方分類
- **IPTC 寫入**：透過 ExifTool 將標題與關鍵字寫入圖片檔（Description、ObjectName、Keywords）
- **Shutterstock**：為每張圖產生專用 CSV，並經 FTP 上傳圖片與 CSV 至 `ftp.shutterstock.com`
- **Adobe Stock**：將所有圖片資訊寫入單一匯總 CSV，供後續在 Adobe Stock 網站手動上傳
- **冷卻機制**：每張圖處理後等待約 65 秒再處理下一張，降低 API／上傳負載

## 環境需求

- Python 3.x
- [ExifTool](https://exiftool.org/)（需將 `exiftool.exe` 放在專案目錄，或確保在系統 PATH 中）
- 網路連線（Gemini API、Shutterstock FTP）

## 安裝

1. 複製專案到本機後進入目錄：

   ```bash
   cd auto_image_upload
   ```

2. 建立虛擬環境（建議）：

   ```bash
   python -m venv venv
   venv\Scripts\activate
   ```

3. 安裝依賴：

   ```bash
   pip install -r requirements.txt
   ```

4. 設定環境變數：複製 `example_env.txt` 為 `.env`，並填入真實值：

   ```bash
   copy example_env.txt .env
   ```

   編輯 `.env`，設定：

   | 變數 | 說明 |
   |------|------|
   | `GEMINI_API_KEY` | Google AI Studio / Gemini API 金鑰 |
   | `SS_USER` | Shutterstock 貢獻者帳號 |
   | `SS_PASS` | Shutterstock 帳號密碼 |
   | `LOCATION` | 拍攝地點（供 AI 參考，預設 `Taiwan`） |
   | `MODEL_NAME` | Gemini 模型名稱（例如 `gemini-2.0-flash`） |

## 使用方式

1. 將要上傳的 **JPG/JPEG** 圖片放在與 `upload_to_stock.py` 同一目錄（檔名不含 `_original`）。
2. 在該目錄執行：

   ```bash
   python upload_to_stock.py
   ```

3. 程式會依序：
   - 呼叫 Gemini 分析每張圖並取得標題、關鍵字、分類
   - 用 ExifTool 寫入 IPTC
   - 產生該圖專用的 Shutterstock CSV 並上傳圖片與 CSV 到 FTP
   - 將該圖資料追加到 Adobe Stock 匯總 CSV
   - 上傳成功後刪除該張圖的臨時 Shutterstock CSV
   - 每張圖之間冷卻約 65 秒（可按 Ctrl+C 中斷）

## 產出檔案

- **每張圖（Shutterstock）**：上傳前會產生與圖片同名的 `.csv`，上傳完成後會自動刪除。
- **Adobe Stock**：同一目錄下會產生 `{LOCATION}_Adobe_Stock.csv`（例如 `Taiwan_Adobe_Stock.csv`），需自行到 Adobe Stock 網站手動上傳此 CSV 與對應圖片。

## 注意事項

- `.env` 含敏感資訊，請勿提交到版控；專案已透過 `.gitignore` 忽略 `.env`。
- 圖片檔、ExifTool 備份檔（`*_original`）等亦在 `.gitignore` 中，可依需求調整。
- 若 Gemini 分析失敗，該張圖會被跳過，不寫入 IPTC、不產生 CSV、不上傳。
- Shutterstock 分類需為官方列表中的 1～2 個，AI 會從程式內建列表挑選並格式化。

## 授權

依專案設定為準。
