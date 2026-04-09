import asyncio
import logging
import math
from abc import abstractmethod, ABC
from typing import Generator

from operator import mul, add

from GhostBot import logger
from GhostBot.client_window import Win32ClientWindow
from GhostBot.config import Config, ConfigLoader, LoginDetailsConfigLoader
from GhostBot.controller.async_task_runner import AsyncTaskRunner
from GhostBot.controller.login_controller import LoginController
from GhostBot.enums.bot_status import BotStatus
from GhostBot.functions import Attack, Buffs, Fairy, Petfood, Regen, Runner, Sell, Delete
from GhostBot.lib.math import linear_distance, position_difference, scale_minimap_move_distance, coords_to_map_screen_pos
from GhostBot.lib.talisman_ui_locations import UI_locations
from GhostBot.lib.win32.process import PymemProcess
from GhostBot.map_navigation import location_to_zone_map, zones


class BotClientWindow(Win32ClientWindow):
    running: bool = False
    bot_status: BotStatus = BotStatus.created
    config: Config = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.disconnected:
            self.bot_status = BotStatus.disconnected
        self.load_config()

    def to_json(self) -> dict:
        return dict(
            name=self.name,
            status=self.bot_status.name,
            hp=self.hp,
            mana=self.mana,
            max_hp=self.max_hp,
            max_mana=self.max_mana,
            level=self.level,
            target_name=self.target_name,
            target_hp=self.target_hp,
            location_x=self.location_x,
            location_y=self.location_y,
            location_name=self.location_name,
            pet_active=self.pet_active,
            sitting=self.sitting,
            in_battle=self.in_battle,
            inventory_open=self.inventory_open,
            #target_location=self.target_location,
            mounted=self.on_mount,
            window_pos=self.get_window_pos(),
            window_size=self.get_window_size(),
        )

    async def mount(self, _key=0):
        if self.config.sell is not None and self.config.sell.use_mount:
            await super().mount(_key)

    async def unmount(self, _key=0):
        if self.config.sell is not None and self.config.sell.use_mount:
            await super().dismount(_key)

    def load_config(self):
        self.set_config(ConfigLoader(self).load())

    def set_config(self, config: Config):
        self.config = config

    @property
    def bot_status_string(self) -> str:
        return str(self.bot_status.name)

    @property
    def hp_percent(self) -> float:
        return self.hp / self.max_hp

    @property
    def mana_percent(self) -> float:
        return self.mana / self.max_mana

    def start_bot(self):
        logger.info(f'{self.name}: Starting...')
        if self.disconnected:
            self.bot_status = BotStatus.disconnected
            logger.info(f'{self.name}: Client disconnected.')
        self.bot_status = BotStatus.starting
        self.running = True
        self.load_config()

    def stop_bot(self):
        logger.info(f'{self.name}: Stopping...')
        self.bot_status = BotStatus.stopping
        self.running = False

    async def move_to_pos(self, target_pos):
        """
        moves to `target_pos`, will invoke map based pathing if distance is too far.
        :param target_pos: `tuple(x, y)` coordinates to move too
        """
        while linear_distance(self.location, target_pos) > 50 and self.running:
            logger.debug(f"{self.name} moving via map")
            return await self._move_to_pos_via_map(target_pos)

        pos_diff = position_difference(self.location, target_pos)

        pos_diff_mm_pix = tuple(map(mul, pos_diff, (-1.7, 1.7)))  # corrected to represent 1 pixel per meter

        minimap_relative_pos = scale_minimap_move_distance(pos_diff_mm_pix)
        minimap_pos: tuple[float, float] = tuple(map(math.ceil, map(add, UI_locations.minimap_centre, minimap_relative_pos)))  # mouse position

        logger.debug(f'{self.name}: clicking {minimap_relative_pos}')  # relative to minimap center
        await self.right_click(minimap_pos)
        await self.block_while_moving()

    async def _move_to_pos_via_map(self, target_pos: tuple[int, int]):
        zone = location_to_zone_map[self.location_name.strip()]
        screen_coords = coords_to_map_screen_pos(
            zones[zone],
            target_pos
        )
        # Open the map, and try a list of position offsets, starting at the exact point we want to go to
        # this avoids movement being blocked when team members are already where we want to be
        offsets = ((0, 0), (20, 0), (-20, 0), (20, 20), (-20, 20), (-20, -20), (0, -20), (-20, 20), (0, 20))
        self.press_key('m')
        await asyncio.sleep(1)
        _loc = self.location
        await self.right_click(tuple(map(add, screen_coords, (-30, -30)))) # Click away from tgt to clear possible existing tgt
        for offset in offsets:
            path_tgt = tuple(map(add, screen_coords, offset))
            await self.right_click(path_tgt)
            await asyncio.sleep(2)
            if linear_distance(_loc, self.location) > 1:
                # If we've started moving, we can stop trying offsets
                break
        else:
            logger.info(f'{self.name}: failed pathing via map')
            self.press_key('m')
            return False

        await asyncio.sleep(1)
        self.press_key('m')
        await self.block_while_moving(path_tgt)
        if target_pos != path_tgt:
            # If we moved to a non-zero offset location, we will need to use the minimap to move to the right spot
            # we're close enough now that it'll work.
            await self.move_to_pos(target_pos)
            await self.block_while_moving()
        return True

    async def block_while_moving(self, destination=None):
        while self.running:
            _location = self.location
            await asyncio.sleep(3)
            if destination is not None:
                if linear_distance(destination, self.location) < 40:  # if we're close enough, no point overshooting.
                    break
            if linear_distance(self.location, _location) < 1:
                break



