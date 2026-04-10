from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Iterable

from ui.starry_chrome import StarryPalette
from ui.theme import ScenePalette, rgba


@dataclass(frozen=True)
class ThemeProfile:
    id: str
    name: str
    tagline: str
    accent: str
    accent_strong: str
    accent_soft: str
    brass: str
    success: str
    warning: str
    danger: str
    text_primary: str
    text_secondary: str
    text_muted: str
    text_dim: str
    sky_top: str
    sky_mid: str
    sky_bottom: str
    panel_top: str
    panel_bottom: str
    panel_edge: str
    glass: str
    field_fill: str
    field_fill_hover: str
    field_border: str
    field_border_focus: str
    button_fill: str
    button_fill_hover: str
    button_fill_active: str
    window_overlay_top: str
    window_overlay_bottom: str
    titlebar_surface: str
    titlebar_button: str
    theme_tag_bg: str
    theme_tag_border: str
    line: str
    line_soft: str
    star_soft: str
    star_strong: str
    scrollbar_handle: str
    scrollbar_handle_hover: str
    icon_color: str
    light_surface: str


@dataclass(frozen=True)
class BackgroundVariant:
    id: str
    title: str
    subtitle: str
    motif: str
    accent_bias: str
    secondary_bias: str
    mist_ratio: float
    star_density: int
    horizon_ratio: float
    glow_ratio: float


@dataclass(frozen=True)
class BackgroundSpec:
    id: str
    theme_id: str
    theme_name: str
    variant_id: str
    title: str
    subtitle: str
    motif: str
    filename: str
    sky_top: str
    sky_mid: str
    sky_bottom: str
    accent_primary: str
    accent_secondary: str
    glow_color: str
    horizon_color: str
    mist_ratio: float
    star_density: int
    line_tint: str
    text_primary: str
    text_secondary: str


def _hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    value = hex_color.lstrip("#")
    return int(value[0:2], 16), int(value[2:4], 16), int(value[4:6], 16)


def mix_hex(left: str, right: str, ratio: float) -> str:
    ratio = max(0.0, min(1.0, ratio))
    lr, lg, lb = _hex_to_rgb(left)
    rr, rg, rb = _hex_to_rgb(right)
    red = int(lr + (rr - lr) * ratio)
    green = int(lg + (rg - lg) * ratio)
    blue = int(lb + (rb - lb) * ratio)
    return f"#{red:02x}{green:02x}{blue:02x}"


def assets_root() -> Path:
    return Path(__file__).resolve().parent.parent / "assets"


def wallpaper_root() -> Path:
    path = assets_root() / "wallpapers"
    path.mkdir(exist_ok=True)
    return path


