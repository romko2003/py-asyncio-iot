import asyncio
import time

from app.iot.devices import Light as HueLightDevice, Speaker as SmartSpeakerDevice, SmartToilet as SmartToiletDevice
from app.iot.service import IoTService
from app.iot.message import Message, MessageType
from app.iot.utils import run_parallel, run_sequence


async def async_main() -> None:
    service = IoTService()

    # --- реєструємо девайси (паралельно) ---
    # якщо register_device вже async і повертає id — збираємо їх через gather
    hue_light = HueLightDevice()
    speaker = SmartSpeakerDevice()
    toilet = SmartToiletDevice()

    hue_light_id, speaker_id, toilet_id = await asyncio.gather(
        service.register_device(hue_light),
        service.register_device(speaker),
        service.register_device(toilet),
    )

    # === WAKE-UP PROGRAM ===
    # 1) Паралельно: вмикаємо світло і колонку
    await run_parallel(
        service.send_message(Message(hue_light_id, MessageType.SWITCH_ON)),
        service.send_message(Message(speaker_id, MessageType.SWITCH_ON)),
    )
    # 2) Після увімкнення колонки — ПОСЛІДОВНО запускаємо музику
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
    # 3) Паралельно: гасимо світло, а для туалету робимо ПОСЛІДОВНО flush -> clean,
    #    і (за потреби) вимикаємо колонку після зупинки/музики.
    await run_parallel(
        service.send_message(Message(hue_light_id, MessageType.SWITCH_OFF)),
        run_sequence(
            service.send_message(Message(toilet_id, MessageType.FLUSH)),
            service.send_message(Message(toilet_id, MessageType.CLEAN)),
        ),
        # якщо у тебе є окремий MessageType.STOP_SONG — додай його перед SWITCH_OFF
        service.send_message(Message(speaker_id, MessageType.SWITCH_OFF)),
    )


def main() -> None:
    start = time.perf_counter()
    asyncio.run(async_main())
    end = time.perf_counter()
    print("Elapsed:", end - start)


if __name__ == "__main__":
    main()
