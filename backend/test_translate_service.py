from services.translate_service import translate_title_with_rules


def test_title_rule_translation_keeps_core_product_terms() -> None:
    title = (
        "[6\uc6d4\uc62c\ud53d/\ubbf8\ub2c8\ube0c\uc99d\uc815\uae30\ud68d] "
        "3CE \ubb34\ub4dc\ub808\uc2dc\ud53c \ud398\uc774\uc2a4 \ube14\ub7ec\uc26c "
        "\ub2e8\ud488/\uae30\ud68d"
    )

    translated = translate_title_with_rules(title)

    assert "Olive Young Pick" in translated
    assert "\u8ff7\u4f60\u5237\u8d60\u54c1\u4f01\u5212" in translated
    assert "\u9762\u90e8\u816e\u7ea2" in translated
    assert "\u5355\u54c1" in translated


def test_title_rule_translation_does_not_collapse_unknown_korean_to_punctuation() -> None:
    title = (
        "[\ud488\uc808\ub300\ub780/\ub2e8\uc885\ud15c\ubd80\ud65c] "
        "\ub124\uc774\ubc0d \ud50c\ub7ec\ud53c \ud30c\uc6b0\ub354 \ube14\ub7ec\uc26c"
    )

    translated = translate_title_with_rules(title)

    assert translated not in {"", "[]", "[/]", "/"}
    assert "\u65ad\u8d27\u70ed\u5356" in translated
    assert "\u505c\u4ea7\u6b3e\u56de\u5f52" in translated
    assert "\u7c89\u8d28\u816e\u7ea2" in translated


def test_title_rule_translation_covers_screenshot_titles() -> None:
    titles = [
        (
            "\ub118\ubc84\uc988\uc778 1\ubc88 \ud310\ud1a0\ud150\uc0b0 "
            "\uc2a4\ud0a8\ucf00\uc5b4100 \uae00\ub7ec\uc26c \uae30\ud68d\uc138\ud2b8 "
            "(+\ud53c\ud504 1\uac1c)"
        ),
        (
            "[2025\uc5b4\uc6cc\uc9881\uc704] \uc5d0\uc2a4\ud2b8\ub77c "
            "\uc544\ud1a0\ubca0\ub9ac\uc5b4365 \ud06c\ub9bc 80ml "
            "\uae30\ud68d\uc138\ud2b8 (+\ud558\uc774\ub4dc\ub85c "
            "\uc5d0\uc13c\uc2a425ml+\uc575\ud50c7ml)"
        ),
        (
            "[6\uc6d4 \uc62c\uc601\ud53d/\ud55c\uc815\uae30\ud68d\uc138\ud2b8] "
            "Anua \ud53c\ub514\uc54c\uc5d4 \ud788\uc54c\ub8e8\ub860\uc0b0 "
            "\ucea1\uc290 100 \uc138\ub7fc 30ml \ub354\ube14\uae30\ud68d\uc138\ud2b8 "
            "(+\ud53c\ub514\uc54c\uc5d4 \ub9c8\uc2a4\ud06c 1\ub9e4)"
        ),
    ]

    translated = [translate_title_with_rules(title) for title in titles]

    assert "numbuzin" in translated[0]
    assert "\u6cdb\u9187" in translated[0]
    assert "\u62a4\u80a4" in translated[0]
    assert "\u4f01\u5212\u5957\u88c5" in translated[0]
    assert "AESTURA" in translated[1]
    assert "Atobarrier365" in translated[1]
    assert "\u971c 80ml" in translated[1]
    assert "\u7cbe\u534e25ml+\u5b89\u74f67ml" in translated[1]
    assert "Anua" in translated[2]
    assert "PDRN" in translated[2]
    assert "\u900f\u660e\u8d28\u9178" in translated[2]
    assert "\u80f6\u56ca 100 \u7cbe\u534e 30ml" in translated[2]
    assert "\u9762\u819c 1\u7247" in translated[2]
