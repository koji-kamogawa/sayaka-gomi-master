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
    if df is None:
        return None
    mask = df['品名'].str.contains(item_name, case=False, na=False)
    matches = df[mask]
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
                st.session_state.selected_index = None

    # 複数一致時の選択UI
    if 'matches' in st.session_state and st.session_state.matches is not None:
        matches = st.session_state.matches
        items_list = matches['品名'].tolist()
        selected_item = st.selectbox("複数の品目が見つかりました。該当するものを選択してください:", items_list, key="select_item")
        if st.button("この品目で決定"):
            selected_row = matches[matches['品名'] == selected_item].iloc[0]
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
