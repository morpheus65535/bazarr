# coding=utf-8
# fmt: off


def parse_language_token(language):
    if not isinstance(language, str):
        return None

    parts = [part.strip().lower() for part in language.split(":")]
    base_language = parts[0]
    if not base_language:
        return None

    flags = {part for part in parts[1:] if part}
    allowed_flags = {"hi", "forced"}
    if flags - allowed_flags:
        return None

    hi = "hi" in flags
    forced = "forced" in flags

    canonical_parts = [base_language]
    if forced:
        canonical_parts.append("forced")
    if hi:
        canonical_parts.append("hi")
    canonical = ":".join(canonical_parts)

    return canonical, (base_language, str(hi), str(forced))
