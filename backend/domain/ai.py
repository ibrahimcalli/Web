"""AI sağlayıcı sabitleri."""
AI_SAGLAYICI_URLS = {
    "deepseek": "https://api.deepseek.com/v1/chat/completions",
    "groq":     "https://api.groq.com/openai/v1/chat/completions",
    "openai":   "https://api.openai.com/v1/chat/completions",
}
AI_SAGLAYICI_MODEL = {
    "deepseek": "deepseek-chat",
    "groq":     "llama-3.3-70b-versatile",
    "openai":   "gpt-4o-mini",
}
