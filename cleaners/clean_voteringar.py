def clean_voteringar(data):
    voteringar = data["voteringlista"]["votering"]

    if isinstance(voteringar, dict):
        voteringar = [voteringar]

    cleaned = []
    for v in voteringar:
        votering_id = v.get("votering_id", "")
        intressent_id = v.get("intressent_id", "")
        unique_id = f"{votering_id}_{intressent_id}"

        cleaned.append({
            "id": unique_id,
            "titel": v.get("beteckning"),
            "punkt": v.get("punkt"),
            "riksmote": v.get("rm"),
            "talare": v.get("namn"),
            "parti": v.get("parti"),
            "datum": v.get("systemdatum"),
            "rost": v.get("rost"),           
            "intressent_id": intressent_id   
        })

    return cleaned