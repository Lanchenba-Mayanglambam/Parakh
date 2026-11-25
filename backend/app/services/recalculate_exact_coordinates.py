import os
import re
import math
import hashlib
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Comprehensive landmark and locality coordinates for high-precision geocoding
LOCALITY_LOOKUP = {
    # Manipur Localities, Villages, Leikais, and Landmarks
    'arapti': (24.7168, 93.9412),
    'lilong': (24.7180, 93.9380),
    'paona mongpham': (24.7165, 93.9408),
    'keishamthong': (24.7935, 93.9312),
    'top leirak': (24.7935, 93.9312),
    'kwakeithel': (24.7788, 93.9215),
    'akham leikai': (24.7788, 93.9215),
    'soibam leikai': (24.8020, 93.9565),
    'porompat': (24.8020, 93.9565),
    'esu campus': (24.7952, 93.9538),
    'wangkhei': (24.7952, 93.9538),
    'akampat': (24.7865, 93.9650),
    'ideal girls college': (24.7865, 93.9650),
    'amwju': (24.8015, 93.9440),
    'press colony': (24.8015, 93.9440),
    'singjamei': (24.7750, 93.9350),
    'oinam thingel': (24.7750, 93.9350),
    'kumbi': (24.4530, 93.8180),
    'kangjeibung': (24.4530, 93.8180),
    'kwakta': (24.4920, 93.7650),
    'santhong': (24.4920, 93.7650),
    'leimapokpam': (24.6980, 93.8120),
    'patsoi': (24.7890, 93.8720),
    'awang leikai': (24.7890, 93.8720),
    'moidangpok': (24.8210, 93.8340),
    'kangmong': (24.7650, 93.8560),
    'konthoujam': (24.8050, 93.8420),
    'khurai': (24.8155, 93.9582),
    'kongpal': (24.8155, 93.9582),
    'thongam leikai': (24.8155, 93.9582),
    'shangshak': (25.0420, 94.3350),
    'teinem': (25.1380, 94.3050),
    'ringui': (25.0850, 94.2750),
    'phalee': (25.1520, 94.2850),
    'mongkot chepu': (25.0120, 94.2980),
    'zingsui': (25.0450, 94.4850),
    'leishi': (24.9820, 94.4250),
    'irong chesaba': (24.5120, 93.9450),
    'tuibong': (24.3480, 93.6880),
    'peace ground': (24.3480, 93.6880),
    'm songgel': (24.3280, 93.6780),
    's molhoi': (24.3150, 93.6650),
    'bisanmual': (24.3150, 93.6650),
    'sangaikot': (24.2650, 93.7250),
    'g songgel': (24.2650, 93.7250),
    'koite': (24.3350, 93.6920),
    's mongjang': (24.3350, 93.6920),
    'teiseng': (24.3580, 93.7120),
    'thingkangphai': (24.3210, 93.6910),
    'songpi': (24.3310, 93.6820),
    'mission compound': (24.3310, 93.6820),
    'henglep': (24.4250, 93.5850),
    'd minlun': (24.4250, 93.5850),
    'kolhen': (24.4250, 93.5850),
    'moreh': (24.2480, 94.3050),
    'lhungjang': (24.9650, 93.9850),
    'awaching': (24.8320, 94.0250),
    'lamjing meira ching': (24.8320, 94.0250),
    'tuili leibul': (24.2850, 93.6450),
    'phungchongjang': (24.2850, 93.6450),
    'lamphelpat': (24.8120, 93.9210),
    'rims': (24.8120, 93.9210),

    # Major Indian Cities Sub-Localities
    # Delhi
    'rohini': (28.7145, 77.1158),
    'dwarka': (28.5921, 77.0460),
    'karol bagh': (28.6514, 77.1907),
    'chandni chowk': (28.6506, 77.2303),
    'connaught place': (28.6315, 77.2167),
    'saket': (28.5244, 77.2066),
    'lajpat nagar': (28.5677, 77.2433),
    'janakpuri': (28.6219, 77.0878),
    'shahdara': (28.6738, 77.2920),
    'najafgarh': (28.6092, 76.9798),
    'pitampura': (28.6990, 77.1384),
    'mayur vihar': (28.6096, 77.2990),
    'vasant kunj': (28.5293, 77.1550),

    # Varanasi
    'godowlia': (25.3090, 83.0060),
    'sarnath': (25.3811, 83.0214),
    'bhu': (25.2677, 82.9913),
    'banaras hindu university': (25.2677, 82.9913),
    'assi ghat': (25.2885, 83.0039),
    'kashi': (25.3109, 83.0107),
    'shivpur': (25.3610, 82.9720),

    # Lucknow
    'gomti nagar': (26.8500, 80.9990),
    'hazratganj': (26.8530, 80.9450),
    'alambagh': (26.8150, 80.9020),
    'indira nagar': (26.8850, 80.9900),
    'charbagh': (26.8310, 80.9220),

    # Pune
    'shivajinagar': (18.5308, 73.8475),
    'kothrud': (18.5074, 73.8077),
    'hadapsar': (18.5089, 73.9260),
    'hinjawadi': (18.5913, 73.7389),
    'pimpri': (18.6279, 73.8009),
    'chinchwad': (18.6298, 73.7997),
    'wakad': (18.5987, 73.7680),

    # Mumbai
    'andheri': (19.1136, 72.8697),
    'bandra': (19.0596, 72.8295),
    'borivali': (19.2307, 72.8567),
    'dadar': (19.0178, 72.8478),
    'colaba': (18.9067, 72.8147),
    'kurla': (19.0726, 72.8845),
    'chembur': (19.0522, 72.8994),

    # Kolkata
    'salt lake': (22.5868, 88.4178),
    'new town': (22.5850, 88.4700),
    'howrah': (22.5958, 88.2636),
    'alipore': (22.5290, 88.3300),
    'gariahat': (22.5180, 88.3680),
    'dum dum': (22.6450, 88.4280),

    # Bengaluru
    'whitefield': (12.9698, 77.7500),
    'indiranagar': (12.9784, 77.6408),
    'koramangala': (12.9352, 77.6245),
    'jayanagar': (12.9308, 77.5838),
    'yelahanka': (13.1007, 77.5963),
    'electronic city': (12.8399, 77.6770),

    # Patna
    'kankarbagh': (25.5900, 85.1550),
    'danapur': (25.6300, 85.0400),
    'patliputra': (25.6250, 85.1100),
    'rajendra nagar': (25.6020, 85.1680),

    # Jaipur
    'malviya nagar': (26.8540, 75.8240),
    'mansarovar': (26.8520, 75.7680),
    'vaishali nagar': (26.9080, 75.7380),
    'sanganer': (26.8180, 75.7890),
    'amer': (26.9855, 75.8513),
}

