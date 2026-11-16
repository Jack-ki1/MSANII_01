"""Regions, countries and the genre catalogue. Region membership is a practical grouping for A&R scouting, not a political statement."""
REGIONS = {
    "East Africa": {"KE": "Kenya", "TZ": "Tanzania", "UG": "Uganda", "RW": "Rwanda", "BI": "Burundi", "ET": "Ethiopia", "SS": "South Sudan", "SO": "Somalia", "DJ": "Djibouti", "ER": "Eritrea"},
    "West Africa": {"NG": "Nigeria", "GH": "Ghana", "SN": "Senegal", "CI": "Cote d'Ivoire", "ML": "Mali", "BF": "Burkina Faso", "GN": "Guinea", "SL": "Sierra Leone", "LR": "Liberia", "GM": "Gambia", "BJ": "Benin", "TG": "Togo", "NE": "Niger", "CV": "Cabo Verde", "GW": "Guinea-Bissau", "MR": "Mauritania"},
    "Southern Africa": {"ZA": "South Africa", "ZW": "Zimbabwe", "ZM": "Zambia", "MW": "Malawi", "MZ": "Mozambique", "BW": "Botswana", "NA": "Namibia", "AO": "Angola", "LS": "Lesotho", "SZ": "Eswatini", "MG": "Madagascar", "MU": "Mauritius", "KM": "Comoros", "SC": "Seychelles"},
    "North Africa": {"EG": "Egypt", "MA": "Morocco", "DZ": "Algeria", "TN": "Tunisia", "LY": "Libya", "SD": "Sudan"},
    "Central Africa": {"CD": "DR Congo", "CG": "Congo", "CM": "Cameroon", "GA": "Gabon", "CF": "Central African Republic", "TD": "Chad", "GQ": "Equatorial Guinea", "ST": "Sao Tome and Principe"},
}
DEFAULT_REGION = "East Africa"
CTRY = {c: n for cs in REGIONS.values() for c, n in cs.items()}
GENRES = ["Afrobeats", "Afrobeat", "Afropop", "Afro-fusion", "Afro-soul", "Afro-house", "Afro-jazz", "Afro-trap", "Afro-dancehall", "Afro-gospel", "Amapiano", "Gqom", "Kwaito",
          "Bongo Flava", "Singeli", "Gengetone", "Genge", "Kapuka", "Benga", "Ohangla", "Mugithi", "Chakacha", "Taarab", "Zilizopendwa", "Kidandali", "Kadongo Kamu",
          "Lingala", "Soukous", "Ndombolo", "Congolese Rumba", "Rumba", "Highlife", "Hiplife", "Azonto", "Juju", "Fuji", "Apala", "Mbalax", "Coupe-decale", "Zouk", "Kizomba", "Kuduro", "Semba", "Morna",
          "Mbaqanga", "Maskandi", "Isicathamiya", "Ethio-jazz", "Ethiopian Pop", "Tigrigna Pop", "Eskista", "Chaabi", "Rai", "Gnawa",
          "Hip hop", "Rap", "Drill", "Trap", "R&B", "Soul", "Neo-soul", "Pop", "Dance pop", "Indie pop", "Alternative", "Rock", "Folk", "Acoustic", "Traditional", "Spoken word",
          "Reggae", "Dancehall", "Ragga", "Dub", "Gospel", "Worship", "Contemporary Gospel", "Jazz", "Blues", "Electronic", "House", "Deep house", "Techno", "Drum and bass", "EDM", "Lo-fi"]
