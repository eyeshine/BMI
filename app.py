# ==========================================
# 專案名稱：自製BMI健康管理程式 (Windows UI 專案版)
# 目的：提供自主學習成果報告之系統實作，具備圖形化資料選取、資料視覺化與多格式存取功能
# ==========================================

# ------------------------------------------
# 1. 匯入開發所需之標準函式庫與外部套件
# ------------------------------------------
import streamlit as st          # 目的：構建現代化、響應式的 Windows 本地端網頁 GUI 介面
import pandas as pd             # 目的：高效處理與轉換二維表格數據，方便繪圖與匯出檔案
import json                     # 目的：處理 JSON 格式的序列化與反序列化，用於完整保存與讀取專案
import os                       # 目的：處理檔案系統路徑（如路徑合併、目錄存在檢查）
from datetime import datetime   # 目的：取得當前系統時間，用於自動生成絕不重複的檔名
import plotly.express as px     # 目的：繪製具備高度互動性與美觀的儀表板圖表

# 理由：在 Windows 本地運行時，Tkinter 能夠直接喚醒系統原生的「資料夾選取」與「檔案選取」對話框
import tkinter as tk
from tkinter import filedialog

# ------------------------------------------
# 2. 初始系統狀態設定 (Streamlit Session State)
# ------------------------------------------
# 目的：在網頁每次因元件觸發重新整理時，保留當前的工作數據。
if 'bmi_history' not in st.session_state:
    st.session_state['bmi_history'] = []  # 用途：存放當前所有的歷史紀錄數據（List of Dict）

if 'selected_folder' not in st.session_state:
    st.session_state['selected_folder'] = os.getcwd()  # 用途：記錄當前選定的儲存資料夾路徑，預設為當前程式執行路徑

if 'selected_file' not in st.session_state:
    st.session_state['selected_file'] = ""  # 用途：記錄當前選定要讀取的專案檔案路徑

# ------------------------------------------
# 3. 定義 Windows 原生對話框呼叫函式 (Tkinter 整合)
# ------------------------------------------
def select_folder_via_dialog():
    """
    目的：喚醒 Windows 原生的資料夾選取視窗。
    用途：讓使用者能以圖形化界面選擇儲存路徑。
    理由：使用 -topmost 屬性將 Tkinter 視窗強制置於瀏覽器最前端，避免被遮擋，並在選取完畢後立即銷毀 root 以防記憶體殘留。
    """
    try:
        root = tk.Tk()
        root.withdraw()  # 隱藏主視窗，僅顯示對話框
        root.wm_attributes('-topmost', 1)  # 強制將視窗置頂
        folder_path = filedialog.askdirectory(master=root)
        root.destroy()  # 銷毀視窗
        return folder_path
    except Exception as e:
        # 理由：若在非 GUI 環境下運行，返回 None 避免程式崩潰
        return None

def select_file_via_dialog():
    """
    目的：喚醒 Windows 原生的檔案選取視窗。
    用途：讓使用者直接點選要讀取的專案檔（副檔名限制為 .json）。
    理由：透過 filetypes 限制使用者僅能選取 JSON 格式，減少因讀取錯誤格式而造成的當機風險。
    """
    try:
        root = tk.Tk()
        root.withdraw()
        root.wm_attributes('-topmost', 1)
        file_path = filedialog.askopenfilename(
            master=root,
            filetypes=[("JSON 專案檔", "*.json")]
        )
        root.destroy()
        return file_path
    except Exception as e:
        return None

# ------------------------------------------
# 4. 核心計算與健康管理建議邏輯
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
# 5. 網頁介面排版 (Streamlit Windows UI)
# ------------------------------------------
st.set_page_config(page_title="自製BMI健康管理系統", layout="wide")

st.title("🛡️ 自製 BMI 健康管理程式 & 數據分析儀表板")
st.caption("自主學習成果專案 - 提供 Windows 本地端原生檔案存取與高階資料分析儀表板。")