# Explicit dictionary for all 157 districts not directly named in district_coordinates.csv
SPECIAL_DISTRICTS = {
    ("West Bengal", "South 24 Parganas"): (22.1352, 88.4016),
    ("West Bengal", "North 24 Parganas"): (22.7230, 88.4800),
    ("West Bengal", "Darjeeling"): (27.0410, 88.2663),
    ("West Bengal", "Malda"): (25.0000, 88.1400),
    ("West Bengal", "Cooch Behar"): (26.3200, 89.4500),

    ("Uttar Pradesh", "Pratapgarh"): (25.8966, 81.9444),
    ("Uttar Pradesh", "Shrawasti"): (27.7025, 81.9611),
    ("Uttar Pradesh", "Sant Kabir Nagar"): (26.7845, 83.0560),
    ("Uttar Pradesh", "Mau"): (25.9417, 83.5611),
    ("Uttar Pradesh", "Mahrajganj"): (27.1400, 83.5600),
    ("Uttar Pradesh", "Bara Banki"): (26.9200, 81.1800),
    ("Uttar Pradesh", "Balrampur"): (27.4300, 82.1800),

    ("Punjab", "Ferozepur"): (30.9237, 74.6065),
    ("Punjab", "Mansa"): (29.9880, 75.3888),
    ("Punjab", "S.A.S Nagar"): (30.7046, 76.7179),
    ("Punjab", "Fatehgarh Sahib"): (30.6475, 76.3980),
    ("Punjab", "Malerkotla"): (30.5256, 75.8872),

    ("Odisha", "Nayagada"): (20.1264, 85.1050),
    ("Odisha", "Kataka"): (20.4625, 85.8828),
    ("Odisha", "Baragada"): (21.3333, 83.6167),
    ("Odisha", "Sundaragada"): (22.1200, 84.0300),
    ("Odisha", "Kandhamala"): (20.3000, 84.2000),
    ("Odisha", "Jajpur"): (20.8500, 86.3333),
    ("Odisha", "Kendrapada"): (20.5000, 86.4200),
    ("Odisha", "Anugola"): (20.8400, 85.1000),
    ("Odisha", "Subarnapur"): (20.8300, 83.9200),
    ("Odisha", "Debagada"): (21.5300, 84.7300),

    ("Andhra Pradesh", "Annamayya"): (14.1500, 78.8000),
    ("Andhra Pradesh", "Y.S.R. Kadapa"): (14.4673, 78.8242),
    ("Andhra Pradesh", "Sri Potti Sriramulu Nellore"): (14.4426, 79.9865),
    ("Andhra Pradesh", "Tirupati"): (13.6288, 79.4192),
    ("Andhra Pradesh", "Nandyal"): (15.4886, 78.4836),
    ("Andhra Pradesh", "Ananthapuramu"): (14.6819, 77.6006),
    ("Andhra Pradesh", "Dr. B.R. Ambedkar Konaseema"): (16.5700, 81.9900),
    ("Andhra Pradesh", "Bapatla"): (15.9042, 80.4678),
    ("Andhra Pradesh", "Anakapalli"): (17.6913, 83.0039),
    ("Andhra Pradesh", "Sri Sathya Sai"): (14.1600, 77.8100),
    ("Andhra Pradesh", "Eluru"): (16.7107, 81.0952),
    ("Andhra Pradesh", "Alluri Sitharama Raju"): (18.0700, 82.6700),
    ("Andhra Pradesh", "Palnadu"): (16.2333, 80.0500),
    ("Andhra Pradesh", "Parvathipuram Manyam"): (18.7800, 83.4200),
    ("Andhra Pradesh", "Ntr"): (16.5062, 80.6480),
    ("Andhra Pradesh", "Kakinada"): (16.9891, 82.2475),
    ("Andhra Pradesh", "Mahabubnagar"): (16.7450, 77.9850),
    ("Andhra Pradesh", "Ranga Reddy"): (17.3364, 78.4735),

    ("Telangana", "Jagitial"): (18.7917, 78.9128),
    ("Telangana", "Ranga Reddy"): (17.3364, 78.4735),
    ("Telangana", "Jangoan"): (17.7258, 79.1558),
    ("Telangana", "Warangal"): (17.9689, 79.5941),
    ("Telangana", "Mahabubnagar"): (16.7450, 77.9850),
    ("Telangana", "Medchal Malkajgiri"): (17.6297, 78.4814),
    ("Telangana", "Hanumakonda"): (18.0131, 79.5603),
    ("Telangana", "Peddapalli"): (18.6167, 79.3833),
    ("Telangana", "Jayashankar Bhupalapally"): (18.4300, 79.8600),

    ("Himachal Pradesh", "Mandi"): (31.7087, 76.9320),
    ("Himachal Pradesh", "Una"): (31.4685, 76.2708),
    ("Himachal Pradesh", "Lahaul And Spiti"): (32.5700, 77.0300),

    ("Chhattisgarh", "Sakti"): (21.9667, 82.9667),
    ("Chhattisgarh", "Janjgir-Champa"): (22.0167, 82.5833),
    ("Chhattisgarh", "Gaurela-Pendra-Marwahi"): (22.7500, 81.9200),
    ("Chhattisgarh", "Kabeerdham"): (22.0167, 81.2500),
    ("Chhattisgarh", "Balodabazar-Bhatapara"): (21.6600, 81.9500),
    ("Chhattisgarh", "Sarangarh-Bilaigarh"): (21.5900, 83.0800),
    ("Chhattisgarh", "Dakshin Bastar Dantewada"): (18.9000, 81.3500),
    ("Chhattisgarh", "Uttar Bastar Kanker"): (20.2700, 81.4900),
    ("Chhattisgarh", "Balrampur-Ramanujganj"): (23.6150, 83.6050),
    ("Chhattisgarh", "Manendragarh-Chirmiri-Bharatpur"): (23.2100, 82.2000),
    ("Chhattisgarh", "Korea"): (23.2500, 82.5500),
    ("Chhattisgarh", "Mohla-Manpur-Ambagarh Chouki"): (20.9500, 80.7300),
    ("Chhattisgarh", "Khairagarh-Chhuikhadan-Gandai"): (21.4200, 80.9700),

    ("Gujarat", "Dahod"): (22.8396, 74.2536),
    ("Gujarat", "Ahmedabad"): (23.0225, 72.5714),
    ("Gujarat", "Narmada"): (21.8700, 73.5500),
    ("Gujarat", "Arvalli"): (23.5000, 73.3000),
    ("Gujarat", "Dangs"): (20.8000, 73.7000),
    ("Gujarat", "Vav-Tharad"): (24.3900, 71.6300),

    ("Madhya Pradesh", "Narmadapuram"): (22.7533, 77.7289),
    ("Madhya Pradesh", "Narsimhapur"): (22.9431, 79.1961),
    ("Madhya Pradesh", "Khandwa"): (21.8314, 76.3498),
    ("Madhya Pradesh", "Maihar"): (24.2667, 80.7500),
    ("Madhya Pradesh", "Pandhurna"): (21.6000, 78.5300),
    ("Madhya Pradesh", "Mauganj"): (24.6800, 81.8700),
    ("Madhya Pradesh", "Agar-Malwa"): (23.7100, 76.0100),

    ("Bihar", "Kaimur"): (25.0444, 83.5850),

    ("Maharashtra", "Ahilyanagar"): (19.0952, 74.7480),
    ("Maharashtra", "Chhatrapati Sambhajinagar"): (19.8762, 75.3433),
    ("Maharashtra", "Dharashiv"): (18.1856, 76.0419),

    ("Jharkhand", "East Singhbum"): (22.8046, 86.2029),

    ("Tamil Nadu", "Kallakurichi"): (11.7380, 78.9639),
    ("Tamil Nadu", "Mayiladuthurai"): (11.1000, 79.6500),

    ("Delhi", "South"): (28.5000, 77.2000),
    ("Delhi", "East"): (28.6273, 77.2784),
    ("Delhi", "North West"): (28.7200, 77.1000),
    ("Delhi", "Central)"): (28.6400, 77.2200),
    ("Delhi", "Central"): (28.6400, 77.2200),
    ("Delhi", "North"): (28.7041, 77.1025),
    ("Delhi", "South West"): (28.5921, 77.0460),
    ("Delhi", "South East"): (28.5500, 77.2700),
    ("Delhi", "West"): (28.6700, 77.0700),
    ("Delhi", "North East"): (28.7000, 77.2700),

    ("Karnataka", "Bengaluru South"): (12.9100, 77.5800),
    ("Karnataka", "Chamarajanagar"): (11.9261, 76.9437),
    ("Karnataka", "Vijayanagara"): (15.2700, 76.3900),
    ("Karnataka", "Dangs"): (15.2700, 76.3900),

    ("Rajasthan", "Deeg"): (27.4722, 77.3250),
    ("Rajasthan", "Jalore"): (25.3444, 72.6153),
    ("Rajasthan", "Shahpura"): (25.6333, 74.9333),
    ("Rajasthan", "Balotra"): (25.8300, 72.2400),
    ("Rajasthan", "Didwana-Kuchaman"): (27.4000, 74.5700),
    ("Rajasthan", "Hanumangarh"): (29.5800, 74.3200),
    ("Rajasthan", "Pratapgarh"): (24.0300, 74.7800),
    ("Rajasthan", "Neem Ka Thana"): (27.7400, 75.7800),
    ("Rajasthan", "Salumbar"): (24.1300, 74.0400),
    ("Rajasthan", "Kotputli-Behror"): (27.7025, 76.2008),
    ("Rajasthan", "Kekri"): (25.9700, 75.1500),
    ("Rajasthan", "Khairthal-Tijara"): (27.9300, 76.6300),
    ("Rajasthan", "Beawar"): (26.1000, 74.3200),
    ("Rajasthan", "Jodhpur Gramin"): (26.2800, 73.0200),
    ("Rajasthan", "Sanchor"): (25.0000, 71.7700),
    ("Rajasthan", "Phalodi"): (27.1300, 72.3600),
    ("Rajasthan", "Jaipur Gramin"): (26.9124, 75.7873),
    ("Rajasthan", "Dudu"): (26.6800, 75.2400),
    ("Rajasthan", "Gangapurcity"): (26.4700, 76.7200),
    ("Rajasthan", "Anoopgarh"): (29.1900, 73.2100),

    ("Sikkim", "Pakyong"): (27.2400, 88.5900),
    ("Sikkim", "Gangtok"): (27.3389, 88.6065),
    ("Sikkim", "Gyalshing"): (27.2800, 88.2500),
    ("Sikkim", "Soreng"): (27.1700, 88.2000),
    ("Sikkim", "Mangan"): (27.5000, 88.5300),
    ("Sikkim", "Namchi"): (27.1700, 88.3500),

    ("Meghalaya", "Ri Bhoi"): (25.9000, 91.8800),
    ("Meghalaya", "Eastern West Khasi Hills"): (25.5200, 91.4500),

    ("Assam", "Kamrup Metro"): (26.1800, 91.7500),
    ("Assam", "Sribhumi"): (24.8700, 92.3600),
    ("Assam", "Tamulpur"): (26.6300, 91.5700),
    ("Assam", "Bajali"): (26.5000, 91.2000),

    ("Tripura", "West Tripura"): (23.8315, 91.2868),

    ("Nagaland", "Mon"): (26.7500, 95.0600),
    ("Nagaland", "Chumoukedima"): (25.7900, 93.7700),
    ("Nagaland", "Tseminyu"): (25.9200, 94.2100),
    ("Nagaland", "Shamator"): (26.0500, 94.8800),
    ("Nagaland", "Noklak"): (26.2000, 95.0000),

    ("Jammu And Kashmir", "Bandipora"): (34.4200, 74.6400),

    ("Lakshadweep", "Lakshadweep District"): (10.5667, 72.6417),

    ("Mizoram", "Siaha"): (22.4800, 92.9700),
    ("Mizoram", "Khawzawl"): (23.5300, 93.1800),
    ("Mizoram", "Saitual"): (23.9700, 92.5700),
    ("Mizoram", "Hnahthial"): (22.9700, 92.9300),

    ("Arunachal Pradesh", "Lower Dibang Valley"): (28.1400, 95.8300),
    ("Arunachal Pradesh", "West Siang)"): (28.1700, 94.6700),
    ("Arunachal Pradesh", "West Siang"): (28.1700, 94.6700),
    ("Arunachal Pradesh", "Leparada"): (27.9000, 94.6000),
    ("Arunachal Pradesh", "Tawang"): (27.5800, 91.8600),
    ("Arunachal Pradesh", "Dibang Valley"): (28.8576, 95.9118),

    ("Andaman And Nicobar Islands", "South Andamans)"): (11.6667, 92.7333),
    ("Andaman And Nicobar Islands", "South Andamans"): (11.6667, 92.7333),
    ("Andaman And Nicobar Islands", "North And Middle Andaman)"): (12.8400, 92.8700),
    ("Andaman And Nicobar Islands", "North And Middle Andaman"): (12.8400, 92.8700),

    ("Chandigarh", "Ferozepur"): (30.7333, 76.7794),
    ("Chandigarh", "S.A.S Nagar"): (30.7333, 76.7794),

    ("Haryana", "Nuh"): (28.1100, 77.0100)
}

