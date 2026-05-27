from __future__ import annotations

import math
import threading
import time
from abc import abstractmethod, ABC
from typing import Generator, TYPE_CHECKING

from operator import mul, add

from GhostBot import logger as _logger
from GhostBot.IPC.server import IPCServerLogHandler
from GhostBot.client_window import Win32ClientWindow
from GhostBot.config import ConfigLoader, LoginDetailsConfigLoader, GhostBotServerConfigLoader
from GhostBot.enums.bot_status import BotStatus
from GhostBot.functions import Attack, Fairy, Boss, Petfood, Runner, Sell
from GhostBot.lib.math import linear_distance, position_difference, scale_minimap_move_distance, coords_to_map_screen_pos
from GhostBot.lib.talisman_ui_locations import UI_locations
from GhostBot.lib.win32.process import PymemProcess
from GhostBot.map_navigation import location_to_zone_map, zones
from GhostBot.server import GhostbotIPCServer


if TYPE_CHECKING:
    from GhostBot.config import Config

lock = threading.Lock()

class BotClientWindow(Win32ClientWindow):
    running: bool = False
    bot_status: BotStatus = BotStatus.created
    config: Config = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.disconnected:
            self.bot_status = BotStatus.disconnected
        self.load_config()
        # Stats simples (dashboard)
        self.kills: int = 0
        self._last_target_hp_seen: int | None = None
        self._farm_start_ts: float | None = None  # timestamp do ultimo Start
        self._xp_gained: int = 0
        self._last_xp: int | None = None
        self._gold_start: int | None = None
        self.drops: dict[str, int] = {}  # contagem de drops da sessao (Dashboard)
        self.current_action: str = "parado"  # acao atual do bot (barra grifada no Dashboard)
        self.sell_requested: bool = False  # mochila cheia detectada -> Sell vende na proxima volta

    def to_json(self) -> dict:
        # Detecção de kill: alvo estava com HP positivo, agora ta None/<0 (dead/no target)
        current_target_hp = self.target_hp
        _last = self._last_target_hp_seen
        if _last is not None and _last > 0:
            # alvo morreu (None/<=0) OU o HP SUBIU (trocou pra um mob novo = o anterior morreu)
            if (current_target_hp is None
                    or (isinstance(current_target_hp, int)
                        and (current_target_hp <= 0 or current_target_hp > _last + 15))):
                self.kills += 1
        self._last_target_hp_seen = current_target_hp

        # Tempo de farm em segundos desde o ultimo Start
        # conta desde o ultimo Start (nao depende da flag running, que pode oscilar)
        if self._farm_start_ts is None:
            farm_time_s = 0
        else:
            farm_time_s = int(__import__("time").time() - self._farm_start_ts)

        # XP ganho na sessao (acumulado; a prova de level-up: ao upar o XP zera)
        _cur_xp = self.pointers.get_xp()
        if _cur_xp is not None:
            if self._last_xp is not None:
                self._xp_gained += (_cur_xp - self._last_xp) if _cur_xp >= self._last_xp else _cur_xp
            self._last_xp = _cur_xp
        # Gold ganho (delta desde o 1o read depois do Start)
        _cur_gold = self.pointers.get_gold()
        if _cur_gold is not None and self._gold_start is None:
            self._gold_start = _cur_gold
        _gold_gained = (_cur_gold - self._gold_start) if (_cur_gold is not None and self._gold_start is not None) else 0

        return dict(
            name=self.name,
            status=self.bot_status.name,
            hp=self.hp,
            mana=self.mana,
            max_hp=self.max_hp,
            max_mana=self.max_mana,
            level=self.level,
            target_name=self.target_name,
            target_hp=current_target_hp,
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
            notification=self.notification,
            confirm=self.pointers.confirm_box(),
            dialog=self.pointers.get_dialog(),
            dc=self.pointers.get_dc(),
            kills=self.kills,
            farm_time_s=farm_time_s,
            energy=self.pointers.get_energy(),
            xp_gained=self._xp_gained,
            gold_gained=_gold_gained,
            drops=dict(self.drops),
            current_action=self.current_action,
        )

    def post_login_setup(self):
        super().post_login_setup()
        self.bot_status = BotStatus.created
        self.load_config()

    def mount(self, _key=0):
        if self.config.sell is not None and self.config.sell.use_mount:
            super().mount(_key)

    def unmount(self, _key=0):
        if self.config.sell is not None and self.config.sell.use_mount:
            super().dismount(_key)

    def load_config(self):
        self.set_config(ConfigLoader(self).load())

    def set_config(self, config: Config):
        self.config = config

    def record_drop(self, name: str, count: int = 1) -> None:
        """Acumula a contagem de drops detectados (usado pelo DropWatch)."""
        self.drops[name] = self.drops.get(name, 0) + count

    def set_action(self, text: str) -> None:
        """Define a acao atual do bot (mostrada grifada no Dashboard)."""
        self.current_action = text

    @property
    def bot_status_string(self) -> str:
        return str(self.bot_status.name)

    @property
    def disconnected(self) -> bool:
        if super().disconnected:
            self.bot_status = BotStatus.disconnected
            return True
        return False

    @property
    def hp_percent(self) -> float:
        return self.hp / self.max_hp

    @property
    def mana_percent(self) -> float:
        return self.mana / self.max_mana

    def start_bot(self):
        import time as _time
        self.logger.info(f'{self.name}: Starting...')
        if self.disconnected:
            self.bot_status = BotStatus.disconnected
            self.logger.info(f'{self.name}: Client disconnected.')
        self.bot_status = BotStatus.starting
        self.running = True
        self.load_config()
        # Reset stats da sessao
        self.kills = 0
        self._farm_start_ts = _time.time()
        self._last_target_hp_seen = None
        self._xp_gained = 0
        self._last_xp = None
        self._gold_start = None
        self.drops = {}
        self.current_action = "iniciando..."
        self.sell_requested = False

    def stop_bot(self):
        self.logger.info(f'{self.name}: Stopping...')
        self.bot_status = BotStatus.stopping
        self.running = False
        self.current_action = "parado"

    def move_to_pos(self, target_pos):
        """
        moves to `target_pos`, will invoke map based pathing if distance is too far.
        :param target_pos: `tuple(x, y)` coordinates to move too
        """
        if not self.running:   # Stop = emergencia: nao inicia movimento
            return
        while linear_distance(self.location, target_pos) > 50 and self.running:
            self.logger.debug(f"{self.name} moving via map")
            return self._move_to_pos_via_map(target_pos)

        pos_diff = position_difference(self.location, target_pos)

        pos_diff_mm_pix = tuple(map(mul, pos_diff, (-1.7, 1.7)))  # corrected to represent 1 pixel per meter

        minimap_relative_pos = scale_minimap_move_distance(pos_diff_mm_pix)
        minimap_pos: tuple[float, float] = tuple(map(math.ceil, map(add, UI_locations.minimap_centre, minimap_relative_pos)))  # mouse position

        self.logger.debug(f'{self.name}: clicking {minimap_relative_pos}')  # relative to minimap center
        self.right_click(minimap_pos)
        self.block_while_moving()

    def move_to_pos_minimap(self, target_pos):
        """Da UM passo em direcao ao alvo pelo minimapa (relativo ao char -> confiavel),
        SEM o mapa-calculado antigo. CRITICO: o clique fica DENTRO do minimapa (70% do
        alcance), NUNCA na borda -- clicar na borda do minimapa vira auto-walk continuo
        (o char anda naquela direcao sem parar). Assim o char vai num PONTO e PARA.
        Espera o passo terminar com TIMEOUT (nunca trava se ficar andando). O chamador
        repete num loop pra cobrir distancias maiores."""
        if not self.running:
            return
        pos_diff = position_difference(self.location, target_pos)
        pos_diff_mm_pix = tuple(map(mul, pos_diff, (-1.7, 1.7)))
        capped = scale_minimap_move_distance(pos_diff_mm_pix)
        inside = tuple(int(v * 0.7) for v in capped)  # recua pra DENTRO do minimapa -> char PARA
        minimap_pos = tuple(map(math.ceil, map(add, UI_locations.minimap_centre, inside)))
        self.right_click(minimap_pos)
        # espera o passo terminar, COM timeout -- nunca trava/anda infinito
        t0 = time.time()
        while self.running and time.time() - t0 < 5:
            _loc = self.location
            time.sleep(1)
            if linear_distance(self.location, _loc) < 1:  # parou de andar
                break

    def _move_to_pos_via_map(self, target_pos: tuple[int, int]):
        if not self.running:   # Stop = emergencia
            return False
        zone = location_to_zone_map[self.location_name.strip()]
        screen_coords = coords_to_map_screen_pos(
            zones[zone],
            target_pos
        )
        # Open the map, and try a list of position offsets, starting at the exact point we want to go to
        # this avoids movement being blocked when team members are already where we want to be
        offsets = ((0, 0), (20, 0), (-20, 0), (20, 20), (-20, 20), (-20, -20), (0, -20), (-20, 20), (0, 20))
        with self.map():
            time.sleep(1)
            _loc = self.location
            self.right_click(tuple(map(add, screen_coords, (-30, -30)))) # Click away from tgt to clear possible existing tgt
            for offset in offsets:
                if not self.running:   # Stop no meio do pathing -> aborta (o 'with' fecha o mapa)
                    return False
                path_tgt = tuple(map(add, screen_coords, offset))
                self.right_click(path_tgt)
                time.sleep(2)
                if linear_distance(_loc, self.location) > 1:
                    # If we've started moving, we can stop trying offsets
                    break
            else:
                self.logger.info(f'{self.name}: failed pathing via map')
                return False

        self.block_while_moving(path_tgt)
        if target_pos != path_tgt:
            # If we moved to a non-zero offset location, we will need to use the minimap to move to the right spot
            # we're close enough now that it'll work.
            self.move_to_pos(target_pos)
            self.block_while_moving()
        return True

    def block_while_moving(self, destination=None):
        while self.running:
            _location = self.location
            time.sleep(1)
            if destination is not None:
                if linear_distance(destination, self.location) < 40:  # if we're close enough, no point overshooting.
                    self.logger.debug("block_while_moving: unblocking due to proximity")
                    break
            if linear_distance(self.location, _location) < 1:
                self.logger.debug("block_while_moving: unblocking due to no movement")
                break


