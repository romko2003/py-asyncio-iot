import asyncio
import time

from app.iot.devices import HueLightDevice, SmartSpeakerDevice, SmartToiletDevice
from app.iot.message import Message, MessageType
from app.iot.service import IoTService
from app.iot.utils import run_parallel, run_sequence


async def async_main() -> None:
    service = IoTService()

    # створюємо девайси з ІМЕНАМИ (варіант В)
    hue_light = HueLightDevice("HueLight")
    speaker = SmartSpeakerDevice("SmartSpeaker")
    toilet = SmartToiletDevice("SmartToilet")

    # реєструємо девайси ПАРАЛЕЛЬНО
    hue_light_id, speaker_id, toilet_id = await asyncio.gather(
        service.register_device(hue_light),
        service.register_device(speaker),
        service.register_device(toilet),
    )

    # === WAKE-UP PROGRAM ===
    # паралельно: увімкнути світло і колонку
    await run_parallel(
        service.send_message(Message(hue_light_id, MessageType.SWITCH_ON)),
        service.send_message(Message(speaker_id, MessageType.SWITCH_ON)),
    )
    # потім — програти трек (послідовно після вмикання)
    await run_sequence(
        service.send_message(
            Message(
                speaker_id,
                MessageType.PLAY_SONG,
                "Rick Astley - Never Gonna Give You Up",
            )
        )
    )

    # === SLEEP PROGRAM ===
    # паралельно: вимкнути світло; для туалету — послідовно flush -> clean;
    # колонку — вимкнути (за наявності STOP_SONG додай його перед SWITCH_OFF)
    await run_parallel(
        service.send_message(Message(hue_light_id, MessageType.SWITCH_OFF)),
        run_sequence(
            service.send_message(Message(toilet_id, MessageType.FLUSH)),
            service.send_message(Message(toilet_id, MessageType.CLEAN)),
        ),
        service.send_message(Message(speaker_id, MessageType.SWITCH_OFF)),
    )


def main() -> None:
    start = time.perf_counter()
    asyncio.run(async_main())
    end = time.perf_counter()
    print("Elapsed:", end - start)


if __name__ == "__main__":
    main()
