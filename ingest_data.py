import pandas as pd
from sqlalchemy import create_engine
from time import time

# 1. Creazione della connessione al DB Postgres su Docker
# Formato: postgresql+psycopg2://utente:password@host:porta_esterna/nome_db N.B Attento alla versione di psycopg2 potrebbe cambiare
engine = create_engine('postgresql+psycopg2://postgres:postgres@localhost:5433/ny_taxi')

# 2. Caricamento del file CSV delle zone (file piccolo, ~265 righe)
df_zones = pd.read_csv('taxi_zone_lookup.csv')
df_zones.to_sql(name='taxi_zones', con=engine, if_exists='replace', index=False)

# 3. Caricamento dei Green Taxi di Novembre 2025 (.parquet)
t_start = time()
df_green = pd.read_parquet('green_tripdata_2025-11.parquet')

# Opzionale ma consigliato: forziamo i campi data a datetime per sicurezza
# (Il formato Parquet di solito conserva già i tipi corretti, a differenza del CSV)
df_green['lpep_pickup_datetime'] = pd.to_datetime(df_green['lpep_pickup_datetime'])
df_green['lpep_dropoff_datetime'] = pd.to_datetime(df_green['lpep_dropoff_datetime'])

print(f"File letto ({len(df_green)} righe). Scrittura nel database in corso...")

# Scrittura su Postgres a blocchi (chunksize) per non saturare la memoria
df_green.to_sql(
    name='green_taxi_trips',
    con=engine,
    if_exists='replace',
    index=False,
    chunksize=10000
)

t_end = time()
print(f"Tabella 'green_taxi_trips' completata in {t_end - t_start:.2f} secondi!")
# quella del time è una chicca 