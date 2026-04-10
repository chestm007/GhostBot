import asyncio
import os

import pytest

from mocks.mock_client import client
from GhostBot.controller.login_controller import LoginController, LoginLock


class TestLoginController:

    def teardown_method(self):
        # assure the lock is always released when a new test runs
        LoginController._login_lock.release()

    def setup_class(self):
        self.login_lock_default_frequency = float(LoginLock._poll_frequency)
        LoginLock._poll_frequency = 0.01

    def teardown_class(self):
        LoginLock._poll_frequency = self.login_lock_default_frequency

    @pytest.mark.asyncio
    @pytest.mark.use_fixtures("client")
    async def test_login_lock(self, client):
        lc1 = LoginController(client)

        async with lc1._login_lock:

            assert lc1._login_lock.locked
        assert lc1._login_lock.unlocked

    @pytest.mark.asyncio
    @pytest.mark.use_fixtures("client")
    async def test_login_lock_applies_to_all_instances_of_login_controller(self, client):
        lc1 = LoginController(client)
        lc2 = LoginController(client)

        async with lc1._login_lock:

            assert lc1._login_lock.locked

            with pytest.raises(TimeoutError):
                async with asyncio.timeout(0.1):
                    async with lc2._login_lock:
                        assert False  # This shouldnt be reachable, as the lock should be acquired from lc1
            assert lc2._login_lock.locked
            assert lc1._login_lock.locked
        assert lc1._login_lock.unlocked

    @pytest.mark.asyncio
    @pytest.mark.use_fixtures("client")
    async def test_login_lock_applies_to_instances_of_login_controller_created_after_lock_aquired(self, client):
        lc1 = LoginController(client)

        async with lc1._login_lock:
            assert lc1._login_lock.locked

            lc2 = LoginController(client)
            with pytest.raises(TimeoutError):
                async with asyncio.timeout(0.1):
                    async with lc2._login_lock:
                        assert False  # This shouldnt be reachable, as the lock should be acquired from lc1
            assert lc2._login_lock.locked
            assert lc1._login_lock.locked
        assert lc1._login_lock.unlocked

    @pytest.mark.asyncio
    @pytest.mark.use_fixtures("client")
    async def test_login_lock_applies_to_instances_of_login_controller_created_inside_timeout_context(self, client):
        lc1 = LoginController(client)
        print(lc1._login_lock._poll_frequency)

        async with lc1._login_lock:
            assert lc1._login_lock.locked

            with pytest.raises(TimeoutError):
                async with asyncio.timeout(0.1):
                    lc2 = LoginController(client)
                    async with lc2._login_lock:
                        assert False  # This shouldnt be reachable, as the lock should be acquired from lc1
            assert lc2._login_lock.locked
            assert lc1._login_lock.locked
        assert lc1._login_lock.unlocked

    @pytest.mark.usefixtures('client')
    def test_login_controller_detects_stage_enter_credentials(self, client):
        client._image = os.path.join(client._path_base, "images", 'login_enter_credentials_SS.bmp')
        lc = LoginController(client)
        assert lc.current_stage == LoginController.LoginStage.enter_credentials

    @pytest.mark.usefixtures('client')
    def test_login_controller_detects_stage_server_select(self, client):
        client._image = os.path.join(client._path_base, "images", 'login_server_select_SS.bmp')
        lc = LoginController(client)
        assert lc.current_stage == LoginController.LoginStage.server_select

    @pytest.mark.usefixtures('client')
    def test_login_controller_detects_stage_login_queue(self, client):
        client._image = os.path.join(client._path_base, "images", 'login_queue_SS.bmp')
        lc = LoginController(client)
        assert lc.current_stage == LoginController.LoginStage.login_queue

    @pytest.mark.usefixtures('client')
    def test_login_controller_detects_stage_character_select(self, client):
        client._image = os.path.join(client._path_base, "images", 'login_character_select_SS.bmp')
        client.pointers.get_level = lambda: None
        lc = LoginController(client)
        assert lc.current_stage == LoginController.LoginStage.character_select

    # TODO: test login logic flow. -too hard basket- for now