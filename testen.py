#testen voor git

# nieuwe code voor de toekomst en mergennn


import pandas as pd
import requests

# 1. Gebruik je eigen key
Key = "046SOW0RCBGPECLG"

# 2. Gebruik een f-string (f"...") om de variabele 'Key' in de URL te plaatsen
url = f'https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol=IBM&apikey={Key}'

r = requests.get(url)
data = r.json()

# 3. Zet om naar DataFrame en gebruik .T om datums naar de rijen te verplaatsen
# We gebruiken .from_dict() voor meer controle
IBM = pd.DataFrame.from_dict(data['Time Series (Daily)'], orient='index')

# Optioneel: zet de index om naar echte datums en de cijfers naar floats
IBM.index = pd.to_datetime(IBM.index)
IBM = IBM.astype(float)

print(IBM.head())