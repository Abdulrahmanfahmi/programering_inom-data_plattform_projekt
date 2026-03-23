def clean_anforanden(data):
    cleaned = []
    speeches = data.get("anforandelista", {}).get("anforande", [])
    if isinstance(speeches, dict):
        speeches = [speeches]
    for a in speeches:
        if not isinstance(a, dict):
            continue
        cleaned.append({
            "id": a.get("anforande_id"),
            "talare": a.get("talare"),
            "parti": a.get("parti"),
            "text": a.get("anforandetext"),
            "intressent_id": a.get("intressent_id")
        })
    return cleaned