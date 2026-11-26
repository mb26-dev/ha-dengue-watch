"""Constants for Dengue Watch Thailand."""

from datetime import timedelta

DOMAIN = "dengue_watch"
NAME = "Dengue Watch Thailand"
ATTRIBUTION = (
    "Data: Digital Disease Surveillance (Report 506), Department of Disease Control, "
    "Ministry of Public Health Thailand. Unofficial integration, not affiliated with the DDC."
)

CONF_PROVINCE = "province"

# The DDS dashboard "Disease situation" (รายงานสถานการณ์โรค) on the DDC Tableau server.
# View 2 is the weekly line chart with the five years before; the URL filters pick the
# diseases and the province. The dashboard is refreshed about every 6 hours.
BASE_URL = "https://dvis3.ddc.moph.go.th/t/DDC_CENTER_DOE/views/_17806397830560/2.csv"
DASHBOARD_URL = "https://ddsdoe.ddc.moph.go.th/dds-portal/"
# all three dengue diagnoses of Report 506 (note the trailing space DDC uses in the first one)
DISEASES = "Dengue fever ,Dengue haemorrhagic fever (DHF),Dengue shock syndrome (DSS)"

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
