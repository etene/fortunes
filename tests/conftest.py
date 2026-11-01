import pytest
from pathlib import Path

from tests.factories import _author_factory  # noqa: F401
from tests.factories import _fortune_factory  # noqa: F401
from tests.factories import author, fortune  # noqa: F401
from tests.immich_mock import immich_mock, _fake_jpeg_image  # noqa: F401


@pytest.fixture(name="test_data_dir", scope="session")
def _test_data_dir() -> Path:
    datadir = Path(__file__).parent / "data"
    assert datadir.is_dir()
    return datadir
