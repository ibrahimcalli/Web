"""Slug üretimi."""
import re

def slug_olustur(baslik: str) -> str:
    tr_map = str.maketrans("gusiocGUSIOC", "gusiocGUSIOC")
    harfler = {"ğ":"g","ü":"u","ş":"s","ı":"i","ö":"o","ç":"c",
               "Ğ":"G","Ü":"U","Ş":"S","İ":"I","Ö":"O","Ç":"C"}
    s = baslik.lower()
    for k, v in harfler.items():
        s = s.replace(k, v)
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s[:80]
