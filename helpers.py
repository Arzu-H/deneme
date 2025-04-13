import re
from datetime import datetime
import pandas as pd
from config import PREFERENCES_FILE

def clean_preferences(prefs_str):
    if not prefs_str or prefs_str.lower() in ["none", "no", ""]:
        return None
    
    prefs = []
    seen = set()
    for pref in re.split(r',|\n', prefs_str.lower()):
        pref = pref.strip()
        if pref and pref not in seen:
            prefs.append(pref)
            seen.add(pref)
    
    return prefs if prefs else None

def update_user_preferences(name, new_prefs):
    global users_df
    
    cleaned = clean_preferences(new_prefs)
    if not cleaned:
        return False
    
    now = datetime.now().isoformat()
    
    if name in users_df['name'].values:
        idx = users_df.index[users_df['name'] == name].tolist()[0]
        existing = clean_preferences(users_df.at[idx, 'preferences']) or []
        updated = list(set(existing + cleaned))
        users_df.at[idx, 'preferences'] = ', '.join(updated)
        users_df.at[idx, 'last_updated'] = now
    else:
        users_df = pd.concat([users_df, pd.DataFrame([{'name': name, 'preferences': ', '.join(cleaned), 'last_updated': now}])], ignore_index=True)
    
    users_df.to_csv(PREFERENCES_FILE, index=False)
    return True
