"""RU↔EN словарь моды — мост между русским каталогом и англоязычным движком.

Движок из репозитория ``karalik19-a11y/-`` написан вокруг английских
атрибутов («sheer», «oversized», «deconstructed»). Каталог asStylist и запросы
пользователей — на русском. Этот модуль переводит русские названия вещей,
стили, настроения и свободные текстовые запросы в словарь движка.

Ключи таблиц записаны в виде основ; для токенов применяется лёгкий стеммер
(``stem_ru``), поэтому «шерстяное», «шерстяной» и «шерсть» попадают в одну
запись «шерст».
"""

from __future__ import annotations

import re

__all__ = [
    "APP_SLOT_HINTS",
    "CATEGORY_PRIORITY",
    "EN_TO_RU",
    "RU_AESTHETIC_TERMS",
    "RU_COLORS",
    "RU_GARMENTS",
    "RU_MATERIALS",
    "RU_SILHOUETTES",
    "RU_STOPWORDS",
    "aesthetic_label_ru",
    "detect_colors",
    "detect_terms",
    "engine_category",
    "material_label_ru",
    "matches_token",
    "normalize",
    "role_label_ru",
    "silhouette_label_ru",
    "stem_ru",
    "taste_label_ru",
    "tokenize",
    "translate_text",
]

# ─── нормализация и стемминг ────────────────────────────────────────────────

_SUFFIXES: tuple[str, ...] = (
    "еннейш", "ейш",
    "ами", "ями", "ого", "его", "ому", "ему", "ыми", "ими",
    "ая", "яя", "ое", "ее", "ые", "ие", "ой", "ей", "ых", "их",
    "ом", "ем", "ам", "ям", "ый", "ий", "ую", "юю",
    "а", "я", "о", "е", "ы", "и", "ь", "й", "у", "ю",
)

#: Всё, что не буква/цифра (подчёркивание сохраняем как разделитель).
_NON_WORD = re.compile(r"[^\w]+", re.UNICODE)


def normalize(text: str) -> str:
    """Нижний регистр, ``ё→е``, дефисы и знаки препинания → пробел."""
    lowered = (text or "").lower().replace("ё", "е")
    return _NON_WORD.sub(" ", lowered).strip()


def stem_ru(token: str) -> str:
    """Очень грубый стеммер: срезает типовое окончание, оставляя ≥ 3 символа."""
    if len(token) <= 4:
        return token
    for suffix in _SUFFIXES:
        if len(token) - len(suffix) >= 3 and token.endswith(suffix):
            return token[: -len(suffix)]
    return token


def tokenize(text: str) -> list[str]:
    return [stem_ru(part) for part in normalize(text).split() if len(part) > 1]


#: Допустимые «хвосты» при сравнении основы со словом из текста. Без этого
#: правила трёхбуквенные ключи («юбк», «бел», «час») склеивали бы лишнее
#: («часть» → часы), а короткие основы не находились бы вовсе.
_TAILS: tuple[str, ...] = (
    "а", "я", "ы", "и", "е", "у", "ю", "о", "ь", "й",
    "ой", "ей", "ов", "ев", "ам", "ям", "ах", "ях", "ом", "ем",
    "ая", "яя", "ое", "ее", "ые", "ие", "ый", "ий", "ых", "их",
    "ого", "его", "ому", "ему", "ыми", "ими", "ью", "ию",
    "ым", "им", "н", "нного", "тского",
    # словообразовательные «хвосты» прилагательных («шерст+ян+ое»,
    # «готи+ческ+ий», «асимметри+чн+ая») — сравнение идёт по основам
    "ск", "еск", "ческ", "ийск", "овск", "евск", "ич", "ичн",
    "ян", "янн", "енн", "онн", "альн", "ельн", "ив", "лив", "чив",
    "ат", "оват", "чат", "ист", "аст", "нн", "к", "ок", "ек", "ик",
)


