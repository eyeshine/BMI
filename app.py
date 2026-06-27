# ==========================================
# 專案名稱：自製BMI健康管理程式 (現代網頁 UI 版)
# 目的：使用 Streamlit 內建網頁元件替代 Tkinter，完美適配本地端與雲端環境
# ==========================================

# ------------------------------------------
# 1. 匯入開發所需之標準函式庫與外部套件
# ------------------------------------------
import streamlit as st          # 目的：建構現代化、響應式的網頁型 Windows 本地/雲端 GUI 介面
import pandas as pd             # 目的：處理與轉換二維表格數據，進行資料排序與下載緩衝
import json                     # 目的：解析上傳的 JSON 與封裝要下載的專案資料
import os                       # 目的：處理檔案與路徑的基本判定（此版主要用於環境相容性檢查）
import io                       # 目的：在不產生本地實體檔案的前提下，於記憶體中建立二進位資料流（Buffer）
from datetime import datetime   # 目的：取得當前時間，自動生成絕不重複的下載檔名
import matplotlib.pyplot as plt # 目的：用於繪製歷史健康狀態比例圖（圓餅圖）

# 理由：已根據現代網頁開發規範，將 tkinter 與 filedialog 完全移除，避免執行緒衝突與防礙網頁運作。

# ------------------------------------------
# 2. 初始系統狀態設定 (Streamlit Session State)
# ------------------------------------------
# 目的：在網頁每次因元件觸發重新整理時，保留當前的工作數據。
if 'bmi_history' not in st.session_state:
    st.session_state['bmi_history'] = []  # 用途：存放當前所有的歷史紀錄數據（List of Dict）

# ------------------------------------------
# 3. 核心計算與健康管理建議邏輯
# ------------------------------------------
def calculate_bmi(height_cm, weight_kg):
    """
    目的：依身高與體重計算 BMI 並進行體格判定。
    用途：數據登錄時自動計算結果。
    理由：依據衛生福利部標準進行判定，公分必須先除以 100 換算為公尺才能帶入公式。
    """
    height_m = height_cm / 100.0
    bmi_value = round(weight_kg / (height_m ** 2), 2)
    
    if bmi_value < 18.5:
        status = "體重過輕"
    elif 18.5 <= bmi_value < 24.0:
        status = "健康體重"
    elif 24.0 <= bmi_value < 27.0:
        status = "體重過重"
    elif 27.0 <= bmi_value < 30.0:
        status = "輕度肥胖"
    elif 30.0 <= bmi_value < 35.0:
        status = "中度肥胖"
    else:
        status = "重度肥胖"
        
    return bmi_value, status

def generate_health_advice(status, bmi):
    """
    目的：提供符合受試者體型狀況的日常建議。
    用途：呈現在儀表板右下方的關懷模組中。
    """
    if status == "體重過輕":
        return f"您的 BMI 為 {bmi} ({status})。建議增加營養攝取，並搭配適度重量訓練以增加肌肉量。"
    elif status == "健康體重":
        return f"您的 BMI 為 {bmi} ({status})。體態非常標準！請繼續維持均衡飲食與規律運動。"
    elif status == "體重過重":
        return f"您的 BMI 為 {bmi} ({status})。目前已偏重，建議減少高熱量零食，增加蔬菜攝取並維持有氧運動。"
    else:
        return f"您的 BMI 為 {bmi} ({status})。建議諮詢營養師，調整每日飲食總熱量，並循序漸進增加運動時間。"

# ------------------------------------------
# 4. 網頁介面排版 (Streamlit Windows UI)
# ------------------------------------------
st.set_page_config(page_title="自製BMI健康管理系統", layout="wide")

st.title("🛡️ 自製 BMI 健康管理程式 & 數據分析儀表板")
st.caption("自主學習成果專案 - 使用網頁標準元件（File Uploader & Download Button）建置安全穩定的存取介面。")

# 建立分頁標籤，切換「數據登錄與檔案管理」與「圖表儀表板」
tab1, tab2 = st.tabs(["📝 數據登錄與專案管理", "📊 趨勢儀表板與健康建議"])

