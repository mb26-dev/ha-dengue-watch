"""Constants for Mosquito Watch Thailand (formerly Dengue Watch Thailand)."""

from datetime import timedelta

DOMAIN = "dengue_watch"
NAME = "Mosquito Watch Thailand"
ATTRIBUTION = (
    "Data: Digital Disease Surveillance (Report 506), Department of Disease Control, "
    "Ministry of Public Health Thailand. Unofficial integration, not affiliated with the DDC."
)

CONF_PROVINCE = "province"  # version 1 entries (one province, dengue only)
CONF_PROVINCES = "provinces"
CONF_DISEASES = "diseases"

# The DDS dashboard "Disease situation" (รายงานสถานการณ์โรค) on the DDC Tableau server.
# View 2 is the weekly line chart with the five years before; the URL filters pick the
# diseases and the province. The dashboard is refreshed about every 6 hours.
BASE_URL = "https://dvis3.ddc.moph.go.th/t/DDC_CENTER_DOE/views/_17806397830560/2.csv"
DASHBOARD_URL = "https://ddsdoe.ddc.moph.go.th/dds-portal/"
# mosquito-borne diseases of Report 506 and the values of the dashboard's disease filter
# (note the trailing space DDC uses in "Dengue fever ")
DISEASES: dict[str, dict[str, str]] = {
    "dengue": {"name": "Dengue", "filter": "Dengue fever ,Dengue haemorrhagic fever (DHF),Dengue shock syndrome (DSS)"},
    "malaria": {"name": "Malaria", "filter": "Malaria"},
    "chikungunya": {"name": "Chikungunya", "filter": "Chikungunya fever"},
    "zika": {"name": "Zika", "filter": "Zika virus disease"},
}
DEFAULT_DISEASES = list(DISEASES)
NEARBY_KM = 110  # provinces suggested around the home province

REQUEST_GAP = 2.0  # seconds between two exports, to go easy on the DDC server
CACHE_VERSION = 1

UPDATE_INTERVAL = timedelta(hours=6)
REQUEST_TIMEOUT = 120  # the dashboard needs 5 - 30 s for an export
USER_AGENT = "HomeAssistant-dengue_watch (+https://github.com/mb26-dev/ha-dengue-watch)"

# English name -> name used by the DDC (Thai)
PROVINCES: dict[str, str] = {
    "Amnat Charoen": "อำนาจเจริญ",
    "Ang Thong": "อ่างทอง",
    "Bangkok": "กรุงเทพมหานคร",
    "Bueng Kan": "บึงกาฬ",
    "Buriram": "บุรีรัมย์",
    "Chachoengsao": "ฉะเชิงเทรา",
    "Chai Nat": "ชัยนาท",
    "Chaiyaphum": "ชัยภูมิ",
    "Chanthaburi": "จันทบุรี",
    "Chiang Mai": "เชียงใหม่",
    "Chiang Rai": "เชียงราย",
    "Chonburi": "ชลบุรี",
    "Chumphon": "ชุมพร",
    "Kalasin": "กาฬสินธุ์",
    "Kamphaeng Phet": "กำแพงเพชร",
    "Kanchanaburi": "กาญจนบุรี",
    "Khon Kaen": "ขอนแก่น",
    "Krabi": "กระบี่",
    "Lampang": "ลำปาง",
    "Lamphun": "ลำพูน",
    "Loei": "เลย",
    "Lopburi": "ลพบุรี",
    "Mae Hong Son": "แม่ฮ่องสอน",
    "Maha Sarakham": "มหาสารคาม",
    "Mukdahan": "มุกดาหาร",
    "Nakhon Nayok": "นครนายก",
    "Nakhon Pathom": "นครปฐม",
    "Nakhon Phanom": "นครพนม",
    "Nakhon Ratchasima": "นครราชสีมา",
    "Nakhon Sawan": "นครสวรรค์",
    "Nakhon Si Thammarat": "นครศรีธรรมราช",
    "Nan": "น่าน",
    "Narathiwat": "นราธิวาส",
    "Nong Bua Lamphu": "หนองบัวลำภู",
    "Nong Khai": "หนองคาย",
    "Nonthaburi": "นนทบุรี",
    "Pathum Thani": "ปทุมธานี",
    "Pattani": "ปัตตานี",
    "Phang Nga": "พังงา",
    "Phatthalung": "พัทลุง",
    "Phayao": "พะเยา",
    "Phetchabun": "เพชรบูรณ์",
    "Phetchaburi": "เพชรบุรี",
    "Phichit": "พิจิตร",
    "Phitsanulok": "พิษณุโลก",
    "Phra Nakhon Si Ayutthaya": "พระนครศรีอยุธยา",
    "Phrae": "แพร่",
    "Phuket": "ภูเก็ต",
    "Prachinburi": "ปราจีนบุรี",
    "Prachuap Khiri Khan": "ประจวบคีรีขันธ์",
    "Ranong": "ระนอง",
    "Ratchaburi": "ราชบุรี",
    "Rayong": "ระยอง",
    "Roi Et": "ร้อยเอ็ด",
    "Sa Kaeo": "สระแก้ว",
    "Sakon Nakhon": "สกลนคร",
    "Samut Prakan": "สมุทรปราการ",
    "Samut Sakhon": "สมุทรสาคร",
    "Samut Songkhram": "สมุทรสงคราม",
    "Saraburi": "สระบุรี",
    "Satun": "สตูล",
    "Sing Buri": "สิงห์บุรี",
    "Sisaket": "ศรีสะเกษ",
    "Songkhla": "สงขลา",
    "Sukhothai": "สุโขทัย",
    "Suphan Buri": "สุพรรณบุรี",
    "Surat Thani": "สุราษฎร์ธานี",
    "Surin": "สุรินทร์",
    "Tak": "ตาก",
    "Trang": "ตรัง",
    "Trat": "ตราด",
    "Ubon Ratchathani": "อุบลราชธานี",
    "Udon Thani": "อุดรธานี",
    "Uthai Thani": "อุทัยธานี",
    "Uttaradit": "อุตรดิตถ์",
    "Yala": "ยะลา",
    "Yasothon": "ยโสธร",
}

