"""Domain sabitleri - Kategoriler ve form alanları."""
from __future__ import annotations

KATEGORILER = {
    "Konut":           ["Satılık", "Kiralık", "Devren Satılık", "Devren Kiralık"],
    "İş Yeri":         ["Satılık", "Kiralık", "Devren Satılık", "Devren Kiralık"],
    "Arsa":            ["Satılık", "Kiralık"],
    "Konut Projeleri": ["Satılık"],
    "Bina":            ["Satılık", "Kiralık"],
    "Devre Mülk":      ["Satılık", "Kiralık"],
    "Turistik Tesis":  ["Satılık", "Kiralık"],
}

ILAN_TIPLERI = {
    "Konut": {
        "Satılık":        ["Daire", "Rezidans", "Villa", "Yazlık", "Müstakil Ev", "Kooperatif", "Bungalov"],
        "Kiralık":        ["Daire", "Rezidans", "Villa", "Yazlık", "Müstakil Ev"],
        "Devren Satılık": ["Daire", "Rezidans", "Villa", "Müstakil Ev"],
        "Devren Kiralık": ["Daire", "Rezidans", "Villa", "Müstakil Ev"],
    },
    "İş Yeri": {
        "Satılık":        ["Ofis", "Dükkan/Mağaza", "Depo/Antrepo", "Atölye", "Fabrika", "Akaryakıt İstasyonu"],
        "Kiralık":        ["Ofis", "Dükkan/Mağaza", "Depo/Antrepo", "Atölye", "Fabrika"],
        "Devren Satılık": ["Ofis", "Dükkan/Mağaza", "Atölye"],
        "Devren Kiralık": ["Ofis", "Dükkan/Mağaza", "Atölye"],
    },
    "Arsa": {
        "Satılık": ["Konut Arsası", "Ticari Arsa", "Tarla", "Bahçe", "Bağ", "Çiftlik"],
        "Kiralık": ["Tarla", "Bahçe", "Bağ"],
    },
    "Konut Projeleri": {
        "Satılık": ["Daire", "Villa", "Rezidans", "Müstakil"],
    },
    "Bina": {
        "Satılık": ["Apartman", "İş Merkezi", "Fabrika", "Otel"],
        "Kiralık": ["Apartman", "İş Merkezi"],
    },
    "Devre Mülk": {
        "Satılık": ["Devre Mülk"],
        "Kiralık": ["Devre Mülk"],
    },
    "Turistik Tesis": {
        "Satılık": ["Otel", "Pansiyon", "Tatil Köyü", "Kamp Alanı"],
        "Kiralık": ["Otel", "Pansiyon", "Tatil Köyü", "Kamp Alanı"],
    },
}

ALAN_SABLONLARI = {
    "konut_satilik": [
        {"key": "net_m2", "label": "Net m²", "type": "number"},
        {"key": "brut_m2", "label": "Brüt m²", "type": "number"},
        {"key": "oda_sayisi", "label": "Oda Sayısı", "type": "text"},
        {"key": "bina_yasi", "label": "Bina Yaşı", "type": "number"},
        {"key": "isitma", "label": "Isıtma", "type": "text"},
    ],
    "konut_kiralik": [
        {"key": "net_m2", "label": "Net m²", "type": "number"},
        {"key": "brut_m2", "label": "Brüt m²", "type": "number"},
        {"key": "oda_sayisi", "label": "Oda Sayısı", "type": "text"},
        {"key": "esya_durumu", "label": "Eşya Durumu", "type": "text"},
    ],
}


def get_kategoriler() -> dict:
    return KATEGORILER


def get_ilan_tipleri() -> dict:
    return ILAN_TIPLERI


def get_alan_sablonlari() -> dict:
    return ALAN_SABLONLARI