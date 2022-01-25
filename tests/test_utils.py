import unittest

from stove.utils import (
    import_all_modules_from_name,
    import_all_modules_from_path,
    is_pkg_name,
    is_pkg_path,
    reload_all_modules_from_name,
    reload_all_modules_from_path,
    search_modules_from_name,
    search_modules_from_path,
    search_pkgs_under,
)


class TestUtils(unittest.TestCase):

    def test_search_modules_from_name(self) -> None:
        search_modules_from_name("stove")

    def test_search_modules_from_path(self) -> None:
        search_modules_from_path("./stove")

    def test_import_all_modules_from_name(self) -> None:
        import_all_modules_from_name("stove")

    def test_import_all_modules_from_path(self) -> None:
        import_all_modules_from_path("./stove")

    def test_reload_all_modules_from_name(self) -> None:
        reload_all_modules_from_name("stove")

    def test_reload_all_modules_from_path(self) -> None:
        reload_all_modules_from_path("./stove")

    def test_is_pkg_name(self) -> None:
        self.assertTrue(is_pkg_name("stove"))

    def test_is_pkg_path(self) -> None:
        self.assertTrue(is_pkg_path("./stove"))

    def test_search_pkgs_under(self) -> None:
        search_pkgs_under(".")


if __name__ == "__main__":
    unittest.main()
