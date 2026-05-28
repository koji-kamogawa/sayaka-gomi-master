import streamlit as st
import pandas as pd
import os
import openai
from datetime import datetime
import random

# ページ設定
st.set_page_config(
    page_title="ゴミ分別アシスタント",
    page_icon="🗑️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# カスタムCSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #2E7D32;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #555;
        text-align: center;
        margin-bottom: 2rem;
    }
    .result-card {
        background: linear-gradient(135deg, #E8F5E9 0%, #C8E6C9 100%);
        border-radius: 15px;
        padding: 20px;
        margin: 10px 0;
        border-left: 5px solid #2E7D32;
    }
    .day-badge {
        display: inline-block;
        background-color: #2E7D32;
        color: white;
        padding: 5px 15px;
        border-radius: 20px;
        font-weight: 600;
        margin: 3px;
    }
    .stButton > button {
        background-color: #2E7D32;
        color: white;
        border-radius: 25px;
        padding: 10px 30px;
        font-weight: 600;
        border: none;
        transition: all 0.3s ease;
    }
    .stButton > button:hover {
        background-color: #1B5E20;
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(46,125,50,0.3);
    }
    @media (prefers-color-scheme: dark) {
        .result-card {
            background: linear-gradient(135deg, #1B5E20 0%, #2E7D32 100%);
            color: #E8F5E9;
        }
        .sub-header {
            color: #BDBDBD;
        }
    }
</style>
""", unsafe_allow_html=True)

# CSVデータの読み込み
@st.cache_data
def load_garbage_data():
    """ゴミ分別データをCSVから読み込む"""
    try:
        df = pd.read_csv('gomibetsu2.csv', encoding='utf-8')
        # カラム名を確認し、必要に応じて調整
        # 想定カラム: A列=ゴミ種別, B列=分別区分, C列=回収頻度, D列=北・東地区, E列=南・西地区
        expected_cols = ['ゴミ種別', '分別区分', '回収頻度', '北・東地区', '南・西地区']
        if len(df.columns) >= 5:
            df.columns = expected_cols[:len(df.columns)]
        return df
    except FileNotFoundError:
        st.error("gomibetsu2.csv が見つかりません。ファイルをアップロードしてください。")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"CSV読み込みエラー: {e}")
        return pd.DataFrame()

# セッション状態の初期化
if 'show_result' not in st.session_state:
    st.session_state.show_result = False
if 'selected_garbage' not in st.session_state:
    st.session_state.selected_garbage = None
if 'selected_area' not in st.session_state:
    st.session_state.selected_area = None
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

# データ読み込み
df = load_garbage_data()

# メインヘッダー
st.markdown('<div class="main-header">🗑️ ゴミ分別アシスタント</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">ゴミの種別とお住まいの地区を選択して、回収日を確認しましょう</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">【非公式版】2026年4月28日時の公開データに基づいています</div>', unsafe_allow_html=True)

# 画像表示（sayaka.png と 分別地区画像.jpg）
col_img, col_main = st.columns([1, 3])
with col_img:
    try:
        st.image('sayaka.png', width=150)
        st.image('分別地区画像.jpg', width=150)
    except:
        st.write("📦")

with col_main:
    if not df.empty:
        # ゴミ種別の選択
        garbage_types = df['ゴミ種別'].dropna().unique().tolist()
        selected_garbage = st.selectbox(
            "🗑️ ゴミの種別を選択してください",
            options=garbage_types,
            index=None,
            placeholder="選択してください..."
        )
        
        # 地区の選択
        area_options = ['北・東地区', '南・西地区']
        selected_area = st.radio(
            "📍 お住まいの地区を選択してください",
            options=area_options,
            horizontal=True,
            index=None
        )
        
        # 検索ボタン
        col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 2])
        with col_btn1:
            if st.button("🔍 回収日を確認", use_container_width=True):
                if selected_garbage and selected_area:
                    st.session_state.show_result = True
                    st.session_state.selected_garbage = selected_garbage
                    st.session_state.selected_area = selected_area
                else:
                    st.warning("ゴミ種別と地区の両方を選択してください。")
        
        with col_btn2:
            if st.button("🔄 リセット", use_container_width=True):
                st.session_state.show_result = False
                st.session_state.selected_garbage = None
                st.session_state.selected_area = None
                st.rerun()
        
        # 結果表示
        if st.session_state.show_result and st.session_state.selected_garbage and st.session_state.selected_area:
            garbage = st.session_state.selected_garbage
            area = st.session_state.selected_area
            
            # 該当行を取得
            row = df[df['ゴミ種別'] == garbage]
            
            if not row.empty:
                row_data = row.iloc[0]
                collection_day = row_data[area] if area in row_data else '情報なし'
                category = row_data['分別区分'] if '分別区分' in row_data else '情報なし'
                
                st.markdown(f"""
                <div class="result-card">
                    <h3>📋 回収日情報</h3>
                    <p><strong>🗑️ ゴミ種別:</strong> {garbage}</p>
                    <p><strong>📂 分別区分:</strong> {category}</p>
                    <p><strong>📍 地区:</strong> {area}</p>
                    <p><strong>📅 回収日:</strong> <span class="day-badge">{collection_day}</span></p>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.warning("該当するデータが見つかりませんでした。")
    else:
        st.warning("データを読み込めませんでした。gomibetsu2.csv が正しく配置されているか確認してください。")

# 区切り線
st.markdown("---")

# AIチャットセクション（既存機能の維持）
st.markdown("### 🤖 AI分別アシスタントに質問する")

# DeepSeek API設定
def get_deepseek_response(user_message):
    """DeepSeek APIを使用して応答を生成"""
    api_key = os.environ.get("DEEPSEEK_API_KEY")
    if not api_key:
        return "APIキーが設定されていません。環境変数 DEEPSEEK_API_KEY を設定してください。"
    
    try:
        client = openai.OpenAI(
            api_key=api_key,
            base_url="https://api.deepseek.com"
        )
        
        # システムプロンプト
        system_prompt = """あなたはゴミ分別の専門アシスタントです。
ユーザーからの質問に対して、ゴミの分別方法や回収日について丁寧に回答してください。
回答は日本語で、簡潔かつ正確に行ってください。"""
        
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            max_tokens=500,
            temperature=0.7
        )
        
        return response.choices[0].message.content
    except Exception as e:
        return f"エラーが発生しました: {str(e)}"

# チャット履歴の表示
for message in st.session_state.chat_history:
    with st.chat_message(message["role"]):
        st.write(message["content"])

# チャット入力
if user_input := st.chat_input("ゴミの分別について質問してください..."):
    # ユーザーメッセージを表示
    with st.chat_message("user"):
        st.write(user_input)
    st.session_state.chat_history.append({"role": "user", "content": user_input})
    
    # AI応答を生成
    with st.chat_message("assistant"):
        with st.spinner("考え中..."):
            response = get_deepseek_response(user_input)
            st.write(response)
    st.session_state.chat_history.append({"role": "assistant", "content": response})

# フッター
st.markdown("""
<div style="text-align: center; padding: 20px; color: #888; font-size: 0.8rem;">
    © 2024 ゴミ分別アシスタント | 正しい分別で美しい街づくり
</div>
""", unsafe_allow_html=True)
