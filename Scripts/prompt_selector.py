import sqlite3

def select_prompt(summary_keywords, interaction_type):
    """
    Selects a prompt from the database based on summary keywords and interaction type.
    """
    conn = sqlite3.connect("prompt_frameworks.db")
    c = conn.cursor()

    # Simplified keyword matching (can be enhanced with more sophisticated NLP techniques)
    query = """
    SELECT prompt FROM frameworks 
    WHERE name = ?
    """
    c.execute(query, (interaction_type,))
    result = c.fetchone()
    conn.close()
    return result[0] if result else None
