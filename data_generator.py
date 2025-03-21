import pandas as pd
import numpy as np
import random
import string
from datetime import datetime, timedelta

def generate_random_string(length=6):
    """지정된 길이의 랜덤 영문 문자열 생성"""
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for i in range(length))

def generate_sequential_dates(start_date, end_date):
    """지정된 범위 내의 순차적인 날짜 리스트 생성"""
    date_list = []
    current_date = start_date
    while current_date <= end_date:
        date_list.append(current_date.strftime('%Y-%m-%d'))
        current_date += timedelta(days=1)
    return date_list

def generate_data():
    # 날짜 범위 설정
    start_date = datetime(2025, 1, 1)
    end_date = datetime(2025, 3, 20)
    date_list = generate_sequential_dates(start_date, end_date)

    # 데이터 생성
    num_rows = len(date_list)  # 날짜 리스트 길이만큼 데이터 행 수 설정

    diary_entries = [
        "오늘 날씨는 화창했지만, 미세먼지가 심해서 마스크를 꼭 써야 했다. 그래도 오랜만에 햇빛을 보니 기분이 조금 나아졌다.",
        "새로운 요리책을 샀는데, 맛있는 레시피가 너무 많아서 뭘 먼저 만들어야 할지 고민이다. 주말에 시간을 내서 하나씩 도전해 봐야겠다.",
        "친구가 힘든 일이 있다며 늦은 시간에 전화를 걸어왔다. 밤새도록 이야기를 들어주고 나니, 마음이 조금은 편안해진 것 같다.",
        "회사에서 새로운 프로젝트를 맡게 되었는데, 생각보다 어려운 점이 많다. 하지만 동료들과 함께라면 잘 해낼 수 있을 것 같다.",
        "퇴근길에 좋아하는 가수의 신곡을 들었는데, 노래가 너무 좋아서 집에 오는 길이 전혀 지루하지 않았다. 역시 음악은 나의 활력소다.",
        "오랜만에 동네 서점에 갔는데, 예쁜 엽서가 많아서 몇 장 샀다. 좋아하는 친구들에게 손편지를 써서 보내야겠다.",
        "집 근처에 새로 생긴 카페에 갔는데, 커피 맛도 좋고 분위기도 아늑해서 마음에 쏙 들었다. 앞으로 자주 방문하게 될 것 같다.",
        "오늘은 집에서 푹 쉬면서 영화를 봤다. 맛있는 간식을 먹으면서 좋아하는 영화를 보니, 스트레스가 싹 풀리는 기분이었다.",
        "새로운 운동을 시작했는데, 생각보다 힘들어서 깜짝 놀랐다. 하지만 꾸준히 하면 체력이 좋아지겠지? 내일도 열심히 운동해야겠다.",
        "오늘 꿈에서 아주 신나는 모험을 했는데, 현실에서도 그런 일이 일어났으면 좋겠다. 꿈속에서 만난 멋진 풍경이 아직도 눈에 선하다."
    ]

    data = {
        'id': [generate_random_string() for _ in range(num_rows)],
        'user_id': [random.randint(0, 10) for _ in range(num_rows)], # user_id를 0~10 사이의 랜덤 정수로 생성
        'user_input': [random.choice(diary_entries) for _ in range(num_rows)],
        'physical': np.random.randint(0, 3, num_rows),
        'knowledge': np.random.randint(0, 3, num_rows),
        'mental': np.random.randint(0, 3, num_rows),
        'timestamp': date_list
    }

    # 데이터프레임 생성
    df = pd.DataFrame(data)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    return df

if __name__ == "__main__":
    df = generate_data()
    print(df.head())