def matches_token(token: str, key: str) -> bool:
    """Совпадение основ: точное или ключ + типовое окончание."""
    if not token or not key:
        return False
    if token == key:
        return True
    if token.startswith(key):
        return token[len(key) :] in _TAILS
    if len(token) >= 4 and key.startswith(token):
        return key[len(token) :] in _TAILS
    return False


#: обратная совместимость с внутренними вызовами
_matches = matches_token


# ─── словари ────────────────────────────────────────────────────────────────

#: Русские названия вещей → словарь движка (категории ролей + атрибуты).
RU_GARMENTS: dict[str, str] = {
    "пальт": "coat",
    "тренч": "trench coat",
    "пуховик": "puffer coat",
    "бомбер": "bomber jacket",
    "парк": "parka jacket",
    "куртк": "jacket",
    "косух": "leather biker jacket",
    "жакет": "blazer jacket",
    "пиджак": "blazer jacket",
    "блейзер": "blazer jacket",
    "ветровк": "jacket technical",
    "жилет": "vest",
    "рубашк": "shirt",
    "футболк": "t-shirt top",
    "лонгслив": "long sleeve top",
    "свитшот": "sweatshirt top",
    "худи": "hoodie top",
    "водолазк": "turtleneck top",
    "боди": "bodysuit top",
    "поло": "polo shirt",
    "топ": "top",
    "бюстье": "bustier top",
    "блуз": "blouse top",
    "свитер": "sweater knit",
    "джемпер": "jumper knit",
    "кардиган": "cardigan knit",
    "кофт": "cardigan knit",
    "плать": "dress",
    "сарафан": "dress",
    "юбк": "skirt",
    "брюк": "trousers",
    "джинс": "denim jeans",
    "шорт": "shorts",
    "легинс": "leggings",
    "комбинезон": "jumpsuit",
    "кроссовк": "sneakers shoes",
    "кед": "sneakers shoes",
    "ботинк": "boots",
    "ботильон": "boots",
    "сапог": "boots",
    "лофер": "loafers shoes",
    "мокасин": "loafers shoes",
    "балетк": "ballet flats shoes",
    "сандал": "sandals shoes",
    "туфл": "heels shoes",
    "угг": "boots",
    "сумк": "bag",
    "рюкзак": "backpack bag",
    "шоппер": "tote bag",
    "клатч": "clutch bag",
    "кроссбоди": "crossbody bag",
    "ремен": "belt",
    "поясн": "belt bag",
    "шарф": "scarf",
    "платок": "scarf",
    "шапк": "beanie",
    "кепк": "cap",
    "перчатк": "gloves",
    "очк": "sunglasses",
    "серьг": "earrings",
    "цеп": "chain",
    "час": "watch",
    "носк": "socks",
    "галстук": "tie",
}

#: Материалы и фактуры.
RU_MATERIALS: dict[str, str] = {
    "шерст": "wool heavy",
    "кашемир": "cashmere wool",
    "хлоп": "cotton",
    "хлопчатобумаж": "cotton",
    "шелк": "silk fluid",
    "льнян": "linen",
    "кожан": "leather heavy",
    "кож": "leather",
    "замш": "suede",
    "деним": "denim",
    "джинсов": "denim",
    "трикотаж": "knit",
    "вискоз": "viscose fluid",
    "шифон": "chiffon sheer",
    "органз": "organza sheer",
    "атлас": "satin fluid",
    "креп": "crepe fluid",
    "нейлон": "nylon technical",
    "полиэстер": "polyester technical",
    "мембран": "performance technical",
    "мохер": "mohair textured",
    "велюр": "velvet",
    "бархат": "velvet",
    "мехов": "fur",
    "мех": "fur",
    "флис": "fleece",
    "стеган": "quilted padded textured",
    "вязан": "knitted textured",
    "кружев": "lace",
    "сетк": "mesh sheer",
    "прозрач": "sheer transparent",
    "полупрозрач": "sheer translucent",
    "технолог": "technical",
    "плотн": "heavy",
    "тонк": "light",
    "легк": "light",
    "премиум": "premium",
    "кашемиров": "cashmere",
    "лен": "linen",
}

