from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import as_completed

from loguru import logger
import requests
import snoop

from killmail_resolver import KillmailResolver


class LookupController:
    def __init__(self, char_name, max_n):
        self.cn = char_name
        self.id = ""
        self.kills_json = ""
        self.recent_kills = ""
        self.losses_json = ""
        self.recent_losses = ""
        self.recent_kill_hashes = ""
        self.recent_loss_hashes = ""
        self.alltime_kills = ""
        self.alltime_loss = ""
        self.alltime_solo_kills = ""
        self.alltime_solo_losses = ""
        self.bday = ""
        self.last_kill = ""
        self.last_kill_readable = ""
        self.last_loss = ""
        self.last_loss_readable = ""
        self.kills_list = ""
        self.losses_list = ""
        self.max_n = max_n

        self.get_id()
        self.get_kills_json()
        self.get_losses_json()
        self.get_char_stats()
        self.kb_populate()
        self.print_report()

    # @snoop
    def get_id(self):
        logger.info("Getting character ID for {}...", self.cn)
        url = "https://esi.evetech.net/latest/universe/ids/?datasource=tranquility&language=en"
        payload = f'["{self.cn}"]'

        # logger.info("Name: {cn} | Payload: {payload}", cn=self.cn, payload=payload)

        req_obj = requests.post(url, data=payload)
        req_json = req_obj.json()
        char_id = req_json["characters"][0]["id"]
        self.id = char_id

        logger.info("Character ID: {id}", id=char_id)

    # @snoop
    def get_kills_json(self):
        logger.info("Fetching recent kill information for {}...", self.cn)
        url = f"https://zkillboard.com/api/kills/characterID/{self.id}/"
        robj = requests.get(url)
        kills_json = robj.json()
        self.kills_json = kills_json

        recent_kills = []
        recent_kill_hashes = []
        for n in range(0, self.max_n):
            recent_kills.append(kills_json[n]["killmail_id"])
            recent_kill_hashes.append(kills_json[n]["zkb"]["hash"])

        self.recent_kills = recent_kills
        self.recent_kill_hashes = recent_kill_hashes

    def get_losses_json(self):
        logger.info("Fetching recent loss information for {}...", self.cn)
        url = f"https://zkillboard.com/api/losses/characterID/{self.id}/"
        robj = requests.get(url)
        losses_json = robj.json()
        self.losses_json = losses_json

        recent_losses = []
        recent_loss_hashes = []
        for n in range(0, self.max_n):
            recent_losses.append(losses_json[n]["killmail_id"])
            recent_loss_hashes.append(losses_json[n]["zkb"]["hash"])

        self.recent_losses = recent_losses
        self.recent_loss_hashes = recent_loss_hashes

    def get_char_stats(self):
        logger.info("Fetching zkillboard stats for {}...", self.cn)

        zurl = f"https://zkillboard.com/api/stats/characterID/{self.id}/"
        zrobj = requests.get(zurl)
        stats_json = zrobj.json()

        eurl = f"https://esi.evetech.net/latest/characters/{self.id}/"
        erobj = requests.get(eurl)
        erjson = erobj.json()

        self.bday = erjson["birthday"]
        self.alltime_kills = stats_json["shipsDestroyed"]
        self.alltime_loss = stats_json["shipsLost"]

        # Zkill might now show this regardless of if number is 0, commenting out for testing
        # if not stats_json["soloKills"]:
        #     self.alltime_solo_kills = 0
        # else:
        #     self.alltime_solo_kills = stats_json["soloKills"]
        # if not stats_json["soloLosses"]:
        #     self.alltime_solo_losses = 0
        # else:
        #     self.alltime_solo_losses = stats_json["soloLosses"]

    def lazy_init(self, *args):
        k = KillmailResolver()
        k.hook(args)
        return k

    def kb_populate(self):
        self.kills_list = []

        logger.info("Populating recent kills...")

        # hacky list expansion
        hacky_char_id_list = []
        recent_kills = self.recent_kills
        recent_kill_hashes = self.recent_kill_hashes
        for x in self.recent_kills:
            hacky_char_id_list.append(self.id)

        with ThreadPoolExecutor(max_workers=5) as executor:

            future_result = executor.map(
                self.lazy_init, recent_kills, recent_kill_hashes, hacky_char_id_list
            )

            for future in future_result:
                self.kills_list.append(future)

        logger.info("Populating recent losses...")
        self.losses_list = []
        with ThreadPoolExecutor(max_workers=5) as executor:

            future_result = executor.map(
                self.lazy_init,
                self.recent_losses,
                self.recent_loss_hashes,
                hacky_char_id_list,
            )

            for future in future_result:
                self.losses_list.append(future)

    def print_report(self):
        logger.info("Generating report...")
        print(f"\n\n\n")
        print(f"Character name: {self.cn}")
        print(f"Character ID: {self.id}")
        print(f"Character born on: {self.bday}")
        print(f"\n")
        print(f"Total kills: {self.alltime_kills}")
        print(f"Total losses: {self.alltime_loss}")
        print(f"Total solo kills: {self.alltime_solo_kills}")
        print(f"Total solo losses: {self.alltime_solo_losses}")
        print(f"\n")
        print(
            f"Last kill was {self.kills_list[0].kill_date} which was {self.kills_list[0].kill_days} days ago"
        )
        print(
            f"Last loss was {self.losses_list[0].kill_date} which was {self.losses_list[0].kill_days} days ago"
        )
        print(f"\n")
        print(f"Zkill url: https://zkillboard.com/character/{self.id}/")
        print(f"Evewho url: https://evewho.com/character/{self.id}")
        print(f"\n")
        print(f"Most recent kills:")
        for idx, kill in enumerate(self.kills_list):
            print(
                f"( https://zkillboard.com/kill/{self.kills_list[idx].i}/ ) On {self.kills_list[idx].kill_date} Killed a {self.kills_list[idx].oppo_ship_type} while flying a {self.kills_list[idx].pla_ship_type} in {self.kills_list[idx].loc_name}"
            )
        print(f"Most recent losses:")
        for idx, loss in enumerate(self.losses_list):
            print(
                f"( https://zkillboard.com/kill/{self.losses_list[idx].i}/ ) On {self.losses_list[idx].kill_date} Lost a {self.losses_list[idx].pla_ship_type} in {self.losses_list[idx].loc_name}"
            )