class BotController(ABC):

    _pymem_process = PymemProcess
    login_config = None

    def __init__(self, host=None, port = None, close_disconnected_clients: bool = True):
        self.server = GhostbotIPCServer(bot_controller=self, host=host, port=port)
        self._ipc_log_handler = IPCServerLogHandler(self.server)
        self._close_disconnected_clients = close_disconnected_clients
        self.logger = _logger.getChild(self.__class__.__name__)
        self._running = False
        self._controller_start_time = time.time()
        self.clients: dict[str, BotClientWindow] = dict()
        self._pending_clients: dict[str, BotClientWindow] = dict()
        self.login_queue: dict[int, BotClientWindow] = dict()
        self.requested_logins: list[str] = []
        self._seen_clients = []
        self.logger.addHandler(self._ipc_log_handler)

        GhostBotServerConfigLoader().load()
        self._load_login_config()
        self._cached_eligible_logins: dict[str, LoginDetailsConfigLoader.CharDetails] = {}

    @property
    def running(self):
        return self._running

    @property
    def _total_running_secs(self):
        return int(time.time() - self._controller_start_time)

    def _load_login_config(self):
        self.login_config = LoginDetailsConfigLoader().load()

    def _eligible_logins(self):
        def _eligible_login_generator():
            logged_in_clients = self.client_keys + list(self._pending_clients.keys())
            for k, v in self.login_config.items():
                if k not in logged_in_clients:
                    if (k in self.requested_logins) or v.enabled:
                        yield k, v
        with lock:
            return {k: v for k, v in _eligible_login_generator()}

    def _scan_for_clients(self):
        current_running_procs = self._pymem_process.list_clients()

        def remove_closed_clients():
            with lock:
                for k, v in list(self.clients.items()):
                    if (c_pid := v.proc.process_id) not in (p.process_id for p in current_running_procs):
                        self.logger.info("removing [%s]", c_pid)
                        try:
                            self.stop_bot(self.remove_client(v, close=self._close_disconnected_clients))
                        except Exception as e:
                            self.logger.exception(e)

        current_client_proc_ids = {c.proc.process_id for c in self.clients.values()}
        running_ids = [p.process_id for p in current_running_procs]

        # So pula o scan se NADA mudou E todos os processos rodando ja viraram
        # clients na lista. Se um client existe mas ainda nao foi promovido (ex:
        # abriu antes de logar -> name=None), segue escaneando ate ele logar --
        # senao ele some da lista ate o bot ser reiniciado.
        all_registered = all(pid in current_client_proc_ids for pid in running_ids)
        if running_ids == self._seen_clients and all_registered:
            self.logger.debug('No change in running processes')
            return

        self._seen_clients = running_ids

        remove_closed_clients()

        for proc in current_running_procs:
            if proc.process_id in current_client_proc_ids:
                self.logger.debug("Process [%s] already registered with BotController, skipping.", proc.process_id)
                continue
            client = BotClientWindow(proc)
            try:
                if client.name is None and client.get_window_name() not in self._pending_clients.keys():
                    self.logger.debug("[%s] client.name is None, possibly hasnt logged in yet", proc.process_id)
                    if proc.process_id not in self.login_queue.keys():
                        self.logger.info("[%s] adding process to login_queue routine", proc.process_id)
                        self.login_queue[proc.process_id] = client
                    continue
                if 0 > client.level >= 89:
                    self.logger.info("[%s] client.level(%s) < 0 or > 89.", proc.process_id, client.level)
                    continue

                if client.disconnected:
                    self.logger.info(
                        'Detected disconnected client window for char [%s], attempting to restart',
                        client.name
                    )
                    self.remove_client(client, close=self._close_disconnected_clients)
                    time.sleep(0.5)
                else:
                    if client.name not in self.client_keys:
                        self.logger.info('adding client %s %s', client.name, client.disconnected)
                        self.add_client(BotClientWindow(proc))
                    else:
                        self.logger.debug('client %s already exists, skipping', client.identifier)

            except (TypeError, AttributeError):
                # TODO: do i want to track this for the autologin? might be an alright hook
                #       especially if we know which char to log...
                self.logger.info('cannot add client %s', proc)

    @property
    def client_keys(self) -> list[str]:
        return list(str(k) for k in self.clients.keys())

    def add_client(self, client: BotClientWindow) -> BotClientWindow:
        with lock:
            self.clients[client.name] = client
            self.server.send_to_all(self.server.bot_controller_clients_message)
            return client

    def remove_client(self, client: BotClientWindow, close=True) -> BotClientWindow:
        try:
            self.clients.pop(client.name)
            self.server.send_to_all(self.server.bot_controller_clients_message)
        except KeyError:
            self.logger.info(
                'client window for char %s not in registered clients list, this is normal if this is a '
                'fresh restart of the bot controller', client.identifier)
        if close:
            self.logger.info(
                'client window for char %s will be closed', client.identifier
            )
            client.close_window()
        return client

    @abstractmethod
    def start_bot(self, client: BotClientWindow | str) -> None: ...

    def reload_bot_config(self, client: str | BotClientWindow) -> None:
        if isinstance(client, str):
            if (client := self.get_client(client)) is None:
                self.logger.warning('no client %s', client)
                return
        client.load_config()

    def get_client(self, name) -> BotClientWindow | None:
        client = self.clients.get(name)
        if client is None:
            self.logger.warning('no client %s', client)
        return client

    def trigger_sell_now(self, client_name: str) -> bool:
        """Dispara a rotina de Sell uma vez, fora do ciclo agendado.

        Usado pelo botao 'Vender agora' da UI. Bypassa o intervalo configurado e o
        check de should_run. Roda em thread daemon pra nao bloquear o server.
        """
        client = self.get_client(client_name)
        if client is None:
            self.logger.warning('trigger_sell_now: client %s nao encontrado', client_name)
            return False
        if client.config is None or client.config.sell is None:
            self.logger.warning('trigger_sell_now: %s nao tem config de sell', client_name)
            return False

        _task_name = f"sell_now_{client.name}"

        def _go():
            _prev_status = client.bot_status
            _prev_running = client.running
            try:
                self.logger.info("%s: trigger_sell_now firing", client.name)
                # Status precisa estar running pra Runner.run() permitir, e bypass do
                # check de intervalo chamando _run direto.
                client.bot_status = BotStatus.running
                client.running = True
                try:
                    Sell(client)._run()
                finally:
                    # Se o Stop (emergencia) foi apertado durante a venda, client.running
                    # ja foi pra False -> NAO ressuscitar; fica parado.
                    if not client.running:
                        client.bot_status = BotStatus.stopped
                        self.logger.info("%s: trigger_sell_now interrompido pelo Stop", client.name)
                    else:
                        client.running = _prev_running
                        client.bot_status = _prev_status
                        self.logger.info("%s: trigger_sell_now done", client.name)
            except Exception as e:
                self.logger.exception(e)
            finally:
                _tasks = getattr(self, '_tasks', None)
                if _tasks is not None:
                    _tasks.pop(_task_name, None)

        # registra a thread (em vez de soltar daemon) pra o Stop conseguir esperar/parar
        if hasattr(self, '_add_task'):
            self._add_task(_go, _task_name)
        else:
            threading.Thread(target=_go, daemon=True).start()
        return True

    def _get_functions_for_client(self, client: BotClientWindow) -> Generator[Runner, None, None]:
        # Delete REMOVIDO do app (risco de apagar item sem querer). Nao roda mais.
        if client.config.sell is not None:
            yield Sell(client)
        if client.config.pet is not None:
            yield Petfood(client)
        if client.config.attack is not None:
            yield Attack(client)
        if client.config.fairy is not None:
            yield Fairy(self, client)
        if client.config.boss is not None:
            yield Boss(client)
        # DropWatch (OCR de drop) e DeathAlert NAO ficam aqui no loop sequencial -- rodam
        # numa THREAD paralela (ver ThreadedBotController._run_monitor), pra nao serem
        # atrasados pelo combate (era a causa do "as vezes detecta, as vezes nao").

    @abstractmethod
    def stop_all_bots(self, timeout=30) -> None: ...

    @abstractmethod
    def stop_bot(self, client: str | BotClientWindow, timeout=5) -> None: ...

    @abstractmethod
    def listen(self, host=None, port=None): ...

    def shutdown(self):
        self._running = False
        self.stop_all_bots(5)