#: Крой, силуэт, конструкция.
RU_SILHOUETTES: dict[str, str] = {
    "оверсайз": "oversized",
    "объемн": "voluminous oversized",
    "обьемн": "voluminous oversized",
    "широк": "wide leg relaxed",
    "притал": "fitted slim",
    "свободн": "relaxed loose",
    "асимметр": "asymmetric deconstructed",
    "деконстру": "deconstructed",
    "архитектур": "architectural structured",
    "структур": "structured",
    "удлинен": "longline elongated",
    "длин": "longline",
    "коротк": "cropped short",
    "кроп": "cropped",
    "макси": "maxi longline",
    "мини": "mini cropped",
    "миди": "midi",
    "драпиров": "draped",
    "плисс": "pleated",
    "лоскутн": "deconstructed",
    "потерт": "distressed washed",
    "рван": "distressed",
    "двубортн": "double breasted tailored",
    "однобортн": "single breasted tailored",
    "спортивн": "performance technical",
    "классическ": "classic tailored",
    "базов": "basic",
    "строг": "precise minimal",
    "прям": "straight",
    "с прямыми": "straight",
    "облегающ": "fitted bodycon",
    "расклешен": "flared",
    "ярусн": "tiered voluminous",
    "воланами": "ruffled romantic",
    "воланы": "ruffled romantic",
    "челси": "chelsea boots",
    "бегов": "performance running shoes",
}

#: Эстетики, настроения и запросные слова: из них собирается engine-запрос.
RU_AESTHETIC_TERMS: dict[str, str] = {
    "индустриальн": "industrial utilitarian",
    "грязн": "raw distressed",
    "романтичн": "romantic",
    "готич": "gothic dark",
    "темн": "dark",
    "черн": "black",
    "бел": "white",
    "минимал": "minimal",
    "монохром": "monochrome minimal",
    "архивн": "archive",
    "винтаж": "vintage archive",
    "авангард": "avant garde experimental",
    "уличн": "street streetwear",
    "стритвир": "streetwear",
    "спорт": "athleisure sport",
    "делов": "business tailored",
    "офисн": "business work",
    "вечерн": "evening editorial",
    "повседневн": "everyday casual",
    "уютн": "cozy",
    "дерзк": "bold",
    "ярк": "bold bright",
    "прозрачн": "sheer transparent",
    "сетчат": "mesh sheer",
    "экспериментальн": "experimental avant garde",
    "текстильн": "textile",
    "клетчат": "check plaid",
    "цветочн": "floral",
    "полосат": "striped",
    "ансамбл": "",
    "образ": "",
    "стиль": "",
    "лук": "",
    "вещ": "",
    "хочу": "",
    "нужен": "",
    "подбер": "",
    "собер": "",
    "найти": "",
    "ищу": "",
    "пожалуйста": "",
}

#: Русские цвета → словарь движка (см. ``FashionIntelligence._extractColor``).
RU_COLORS: dict[str, str] = {
    "черн": "black",
    "бел": "white",
    "сер": "grey",
    "графит": "grey",
    "айвори": "ivory",
    "беж": "beige",
    "песочн": "beige",
    "кэмел": "beige",
    "камел": "beige",
    "коричн": "brown",
    "шоколад": "brown",
    "бордо": "burgundy",
    "бургунд": "burgundy",
    "красн": "red",
    "розов": "pink",
    "пудров": "pink",
    "лаванд": "purple",
    "фиолет": "purple",
    "син": "blue",
    "голуб": "blue",
    "тил": "green",
    "изумруд": "green",
    "зелен": "green",
    "олив": "olive",
    "хаки": "olive",
    "горчичн": "gold",
    "желт": "gold",
    "оранж": "red",
    "серебр": "silver",
    "золот": "gold",
    "терракот": "brown",
    "коралл": "red",
}

