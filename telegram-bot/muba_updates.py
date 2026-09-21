"""MUBA Assistant update UI backed by the canonical project history."""
from __future__ import annotations

from muba_history import (
    UPDATES,
    entries,
    latest_id,
    has_unseen,
    badge_type,
)

UPDATE_LABELS={
"en":{"center":"🔔 MUBA Updates","new":"NEW","updated":"UPDATED","improved":"IMPROVED","fixed":"FIXED","back":"⬅️ Back","open_gallery":"🖼 Open MUBA Gallery","related":"Related units"},
"tr":{"center":"🔔 MUBA Yenilikleri","new":"YENİ","updated":"GÜNCELLENDİ","improved":"İYİLEŞTİRİLDİ","fixed":"DÜZELTİLDİ","back":"⬅️ Geri","open_gallery":"🖼 MUBA Galeri'yi Aç","related":"İlgili birimler"},
"zh":{"center":"🔔 MUBA 更新","new":"新增","updated":"已更新","improved":"已改进","fixed":"已修复","back":"⬅️ 返回","open_gallery":"🖼 打开 MUBA Gallery","related":"相关单元"},
"ar":{"center":"🔔 تحديثات MUBA","new":"جديد","updated":"محدّث","improved":"محسّن","fixed":"تم الإصلاح","back":"⬅️ رجوع","open_gallery":"🖼 فتح MUBA Gallery","related":"الوحدات المرتبطة"},
"hi":{"center":"🔔 MUBA Updates","new":"NEW","updated":"UPDATED","improved":"IMPROVED","fixed":"FIXED","back":"⬅️ वापस","open_gallery":"🖼 MUBA Gallery खोलें","related":"संबंधित इकाइयाँ"},
}

AREA_LABELS={
"en":{"gallery":"🖼 MUBA Gallery","studio":"🎭 MUBA Studio","web":"🌐 Website","telegram":"📌 Telegram","daily":"📰 MUBA Daily","assistant":"🤖 Assistant","guardian":"🛡 Guardian"},
"tr":{"gallery":"🖼 MUBA Galeri","studio":"🎭 MUBA Studio","web":"🌐 Web Sitesi","telegram":"📌 Telegram","daily":"📰 MUBA Daily","assistant":"🤖 Assistant","guardian":"🛡 Guardian"},
"zh":{"gallery":"🖼 MUBA Gallery","studio":"🎭 MUBA Studio","web":"🌐 网站","telegram":"📌 Telegram","daily":"📰 MUBA Daily","assistant":"🤖 Assistant","guardian":"🛡 Guardian"},
"ar":{"gallery":"🖼 MUBA Gallery","studio":"🎭 MUBA Studio","web":"🌐 الموقع","telegram":"📌 Telegram","daily":"📰 MUBA Daily","assistant":"🤖 Assistant","guardian":"🛡 Guardian"},
"hi":{"gallery":"🖼 MUBA Gallery","studio":"🎭 MUBA Studio","web":"🌐 वेबसाइट","telegram":"📌 Telegram","daily":"📰 MUBA Daily","assistant":"🤖 Assistant","guardian":"🛡 Guardian"},
}
