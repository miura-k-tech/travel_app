from flask import Flask, request, render_template
import csv
import random

app = Flask(__name__)

# CSV読み込み関数
def load_travel_data():
    data = []
    with open('travel_data.csv', newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            data.append(row)
    return data

# トップページ：フォーム + 結果表示
@app.route('/', methods=['GET', 'POST'])
def index():
    travel_data = load_travel_data()
    filtered_data = []
    plan = None

    # 都道府県とジャンルの一覧を自動で取得
    prefectures = sorted(set([spot['都道府県'] for spot in travel_data]))
    genres = sorted(set([spot['ジャンル'] for spot in travel_data]))

    # フォームから送信された場合
    selected_pref = request.form.get('prefecture')
    selected_genre = request.form.get('genre')

    selected_days = request.form.get('days', type=int)
    if not selected_days:
        selected_days = 1

    if selected_pref and selected_genre:
        # この都道府県の全てのスポットを取得
        all_pref_spots = [spot for spot in travel_data if spot['都道府県'] == selected_pref]

        if all_pref_spots and selected_days:
            # プラン生成関数を呼び出し
            plan = generate_travel_plan(all_pref_spots, selected_days, selected_genre)
        else:
            # プランが生成できなかった場合、元のフィルタリング結果を表示するか判断
            filtered_data = [spot for spot in travel_data
                             if spot['都道府県'] == selected_pref and spot['ジャンル'] == selected_genre]
            if not filtered_data:
                plan = None
            # filtered_dataがある場合は、それが自動的に表示される

    return render_template('index.html',
        prefectures=prefectures,
        genres=genres,
        filtered_data=filtered_data,
        selected_pref=selected_pref,
        selected_genre=selected_genre,
        selected_days=selected_days,
        plan=plan
    )

# generate_travel_plan関数
def generate_travel_plan(all_pref_spots, days, main_genre):
    plan = {}
    
    # 全てのスポットをジャンルごとに分類
    genre_categorized_spots = {
        '自然': [],
        'グルメ': [],
        '歴史': []
    }
    for spot in all_pref_spots: 
        if spot['ジャンル'] in genre_categorized_spots:
            genre_categorized_spots[spot['ジャンル']].append(spot)
    
    # 各ジャンルのスポットをシャッフルしておく
    for genre in genre_categorized_spots:
        random.shuffle(genre_categorized_spots[genre])

    # 1日あたりの目標スポット数（現在は固定。後でユーザー入力可能に）
    target_spots_per_day = 2 
    
    # 使用済みスポットを追跡するためのセット
    used_spots_names = set() 
    
    # 日数分のプランを生成
    for day_num in range(1, days + 1):
        current_day_spots = []
        
        # その日に利用可能なジャンルのリスト (優先順位を考慮)
        # メインジャンルが最初に来るように
        available_genres_today = [main_genre] + [g for g in genre_categorized_spots.keys() if g != main_genre]
        
        # 1日あたりの目標スポット数に達するまでスポットを追加
        for i in range(target_spots_per_day):
            added_spot = False
            
            # 各ジャンルを優先順位と重複回避を考慮して試していく
            for genre_to_try in available_genres_today:
                # この日の最初のスポットか、その日の既存スポットと異なるジャンルか
                is_different_genre_needed = (i > 0 and current_day_spots) 
                
                # 利用可能なスポットをフィルタリング
                # 1. 未使用であること
                # 2. その日の最初のスポットと異なるジャンルであること（もし必要なら）
                available_spots_in_genre = [
                    s for s in genre_categorized_spots[genre_to_try] 
                    if s['スポット名'] not in used_spots_names and \
                       (not is_different_genre_needed or s['ジャンル'] != current_day_spots[0][1])
                ]
                
                if available_spots_in_genre:
                    spot_to_add = random.choice(available_spots_in_genre)
                    current_day_spots.append((spot_to_add['スポット名'], spot_to_add['ジャンル']))
                    used_spots_names.add(spot_to_add['スポット名'])
                    added_spot = True
                    break

            if not added_spot and i > 0 and current_day_spots:
                for genre_to_try in available_genres_today:
                    available_spots_in_genre = [
                        s for s in genre_categorized_spots[genre_to_try] 
                        if s['スポット名'] not in used_spots_names
                    ]
                    if available_spots_in_genre:
                        spot_to_add = random.choice(available_spots_in_genre)
                        current_day_spots.append((spot_to_add['スポット名'], spot_to_add['ジャンル']))
                        used_spots_names.add(spot_to_add['スポット名'])
                        added_spot = True
                        break
            
            if not added_spot:
                break
        
        if current_day_spots:
            plan[f"{day_num}"] = current_day_spots
        else:
            break

    return plan


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