STATE_CAPITALS = {
    'Andhra Pradesh': (16.5062, 80.6480),
    'Arunachal Pradesh': (27.0844, 93.6053),
    'Assam': (26.1445, 91.7362),
    'Bihar': (25.5941, 85.1376),
    'Chhattisgarh': (21.2514, 81.6296),
    'Goa': (15.4909, 73.8278),
    'Gujarat': (23.2156, 72.6369),
    'Haryana': (30.7333, 76.7794),
    'Himachal Pradesh': (31.1048, 77.1734),
    'Jharkhand': (23.3441, 85.3096),
    'Karnataka': (12.9716, 77.5946),
    'Kerala': (8.5241, 76.9366),
    'Madhya Pradesh': (23.2599, 77.4126),
    'Maharashtra': (19.0760, 72.8777),
    'Manipur': (24.8170, 93.9368),
    'Meghalaya': (25.5788, 91.8933),
    'Mizoram': (23.7271, 92.7176),
    'Nagaland': (25.6751, 94.1086),
    'Odisha': (20.2961, 85.8245),
    'Punjab': (30.7333, 76.7794),
    'Rajasthan': (26.9124, 75.7873),
    'Sikkim': (27.3389, 88.6065),
    'Tamil Nadu': (13.0827, 80.2707),
    'Telangana': (17.3850, 78.4867),
    'Tripura': (23.8315, 91.2868),
    'Uttar Pradesh': (26.8467, 80.9462),
    'Uttarakhand': (30.3165, 78.0322),
    'West Bengal': (22.5726, 88.3639),
    'Delhi': (28.6139, 77.2090),
    'Jammu And Kashmir': (34.0837, 74.7973),
    'Ladakh': (34.1526, 77.5771),
    'Puducherry': (11.9416, 79.8083),
    'Chandigarh': (30.7333, 76.7794),
    'Andaman And Nicobar Islands': (11.6234, 92.7265),
    'Lakshadweep': (10.5667, 72.6417)
}


