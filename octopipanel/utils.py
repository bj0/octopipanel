from pathlib import Path


def rpi_version():
    path = Path('/sys/firmware/devicetree/base/model')
    if path.exists():
        version = path.read_text()
        return version if 'Raspberry' in version else None
    return None