THEME_PROFILES: tuple[ThemeProfile, ...] = (
    ThemeProfile(
        id="orion_blue",
        name="猎户蓝轨",
        tagline="冷静、清晰、适合高密度任务编排",
        accent="#78aef6",
        accent_strong="#d8e9ff",
        accent_soft="rgba(120, 174, 246, 0.18)",
        brass="#d7c8a4",
        success="#88d1ba",
        warning="#d8c18d",
        danger="#d7969b",
        text_primary="#f2f7ff",
        text_secondary="#d8e6f6",
        text_muted="#a7bad1",
        text_dim="#7e94ad",
        sky_top="#081223",
        sky_mid="#10213d",
        sky_bottom="#183355",
        panel_top="#0c1526",
        panel_bottom="#12233c",
        panel_edge="#8ca7d4",
        glass="rgba(255, 255, 255, 0.04)",
        field_fill="rgba(9, 18, 32, 0.82)",
        field_fill_hover="rgba(12, 22, 38, 0.92)",
        field_border="rgba(168, 196, 232, 0.24)",
        field_border_focus="rgba(216, 233, 255, 0.62)",
        button_fill="rgba(16, 29, 50, 0.94)",
        button_fill_hover="rgba(23, 39, 65, 0.98)",
        button_fill_active="#345d92",
        window_overlay_top="#08101d",
        window_overlay_bottom="#11223d",
        titlebar_surface="rgba(9, 18, 30, 0.76)",
        titlebar_button="rgba(255, 255, 255, 0.08)",
        theme_tag_bg="rgba(120, 174, 246, 0.16)",
        theme_tag_border="rgba(120, 174, 246, 0.34)",
        line="rgba(164, 190, 224, 0.26)",
        line_soft="rgba(164, 190, 224, 0.14)",
        star_soft="rgba(219, 232, 248, 0.42)",
        star_strong="rgba(242, 247, 255, 0.90)",
        scrollbar_handle="rgba(219, 232, 248, 0.42)",
        scrollbar_handle_hover="rgba(242, 247, 255, 0.66)",
        icon_color="#dce9fa",
        light_surface="rgba(255, 255, 255, 0.05)",
    ),
    ThemeProfile(
        id="nebula_rose",
        name="玫瑰星云",
        tagline="柔和紫粉过渡，适合写作与复盘场景",
        accent="#d39bf0",
        accent_strong="#fde9ff",
        accent_soft="rgba(211, 155, 240, 0.18)",
        brass="#e2c39a",
        success="#9bd9be",
        warning="#dfc088",
        danger="#e1a0ac",
        text_primary="#fff4ff",
        text_secondary="#f1daf6",
        text_muted="#caa7d4",
        text_dim="#9f83ab",
        sky_top="#14091f",
        sky_mid="#2a1238",
        sky_bottom="#4d1e5c",
        panel_top="#1b0d27",
        panel_bottom="#281338",
        panel_edge="#d39bf0",
        glass="rgba(255, 255, 255, 0.05)",
        field_fill="rgba(28, 11, 40, 0.82)",
        field_fill_hover="rgba(36, 14, 49, 0.92)",
        field_border="rgba(231, 193, 247, 0.24)",
        field_border_focus="rgba(253, 233, 255, 0.62)",
        button_fill="rgba(51, 22, 68, 0.94)",
        button_fill_hover="rgba(69, 30, 92, 0.98)",
        button_fill_active="#8248ab",
        window_overlay_top="#110818",
        window_overlay_bottom="#341541",
        titlebar_surface="rgba(24, 10, 35, 0.76)",
        titlebar_button="rgba(255, 255, 255, 0.07)",
        theme_tag_bg="rgba(211, 155, 240, 0.18)",
        theme_tag_border="rgba(211, 155, 240, 0.34)",
        line="rgba(226, 198, 240, 0.24)",
        line_soft="rgba(226, 198, 240, 0.12)",
        star_soft="rgba(247, 233, 255, 0.40)",
        star_strong="rgba(255, 244, 255, 0.92)",
        scrollbar_handle="rgba(247, 233, 255, 0.40)",
        scrollbar_handle_hover="rgba(255, 244, 255, 0.68)",
        icon_color="#f4dbff",
        light_surface="rgba(255, 255, 255, 0.05)",
    ),
    ThemeProfile(
        id="aurora_jade",
        name="极光青岚",
        tagline="青绿与深蓝融合，适合长期专注与规划",
        accent="#6fd2c3",
        accent_strong="#e3fffb",
        accent_soft="rgba(111, 210, 195, 0.16)",
        brass="#d5c89c",
        success="#90d8b0",
        warning="#d7c086",
        danger="#dc9aa1",
        text_primary="#effffd",
        text_secondary="#d4f5ef",
        text_muted="#9cc7be",
        text_dim="#739891",
        sky_top="#04181d",
        sky_mid="#0c2c32",
        sky_bottom="#11424e",
        panel_top="#0b171a",
        panel_bottom="#10262d",
        panel_edge="#7adccf",
        glass="rgba(255, 255, 255, 0.04)",
        field_fill="rgba(6, 22, 25, 0.82)",
        field_fill_hover="rgba(10, 29, 34, 0.92)",
        field_border="rgba(142, 225, 214, 0.24)",
        field_border_focus="rgba(227, 255, 251, 0.62)",
        button_fill="rgba(11, 36, 41, 0.94)",
        button_fill_hover="rgba(14, 48, 56, 0.98)",
        button_fill_active="#1d6c74",
        window_overlay_top="#061417",
        window_overlay_bottom="#0d2c34",
        titlebar_surface="rgba(7, 19, 21, 0.76)",
        titlebar_button="rgba(255, 255, 255, 0.08)",
        theme_tag_bg="rgba(111, 210, 195, 0.16)",
        theme_tag_border="rgba(111, 210, 195, 0.34)",
        line="rgba(155, 224, 215, 0.22)",
        line_soft="rgba(155, 224, 215, 0.12)",
        star_soft="rgba(224, 255, 250, 0.36)",
        star_strong="rgba(239, 255, 253, 0.88)",
        scrollbar_handle="rgba(224, 255, 250, 0.38)",
        scrollbar_handle_hover="rgba(239, 255, 253, 0.64)",
        icon_color="#d8fff8",
        light_surface="rgba(255, 255, 255, 0.05)",
    ),
    ThemeProfile(
        id="amber_dawn",
        name="琥珀晨辉",
        tagline="低饱和金橙与灰蓝，适合轻亮的学习氛围",
        accent="#d7b277",
        accent_strong="#fff2dd",
        accent_soft="rgba(215, 178, 119, 0.18)",
        brass="#e6d1ab",
        success="#90cfaa",
        warning="#d9b56c",
        danger="#dba0a0",
        text_primary="#fff8f0",
        text_secondary="#f1e5d3",
        text_muted="#c6b096",
        text_dim="#9d8770",
        sky_top="#241714",
        sky_mid="#433128",
        sky_bottom="#6a5446",
        panel_top="#251913",
        panel_bottom="#37281f",
        panel_edge="#d7b277",
        glass="rgba(255, 255, 255, 0.06)",
        field_fill="rgba(32, 22, 16, 0.80)",
        field_fill_hover="rgba(42, 29, 20, 0.90)",
        field_border="rgba(237, 214, 178, 0.24)",
        field_border_focus="rgba(255, 242, 221, 0.62)",
        button_fill="rgba(55, 38, 25, 0.94)",
        button_fill_hover="rgba(73, 51, 33, 0.98)",
        button_fill_active="#8f6840",
        window_overlay_top="#1e140f",
        window_overlay_bottom="#4d372c",
        titlebar_surface="rgba(35, 24, 18, 0.78)",
        titlebar_button="rgba(255, 255, 255, 0.08)",
        theme_tag_bg="rgba(215, 178, 119, 0.18)",
        theme_tag_border="rgba(215, 178, 119, 0.34)",
        line="rgba(236, 216, 184, 0.22)",
        line_soft="rgba(236, 216, 184, 0.12)",
        star_soft="rgba(255, 244, 227, 0.32)",
        star_strong="rgba(255, 248, 240, 0.86)",
        scrollbar_handle="rgba(255, 244, 227, 0.34)",
        scrollbar_handle_hover="rgba(255, 248, 240, 0.60)",
        icon_color="#f7e8d2",
        light_surface="rgba(255, 255, 255, 0.06)",
    ),
    ThemeProfile(
        id="moon_silver",
        name="月霜银灰",
        tagline="中性灰蓝，强调信息秩序与长时间可读性",
        accent="#b7cadf",
        accent_strong="#f5fbff",
        accent_soft="rgba(183, 202, 223, 0.16)",
        brass="#d7ccbb",
        success="#a7d0c0",
        warning="#d8c8a0",
        danger="#d5a2a8",
        text_primary="#f6fbff",
        text_secondary="#e0e9f1",
        text_muted="#acb7c6",
        text_dim="#838f9f",
        sky_top="#0f141c",
        sky_mid="#1d2634",
        sky_bottom="#323f54",
        panel_top="#131922",
        panel_bottom="#1c2633",
        panel_edge="#b7cadf",
        glass="rgba(255, 255, 255, 0.04)",
        field_fill="rgba(16, 22, 30, 0.82)",
        field_fill_hover="rgba(23, 31, 43, 0.92)",
        field_border="rgba(210, 222, 236, 0.22)",
        field_border_focus="rgba(245, 251, 255, 0.60)",
        button_fill="rgba(24, 33, 46, 0.94)",
        button_fill_hover="rgba(35, 47, 64, 0.98)",
        button_fill_active="#5d728a",
        window_overlay_top="#0d1117",
        window_overlay_bottom="#212b39",
        titlebar_surface="rgba(18, 24, 32, 0.78)",
        titlebar_button="rgba(255, 255, 255, 0.08)",
        theme_tag_bg="rgba(183, 202, 223, 0.16)",
        theme_tag_border="rgba(183, 202, 223, 0.32)",
        line="rgba(208, 221, 235, 0.22)",
        line_soft="rgba(208, 221, 235, 0.12)",
        star_soft="rgba(243, 249, 255, 0.34)",
        star_strong="rgba(246, 251, 255, 0.88)",
        scrollbar_handle="rgba(243, 249, 255, 0.34)",
        scrollbar_handle_hover="rgba(246, 251, 255, 0.58)",
        icon_color="#eef5fd",
        light_surface="rgba(255, 255, 255, 0.05)",
    ),
    ThemeProfile(
        id="violet_tide",
        name="潮汐紫幕",
        tagline="紫蓝潮汐层次，适合需要情绪张力但不刺眼的界面",
        accent="#9f98ef",
        accent_strong="#f0eeff",
        accent_soft="rgba(159, 152, 239, 0.18)",
        brass="#d9c8a6",
        success="#9acdb9",
        warning="#d8c28c",
        danger="#d8a0ae",
        text_primary="#f6f3ff",
        text_secondary="#ddd8f8",
        text_muted="#b3acd8",
        text_dim="#8a84ae",
        sky_top="#0d0f24",
        sky_mid="#1d2042",
        sky_bottom="#312f62",
        panel_top="#111427",
        panel_bottom="#1b2140",
        panel_edge="#9f98ef",
        glass="rgba(255, 255, 255, 0.04)",
        field_fill="rgba(15, 18, 37, 0.82)",
        field_fill_hover="rgba(22, 26, 50, 0.92)",
        field_border="rgba(194, 188, 246, 0.22)",
        field_border_focus="rgba(240, 238, 255, 0.60)",
        button_fill="rgba(22, 28, 54, 0.94)",
        button_fill_hover="rgba(33, 41, 76, 0.98)",
        button_fill_active="#5554ab",
        window_overlay_top="#0b0d1e",
        window_overlay_bottom="#242753",
        titlebar_surface="rgba(15, 18, 34, 0.78)",
        titlebar_button="rgba(255, 255, 255, 0.08)",
        theme_tag_bg="rgba(159, 152, 239, 0.16)",
        theme_tag_border="rgba(159, 152, 239, 0.32)",
        line="rgba(206, 201, 247, 0.22)",
        line_soft="rgba(206, 201, 247, 0.12)",
        star_soft="rgba(243, 240, 255, 0.34)",
        star_strong="rgba(246, 243, 255, 0.90)",
        scrollbar_handle="rgba(243, 240, 255, 0.36)",
        scrollbar_handle_hover="rgba(246, 243, 255, 0.62)",
        icon_color="#ece8ff",
        light_surface="rgba(255, 255, 255, 0.05)",
    ),
    ThemeProfile(
        id="coral_horizon",
        name="珊瑚海幕",
        tagline="珊瑚粉与海蓝平衡，适合清晨任务推进场景",
        accent="#ef9a9f",
        accent_strong="#fff0f2",
        accent_soft="rgba(239, 154, 159, 0.18)",
        brass="#e3c6a3",
        success="#9bd3bf",
        warning="#dec18b",
        danger="#f2a0a4",
        text_primary="#fff7f7",
        text_secondary="#f6dfe1",
        text_muted="#d0afb2",
        text_dim="#a78488",
        sky_top="#25121b",
        sky_mid="#4d2436",
        sky_bottom="#7f4160",
        panel_top="#27131c",
        panel_bottom="#3f2030",
        panel_edge="#ef9a9f",
        glass="rgba(255, 255, 255, 0.05)",
        field_fill="rgba(33, 16, 24, 0.82)",
        field_fill_hover="rgba(45, 20, 31, 0.92)",
        field_border="rgba(245, 205, 209, 0.24)",
        field_border_focus="rgba(255, 240, 242, 0.62)",
        button_fill="rgba(56, 26, 40, 0.94)",
        button_fill_hover="rgba(76, 35, 54, 0.98)",
        button_fill_active="#b45b6d",
        window_overlay_top="#1e0e16",
        window_overlay_bottom="#55293d",
        titlebar_surface="rgba(34, 16, 26, 0.76)",
        titlebar_button="rgba(255, 255, 255, 0.08)",
        theme_tag_bg="rgba(239, 154, 159, 0.18)",
        theme_tag_border="rgba(239, 154, 159, 0.34)",
        line="rgba(244, 208, 213, 0.24)",
        line_soft="rgba(244, 208, 213, 0.12)",
        star_soft="rgba(255, 237, 240, 0.34)",
        star_strong="rgba(255, 247, 247, 0.88)",
        scrollbar_handle="rgba(255, 237, 240, 0.34)",
        scrollbar_handle_hover="rgba(255, 247, 247, 0.60)",
        icon_color="#ffe6ea",
        light_surface="rgba(255, 255, 255, 0.05)",
    ),
    ThemeProfile(
        id="forest_constellation",
        name="森野星群",
        tagline="偏墨绿与柔黄，适合低刺激的长期任务环境",
        accent="#88c39a",
        accent_strong="#f1fff3",
        accent_soft="rgba(136, 195, 154, 0.16)",
        brass="#d6c48d",
        success="#9ed2a9",
        warning="#d4bb78",
        danger="#cfa0a3",
        text_primary="#f4fff4",
        text_secondary="#dcf0dd",
        text_muted="#a8c6aa",
        text_dim="#7e9b81",
        sky_top="#0d1a13",
        sky_mid="#183123",
        sky_bottom="#28513a",
        panel_top="#101a14",
        panel_bottom="#17271e",
        panel_edge="#88c39a",
        glass="rgba(255, 255, 255, 0.04)",
        field_fill="rgba(12, 24, 17, 0.82)",
        field_fill_hover="rgba(17, 32, 22, 0.92)",
        field_border="rgba(187, 225, 196, 0.22)",
        field_border_focus="rgba(241, 255, 243, 0.60)",
        button_fill="rgba(18, 31, 22, 0.94)",
        button_fill_hover="rgba(24, 43, 30, 0.98)",
        button_fill_active="#3f7051",
        window_overlay_top="#0c1510",
        window_overlay_bottom="#203526",
        titlebar_surface="rgba(13, 21, 15, 0.76)",
        titlebar_button="rgba(255, 255, 255, 0.07)",
        theme_tag_bg="rgba(136, 195, 154, 0.16)",
        theme_tag_border="rgba(136, 195, 154, 0.32)",
        line="rgba(190, 224, 197, 0.22)",
        line_soft="rgba(190, 224, 197, 0.12)",
        star_soft="rgba(237, 252, 240, 0.32)",
        star_strong="rgba(244, 255, 244, 0.86)",
        scrollbar_handle="rgba(237, 252, 240, 0.34)",
        scrollbar_handle_hover="rgba(244, 255, 244, 0.58)",
        icon_color="#e8fce8",
        light_surface="rgba(255, 255, 255, 0.05)",
    ),
    ThemeProfile(
        id="ocean_milkyway",
        name="海雾银河",
        tagline="海面倒影与银河冷光，适合沉浸式排程",
        accent="#81cfe2",
        accent_strong="#effcff",
        accent_soft="rgba(129, 207, 226, 0.16)",
        brass="#d6cbab",
        success="#8fd0c0",
        warning="#d8c28d",
        danger="#d7a2aa",
        text_primary="#f1fdff",
        text_secondary="#d8f0f4",
        text_muted="#a7c5cf",
        text_dim="#7e9ca7",
        sky_top="#071722",
        sky_mid="#10354a",
        sky_bottom="#1f5572",
        panel_top="#0b1721",
        panel_bottom="#123042",
        panel_edge="#81cfe2",
        glass="rgba(255, 255, 255, 0.04)",
        field_fill="rgba(8, 23, 32, 0.82)",
        field_fill_hover="rgba(13, 31, 43, 0.92)",
        field_border="rgba(185, 233, 242, 0.22)",
        field_border_focus="rgba(239, 252, 255, 0.60)",
        button_fill="rgba(12, 34, 46, 0.94)",
        button_fill_hover="rgba(17, 47, 64, 0.98)",
        button_fill_active="#2a7b90",
        window_overlay_top="#06131b",
        window_overlay_bottom="#173b52",
        titlebar_surface="rgba(8, 22, 30, 0.76)",
        titlebar_button="rgba(255, 255, 255, 0.08)",
        theme_tag_bg="rgba(129, 207, 226, 0.16)",
        theme_tag_border="rgba(129, 207, 226, 0.32)",
        line="rgba(192, 235, 244, 0.22)",
        line_soft="rgba(192, 235, 244, 0.12)",
        star_soft="rgba(235, 252, 255, 0.34)",
        star_strong="rgba(241, 253, 255, 0.88)",
        scrollbar_handle="rgba(235, 252, 255, 0.36)",
        scrollbar_handle_hover="rgba(241, 253, 255, 0.60)",
        icon_color="#e4fbff",
        light_surface="rgba(255, 255, 255, 0.05)",
    ),
    ThemeProfile(
        id="starlight_parchment",
        name="纸月微光",
        tagline="偏暖中性色，参考移动端卡片式柔和明亮表现",
        accent="#bda77c",
        accent_strong="#fffaf0",
        accent_soft="rgba(189, 167, 124, 0.16)",
        brass="#dcc8a0",
        success="#9ac9ad",
        warning="#d3b06c",
        danger="#d7a1a2",
        text_primary="#fffaf3",
        text_secondary="#efe4d3",
        text_muted="#beaf95",
        text_dim="#93856d",
        sky_top="#1f1b18",
        sky_mid="#3a3127",
        sky_bottom="#625345",
        panel_top="#221d17",
        panel_bottom="#352b22",
        panel_edge="#bda77c",
        glass="rgba(255, 255, 255, 0.06)",
        field_fill="rgba(29, 24, 18, 0.78)",
        field_fill_hover="rgba(39, 31, 22, 0.88)",
        field_border="rgba(232, 217, 187, 0.22)",
        field_border_focus="rgba(255, 250, 240, 0.60)",
        button_fill="rgba(50, 40, 27, 0.92)",
        button_fill_hover="rgba(66, 53, 35, 0.96)",
        button_fill_active="#7a6647",
        window_overlay_top="#191510",
        window_overlay_bottom="#43392f",
        titlebar_surface="rgba(29, 24, 18, 0.76)",
        titlebar_button="rgba(255, 255, 255, 0.08)",
        theme_tag_bg="rgba(189, 167, 124, 0.18)",
        theme_tag_border="rgba(189, 167, 124, 0.34)",
        line="rgba(234, 221, 195, 0.22)",
        line_soft="rgba(234, 221, 195, 0.12)",
        star_soft="rgba(255, 248, 235, 0.30)",
        star_strong="rgba(255, 250, 243, 0.84)",
        scrollbar_handle="rgba(255, 248, 235, 0.32)",
        scrollbar_handle_hover="rgba(255, 250, 243, 0.56)",
        icon_color="#f5ead4",
        light_surface="rgba(255, 255, 255, 0.06)",
    ),
    ThemeProfile(
        id="polar_night",
        name="极夜云穹",
        tagline="深海蓝黑与冷白反差，适合信息密集工作流",
        accent="#8db7ff",
        accent_strong="#e8f2ff",
        accent_soft="rgba(141, 183, 255, 0.18)",
        brass="#d7c9ad",
        success="#92ccb5",
        warning="#d4bf90",
        danger="#d89ea7",
        text_primary="#eef5ff",
        text_secondary="#d8e4f5",
        text_muted="#9fb1c9",
        text_dim="#7889a2",
        sky_top="#040913",
        sky_mid="#0a1730",
        sky_bottom="#10264c",
        panel_top="#07101f",
        panel_bottom="#0d1b35",
        panel_edge="#8db7ff",
        glass="rgba(255, 255, 255, 0.04)",
        field_fill="rgba(7, 14, 28, 0.84)",
        field_fill_hover="rgba(10, 19, 37, 0.92)",
        field_border="rgba(179, 208, 255, 0.22)",
        field_border_focus="rgba(232, 242, 255, 0.62)",
        button_fill="rgba(11, 22, 42, 0.96)",
        button_fill_hover="rgba(16, 31, 57, 0.98)",
        button_fill_active="#315a9a",
        window_overlay_top="#040810",
        window_overlay_bottom="#0f2141",
        titlebar_surface="rgba(7, 14, 28, 0.78)",
        titlebar_button="rgba(255, 255, 255, 0.08)",
        theme_tag_bg="rgba(141, 183, 255, 0.16)",
        theme_tag_border="rgba(141, 183, 255, 0.32)",
        line="rgba(197, 217, 247, 0.22)",
        line_soft="rgba(197, 217, 247, 0.12)",
        star_soft="rgba(230, 240, 255, 0.38)",
        star_strong="rgba(238, 245, 255, 0.92)",
        scrollbar_handle="rgba(230, 240, 255, 0.36)",
        scrollbar_handle_hover="rgba(238, 245, 255, 0.66)",
        icon_color="#deecff",
        light_surface="rgba(255, 255, 255, 0.05)",
    ),
)