def load_district_dict(csv_path='/app/district_coordinates.csv'):
    dist_map = {}
    if os.path.exists(csv_path):
        df = pd.read_csv(csv_path)
        for _, row in df.iterrows():
            d_name = str(row['District']).strip().lower()
            try:
                lat = float(row['Latitude'])
                lon = float(row['Longitude'])
                dist_map[d_name] = (lat, lon)
            except Exception:
                pass
    return dist_map


def get_base_coordinate(state: str, district: str, description: str, dist_map: dict):
    state = str(state or '').strip()
    district = str(district or '').strip()
    desc_lower = str(description or '').lower()

    # Tier 1: Check description for exact landmark or locality match
    for landmark, coords in LOCALITY_LOOKUP.items():
        if landmark in desc_lower:
            return coords, "LOCALITY"

    # Tier 2: Check SPECIAL_DISTRICTS mapping
    key = (state, district)
    if key in SPECIAL_DISTRICTS:
        return SPECIAL_DISTRICTS[key], "SPECIAL_DISTRICT"

    # Tier 3: Check district_map
    d_clean = district.lower().replace(' district', '').strip()
    if d_clean in dist_map:
        return dist_map[d_clean], "DISTRICT_CSV"

    # Check partial match in district_map
    for k, coords in dist_map.items():
        if k in d_clean or d_clean in k:
            return coords, "DISTRICT_PARTIAL"

    # Tier 4: Fallback to State Capital
    if state in STATE_CAPITALS:
        return STATE_CAPITALS[state], "STATE_CAPITAL"

    return (20.5937, 78.9629), "INDIA_CENTROID"


