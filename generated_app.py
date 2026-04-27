import streamlit as st
import pandas as pd

def load_data():
    try:
        df = pd.read_csv('gomibetsu.csv')
        return df, None
    except FileNotFoundError:
        uploaded_file = st.file_uploader("'gomibetsu.csv' ファイルをアップロードしてください", type='csv')
        if uploaded_file is not None:
            try:
                df = pd.read_csv(uploaded_file)
                return df, None
            except Exception as e:
                return None, f"ファイル読み込みエラー: {e}"
        else:
            return None, "ファイルがアップロードされていません"

def search_items(item_name, df):
    if df is None or item_name.strip() == "":
        return None
    mask = df['品名'].str.contains(item_name, case=False, na=False)
    matches = df[mask].copy()
    # ユニークなIDを追加（元のインデックスを利用）
    matches['_id'] = matches.index
    return matches

def main():
    st.title('ごみ分別アプリ')
    if 'df' not in st.session_state:
        df, error = load_data()
        if df is not None:
            st.session_state.df = df
        else:
            st.error(error)
            return
    else:
        df = st.session_state.df

    item = st.text_input('品名を入力してください')
    
    if st.button('検索'):
        if item.strip() == "":
            st.warning("品名を入力してください")
            st.session_state.pop('matches', None)
            st.session_state.pop('result', None)
        else:
            matches = search_items(item, df)
            if matches is None or matches.empty:
                st.session_state.result = None
                st.session_state.matches = None
            elif len(matches) == 1:
                st.session_state.result = matches.iloc[0].to_dict()
                st.session_state.matches = None
            else:
                st.session_state.matches = matches
                st.session_state.result = None
                # 選択用の初期値を設定
                st.session_state.selected_index = matches['_id'].iloc[0]

    # 複数一致時の選択UI
    if 'matches' in st.session_state and st.session_state.matches is not None:
        matches = st.session_state.matches
        # 選択肢にIDを含めて重複を避ける
        options = [f"{row['品名']} (ID: {row['_id']})" for _, row in matches.iterrows()]
        selected_option = st.selectbox("複数の品目が見つかりました。該当するものを選択してください:", options, key="select_item")
        if st.button("この品目で決定"):
            # 選択されたオプションからIDを抽出
            selected_id = int(selected_option.split('(ID: ')[1].strip(')'))
            selected_row = matches[matches['_id'] == selected_id].iloc[0]
            st.session_state.result = selected_row.to_dict()
            st.session_state.matches = None
            st.rerun()

    # 結果表示
    if 'result' in st.session_state:
        if st.session_state.result is None:
            st.write('電話で、環境都市部環境クリーンセンターにお問い合わせください')
        else:
            st.write(f"種別: {st.session_state.result['種別']}")
            st.write(f"留意点: {st.session_state.result['留意点']}")

if __name__ == '__main__':
    main()
