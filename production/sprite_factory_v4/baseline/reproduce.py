"""Re-run the preserved V3 without editing it; output outside this evidence directory."""
import argparse
import importlib.util
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workdir', required=True, help='Writable new directory for the baseline run')
    args = parser.parse_args()
    source = Path(__file__).with_name('LastLight_SpriteFactory_V3_iPhone.py')
    spec = importlib.util.spec_from_file_location('last_light_preserved_v3', source)
    factory = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(factory)
    factory.CUSTOM_WORK_FOLDER = str(Path(args.workdir).expanduser().resolve())
    factory.DEMO_MODE = True
    factory.MAX_ITEMS = 24
    factory.main()


if __name__ == '__main__':
    main()
