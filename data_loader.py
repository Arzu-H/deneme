import pandas as pd
import ast
from config import COCKTAIL_CSV_PATH, PREFERENCES_FILE
import os
from langchain.schema import Document


def load_cocktail_documents():
    df = pd.read_csv(COCKTAIL_CSV_PATH)
    df['ingredients'] = df['ingredients'].apply(ast.literal_eval)
    docs = []
    for _, row in df.iterrows():
        content = f"{row['name']}: {', '.join(row['ingredients'])}. {row.get('description', '')}"
        docs.append(Document(
            page_content=content,
            metadata={"name": row["name"]}
        ))
    return docs


def load_user_preferences():
    if os.path.exists(PREFERENCES_FILE):
        return pd.read_csv(PREFERENCES_FILE)
    else:
        return pd.DataFrame(columns=["name", "preferences", "last_updated"])