class BotController(ABC):

    _pymem_process = PymemProcess
    login_config = None

    def __init__(self):
        self.clients: dict[str, BotClientWindow] = dict()
        self._pending_clients: dict[str, BotClientWindow] = dict()
        self.login_queue: dict[int, BotClientWindow] = dict()
        self._seen_clients = []

        self._scan_for_clients()
        self._load_login_config()

    def _load_login_config(self):
        self.login_config = LoginDetailsConfigLoader().load()

    def _eligible_logins(self):
        return {k: v for k, v in self.login_config.items() if (k not in self.client_keys) and (k not in self._pending_clients.keys())}

    def _scan_for_clients(self):
        current_client_proc_ids = {c.proc.process_id for c in self.clients.values()}
        detected_procs = self._pymem_process.list_clients()

        if [p.process_id for p in detected_procs] == self._seen_clients:
            logger.debug('BotController :: not running full client scan as no changes detected to process list.')
            self._seen_clients = [p.process_id for p in detected_procs]
            return

        self._seen_clients = [p.process_id for p in detected_procs]

        _to_remove = []
        for k, v in self.clients.items():
            if (c_pid := v.proc.process_id) not in (p.process_id for p in detected_procs):
                logger.info("removing [%s]", c_pid)
                _to_remove.append(k)
        for k in _to_remove:
            try:
                asyncio.get_running_loop().run_until_complete(self.stop_bot(self.clients.pop(k)))
            except Exception as e:
                logger.info(e)
        for proc in detected_procs:
            if proc.process_id in current_client_proc_ids:
                logger.debug("Process [%s] already registered with BotController, skipping.", proc.process_id)
                continue
            client = BotClientWindow(proc)
            try:
                if client.name is None and client.get_window_name() not in self._pending_clients.keys():
                    logger.debug("[%s] client.name is None, possibly hasnt logged in yet", proc.process_id)
                    if proc.process_id not in self.login_queue.keys():
                        logger.info("[%s] adding process to login_queue routine", proc.process_id)
                        self.login_queue[proc.process_id] = client
                    continue
                if 0 > client.level >= 89:
                    logger.info("[%s] client.level(%s) < 0 or > 89.", proc.process_id, client.level)
                    continue
                if client.name not in self.client_keys:
                    logger.info(f'adding client {client.name} {client.disconnected}')
                    self.add_client(BotClientWindow(proc))
                else:
                    logger.debug(f'client {client.name} already exists, skipping')
            except (TypeError, AttributeError):
                # TODO: do i want to track this for the autologin? might be an alright hook
                #       especially if we know which char to log...
                logger.info(f'cannot add client {proc}')

    @property
    def client_keys(self) -> list[str]:
        return list(str(k) for k in self.clients.keys())

    def add_client(self, client: BotClientWindow) -> None:
        self.clients[client.name] = client

    @abstractmethod
    def start_bot(self, client: BotClientWindow | str) -> None: ...

    def reload_bot_config(self, client: str | BotClientWindow) -> None:
        if isinstance(client, str):
            if (client := self.get_client(client)) is None:
                logger.warning(f'no client {client}')
                return
        client.load_config()

    def get_client(self, name) -> BotClientWindow | None:
        return self.clients.get(name)

    def _get_functions_for_client(self, client: BotClientWindow) -> Generator[Runner, None, None]:
        if client.config.delete is not None:
            yield Delete(client)
        if client.config.sell is not None:
            yield Sell(client)
        if client.config.pet is not None:
            yield Petfood(client)
        if client.config.regen is not None:
            yield Regen(client)
        if client.config.buff is not None:
            yield Buffs(client)
        if client.config.attack is not None:
            yield Attack(client)
        if client.config.fairy is not None:
            yield Fairy(self, client)

    @abstractmethod
    async def stop_all_bots(self, timeout=30) -> None: ...

    @abstractmethod
    async def stop_bot(self, client: str | BotClientWindow, timeout=5) -> None: ...

    @abstractmethod
    async def listen(self, host=None, port=None): ...

