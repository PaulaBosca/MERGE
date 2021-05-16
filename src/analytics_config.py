# Filename: analytics_config.py  SRC: J.Coppens 2020

# File paths

DATAPATH = '../data/7_24_15_10_30/'
ACCEL_DATA = '../data/FlightData.csv'
OUTPATH = '../out/'
IMGPATH = OUTPATH + 'IMG/'
PARABOLAS = OUTPATH + 'parabolas.csv' 
PROCESSED_DATA = OUTPATH + 'processed_data.csv'
RAW_DATA = OUTPATH + 'raw_data.csv'

# thresholds (in m/s^2) for determining when micro-g portion of flight begins/ends
MICRO_G_ENTRY_THRESHOLD = 0.2
MICRO_G_EXIT_THRESHOLD = 0.5

# offset (in seconds) between our tank sensor data and accel data provided by the NRC
OFFSET = 390

# time intervals for different parabolas sets
ALL_PARABOLAS = (1200, 2700)
SET1_PARABOLAS = (1200, 1550)
SET2_PARABOLAS = (1550, 2100)
SET3_PARABOLAS = (2150, 2700)
PARAB01 = (1200, 1300)
PARAB02 = (1280, 1380)
PARAB03 = (1375, 1475)
PARAB04 = (1475, 1575)
PARAB05 = (1550, 1650)
PARAB06 = (1650, 1750)
PARAB07 = (1900, 2000)
PARAB08 = (2000, 2100)
PARAB09 = (2185, 2285)
PARAB10 = (2250, 2350)
PARAB11 = (2500, 2600)
PARAB12 = (2600, 2700)