BACKGROUND_VARIANTS: tuple[BackgroundVariant, ...] = (
    BackgroundVariant(
        id="galaxy_ridge",
        title="星脊",
        subtitle="银河带横贯天顶，山脊压低在远处。",
        motif="galaxy",
        accent_bias="#ffffff",
        secondary_bias="#a4d8ff",
        mist_ratio=0.12,
        star_density=180,
        horizon_ratio=0.78,
        glow_ratio=0.18,
    ),
    BackgroundVariant(
        id="aurora_veil",
        title="极光",
        subtitle="柔和色幕从画面上方垂落，不制造突兀断层。",
        motif="aurora",
        accent_bias="#b6ffe8",
        secondary_bias="#d7d4ff",
        mist_ratio=0.18,
        star_density=130,
        horizon_ratio=0.74,
        glow_ratio=0.28,
    ),
    BackgroundVariant(
        id="ocean_reflection",
        title="海镜",
        subtitle="下半部分保留平静倒影，适合柔和文字阅读。",
        motif="ocean",
        accent_bias="#b7e8ff",
        secondary_bias="#ffe2c3",
        mist_ratio=0.10,
        star_density=120,
        horizon_ratio=0.66,
        glow_ratio=0.20,
    ),
    BackgroundVariant(
        id="mountain_haze",
        title="山岚",
        subtitle="层叠山体与雾气叠加，参考移动端卡片氛围。",
        motif="mountain",
        accent_bias="#cce6ff",
        secondary_bias="#ffe7dd",
        mist_ratio=0.22,
        star_density=105,
        horizon_ratio=0.70,
        glow_ratio=0.16,
    ),
    BackgroundVariant(
        id="cloud_swell",
        title="云海",
        subtitle="云层抬升主体区域，增强底部卡片的层次承托。",
        motif="cloud",
        accent_bias="#fff3df",
        secondary_bias="#d6e7ff",
        mist_ratio=0.24,
        star_density=90,
        horizon_ratio=0.72,
        glow_ratio=0.24,
    ),
)


