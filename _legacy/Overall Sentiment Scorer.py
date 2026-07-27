import numpy as np
import pandas as pd
def compute_overall_score(ratings):
    ratings = [float(r) for r in ratings if r and not pd.isnull(r)]
    mean = np.mean(ratings)
    out_of_5 = round(mean, 2)
    percent = round(mean / 5 * 100, 1)
    return f"{out_of_5}/5 ({percent}%)"
