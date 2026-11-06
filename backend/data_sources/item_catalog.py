"""Conservative exact-name mappings; unknown identities are skipped, never guessed.

Extend after checking weapon, finish, exterior, StatTrak/souvenir and knife star.
Optional BUFF IDs are configured by canonical Steam hash name in BUFF_GOODS_IDS.
"""
MARKET_NAMES = {
    "AK-47 | 红线 (久经沙场)": "AK-47 | Redline (Field-Tested)",
    "AK-47 | 火蛇 (崭新出厂)": "AK-47 | Fire Serpent (Factory New)",
    "AK-47 | 二西莫夫 (久经沙场)": "AK-47 | Asiimov (Field-Tested)",
    "M4A4 | 嚎叫 (久经沙场)": "M4A4 | Howl (Field-Tested)",
    "M4A1 消音型 | 印花集 (崭新出厂)": "M4A1-S | Printstream (Factory New)",
    "AWP | 龙狙 (久经沙场)": "AWP | Dragon Lore (Field-Tested)",
    "AWP | 二西莫夫 (久经沙场)": "AWP | Asiimov (Field-Tested)",
    "沙漠之鹰 | 印花集 (崭新出厂)": "Desert Eagle | Printstream (Factory New)",
    "沙漠之鹰 | 火焰 (崭新出厂)": "Desert Eagle | Blaze (Factory New)",
    "格洛克 18 型 | 渐变之色 (崭新出厂)": "Glock-18 | Fade (Factory New)",
    "爪子刀 | 多普勒 (崭新出厂)": "★ Karambit | Doppler (Factory New)",
    "蝴蝶刀 | 渐变之色 (崭新出厂)": "★ Butterfly Knife | Fade (Factory New)",
    "StatTrak™ AK-47 | 红线 (久经沙场)": "StatTrak™ AK-47 | Redline (Field-Tested)",
    "StatTrak™ AWP | 二西莫夫 (久经沙场)": "StatTrak™ AWP | Asiimov (Field-Tested)",
    "StatTrak™ 沙漠之鹰 | 印花集 (崭新出厂)": "StatTrak™ Desert Eagle | Printstream (Factory New)",
}