def default_theme_id() -> str:
    return THEME_PROFILES[0].id


def list_theme_profiles() -> tuple[ThemeProfile, ...]:
    return THEME_PROFILES


def get_theme_profile(theme_id: str | None) -> ThemeProfile:
    if not theme_id:
        return THEME_PROFILES[0]
    for profile in THEME_PROFILES:
        if profile.id == theme_id:
            return profile
    return THEME_PROFILES[0]


def list_background_variants() -> tuple[BackgroundVariant, ...]:
    return BACKGROUND_VARIANTS


def _filename_for(theme_id: str, variant_id: str) -> str:
    if theme_id == "orion_blue" and variant_id == "galaxy_ridge":
        return "0b4e678caa19b088b4e665ea3a7c4582.jpg"
    return f"{theme_id}_{variant_id}.jpg"


@lru_cache(maxsize=1)
def list_background_specs() -> tuple[BackgroundSpec, ...]:
    specs: list[BackgroundSpec] = []
    for theme in THEME_PROFILES:
        for variant in BACKGROUND_VARIANTS:
            specs.append(
                BackgroundSpec(
                    id=f"{theme.id}_{variant.id}",
                    theme_id=theme.id,
                    theme_name=theme.name,
                    variant_id=variant.id,
                    title=f"{theme.name} · {variant.title}",
                    subtitle=variant.subtitle,
                    motif=variant.motif,
                    filename=_filename_for(theme.id, variant.id),
                    sky_top=mix_hex(theme.sky_top, variant.secondary_bias, 0.10),
                    sky_mid=mix_hex(theme.sky_mid, variant.accent_bias, 0.12),
                    sky_bottom=mix_hex(theme.sky_bottom, variant.secondary_bias, 0.14),
                    accent_primary=mix_hex(theme.accent, variant.accent_bias, 0.30),
                    accent_secondary=mix_hex(theme.brass, variant.secondary_bias, 0.32),
                    glow_color=mix_hex(theme.accent, "#ffffff", variant.glow_ratio),
                    horizon_color=mix_hex(theme.sky_bottom, variant.secondary_bias, variant.horizon_ratio),
                    mist_ratio=variant.mist_ratio,
                    star_density=variant.star_density,
                    line_tint=mix_hex(theme.panel_edge, variant.accent_bias, 0.25),
                    text_primary=theme.text_primary,
                    text_secondary=theme.text_secondary,
                )
            )
    return tuple(specs)


