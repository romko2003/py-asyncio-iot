import asyncio
from typing import Iterable, Any
from app.iot.devices import BaseDevice, Light, Speaker, SmartToilet, CoffeeMaker
from app.iot.message import MessageType


class IoTService:
    def __init__(self) -> None:
        self._devices: dict[str, BaseDevice] = {}

    async def register_device(self, device: BaseDevice) -> str:
        await device.connect()
        device_id = device.name
        self._devices[device_id] = device
        return device_id

    async def register_devices(self, devices: Iterable[BaseDevice]) -> list[str]:
        await asyncio.gather(*(d.connect() for d in devices))
        ids: list[str] = []
        for d in devices:
            device_id = d.name
            self._devices[device_id] = d
            ids.append(device_id)
        return ids

    # ------------------ ОНОВЛЕНО: гнучкий парсер Message ------------------
    async def send_message(self, message: Any) -> None:
        """
        Підтримує різні назви полів у Message:
          - device_id / device / id
          - type / message_type / msg_type
          - payload / data / value
        Приймає type як Enum (MessageType) або як рядок ("SWITCH_ON"/"flush"/тощо).
        """
        device_id = (
            getattr(message, "device_id", None)
            or getattr(message, "device", None)
            or getattr(message, "id", None)
        )
        msg_type = (
            getattr(message, "type", None)
            or getattr(message, "message_type", None)
            or getattr(message, "msg_type", None)
        )
        payload = (
            getattr(message, "payload", None)
            or getattr(message, "data", None)
            or getattr(message, "value", None)
        )

        if device_id is None:
            raise AttributeError("Message missing device_id/device/id")
        if msg_type is None:
            raise AttributeError("Message missing type/message_type/msg_type")

        device = self._devices[device_id]

        # нормалізуємо тип у РЯДОК команди, з урахуванням конкретного девайсу
        def normalize_type(mt: Any) -> str:
            # якщо Enum -> беремо .name або .value; якщо рядок — лишаємо
            if isinstance(mt, MessageType):
                name = getattr(mt, "name", None)
                return name or str(getattr(mt, "value", mt))
            if hasattr(mt, "name"):
                return str(mt.name)
            if hasattr(mt, "value") and not isinstance(mt, (str, bytes)):
                return str(mt.value)
            return str(mt)

        mt_name = normalize_type(msg_type).upper()

        # МАПА: MessageType/рядок → конкретні команди, які чекають пристрої
        if isinstance(device, Light):
            if mt_name in ("SWITCH_ON", "ON"):
                cmd, pl = "on", None
            elif mt_name in ("SWITCH_OFF", "OFF"):
                cmd, pl = "off", None
            else:
                cmd, pl = mt_name.lower(), payload

        elif isinstance(device, Speaker):
            if mt_name in ("SWITCH_ON", "POWER_ON"):
                cmd, pl = "power_on", None
            elif mt_name in ("SWITCH_OFF", "POWER_OFF"):
                cmd, pl = "power_off", None
            elif mt_name in ("PLAY_SONG", "PLAY"):
                cmd, pl = "play", payload
            elif mt_name in ("STOP_SONG", "STOP"):
                cmd, pl = "stop", None
            else:
                cmd, pl = mt_name.lower(), payload

        elif isinstance(device, SmartToilet):
            if mt_name in ("FLUSH",):
                cmd, pl = "flush", None
            elif mt_name in ("CLEAN",):
                cmd, pl = "clean", None
            else:
                cmd, pl = mt_name.lower(), payload

        elif isinstance(device, CoffeeMaker):
            if mt_name in ("BREW", "MAKE_COFFEE"):
                cmd, pl = "brew", None
            else:
                cmd, pl = mt_name.lower(), payload

        else:
            cmd, pl = mt_name.lower(), payload

        await device.handle(cmd, pl)

    async def disconnect_all(self) -> None:
        await asyncio.gather(*(d.disconnect() for d in self._devices.values()))
