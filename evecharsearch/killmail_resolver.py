import requests
from loguru import logger
import snoop
from datetime import date, datetime


class KillmailResolver:
    def __init__(self, kill_id, kill_hash, char_id):
        self.i = kill_id
        self.h = kill_hash
        self.c = char_id

        self.kill_json = ""

        self.kill_time = ""
        self.oppo_ship = ""
        self.pla_ship = ""
        self.loc_id = ""

        self.oppo_ship_type = ""
        self.pla_ship_type = ""
        self.loc_name = ""
        self.kill_days = ""
        self.kill_date = ""

    def dispatcher(self):
        self.get_kill()
        logger.info("Parsing kill {}...", self.i)
        self.parse_kill()
        self.resolve_ids()

    def get_kill(self):
        url = f"https://esi.evetech.net/latest/killmails/{self.i}/{self.h}/?datasource=tranquility"
        robj = requests.get(url)
        rjson = robj.json()
        self.kill_json = rjson
        l = len(rjson)
        # logger.info("JSON Length: {}", l)

    def parse_kill(self):
        self.kill_time = self.kill_json["killmail_time"]

        if self.kill_json["victim"]["character_id"] == self.c:
            self.pla_ship = self.kill_json["victim"]["ship_type_id"]
            self.oppo_ship = (
                "601"  # for a loss we don't care about opponent ship so set to ibis
            )
        else:
            for attacker in self.kill_json["attackers"]:
                if attacker["character_id"] == self.c:
                    self.pla_ship = attacker["ship_type_id"]
                    self.oppo_ship = self.kill_json["victim"]["ship_type_id"]
        self.loc_id = self.kill_json["solar_system_id"]

        init_date = self.kill_json["killmail_time"]
        date_snip = init_date[0:10]
        self.kill_date = date_snip

        dd = datetime.utcnow().date() - datetime.strptime(date_snip, "%Y-%m-%d").date()
        self.kill_days = dd.days

        # logger.info("time: {}, vic: {}, att: {}, loc: {}", self.kill_time, self.vic_ship, self.att_ship, self.loc_id)

    # @snoop
    def resolve_ids(self):
        url = "https://esi.evetech.net/latest/universe/names/?datasource=tranquility"

        payload = [self.oppo_ship, self.pla_ship, self.loc_id]

        robj = requests.post(url, json=payload)
        rjson = robj.json()

        # logger.info("{}", rjson)

        self.oppo_ship_type = rjson[0]["name"]
        self.pla_ship_type = rjson[1]["name"]
        self.loc_name = rjson[2]["name"]

        # logger.info("vic ship: {} att ship: {} loc: {}", self.vic_ship_type, self.att_ship_type, self.loc_name)