# 建立分頁標籤，切換「登錄與檔案管理」與「圖表儀表板」
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
    # 5.2 專案檔案存取與匯出 (支援圖形化瀏覽)
    # ------------------------------------------
    with col_file:
        st.subheader("📁 專案儲存與讀取 (Windows UI 原生選取)")
        
        # 理由：實作「讓使用者以輸入的方式選擇儲存資料夾路徑」與「可點選瀏覽」雙軌制
        st.write("**1. 儲存路徑設定**")
        col_dir_text, col_dir_btn = st.columns([3, 1])
        with col_dir_text:
            # 理由：允許手動直接輸入/貼上路徑
            manual_dir = st.text_input(
                "儲存資料夾路徑", 
                value=st.session_state['selected_folder'],
                label_visibility="collapsed"
            )
            st.session_state['selected_folder'] = manual_dir
        with col_dir_btn:
            # 理由：按下後開啟原生視窗選取資料夾並更新文字框內容
            if st.button("📁 瀏覽...", use_container_width=True):
                chosen_dir = select_folder_via_dialog()
                if chosen_dir:
                    st.session_state['selected_folder'] = chosen_dir
                    st.rerun()  # 重新整理以更新顯示路徑

        # [功能 3] 按鈕：儲存專案 (不重複檔名)
        if st.button("💾 儲存完整專案檔 (.json)", use_container_width=True):
            target_dir = st.session_state['selected_folder']
            if os.path.exists(target_dir):
                # 理由：檔名格式為 bmi_project_YYYYMMDD_HHMMSS.json，因時間至秒級，每次儲存絕對不重複
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                save_filename = f"bmi_project_{timestamp}.json"
                save_path = os.path.join(target_dir, save_filename)
                
                with open(save_path, 'w', encoding='utf-8') as f:
                    json.dump(st.session_state['bmi_history'], f, ensure_ascii=False, indent=4)
                st.success(f"專案儲存成功！檔名：{save_filename}")
            else:
                st.error("儲存資料夾路徑無效，請重新檢查。")

        st.divider()

        # [功能 4]：讀取檔案 (使用選擇檔案的方式)
        st.write("**2. 讀取現有專案**")
        col_file_text, col_file_btn = st.columns([3, 1])
        with col_file_text:
            # 理由：不可編輯，僅用於顯示使用者透過對話框選取的文件完整路徑
            st.text_input(
                "已選擇的專案檔案", 
                value=st.session_state['selected_file'],
                disabled=True,
                label_visibility="collapsed"
            )
        with col_file_btn:
            # 理由：符合「讀起檔案也是用選擇檔案的方式」
            if st.button("🔍 瀏覽檔案...", use_container_width=True):
                chosen_file = select_file_via_dialog()
                if chosen_file:
                    st.session_state['selected_file'] = chosen_file
                    st.rerun()

        if st.button("📂 載入選定檔案", use_container_width=True):
            file_to_load = st.session_state['selected_file']
            if file_to_load and os.path.exists(file_to_load):
                with open(file_to_load, 'r', encoding='utf-8') as f:
                    st.session_state['bmi_history'] = json.load(f)
                st.success(f"已成功載入專案！檔案：{os.path.basename(file_to_load)}")
            else:
                st.error("請先點擊上方『瀏覽檔案』選擇有效的專案檔。")

        st.divider()

        # [功能 5]：儲存所有資料為 Excel (.xlsx) 或 CSV
        st.write("**3. 匯出 Excel / CSV 表格**")
        export_mode = st.radio("選擇匯出格式：", ["Excel (.xlsx)", "CSV (.csv)"], horizontal=True)
        if st.button("📥 匯出資料", use_container_width=True):
            if not st.session_state['bmi_history']:
                st.error("無任何歷史數據可供匯出！")
            else:
                target_dir = st.session_state['selected_folder']
                if os.path.exists(target_dir):
                    df_to_export = pd.DataFrame(st.session_state['bmi_history'])
                    timestamp_export = datetime.now().strftime("%Y%m%d_%H%M%S")
                    
                    if export_mode == "Excel (.xlsx)":
                        export_filename = f"bmi_data_{timestamp_export}.xlsx"
                        export_path = os.path.join(target_dir, export_filename)
                        # 理由：pandas 輸出 Excel 需要 openpyxl 套件
                        df_to_export.to_excel(export_path, index=False)
                    else:
                        export_filename = f"bmi_data_{timestamp_export}.csv"
                        export_path = os.path.join(target_dir, export_filename)
                        # 理由：utf-8-sig 能防止中文在 Windows Excel 中開啟時發生亂碼
                        df_to_export.to_csv(export_path, index=False, encoding='utf-8-sig')
                        
                    st.success(f"匯出成功！檔案存放在：\n{export_path}")
                else:
                    st.error("指定的儲存資料夾路徑不存在。")

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
        st.info("尚無資料。請於左側登錄數據，或於右側載入歷史專案檔。")


# ==========================================
# TAB 2：趨勢儀表板與健康建議
# ==========================================
with tab2:
    st.subheader("📊 歷史健康數據 Dashboard")
    
    # 理由：若無資料，繪圖引擎會報錯，故以條件式分支提示使用者先登錄數據
    if not st.session_state['bmi_history']:
        st.warning("目前無任何資料，請先新增或讀取檔案以生成分析圖表。")
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
            fig_bmi_line = px.line(
                df_plot, 
                x='Date', 
                y='BMI', 
                title='BMI 歷史起伏曲線',
                labels={'Date': '時間', 'BMI': 'BMI 數值'},
                markers=True  # 理由：強制顯示數據點，避免只有單一數據時折線圖無法呈點
            )
            st.plotly_chart(fig_bmi_line, use_container_width=True)
            
        with col_c2:
            st.write("**⚖️ 體重推移圖 (體重紀錄對比)**")
            fig_weight_line = px.line(
                df_plot, 
                x='Date', 
                y='Weight', 
                title='體重歷史起伏曲線',
                labels={'Date': '時間', 'Weight': '體重 (kg)'},
                markers=True
            )
            fig_weight_line.update_traces(line_color='#FF5733') # 理由：使用不同色系進行區隔，增進視覺易讀性
            st.plotly_chart(fig_weight_line, use_container_width=True)
            
        st.divider()
        
        # 理由：實作「體態分佈比例」與「健康管理建議」並排
        col_pie, col_advice = st.columns([1, 1.2])
        
        with col_pie:
            st.write("**🍕 體態分佈比例 (歷史健康狀態佔比)**")
            status_df = df_plot['Status'].value_counts().reset_index()
            status_df.columns = ['體態狀態', '次數']
            
            fig_pie_chart = px.pie(
                status_df, 
                values='次數', 
                names='體態狀態', 
                title='歷史記錄體態判定比例',
                hole=0.4  # 理由：Donut 甜甜圈圖外觀更具現代設計感
            )
            st.plotly_chart(fig_pie_chart, use_container_width=True)
            
        with col_advice:
            st.write("**🩺 專屬健康管理建議**")
            advice_content = generate_health_advice(latest['Status'], latest['BMI'])
            st.info(f"**【給 {latest['Name']} 的健康維護指引】**\n\n{advice_content}\n\n*提示：本數據僅供自我追蹤參考，具體減重與體態管理方針請諮詢合格醫療專業人員。*")