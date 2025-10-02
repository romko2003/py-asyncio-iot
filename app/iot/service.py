import asyncio
from typing import Iterable

from .utils import run_parallel, run_sequence
from .devices import BaseDevice


class IoTService:
    def __init__(self) -> None:
        self._devices: dict[str, BaseDevice] = {}

    async def register_devices(self, devices: Iterable[BaseDevice]) -> None:
        """Реєстрація (конект) девайсів — ПАРАЛЕЛЬНО (швидко)."""
        for d in devices:
            self._devices[d.name] = d

        await asyncio.gather(*(d.connect() for d in devices))
        print("[Service] all devices registered")

    async def send_message(self, device_name: str, command: str, payload=None) -> None:
        """Маршрутизуємо команди на потрібний девайс (async)."""
        device = self._devices[device_name]
        await device.handle(command, payload)

    async def disconnect_all(self) -> None:
        await asyncio.gather(*(d.disconnect() for d in self._devices.values()))
        print("[Service] all devices disconnected")

    async def run(self) -> None:
        """Тут ми конструюємо wake_up та sleep програми
        БЕЗ окремих змінних-наборів, а через поєднання run_sequence/parallel.
        """
        print("[Service] === WAKE UP PROGRAM ===")

        # 1) Паралельно: вмикаємо світло, вмикаємо спікер, ставимо каву
        await run_parallel(
            self.send_message("Light", "on"),
            self.send_message("Speaker", "power_on"),
            self.send_message("CoffeeMaker", "brew"),
        )

        # 2) ПОСЛІДОВНО для SmartToilet: flush -> clean
        await run_sequence(
            self.send_message("SmartToilet", "flush"),
            self.send_message("SmartToilet", "clean"),
        )

        # 3) ПОСЛІДОВНО для музики: Після power_on — play
        await run_sequence(
            self.send_message("Speaker", "play", payload="morning_lofi.mp3"),
        )

        print("[Service] === SLEEP PROGRAM ===")

        # 4) ПОСЛІДОВНІ та ПАРАЛЕЛЬНІ кроки відпочинку.
        #    - спочатку зупиняємо музику, тільки потім вимикаємо спікер (послідовно)
        #    - паралельно: гасимо світло
        await run_parallel(
            run_sequence(
                self.send_message("Speaker", "stop"),
                self.send_message("Speaker", "power_off"),
            ),
            self.send_message("Light", "off"),
        )

        # 5) Для прикладу: нічний цикл туалету (нічого критичного, просто показ)
        await run_sequence(
            self.send_message("SmartToilet", "flush"),
            self.send_message("SmartToilet", "clean"),
        )

        print("[Service] === DONE ===")
