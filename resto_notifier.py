"""
نظام التنبيهات الذكي لحجز وجبات المطعم الجامعي (Progrès) عبر ntfy
الموضوع (Topic): gp_constantine_chem4_alert_2026
"""

import sys
import json
import datetime
import urllib.request
import urllib.error

# إعدادات ntfy
NTFY_URL = "https://ntfy.sh"
TOPIC = "gp_constantine_chem4_alert_2026"

# تاريخ البداية المرجعي (يوم الإثنين 9 نوفمبر 2026 - أول يوم تذكير قادم)
REFERENCE_DATE = datetime.date(2026, 11, 9)

# أسماء الأيام والشهور بالعربية
ARABIC_DAYS = ["الإثنين", "الثلاثاء", "الأربعاء", "الخميس", "الجمعة", "السبت", "الأحد"]
ARABIC_MONTHS = [
    "", "جانفي", "فيفري", "مارس", "أفريل", "ماي", "جوان",
    "جويلية", "أوت", "سبتمبر", "أكتوبر", "نوفمبر", "ديسمبر"
]


def format_date_ar(d: datetime.date) -> str:
    return f"{ARABIC_DAYS[d.weekday()]} {d.day} {ARABIC_MONTHS[d.month]}"


def is_reminder_day(target_date: datetime.date) -> bool:
    """التحقق مما إذا كان التاريخ يوافق دورة التذكير كل 3 أيام"""
    delta = (target_date - REFERENCE_DATE).days
    return delta % 3 == 0


def get_target_booking_days(reminder_date: datetime.date):
    """حساب الأيام الثلاثة التي سيتم حجزها في هذا اليوم"""
    d1 = reminder_date + datetime.timedelta(days=1)
    d2 = reminder_date + datetime.timedelta(days=2)
    d3 = reminder_date + datetime.timedelta(days=3)
    return d1, d2, d3


def send_ntfy_notification(title: str, message: str, priority: int = 4, tags=None):
    """إرسال إشعار عبر ntfy واضح ومركّز على التذكير بالمواعيد"""
    if tags is None:
        tags = ["bell", "fork_and_knife"]

    payload = {
        "topic": TOPIC,
        "title": title,
        "message": message,
        "priority": priority,
        "tags": tags,
        # لا نضع روابط لتفادي أخطاء النظام، فالهدف هو التنبيه الصوتي والنصي الفوري
    }

    req = urllib.request.Request(
        NTFY_URL,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST"
    )

    try:
        with urllib.request.urlopen(req) as resp:
            data = resp.read().decode("utf-8")
            print(f"✅ تم إرسال الإشعار بنجاح: {data}")
            return True
    except urllib.error.URLError as e:
        print(f"❌ خطأ أثناء إرسال الإشعار: {e}", file=sys.stderr)
        return False


def build_message(batch_num: int, reminder_date: datetime.date):
    """صياغة نص الإشعار المخصص لكل دفعة وتحديد الأيام المستهدفة بدقة"""
    d1, d2, d3 = get_target_booking_days(reminder_date)
    days_text = f"{format_date_ar(d1)}، {format_date_ar(d2)}، و{format_date_ar(d3)}"

    if batch_num == 1:
        # الدفعة 1: صباحية (هادئة/تذكيرية)
        title = "☀️ تذكير صباحي: موعد حجز وجبات الريستو"
        message = (
            f"صباح الخير! اليوم هو موعد تجديد وجباتك في تطبيق Progrès.\n"
            f"يجب عليك الحجز الآن للأيام القادمة:\n"
            f"📌 {days_text}\n"
            f"تذكر: الحجز مبكراً يضمن وجبتك دون نسيان!"
        )
        priority = 3
        tags = ["bell", "fork_and_knife"]

    elif batch_num == 2:
        # الدفعة 2: بعد العصر (تنبيه)
        title = "⚠️ تنبيه المساء: هل حجزت وجباتك؟"
        message = (
            f"تنبيه هام! لم تحجز وجبات الريستو بعد؟\n"
            f"يجب عليك الحجز الآن لتأمين وجباتك للأيام التالية:\n"
            f"📌 {days_text}\n"
            f"تطبيق Progrès يغلق حجز الغد بحلول منتصف الليل."
        )
        priority = 4
        tags = ["warning", "fork_and_knife"]

    elif batch_num == 3:
        # الدفعة 3: ليلية (طارئة - أقصى أولوية مع صوت تنبيه عالي واهتزاز)
        title = "🚨 إنذار أخير: يجب عليك الحجز الآن فوراً!"
        message = (
            f"يجب عليك الحجز الآن قبل إغلاق النظام الليلة!\n"
            f"إذا لم تحجز الآن، فلن تتمكن من الأكل غداً في الريستو إطلاقاً بسبب قاعدة الـ 24 ساعة.\n"
            f"الأيام المستهدفة: {days_text}."
        )
        priority = 5  # Urgent priority in ntfy
        tags = ["rotating_light", "alarm_clock", "x"]
    else:
        raise ValueError(f"رقم دفعة غير صالح: {batch_num}")

    return title, message, priority, tags


def run(batch_num: int, force: bool = False):
    today = datetime.date.today()
    if not force and not is_reminder_day(today):
        print(f"اليوم {today} ليس يوم تذكير. يوم التذكير التالي سيكون في الدورة المحددة.")
        return

    title, message, priority, tags = build_message(batch_num, today)
    print(f"🚀 جاري إرسال الدفعة {batch_num}...")
    send_ntfy_notification(title, message, priority, tags)


if __name__ == "__main__":
    # تشغيل السكريبت يدويًا أو عبر المجدول
    # الاستخدام: python resto_notifier.py <رقم_الدفعة: 1 أو 2 أو 3> [--force]
    args = sys.argv[1:]
    force_flag = "--force" in args
    batch_args = [a for a in args if a.isdigit()]

    if batch_args:
        batch = int(batch_args[0])
        run(batch, force=force_flag)
    else:
        print("الاستخدام: python resto_notifier.py <1 أو 2 أو 3> [--force]")
        print("مثال لاختبار الدفعة الأولى الآن: python resto_notifier.py 1 --force")