RU_STOPWORDS: frozenset[str] = frozenset(
    {
        "и", "в", "на", "с", "со", "для", "под", "из", "от", "до", "по", "к", "ко",
        "мне", "мой", "моя", "мои", "это", "как", "что", "чтобы", "очень", "можно",
        "the", "and", "with", "for", "look", "outfit", "style", "fashion",
    }
)

#: Английские термины движка → русские подписи (для объяснений и UI).
EN_TO_RU: dict[str, str] = {
    "oversized": "оверсайз",
    "voluminous": "объёмный",
    "structured": "структурный",
    "architectural": "архитектурный",
    "deconstructed": "деконструированный",
    "asymmetric": "асимметричный",
    "elongated": "вытянутый",
    "longline": "удлинённый",
    "cropped": "укороченный",
    "fitted": "приталенный",
    "slim": "узкий",
    "relaxed": "свободный",
    "regular": "прямой",
    "sheer": "полупрозрачный",
    "mesh": "сетчатый",
    "translucent": "просвечивающий",
    "transparent": "прозрачный",
    "heavy": "плотный",
    "fluid": "текучий",
    "technical": "технологичный",
    "textured": "фактурный",
    "quilted": "стёганый",
    "knitted": "вязаный",
    "leather": "кожа",
    "wool": "шерсть",
    "cashmere": "кашемир",
    "silk": "шёлк",
    "linen": "лён",
    "cotton": "хлопок",
    "denim": "деним",
    "nylon": "нейлон",
    "velvet": "бархат",
    "suede": "замша",
    "fur": "мех",
    "industrial": "индустриальный",
    "romantic": "романтичный",
    "gothic": "готический",
    "minimal": "минимализм",
    "archive": "архив",
    "avantgarde": "авангард",
    "avant garde": "авангард",
    "editorial": "эдиториал",
    "street": "стрит",
    "streetwear": "стритвир",
    "utilitarian": "утилитарный",
    "workwear": "рабочий стиль",
    "military": "милитари",
    "quiet luxury": "тихая роскошь",
    "distressed": "потёртый",
    "raw": "raw-крой",
    "black": "чёрный",
    "white": "белый",
    "grey": "серый",
    "navy": "тёмно-синий",
    "beige": "бежевый",
    "brown": "коричневый",
    "olive": "оливковый",
    "burgundy": "бордовый",
    "green": "зелёный",
    "red": "красный",
    "blue": "синий",
    "pink": "розовый",
    "purple": "фиолетовый",
    "gold": "золото",
    "silver": "серебро",
}

#: Порядок разрешения категории по названию: берём первое совпадение.
CATEGORY_PRIORITY: tuple[str, ...] = (
    "coat",
    "jacket",
    "blazer",
    "dress",
    "jumpsuit",
    "skirt",
    "trousers",
    "jeans",
    "boots",
    "sneakers",
    "shoes",
    "bag",
    "cardigan",
    "knit",
    "sweater",
    "shirt",
    "blouse",
    "top",
    "vest",
    "accessory",
)

#: Какая категория движка в какой слот приложения попадает.
APP_SLOT_HINTS: dict[str, str] = {
    "coat": "outerwear",
    "jacket": "outerwear",
    "blazer": "outerwear",
    "trench": "outerwear",
    "top": "top",
    "shirt": "top",
    "blouse": "top",
    "knit": "top",
    "sweater": "top",
    "cardigan": "top",
    "trousers": "bottom",
    "jeans": "bottom",
    "skirt": "bottom",
    "shorts": "bottom",
    "dress": "dress",
    "jumpsuit": "dress",
    "boots": "shoes",
    "sneakers": "shoes",
    "shoes": "shoes",
    "bag": "bag",
    "accessory": "accessory",
}

