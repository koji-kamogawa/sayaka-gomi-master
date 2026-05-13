import streamlit as st
import pandas as pd
import unicodedata

def load_data():
    try:
        df = pd.read_csv('gomibetsu.csv', encoding='utf-8')
        df['品名'] = df['品名'].astype(str).apply(lambda x: unicodedata.normalize('NFKC', x).strip())
        return df, None
    except FileNotFoundError:
        uploaded_file = st.file_uploader("'gomibetsu.csv' ファイルをアップロードしてください", type='csv')
        if uploaded_file is not None:
            try:
                df = pd.read_csv(uploaded_file, encoding='utf-8')
                df['品名'] = df['品名'].astype(str).apply(lambda x: unicodedata.normalize('NFKC', x).strip())
                return df, None
            except Exception as e:
                return None, f"ファイル読み込みエラー: {e}"
        else:
            return None, "ファイルがアップロードされていません"

def search_items(item_name, df):
    if df is None or not item_name.strip():
        return None
    # 入力クエリの正規化とクリーニング
    query = unicodedata.normalize('NFKC', item_name.strip())
    if not query:
        return None
    # 品名カラムを正規化済みのものを使う（load_data時に正規化済み）
    mask = df['品名'].str.contains(query, case=False, na=False, regex=False)
    matches = df[mask].copy()
    if matches.empty:
        return None
    matches['_id'] = matches.index
    return matches

def main():
    col_logo, col_title = st.columns([1, 8], vertical_alignment="center")
    with col_logo:
        st.image('sayaka.png', width=70)
    with col_title:
        st.title("逗子市ごみ分別マスター")
    st.write('【非公式版】2026年4月28日時の公開データに基づいています')

    if 'df' not in st.session_state:
        df, error = load_data()
        if df is not None:
            st.session_state.df = df
        else:
            st.error(error)
            return
    else:
        df = st.session_state.df

    # テキスト入力欄の上書き要求があれば、ここで反映
    if 'pending_item' in st.session_state:
        st.session_state.item_input = st.session_state.pending_item
        del st.session_state.pending_item

    # テキスト入力
    item = st.text_input('品名を入力してください', key='item_input')

    if st.button('検索'):
        if not item.strip():
            st.warning("品名を入力してください")
            st.session_state.pop('matches', None)
            st.session_state.pop('result', None)
        else:
            matches = search_items(item, df)
            if matches is None:
                st.session_state.result = None
                st.session_state.matches = None
            else:
                # 1件でも複数でも matches を保存し、選択UIで表示する
                st.session_state.matches = matches
                st.session_state.result = None
                st.session_state.selected_index = matches['_id'].iloc[0]

    # 候補選択UI（1件または複数）
    if 'matches' in st.session_state and st.session_state.matches is not None:
        matches = st.session_state.matches
        # 件数に応じたメッセージ
        if len(matches) == 1:
            st.write("以下の品目が見つかりました。よろしければ決定ボタンを押してください。")
        else:
            st.write("複数の品目が見つかりました。該当するものを選択してください:")
        options = [f"{row['品名']} (ID: {row['_id']})" for _, row in matches.iterrows()]
        selected_option = st.selectbox("品目を選択", options, key="select_item")
        if st.button("この品目で決定"):
            selected_id = int(selected_option.split('(ID: ')[1].strip(')'))
            selected_row = matches[matches['_id'] == selected_id].iloc[0]
            st.session_state.result = selected_row.to_dict()
            st.session_state.matches = None
            # 選択した品名をテキスト入力に反映（次回描画時）
            st.session_state.pending_item = selected_row['品名']
            st.rerun()

    # 結果表示
    if 'result' in st.session_state:
        result = st.session_state.result
        if result is None:
            st.write('電話で、環境都市部環境クリーンセンターにお問い合わせください')
        else:
            shubetsu = result.get('種別', '情報なし')
            chuiten = result.get('留意点', '情報なし')
            st.write(f"種別: {shubetsu}")
            st.write(f"留意点: {chuiten}")

if __name__ == '__main__':
    main()