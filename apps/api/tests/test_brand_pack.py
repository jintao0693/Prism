"""Brand Pack 解析烟测。"""

from app.services.brand.pack import DEFAULT_BRAND_PACK, pack_from_dict


def test_pack_from_dict_merges_defaults() -> None:
    pack = pack_from_dict({"name": "星辰发行周", "keywords": ["探索"]})
    assert pack.name == "星辰发行周"
    assert pack.primary_color == DEFAULT_BRAND_PACK["primaryColor"]
    assert pack.keywords == ["探索"]
    assert "霓虹" in "、".join(pack.forbidden)


def test_pack_from_dict_none_uses_defaults() -> None:
    pack = pack_from_dict(None)
    assert pack.name == DEFAULT_BRAND_PACK["name"]
    assert pack.tone_hint