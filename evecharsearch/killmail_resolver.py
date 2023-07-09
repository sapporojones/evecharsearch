from datetime import date, datetime

from loguru import logger
import requests
import snoop


class KillmailResolver:
    def __init__(self):
        self.i = ""
        self.h = ""
        self.c = ""

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

    def hook(self, *args):
        args = list(args[0])
        self.i = args[0]
        self.h = args[1]
        self.c = args[2]
        self.get_kill()
        self.parse_kill()
        self.resolve_ids()

    def get_kill(self):
        url = f"https://esi.evetech.net/latest/killmails/{self.i}/{self.h}/?datasource=tranquility"
        robj = requests.get(url)
        rjson = robj.json()
        self.kill_json = rjson

    def parse_kill(self):
        self.kill_time = self.kill_json["killmail_time"]

        try:
            if self.kill_json["victim"]["character_id"] == self.c:
                self.pla_ship = self.kill_json["victim"]["ship_type_id"]
                self.oppo_ship = (
                    "601"  # for a loss we don't care about opponent ship so set to ibis
                )
            else:
                for attacker in self.kill_json["attackers"]:
                    # breakpoint()
                    if attacker["character_id"] == self.c:
                        self.pla_ship = attacker["ship_type_id"]
                        self.oppo_ship = self.kill_json["victim"]["ship_type_id"]
                    else:
                        pass
        # The below KeyError is the likely result of the kill showing a weapon type instead of a ship
        except KeyError:
            for attacker in self.kill_json["attackers"]:
                # if attacker block is 6 it's almost certainly a drone from a citadel we should ignore
                if len(attacker) == 6:
                    pass
                # if attacker block is 5 it's almost certainly an npc participant which we should ignore
                elif len(attacker) == 5:
                    pass
                else:
                    if attacker["character_id"] == self.c:
                        self.pla_ship = attacker["weapon_type_id"]
                        self.oppo_ship = self.kill_json["victim"]["ship_type_id"]

        self.loc_id = self.kill_json["solar_system_id"]

        init_date = self.kill_json["killmail_time"]
        date_snip = init_date[0:10]
        self.kill_date = date_snip

        dd = datetime.utcnow().date() - datetime.strptime(date_snip, "%Y-%m-%d").date()
        self.kill_days = dd.days

    def resolve_ids(self):
        url = "https://esi.evetech.net/latest/universe/names/?datasource=tranquility"

        payload = [self.oppo_ship, self.pla_ship, self.loc_id]
        if len(payload) == len(set(payload)):
            robj = requests.post(url, json=payload)
            rjson = robj.json()
            self.oppo_ship_type = rjson[0]["name"]
            self.pla_ship_type = rjson[1]["name"]
            self.loc_name = rjson[2]["name"]

        else:
            payload = [self.oppo_ship]
            robj = requests.post(url, json=payload)
            rjson = robj.json()
            self.oppo_ship_type = rjson[0]["name"]

            payload = [self.pla_ship]
            robj = requests.post(url, json=payload)
            rjson = robj.json()
            self.pla_ship_type = rjson[0]["name"]

            payload = [self.loc_id]
            robj = requests.post(url, json=payload)
            rjson = robj.json()
            self.loc_name = rjson[0]["name"]