def get_background_spec(background_id: str | None) -> BackgroundSpec:
    specs = list_background_specs()
    if background_id:
        for spec in specs:
            if spec.id == background_id:
                return spec
    return specs[0]


def list_backgrounds_for_theme(theme_id: str | None) -> tuple[BackgroundSpec, ...]:
    theme_key = get_theme_profile(theme_id).id
    return tuple(spec for spec in list_background_specs() if spec.theme_id == theme_key)


def default_background_for_theme(theme_id: str | None) -> str:
    return list_backgrounds_for_theme(theme_id)[0].id


def background_path(background_id: str | None) -> Path:
    spec = get_background_spec(background_id)
    return wallpaper_root() / spec.filename


def available_background_paths() -> dict[str, Path]:
    return {spec.id: wallpaper_root() / spec.filename for spec in list_background_specs()}


def theme_background_count(theme_id: str | None) -> int:
    return len(list_backgrounds_for_theme(theme_id))


def theme_preview_swatches(theme_id: str | None) -> tuple[str, str, str, str]:
    profile = get_theme_profile(theme_id)
    return (
        profile.accent,
        profile.brass,
        mix_hex(profile.sky_mid, profile.accent, 0.40),
        mix_hex(profile.sky_bottom, profile.success, 0.34),
    )