def resolve_project_coordinates(p_id: str, state: str, district: str, description: str, dist_map: dict):
    base_coords, match_tier = get_base_coordinate(state, district, description, dist_map)
    base_lat, base_lon = base_coords

    # Hash for deterministic micro-dispersion
    h = int(hashlib.md5(p_id.encode('utf-8')).hexdigest()[:8], 16)

    if match_tier == "LOCALITY":
        # At the exact locality level:
        # Micro-offset only 15 to 30 meters so markers at the same site don't perfectly overlap
        # 0.0001 degrees latitude is ~11.1 meters, longitude is ~10.2 meters
        offset_lat = ((h % 21) - 10) * 0.000020  # Max +- 22 meters
        offset_lon = (((h >> 5) % 21) - 10) * 0.000020
    else:
        # District level:
        # Keep tightly within 300 - 800 meters of district center
        offset_lat = ((h % 51) - 25) * 0.00015  # Max +- 400 meters
        offset_lon = (((h >> 6) % 51) - 25) * 0.00015

    final_lat = round(base_lat + offset_lat, 6)
    final_lon = round(base_lon + offset_lon, 6)

    return final_lat, final_lon, match_tier


def run_coordinate_update():
    from app.db.session import engine, SessionLocal
    from app.db.models import Project
    from sqlalchemy import text

    print("Loading district dataset...")
    dist_map = load_district_dict('/app/district_coordinates.csv')
    print(f"Loaded {len(dist_map)} districts from CSV.")

    db = SessionLocal()
    print("Fetching projects from database...")
    all_projects = db.query(Project.project_id, Project.state, Project.district, Project.description).all()
    total_projects = len(all_projects)
    print(f"Total projects to geocode: {total_projects}")

    tier_counts = {}
    updates = []
    for p_id, state, district, desc in all_projects:
        lat, lon, tier = resolve_project_coordinates(p_id, state, district, desc, dist_map)
        tier_counts[tier] = tier_counts.get(tier, 0) + 1
        updates.append({'p_id': p_id, 'lat': lat, 'lon': lon})

    print("Geocoding classification summary:")
    for tier, cnt in sorted(tier_counts.items(), key=lambda x: -x[1]):
        print(f"  {tier}: {cnt} ({cnt/total_projects*100:.1f}%)")

    print("Updating coordinates in PostgreSQL...")
    batch_size = 5000
    with engine.begin() as conn:
        # Create temp table for fast batch update
        conn.execute(text("CREATE TEMP TABLE tmp_coords (project_id VARCHAR(100), latitude DOUBLE PRECISION, longitude DOUBLE PRECISION) ON COMMIT DROP;"))
        for i in range(0, len(updates), batch_size):
            chunk = updates[i:i + batch_size]
            conn.execute(
                text("INSERT INTO tmp_coords (project_id, latitude, longitude) VALUES (:p_id, :lat, :lon)"),
                chunk
            )
            print(f"  Pushed {min(i + batch_size, len(updates))}/{len(updates)} to temp table...")

        print("Executing bulk UPDATE join...")
        conn.execute(text("""
            UPDATE projects p
            SET latitude = t.latitude,
                longitude = t.longitude,
                updated_at = NOW()
            FROM tmp_coords t
            WHERE p.project_id = t.project_id;
        """))

    print("PostgreSQL update completed successfully!")

    # Check key projects
    test_ids = ['MPLAD-77000', 'MPLAD-15402', 'MPLAD-64814', 'MPLAD-39535', 'MPLAD-59732', 'MPLAD-58604']
    for tid in test_ids:
        p = db.query(Project).filter(Project.project_id == tid).first()
        if p:
            print(f"Verified {p.project_id}: Lat={p.latitude}, Lon={p.longitude} | {p.description[:60]}")

    db.close()

if __name__ == "__main__":
    run_coordinate_update()

