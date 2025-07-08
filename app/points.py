from .config import POINTS

def calculate_points(match_type, prediction, result):
    if match_type == 'MD1':
        return POINTS['MD1'] if prediction == result else 0
    elif match_type in ['MD3', 'MD5']:
        pred_winner = prediction.split('-')[0] > prediction.split('-')[1]
        res_winner = result.split('-')[0] > result.split('-')[1]
        if prediction == result:
            return POINTS[f'{match_type}_SCORE']
        elif pred_winner == res_winner:
            return POINTS[f'{match_type}_WINNER']
    return 0
