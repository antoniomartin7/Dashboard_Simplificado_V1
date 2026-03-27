# crear_referencias.py — Genera Referencias.xlsx con empresas de cartera y seguimiento
# Ejecutar una vez: python crear_referencias.py

import pandas as pd

empresas = [
    # ═══ MI CARTERA ═══
    # --- EE.UU. ---
    {"Ticker": "GOOGL", "Nombre": "Alphabet Inc Class A",           "Es_REIT": False, "Lista": "Cartera"},
    {"Ticker": "META",  "Nombre": "Meta Platforms Inc",              "Es_REIT": False, "Lista": "Cartera"},
    {"Ticker": "MDLZ",  "Nombre": "Mondelez International Inc",     "Es_REIT": False, "Lista": "Cartera"},
    {"Ticker": "KHC",   "Nombre": "The Kraft Heinz Co",             "Es_REIT": False, "Lista": "Cartera"},
    {"Ticker": "VZ",    "Nombre": "Verizon Communications Inc",     "Es_REIT": False, "Lista": "Cartera"},
    {"Ticker": "JNJ",   "Nombre": "Johnson & Johnson",              "Es_REIT": False, "Lista": "Cartera"},
    {"Ticker": "AMZN",  "Nombre": "Amazon.com Inc",                 "Es_REIT": False, "Lista": "Cartera"},
    {"Ticker": "UNH",   "Nombre": "UnitedHealth Group Inc",         "Es_REIT": False, "Lista": "Cartera"},
    {"Ticker": "MSFT",  "Nombre": "Microsoft Corp",                 "Es_REIT": False, "Lista": "Cartera"},
    {"Ticker": "ELV",   "Nombre": "Elevance Health Inc",            "Es_REIT": False, "Lista": "Cartera"},
    {"Ticker": "TROW",  "Nombre": "T. Rowe Price Group Inc",        "Es_REIT": False, "Lista": "Cartera"},
    {"Ticker": "T",     "Nombre": "AT&T Inc",                       "Es_REIT": False, "Lista": "Cartera"},
    {"Ticker": "CVS",   "Nombre": "CVS Health Corp",                "Es_REIT": False, "Lista": "Cartera"},
    {"Ticker": "FLNC",  "Nombre": "Fluence Energy Inc Class A",     "Es_REIT": False, "Lista": "Cartera"},
    {"Ticker": "MMM",   "Nombre": "3M Co",                          "Es_REIT": False, "Lista": "Cartera"},
    # --- REITs Cartera ---
    {"Ticker": "MPW",   "Nombre": "Medical Properties Trust Inc",   "Es_REIT": True,  "Lista": "Cartera"},
    {"Ticker": "WPC",   "Nombre": "W.P. Carey Inc",                 "Es_REIT": True,  "Lista": "Cartera"},
    {"Ticker": "O",     "Nombre": "Realty Income Corp",             "Es_REIT": True,  "Lista": "Cartera"},
    {"Ticker": "IIPR",  "Nombre": "Innovative Industrial Properties","Es_REIT": True,  "Lista": "Cartera"},
    {"Ticker": "PLD",   "Nombre": "Prologis Inc",                   "Es_REIT": True,  "Lista": "Cartera"},

    # ═══ SEGUIMIENTO ═══
    {"Ticker": "ORCL",  "Nombre": "Oracle Corp",                    "Es_REIT": False, "Lista": "Seguimiento"},
    {"Ticker": "NFLX",  "Nombre": "Netflix Inc",                    "Es_REIT": False, "Lista": "Seguimiento"},
    {"Ticker": "ABT",   "Nombre": "Abbott Laboratories",            "Es_REIT": False, "Lista": "Seguimiento"},
    {"Ticker": "ADBE",  "Nombre": "Adobe Inc",                      "Es_REIT": False, "Lista": "Seguimiento"},
    {"Ticker": "PG",    "Nombre": "Procter & Gamble Co",            "Es_REIT": False, "Lista": "Seguimiento"},
    {"Ticker": "KO",    "Nombre": "Coca-Cola Co",                   "Es_REIT": False, "Lista": "Seguimiento"},
    {"Ticker": "BAM",   "Nombre": "Brookfield Asset Management",   "Es_REIT": False, "Lista": "Seguimiento"},
    {"Ticker": "IBKR",  "Nombre": "Interactive Brokers Group",     "Es_REIT": False, "Lista": "Seguimiento"},
    {"Ticker": "PSA",   "Nombre": "Public Storage",                "Es_REIT": True,  "Lista": "Seguimiento"},
]

df = pd.DataFrame(empresas)
df.to_excel("Referencias.xlsx", index=False)
n_cartera = len(df[df['Lista'] == 'Cartera'])
n_seg = len(df[df['Lista'] == 'Seguimiento'])
print(f"✅ Referencias.xlsx creado: {n_cartera} en Cartera + {n_seg} en Seguimiento = {len(df)} total.")