if __name__ == "__main__":
    import os
    from GhostBot.image_finder import ImageFinder
    from GhostBot import logger
    import logging
    import time
    from GhostBot.controller.async_bot_controller import AsyncBotController

    logger.setLevel(logging.DEBUG)

    abc = AsyncBotController()
    asyncio.run(abc._rescan_clients())

    # print(foo)
    #
    # class TestBotController(BotController):
    #     def start_bot(self, client: BotClientWindow | str) -> None:
    #         pass
    #
    #     async def stop_all_bots(self, timeout=30) -> None:
    #         pass
    #
    #     async def stop_bot(self, client: str | BotClientWindow, timeout=5) -> None:
    #         pass
    #
    #     async def listen(self, host=None, port=None):
    #         pass
    #
    # b = TestBotController()
    # atr = AsyncTaskRunner()
    # async def do_stuff():
    #     async def callback(_pid, result):
    #         if not result:
    #             await atr._remove_task(f'task{_pid}')
    #             for k,v in b._pending_clients.items():
    #                 if v == b.login_queue[_pid]:
    #                     b._pending_clients.pop(k)
    #         else:
    #             print('yay')
    #
    #     while True:
    #         print('_eligible_logins', b._eligible_logins())
    #         for pid, _client in b.login_queue.items():
    #             if not b._eligible_logins():
    #                 continue
    #
    #             if f"task{pid}" not in atr._tasks.keys():
    #                 lc = LoginController(_client)
    #
    #                 if lc.current_stage == LoginController.LoginStage.character_select:
    #                     await asyncio.sleep(5)  # fixes a race condition with the client window opening
    #
    #                 char = _client.get_window_name()
    #
    #                 if char in b._eligible_logins().keys() and _client.name is None:
    #                     print(f'[{pid}] resuming login procedure')
    #                     _conf = b._eligible_logins().pop(char)
    #                 elif lc.current_stage == LoginController.LoginStage.enter_credentials:
    #                     print(f'[{pid}] starting login procedure')
    #                     _conf = b._eligible_logins().popitem()
    #                     char = _conf[0]
    #                 else:
    #                     continue
    #
    #                 b._pending_clients[char] = _client
    #
    #                 if lc.current_stage == LoginController.LoginStage.enter_credentials:
    #                     print(f'[{pid}] setting config for LoginController')
    #                     lc.set_config(_conf)
    #                 atr._add_task(lc.handle_login(lambda result: callback(pid, result)), f"task{pid}")
    #         await asyncio.sleep(10)
    #         b._scan_for_clients()
    #
    #
    # asyncio.run(do_stuff())
    #     # if _if.find_ui_element(os.path.join(ImageFinder.misc_folder, 'login_main_page.bmp'),threshold=0.6):
    #     #     # Enter char creds
    #     #     print("enter char creds")
    #     #     _client.type_keys("hi")
    #     # if _if.find_ui_element(os.path.join(ImageFinder.misc_folder, 'login_server_select.bmp'),threshold=0.8):
    #     #     print("server select")
    #     #     asyncio.run(_client.left_click(UI_locations.server_select.light_in_the_darkness))
    #     #     asyncio.run(_client.left_click(UI_locations.server_select.ok))
    #     # if _if.find_ui_element(os.path.join(ImageFinder.misc_folder, 'login_queue.bmp')): #if we arent in the queue
    #     #     print("login_queue")
    #     # else:
    #     #     asyncio.run(_client.left_click((510, 735)))
