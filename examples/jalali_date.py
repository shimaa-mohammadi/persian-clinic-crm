# -*- coding: utf-8 -*-
"""تبدیل تاریخ شمسی (جلالی) و میلادی — بدون وابستگی به کتابخانه خارجی."""

import datetime

MONTH_NAMES = ["فروردین", "اردیبهشت", "خرداد", "تیر", "مرداد", "شهریور",
               "مهر", "آبان", "آذر", "دی", "بهمن", "اسفند"]

# ایندکس بر اساس weekday پایتون (0=دوشنبه ... 5=شنبه 6=یکشنبه)
WEEKDAY_NAMES = ["دوشنبه", "سه‌شنبه", "چهارشنبه", "پنجشنبه", "جمعه",
                 "شنبه", "یکشنبه"]

# موقعیت سال‌های کبیسه در چرخه ۳۳ ساله تقویم شمسی
_LEAP_POSITIONS = (1, 5, 9, 13, 17, 22, 26, 30)

PERSIAN_DIGITS = str.maketrans("۰۱۲۳۴۵۶۷۸۹", "0123456789")
ARABIC_DIGITS = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")

# نقطه اتکا: ۱ فروردین ۱۴۰۵ برابر است با ۲۱ مارس ۲۰۲۶
_ANCHOR_G = datetime.date(2026, 3, 21).toordinal()


def is_jalali_leap(jy):
    return jy % 33 in _LEAP_POSITIONS


def jalali_month_len(jy, jm):
    if jm <= 6:
        return 31
    if jm <= 11:
        return 30
    return 30 if is_jalali_leap(jy) else 29


def _leaps_before(n):
    """تعداد سال‌های کبیسه در بازه سال ۱ تا n شمسی."""
    if n <= 0:
        return 0
    count = (n // 33) * 8
    rem = n % 33
    for p in _LEAP_POSITIONS:
        if p <= rem:
            count += 1
    return count


def _j_abs(jy, jm, jd):
    """شماره مطلق روز نسبت به ابتدای تقویم شمسی."""
    if jm <= 6:
        doy = (jm - 1) * 31 + jd
    else:
        doy = 186 + (jm - 7) * 30 + jd
    return (jy - 1) * 365 + _leaps_before(jy - 1) + doy


_OFFSET = _ANCHOR_G - _j_abs(1405, 1, 1)


def j2g(jy, jm, jd):
    """تبدیل تاریخ شمسی به datetime.date میلادی."""
    if not (1 <= jm <= 12):
        raise ValueError("ماه شمسی باید بین ۱ تا ۱۲ باشد")
    if not (1 <= jd <= jalali_month_len(jy, jm)):
        raise ValueError("روز شمسی نامعتبر است")
    return datetime.date.fromordinal(_j_abs(jy, jm, jd) + _OFFSET)


def g2j(d):
    """تبدیل datetime.date میلادی به (سال، ماه، روز) شمسی."""
    a = d.toordinal() - _OFFSET
    jy = max(1, a // 366)
    while _j_abs(jy + 1, 1, 1) <= a:
        jy += 1
    while jy > 1 and _j_abs(jy, 1, 1) > a:
        jy -= 1
    doy = a - _j_abs(jy, 1, 1) + 1
    if doy <= 186:
        jm = (doy - 1) // 31 + 1
        jd = doy - (jm - 1) * 31
    else:
        jm = (doy - 187) // 30 + 7
        jd = doy - 186 - (jm - 7) * 30
    return jy, jm, jd


def today():
    return datetime.date.today()


def today_iso():
    return datetime.date.today().isoformat()


def iso_to_jstr(iso_date):
    """'2026-11-18' → '1405/08/26'"""
    if not iso_date:
        return "—"
    try:
        d = datetime.date.fromisoformat(str(iso_date)[:10])
    except ValueError:
        return str(iso_date)
    jy, jm, jd = g2j(d)
    return "%d/%02d/%02d" % (jy, jm, jd)


def iso_to_jlong(iso_date):
    """'2026-11-18' → '26 آبان 1405'"""
    if not iso_date:
        return "—"
    try:
        d = datetime.date.fromisoformat(str(iso_date)[:10])
    except ValueError:
        return str(iso_date)
    jy, jm, jd = g2j(d)
    return "%d %s %d" % (jd, MONTH_NAMES[jm - 1], jy)


def weekday_name(iso_date):
    try:
        d = datetime.date.fromisoformat(str(iso_date)[:10])
    except ValueError:
        return ""
    return WEEKDAY_NAMES[d.weekday()]


def parse_jdate(text):
    """ورودی شمسی مثل '1405/08/26' یا '۱۴۰۵-۸-۲۶' → رشته ISO میلادی یا None."""
    if text is None:
        return None
    s = str(text).strip().translate(PERSIAN_DIGITS).translate(ARABIC_DIGITS)
    s = s.replace("-", "/").replace(".", "/").replace("_", "/")
    parts = [p for p in s.split("/") if p.strip()]
    if len(parts) != 3:
        return None
    try:
        jy, jm, jd = int(parts[0]), int(parts[1]), int(parts[2])
    except ValueError:
        return None
    if not (1300 <= jy <= 1500):
        return None
    try:
        return j2g(jy, jm, jd).isoformat()
    except ValueError:
        return None


def parse_money(text):
    """ورودی مثل '2,500,000' یا '۲٫۵۰۰٫۰۰۰' → عدد صحیح یا None."""
    if text is None:
        return None
    s = str(text).strip().translate(PERSIAN_DIGITS).translate(ARABIC_DIGITS)
    s = s.replace("٫", "").replace("،", "").replace("٬", "")
    s = s.replace(",", "").replace(" ", "").replace("تومان", "").replace("ریال", "")
    s = s.strip()
    if not s:
        return None
    try:
        v = int(float(s))
    except ValueError:
        return None
    return v if v >= 0 else None


def jalali_month_range(jy, jm):
    """بازه میلادی (شروع، پایان) یک ماه شمسی — برای فیلترهای ماهانه."""
    start = j2g(jy, jm, 1)
    if jm == 12:
        end = j2g(jy + 1, 1, 1) - datetime.timedelta(days=1)
    else:
        end = j2g(jy, jm + 1, 1) - datetime.timedelta(days=1)
    return start.isoformat(), end.isoformat()


def jalali_month_add(jy, jm, delta):
    """n ماه جابه‌جایی در تقویم شمسی (delta می‌تواند منفی باشد)."""
    m = (jm - 1 + delta) % 12 + 1
    y = jy + (jm - 1 + delta) // 12
    return y, m


def month_label(jy, jm):
    return "%s %d" % (MONTH_NAMES[jm - 1], jy)