def scene_palette_for_theme(theme: ThemeProfile) -> ScenePalette:
    return ScenePalette(
        panel_bg=rgba(theme.panel_bottom, 230),
        panel_text=theme.text_primary,
        panel_text_soft=theme.text_secondary,
        panel_muted=theme.text_muted,
        panel_border=rgba(theme.panel_edge, 50),
        input_bg=theme.field_fill,
        input_text=theme.text_primary,
        input_border=rgba(theme.panel_edge, 46),
        overlay=rgba(theme.sky_top, 165),
        frame_border=rgba(theme.panel_edge, 66),
        view_text=theme.text_secondary,
        view_active_text=theme.text_primary,
        titlebar_bg=rgba(theme.window_overlay_top, 24),
        titlebar_surface=theme.titlebar_surface,
        titlebar_button=theme.titlebar_button,
        titlebar_button_hover=rgba(theme.accent, 36),
        theme_tag_bg=theme.theme_tag_bg,
        theme_tag_border=theme.theme_tag_border,
        dialog_bg=theme.panel_top,
        composer_bg=theme.panel_bottom,
        btn_primary_start=theme.accent,
        btn_primary_end=mix_hex(theme.accent, theme.brass, 0.30),
        btn_primary_hover_start=mix_hex(theme.accent, "#ffffff", 0.16),
        btn_primary_hover_end=mix_hex(theme.brass, "#ffffff", 0.18),
        btn_primary_border=rgba(theme.accent, 110),
        btn_secondary_bg=theme.light_surface,
        btn_secondary_border=rgba(theme.accent, 90),
        calendar_text=theme.text_primary,
        calendar_disabled=theme.text_dim,
        header_text=theme.text_muted,
        icon_color=theme.icon_color,
        scrollbar_handle=theme.scrollbar_handle,
        scrollbar_handle_hover=theme.scrollbar_handle_hover,
        selection_bg=theme.accent_soft,
        checkbox_border=rgba(theme.panel_edge, 88),
        card_secondary_bg=theme.light_surface,
        card_secondary_border=rgba(theme.accent, 80),
    )


