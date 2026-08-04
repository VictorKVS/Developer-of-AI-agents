from dataclasses import dataclass


@dataclass(frozen=True)
class AnalysisProfile:
    key: str
    title: str
    description: str
    system_prompt: str
    disclaimer: str


ANALYSIS_PROFILES = {
    "career_strategist": AnalysisProfile(
        key="career_strategist",
        title="Карьерный стратег",
        description="Профессиональный разбор навыков, целей, рисков и ближайшего плана развития.",
        system_prompt=(
            "Работай как практический карьерный стратег, менеджер развития и наставник. "
            "Оцени профессиональный опыт, переносимые навыки, цели, ограничения, сильные стороны, "
            "риски распыления и реалистичные следующие шаги. Рекомендации должны быть конкретными, "
            "проверяемыми и привязанными к информации из диалога. Не обещай гарантированный успех."
        ),
        disclaimer="Карьерные выводы основаны только на информации из диалога и не гарантируют трудоустройство или коммерческий результат.",
    ),
    "jungian_reflection": AnalysisProfile(
        key="jungian_reflection",
        title="Юнгианская рефлексия",
        description="Мягкий разбор мотивов, повторяющихся образов и возможных архетипических паттернов.",
        system_prompt=(
            "Работай в формате не-клинической юнгианской рефлексии. Отмечай возможные мотивы, "
            "ценности, внутренние противоречия, повторяющиеся образы и архетипические темы "
            "(например, Исследователь, Создатель, Наставник), но представляй их только как гипотезы. "
            "Не ставь диагнозов, не заявляй о скрытых травмах и не выдавай интерпретацию за научно "
            "подтверждённый психологический тест. Заверши практическими вопросами для самоанализа."
        ),
        disclaimer="Это не психологическая диагностика и не медицинская консультация. Архетипические интерпретации являются гипотезами для самоанализа.",
    ),
}

DEFAULT_ANALYSIS_PROFILE = "career_strategist"


def get_analysis_profile(key: str | None) -> AnalysisProfile:
    normalized = (key or DEFAULT_ANALYSIS_PROFILE).strip().lower()
    try:
        return ANALYSIS_PROFILES[normalized]
    except KeyError as exc:
        allowed = ", ".join(ANALYSIS_PROFILES)
        raise ValueError(f"Неизвестный профиль анализа. Допустимые значения: {allowed}.") from exc