# ==========================================
# TAB 1：數據登錄與專案管理
# ==========================================
with tab1:
    # 採用 1:1 的左右對稱雙欄佈局
    col_input, col_file = st.columns([1, 1])
    
    # ------------------------------------------
    # 5.1 數據輸入欄位 (姓名、身高、體重、日期)
    # ------------------------------------------
    with col_input:
        st.subheader("📥 當前健康數據登錄")
        
        name_input = st.text_input("1. 使用者姓名", value="User01")
        height_input = st.number_input("2. 身高 (公分 cm)", min_value=30.0, max_value=250.0, value=170.0, step=0.1)
        weight_input = st.number_input("3. 體重 (公斤 kg)", min_value=10.0, max_value=200.0, value=65.0, step=0.1)
        
        # 理由：符合報告中「以日曆讓使用者選擇日期」之要求
        date_input = st.date_input("4. 記錄日期 (可點擊日曆選擇)", value=datetime.today())
        
        # 按鈕：加入當前紀錄
        if st.button("➕ 新增至當前紀錄", use_container_width=True):
            bmi_calc, status_calc = calculate_bmi(height_input, weight_input)
            new_record = {
                "Name": name_input,
                "Height": height_input,
                "Weight": weight_input,
                "BMI": bmi_calc,
                "Date": str(date_input),  # 理由：轉為字串以利於 JSON 儲存
                "Status": status_calc
            }
            st.session_state['bmi_history'].append(new_record)
            st.success(f"已新增：{name_input} (BMI: {bmi_calc} / {status_calc})")

    # ------------------------------------------
    # 5.2 專案檔案存取與匯出 (使用標準網頁 Uploader/Download 元件)
    # ------------------------------------------
    with col_file:
        st.subheader("📁 專案儲存與讀取 (標準網頁元件)")
        
        # [功能 4] 替代做法：使用 st.file_uploader 進行拖放讀取專案
        # 理由：避免桌面程式的安全沙盒限制，使使用者可透過拖放直接載入歷史 JSON 檔案。
        st.write("**1. 讀取現有專案 (.json)**")
        uploaded_file = st.file_uploader(
            "請上傳您先前儲存的 BMI 歷史紀錄 JSON 檔", 
            type=["json"], 
            key="json_uploader"
        )
        
        # 理由：當使用者上傳檔案時，即時解析資料並覆寫至 Session State
        if uploaded_file is not None:
            try:
                # 使用 json.load 讀取上傳檔案的 Bytes 內容
                loaded_data = json.load(uploaded_file)
                st.session_state['bmi_history'] = loaded_data
                st.success("🎉 專案檔案載入成功！請前往第二分頁查看儀表板結果。")
            except Exception as e:
                st.error(f"檔案解析失敗，可能不是正確的專案格式：{e}")

        st.divider()

        # [功能 3] 替代做法：使用 st.download_button 匯出專案
        # 理由：伺服器無需得知使用者的磁碟路徑，由瀏覽器統一接管下載檔案儲存，符合 Web 標準。
        # 檔名格式為 bmi_project_YYYYMMDD_HHMMSS.json，不重複檔名。
        st.write("**2. 備份與下載目前專案**")
        if st.session_state['bmi_history']:
            # 將當前記憶體中的歷史數據封裝為 JSON 字串
            json_project_data = json.dumps(st.session_state['bmi_history'], ensure_ascii=False, indent=4)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            save_filename = f"bmi_project_{timestamp}.json"
            
            st.download_button(
                label="💾 下載完整專案檔 (.json)",
                data=json_project_data,
                file_name=save_filename,
                mime="application/json",
                use_container_width=True
            )
        else:
            # 理由：當前無資料時，將下載按鈕設為停用 (disabled)，防止下載到空檔案
            st.button("💾 下載完整專案檔 (.json)", disabled=True, use_container_width=True, help="請先新增健康數據才能下載專案。")

        st.divider()

        # [功能 5] 替代做法：匯出 Excel 或 CSV (使用 st.download_button 於記憶體中串流下載)
        # 理由：我們利用 BytesIO（二進位資料流）在記憶體中建立檔案內容，免除伺服器寫入硬碟的權限需求。
        st.write("**3. 匯出 Excel / CSV 數據表格**")
        export_mode = st.radio("選擇下載格式：", ["Excel (.xlsx)", "CSV (.csv)"], horizontal=True)
        
        if st.session_state['bmi_history']:
            df_to_export = pd.DataFrame(st.session_state['bmi_history'])
            timestamp_export = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            if export_mode == "Excel (.xlsx)":
                # 理由：使用 BytesIO 作為虛擬檔案緩衝區，pandas 輸出 Excel 需借助此機制進行記憶體寫入
                buffer = io.BytesIO()
                with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                    df_to_export.to_excel(writer, index=False, sheet_name='BMI紀錄')
                
                excel_filename = f"bmi_data_{timestamp_export}.xlsx"
                st.download_button(
                    label="📥 下載 Excel 報表",
                    data=buffer.getvalue(),
                    file_name=excel_filename,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
            else:
                # 理由：CSV 是文字檔案，可直接利用 string 處理。
                # utf-8-sig 的 BOM 編碼能使 Windows Excel 在開啟此 CSV 時完美呈現中文，不會有亂碼
                csv_data_string = df_to_export.to_csv(index=False, encoding='utf-8-sig')
                csv_filename = f"bmi_data_{timestamp_export}.csv"
                st.download_button(
                    label="📥 下載 CSV 報表",
                    data=csv_data_string,
                    file_name=csv_filename,
                    mime="text/csv",
                    use_container_width=True
                )
        else:
            st.button("📥 下載報表資料", disabled=True, use_container_width=True, help="請先新增健康數據才能匯出資料。")

    # ------------------------------------------
    # 5.3 數據清單表格呈現
    # ------------------------------------------
    st.markdown("### 📋 本地當前工作數據清單")
    if st.session_state['bmi_history']:
        st.dataframe(pd.DataFrame(st.session_state['bmi_history']), use_container_width=True)
        if st.button("🗑️ 清空當前紀錄"):
            st.session_state['bmi_history'] = []
            st.rerun()
    else:
        st.info("尚無資料。請於左側登錄數據，或於右側上傳 JSON 專案檔。")


# ==========================================
# TAB 2：趨勢儀表板與健康建議
# ==========================================
with tab2:
    st.subheader("📊 歷史健康數據 Dashboard")
    
    # 理由：若無資料，繪圖引擎會報錯，故以條件式分支提示使用者先登錄數據
    if not st.session_state['bmi_history']:
        st.warning("目前無任何資料，請先新增數據或在第一分頁上傳專案檔案以生成分析圖表。")
    else:
        # 將資料轉換為 DataFrame 並進行日期型態轉換與排序，確保時序圖顯示正確
        df_plot = pd.DataFrame(st.session_state['bmi_history'])
        df_plot['Date'] = pd.to_datetime(df_plot['Date'])
        df_plot = df_plot.sort_values(by='Date')
        
        # 顯示當前最新的一筆資料狀態
        latest = df_plot.iloc[-1]
        
        st.markdown("### 📊 最新檢測指標")
        col_m1, col_m2, col_m3 = st.columns(3)
        with col_m1:
            st.metric("最新記錄日期", str(latest['Date'].date()))
        with col_m2:
            st.metric("當前 BMI 數值", f"{latest['BMI']} ( {latest['Status']} )")
        with col_m3:
            st.metric("當前體重", f"{latest['Weight']} kg")
            
        st.divider()
        
        # 理由：實作「BMI 變化曲線」與「體重紀錄對比」雙圖並排
        col_c1, col_c2 = st.columns(2)
        
        with col_c1:
            st.write("**📈 BMI 趨勢分析 (BMI 變化曲線)**")
            # 理由：使用 Streamlit 內建 st.line_chart。
            # 先將 Date 轉為字串格式再設為 Index，確保 X 軸標籤在畫面上乾淨整齊。
            df_bmi_chart = df_plot[['Date', 'BMI']].copy()
            df_bmi_chart['Date'] = df_bmi_chart['Date'].dt.strftime('%Y-%m-%d')
            df_bmi_chart = df_bmi_chart.set_index('Date')
            st.line_chart(df_bmi_chart)
            
        with col_c2:
            st.write("**⚖️ 體重推移圖 (體重紀錄對比)**")
            # 理由：同上，不引用 Plotly，改以原生折線圖繪製體重走勢。
            df_weight_chart = df_plot[['Date', 'Weight']].copy()
            df_weight_chart['Date'] = df_weight_chart['Date'].dt.strftime('%Y-%m-%d')
            df_weight_chart = df_weight_chart.set_index('Date')
            st.line_chart(df_weight_chart)
            
        st.divider()
        
        # 理由：實作「體態分佈比例」與「健康管理建議」並排
        col_pie, col_advice = st.columns([1, 1.2])
        
        with col_pie:
            st.write("**🍕 體態分佈比例 (歷史健康狀態佔比)**")
            status_df = df_plot['Status'].value_counts()
            
            # 理由：Windows 系統中 Matplotlib 繪製中文標籤會出現方塊亂碼，因此手動載入「微軟正黑體」字型
            plt.rcParams['font.sans-serif'] = ['Microsoft JhengHei']
            plt.rcParams['axes.unicode_minus'] = False  # 解決負號 '-' 顯示為方塊的問題
            
            fig_pie, ax_pie = plt.subplots(figsize=(6, 4))
            
            # 理由：繪製圓餅圖，autopct 用於顯示百分比格式，startangle 用於旋轉角度。
            # 使用 wedgeprops 調整寬度，可以將常規圓餅圖改造為中空甜甜圈圖（Donut Chart）。
            ax_pie.pie(
                status_df.values, 
                labels=status_df.index, 
                autopct='%1.1f%%', 
                startangle=140,
                wedgeprops=dict(width=0.4, edgecolor='w')
            )
            
            # 理由：將 Matplotlib 圖表的背景設為透明，在明亮或深色主題網頁背景下都不會突兀。
            fig_pie.patch.set_alpha(0.0)
            ax_pie.patch.set_alpha(0.0)
            
            st.pyplot(fig_pie)
            
        with col_advice:
            st.write("**🩺 專屬健康管理建議**")
            advice_content = generate_health_advice(latest['Status'], latest['BMI'])
            st.info(f"**【給 {latest['Name']} 的健康維護指引】**\n\n{advice_content}\n\n*提示：本數據僅供自我追蹤參考，具體減重與體態管理方針請諮詢合格醫療專業人員。*")