def starry_palette_for_theme(theme: ThemeProfile) -> StarryPalette:
    return StarryPalette(
        sky_top=theme.sky_top,
        sky_bottom=theme.sky_bottom,
        panel_top=theme.panel_top,
        panel_bottom=theme.panel_bottom,
        panel_edge=rgba(theme.panel_edge, 55),
        panel_edge_soft=rgba(theme.panel_edge, 28),
        line=theme.line,
        line_soft=theme.line_soft,
        text_primary=theme.text_primary,
        text_secondary=theme.text_secondary,
        text_muted=theme.text_muted,
        text_dim=theme.text_dim,
        accent=theme.accent,
        accent_strong=theme.accent_strong,
        accent_soft=theme.accent_soft,
        accent_line=rgba(theme.accent, 120),
        brass=theme.brass,
        brass_soft=rgba(theme.brass, 42),
        success=theme.success,
        warning=theme.warning,
        danger=theme.danger,
        glass=theme.glass,
        field_fill=theme.field_fill,
        field_fill_hover=theme.field_fill_hover,
        field_border=theme.field_border,
        field_border_focus=theme.field_border_focus,
        button_fill=theme.button_fill,
        button_fill_hover=theme.button_fill_hover,
        button_fill_active=theme.button_fill_active,
        scroll_handle=theme.scrollbar_handle,
        scroll_handle_hover=theme.scrollbar_handle_hover,
        overlay=rgba(theme.window_overlay_top, 180),
        star_soft=theme.star_soft,
        star_strong=theme.star_strong,
        separator=rgba(theme.panel_edge, 36),
    )


def theme_story_lines(theme_id: str | None) -> tuple[str, str, str]:
    profile = get_theme_profile(theme_id)
    return (
        f"主题重心：{profile.tagline}",
        f"主色倾向：{profile.accent} 与 {profile.brass} 做柔和过渡，不使用突兀高饱和撞色。",
        f"阅读策略：正文使用 {profile.text_primary} / {profile.text_secondary}，弱化信息使用 {profile.text_muted}。",
    )


def theme_metric_items(theme_id: str | None) -> tuple[tuple[str, str], ...]:
    theme = get_theme_profile(theme_id)
    return (
        ("背景组数", str(theme_background_count(theme.id))),
        ("信息对比", "柔和高可读"),
        ("按钮风格", "低饱和渐变"),
        ("弹窗基调", theme.name),
    )


def iter_theme_background_pairs() -> Iterable[tuple[ThemeProfile, tuple[BackgroundSpec, ...]]]:
    for theme in THEME_PROFILES:
        yield theme, list_backgrounds_for_theme(theme.id)