#: Значения-«пустышки»: термины, которые не должны попадать в описание вещи.
_EMPTY = {"", " "}


def _table(spec: dict[str, str]) -> dict[str, str]:
    return {stem_ru(key): value for key, value in spec.items()}


_TABLES: dict[str, dict[str, str]] = {
    "garment": _table(RU_GARMENTS),
    "material": _table(RU_MATERIALS),
    "silhouette": _table(RU_SILHOUETTES),
    "aesthetic": _table(RU_AESTHETIC_TERMS),
    "color": _table(RU_COLORS),
}


def detect_terms(text: str, tables: tuple[str, ...] = ("garment", "material", "silhouette", "aesthetic")) -> list[str]:
    """Все термины движка, найденные в русском тексте (по порядку таблиц)."""
    tokens = tokenize(text)
    found: list[str] = []
    seen: set[str] = set()
    for name in tables:
        table = _TABLES[name]
        for token in tokens:
            if token in RU_STOPWORDS:
                continue
            for key, value in table.items():
                if value in _EMPTY or value in seen:
                    continue
                if _matches(token, key):
                    found.append(value)
                    seen.add(value)
                    break
    return found


def translate_text(text: str, tables: tuple[str, ...] = ("garment", "material", "silhouette", "aesthetic")) -> str:
    """Свободный текст → строка с английскими терминами движка."""
    return " ".join(detect_terms(text, tables))


def detect_colors(text: str) -> list[str]:
    """Цвета, найденные в тексте, в словаре движка."""
    tokens = tokenize(text)
    found: list[str] = []
    for token in tokens:
        for key, value in _TABLES["color"].items():
            if _matches(token, key) and value not in found:
                found.append(value)
                break
    return found


def engine_category(name: str, fallback: str = "accessory") -> str:
    """Категория движка для русской названия вещи (coat/boots/top/…)."""
    tokens = tokenize(name)
    hits: list[str] = []
    for token in tokens:
        for key, value in _TABLES["garment"].items():
            if _matches(token, key):
                hits.extend(value.split())
                break
    for candidate in CATEGORY_PRIORITY:
        if candidate in hits:
            return candidate
    # «брюки» дают trousers, «джинсы» — denim jeans; «shoes» ловим как синоним sneakers
    if "shoes" in hits:
        return "sneakers"
    return fallback


def _label(kind: str, term: str | None) -> str:
    if not term:
        return ""
    normalized = str(term).lower()
    if normalized in EN_TO_RU:
        return EN_TO_RU[normalized]
    for key, value in _TABLES[kind].items():  # fallback: ищем по EN-значению
        if normalized in value.split():
            return EN_TO_RU.get(normalized, normalized)
    return EN_TO_RU.get(normalized, normalized)


def silhouette_label_ru(value: str | None) -> str:
    return _label("silhouette", value)


def material_label_ru(value: str | None) -> str:
    return _label("material", value)


def aesthetic_label_ru(value: str | None) -> str:
    return _label("aesthetic", value)


TASTE_LABELS_RU: dict[str, str] = {
    "generic": "масс-маркет",
    "interesting": "интересная вещь",
    "niche": "нишевый бренд",
    "designer": "дизайнерская вещь",
    "archive": "архив",
    "editorial": "эдиториал",
    "cult": "культовая вещь",
    "exceptional": "исключительная вещь",
}

ROLE_LABELS_RU: dict[str, str] = {
    "hero": "ключевая вещь",
    "base": "база образа",
    "layer": "слой",
    "footwear": "обувь",
    "accessory": "аксессуар",
}


def taste_label_ru(taste_category: str | None) -> str:
    return TASTE_LABELS_RU.get(str(taste_category or "").lower(), "интересная вещь")


def role_label_ru(role: str | None) -> str:
    return ROLE_LABELS_RU.get(str(role or "").lower(), "вещь образа")
