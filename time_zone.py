import pandas as pd

tables = pd.read_html('https://timezonedb.com/time-zones')

table = tables[0]

table.to_csv('country_wise_tz.csv')