# province centroids (lon, lat), from the simplified province outlines of the card
CENTROIDS: dict[str, tuple[float, float]] = {
    "Amnat Charoen": (104.769, 15.87),
    "Ang Thong": (100.355, 14.624),
    "Bangkok": (100.621, 13.772),
    "Bueng Kan": (103.721, 18.146),
    "Buriram": (102.972, 14.824),
    "Chachoengsao": (101.446, 13.604),
    "Chai Nat": (100.025, 15.137),
    "Chaiyaphum": (101.802, 16.009),
    "Chanthaburi": (102.12, 12.863),
    "Chiang Mai": (98.734, 18.79),
    "Chiang Rai": (99.866, 19.844),
    "Chonburi": (101.21, 13.197),
    "Chumphon": (99.07, 10.367),
    "Kalasin": (103.629, 16.631),
    "Kamphaeng Phet": (99.502, 16.329),
    "Kanchanaburi": (99.04, 14.585),
    "Khon Kaen": (102.588, 16.404),
    "Krabi": (99.014, 8.153),
    "Lampang": (99.525, 18.352),
    "Lamphun": (98.965, 18.142),
    "Loei": (101.63, 17.409),
    "Lopburi": (100.914, 15.075),
    "Mae Hong Son": (98.027, 18.755),
    "Maha Sarakham": (103.18, 15.994),
    "Mukdahan": (104.525, 16.556),
    "Nakhon Nayok": (101.174, 14.217),
    "Nakhon Pathom": (100.109, 13.924),
    "Nakhon Phanom": (104.435, 17.372),
    "Nakhon Ratchasima": (102.117, 14.958),
    "Nakhon Sawan": (100.132, 15.692),
    "Nakhon Si Thammarat": (99.778, 8.373),
    "Nan": (100.825, 18.845),
    "Narathiwat": (101.722, 6.172),
    "Nong Bua Lamphu": (102.298, 17.173),
    "Nong Khai": (102.842, 17.94),
    "Nonthaburi": (100.389, 13.927),
    "Pathum Thani": (100.679, 14.061),
    "Pattani": (101.353, 6.73),
    "Phang Nga": (98.424, 8.679),
    "Phatthalung": (100.032, 7.513),
    "Phayao": (100.185, 19.228),
    "Phetchabun": (101.147, 16.269),
    "Phetchaburi": (99.614, 12.937),
    "Phichit": (100.357, 16.237),
    "Phitsanulok": (100.53, 16.971),
    "Phra Nakhon Si Ayutthaya": (100.528, 14.341),
    "Phrae": (100.065, 18.195),
    "Phuket": (98.342, 7.975),
    "Prachinburi": (101.625, 14.075),
    "Prachuap Khiri Khan": (99.626, 11.921),
    "Ranong": (98.719, 10.0),
    "Ratchaburi": (99.574, 13.532),
    "Rayong": (101.423, 12.852),
    "Roi Et": (103.826, 15.923),
    "Sa Kaeo": (102.293, 13.777),
    "Sakon Nakhon": (103.822, 17.389),
    "Samut Prakan": (100.706, 13.598),
    "Samut Sakhon": (100.216, 13.572),
    "Samut Songkhram": (99.956, 13.394),
    "Saraburi": (100.939, 14.576),
    "Satun": (99.964, 6.851),
    "Sing Buri": (100.353, 14.922),
    "Sisaket": (104.379, 14.857),
    "Songkhla": (100.582, 6.804),
    "Sukhothai": (99.699, 17.247),
    "Suphan Buri": (99.898, 14.608),
    "Surat Thani": (99.063, 9.031),
    "Surin": (103.669, 14.884),
    "Tak": (98.796, 16.698),
    "Trang": (99.616, 7.529),
    "Trat": (102.535, 12.358),
    "Ubon Ratchathani": (105.12, 15.178),
    "Udon Thani": (102.856, 17.425),
    "Uthai Thani": (99.46, 15.339),
    "Uttaradit": (100.509, 17.742),
    "Yala": (101.225, 6.184),
    "Yasothon": (104.339, 15.89),
}
